import random
import os

from flask import Flask, request, render_template, url_for, session, redirect, flash
from flask import send_file
from PIL import Image
import io

from mu_selectors import parse_wiki_list, parse_in_depth, from_directory
import daily_processor
from datetime import datetime
import json
from itertools import groupby

from config import DAILY_PLAN
from config import PLANNING_SCHEMA
from config import RANDOM_BACKGORUNDS 
import random
TEST = True
#TEST = False

GROUP_REPORT = True
SORT_BY_TOTAL = True
SORT_BY_AVG = False
SORT_BY_N = False

app = Flask(__name__)


@app.route("/")
def index():
    return render_template('index.html')


mu_local_cached = None
mu_global_cached = None

daily_loaded = []

dt = datetime.now()
DATEFORMAT_UNIV = '%d/%m/%y %H:%M:%S.%f'
DATEFORMAT_REPT = '%y%b%d'

TMTS = lambda _ : _.strftime(DATEFORMAT_UNIV)
STTM = lambda _ : datetime.strptime(_, DATEFORMAT_UNIV)
TMTSR = lambda _ : _.strftime(DATEFORMAT_REPT)
STTMR = lambda _ : datetime.strptime(_, DATEFORMAT_REPT)

OPTIMAL_WAKE = TMTS(datetime.now().replace(hour=7, minute=0))
OPTIMAL_SLEEP = TMTS(datetime.now().replace(hour=23, minute=55))

BINARY_FLAGS = {}
BINARY_FLAGS["group_activities"] = False
BINARY_FLAGS["sort_activities"] = False

daily_stack_activities = []
daily_stack_formatted = []
daily_stack_cycles = []
#  daily_marked = []
#  daily_rest = []

def load_daily():
    global daily_loaded
    if not daily_loaded:
        planning_dict = daily_processor.load_planning_json(PLANNING_SCHEMA)

        daily_list = daily_processor.produce_daily_list_by_schema(planning_dict,
                DAILY_PLAN)
        daily_loaded = daily_list

def produce_daily_labels():
    load_daily()
    label = lambda _: _[0]
    time = lambda _ : _[1]["time_estem"]
    marked_check = lambda _ : "marked" in _[1] and _[1]["marked"]
    marked_label = lambda _ : f"{label(_)} [{time(_)}]" if not marked_check(_) else f"{label(_)}"
    #  global daily_marked
    #  global daily_rest
    labels_list = []
    rest_list = []
    cummulative_time = 0
    cummulative_used = 0
    prev_label = ""
    for cycle_index in daily_loaded:
        total_time = sum(time(_) for _ in daily_loaded[cycle_index] if not marked_check(_))
        used_time = sum(time(_) for _ in daily_loaded[cycle_index] if marked_check(_))
        estimate_time = sum(time(_) for _ in daily_loaded[cycle_index])

        cummulative_time += total_time
        cummulative_used += used_time
        rel_time = int(total_time/estimate_time*100)
        rel_cum = int(total_time/(60*17)*100)
        rel_cum_usd =  int(cummulative_used/(60*17)*100)
        rel_cum_nusd =  int(cummulative_time/(60*17)*100)

        prev_label_valid = prev_label and len(prev_label) > 2 and cycle_index[2:] == prev_label[2:]
        prev_label_marked = not prev_label_valid or all(marked_check(_) for _ in daily_loaded[prev_label])
        curr_label_marked = all(marked_check(_) for _ in daily_loaded[cycle_index])

        if curr_label_marked or not prev_label_marked:
            active_list = rest_list
        else:
            active_list = labels_list

        active_list.append([cycle_index])
        if prev_label_marked:
            active_list[-1] +=  [ [marked_label(_),cycle_index+";"+label(_)+";"+str(i),marked_check(_)] for (i,_) in enumerate(daily_loaded[cycle_index]) ]
        active_list[-1] +=  [str(total_time)+"m " + str(rel_time) + "% | " + str(rel_cum) + "%" + f" [{rel_cum_nusd}]"]

        prev_label = cycle_index

    return labels_list, rest_list, cummulative_used


def prepare_mu_rec():
    global mu_local_cached
    global mu_global_cached
    if not mu_local_cached or not mu_global_cached:

        genre = {}
        genre["Classical"] = parse_wiki_list('List_of_composers_by_name')
        genre["Opera"] = parse_wiki_list('List_of_operas_by_composer')
        genre["Alternative Metall"] = parse_wiki_list(
            'List_of_alternative_metal_artists')
        genre["Gothic Metall"] = parse_wiki_list(
            'List_of_gothic_rock_artists')

        # genre["Global"] = parse_wiki_list(
        # 'List_of_music_genres_and_styles', urlify=True)

        # all_genres = parse_in_depth("List_of_music_genres_and_styles")
        all_genres = from_directory(os.path.join(os.getcwd(), "mu"))

        mu_local_cached = genre
        mu_global_cached = all_genres

    # genre.update(all_genres)

    selector = random.choice([mu_local_cached, mu_global_cached])

    mu_genre = random.choice(list(selector.keys()))
    mu_band = random.choice(selector[mu_genre])
    rec = mu_genre + " | " + mu_band
    search_string = mu_band.replace(" ","%20")
    fast_link = f"https://soundcloud.com/search?q={search_string}"
    return rec, fast_link

@app.route('/mark/<marked_id>')
def my_view_func(marked_id):
    global daily_loaded
    global daily_stack_activities
    global daily_stack_formatted

    label = lambda _: _[0]
    time = lambda _ : _[1]["time_estem"]
    marked_check = lambda _ : "marked" in _[1] and _[1]["marked"]

    cummulative_time = 0

    target_cycle, target_label, target_ind = marked_id.split(";")
    found = False
    for cycle_index in daily_loaded:
        if found:
            break
        for i, activity in enumerate(daily_loaded[cycle_index]):
            if target_cycle == cycle_index and target_label == label(activity) and str(i) == target_ind:
                if marked_check(activity):
                    activity[1]["marked"] = False
                    daily_stack_activities = list(filter(lambda _ : _[0] != marked_id, daily_stack_activities))
                else:
                    activity[1]["marked"] = True
                    prev_time = OPTIMAL_WAKE if not daily_stack_activities else daily_stack_activities[-1][3]
                    prev_time = datetime.strptime(prev_time, DATEFORMAT_UNIV)
                    curr_time = datetime.now()
                    time_delta = (curr_time - prev_time).seconds/60
                    time_percent = int(time_delta/time(activity)*100)
                    daily_stack_activities.append([marked_id, label(activity),
                                                   time(activity), curr_time.strftime(DATEFORMAT_UNIV),
                                                   time_percent])

                found = True
                break

    if not GROUP_REPORT:
        daily_stack_formatted = daily_stack_activities[::]
    else:
        daily_stack_formatted = []
        sorted_activities = daily_stack_activities[::]
        sorted_activities.sort(key = lambda _ : _[1])
        for group, entries in groupby(sorted_activities, key = lambda _ : _[1]):
            entries = list(entries)
            group_id = group
            label = group
            time_act = entries[0][2]
            last_time = entries[-1][3]
            total = sum(_[4] for _ in entries)*time_act//100
            avg = sum(_[4] for _ in entries)/len(entries)
            n = len(entries)
            time_percent = "Total: " + str(total) +\
                    "m Avg = " + str(avg) + "% N = " + str(n) +"x |"
            time_percent = time_percent.rjust(50, " ")
            daily_stack_formatted.append([group_id, label, time_act, last_time, time_percent, total, avg, n])
        if SORT_BY_TOTAL:
            daily_stack_formatted.sort(key = lambda _ : _[5])
        elif SORT_BY_AVG:
            daily_stack_formatted.sort(key = lambda _ : _[6])
        else:
            daily_stack_formatted.sort(key = lambda _ : _[7])

    return redirect("/mu/")

@app.route("/mu/", methods=["GET"])
def mu():
    '''return random music suggestion'''
    try:
        if not TEST:
            rec, fast_link = prepare_mu_rec()
        else:
            rec, fast_link = "test", "test"
        daily_labels, rest_labels, abs_time_worked_out = produce_daily_labels()
        rel_time = int(abs_time_worked_out/(60*17)*100)
        rel_day = int(((datetime.now()-STTM(OPTIMAL_WAKE)).seconds/(STTM(OPTIMAL_SLEEP)-STTM(OPTIMAL_WAKE)).seconds)*100)
        meta_rel = int(rel_time/rel_day*1000)
        return render_template('mu.html', mu_reccomendation=rec,
                fast_link=fast_link, daily_labels = daily_labels, rest_labels=rest_labels,
                rel_time = rel_time, rel_day=rel_day, meta_rel=meta_rel, daily_stack = daily_stack_formatted)
    except Exception as e:
        print(e)
        return redirect("/mu/")

@app.route("/groupping_flag/", methods=["GET"])
def groupping():
    global GROUP_REPORT
    GROUP_REPORT = False if GROUP_REPORT else True
    return redirect('/mark/RE;FR;ESH')

@app.route("/total_flag/", methods=["GET"])
def total_sort():
    global SORT_BY_TOTAL
    global SORT_BY_AVG
    global SORT_BY_N
    SORT_BY_TOTAL = True
    SORT_BY_AVG = False
    SORT_BY_N = False
    return redirect('/mark/RE;FR;ESH')

@app.route("/average_flag/", methods=["GET"])
def average_sort():
    global SORT_BY_TOTAL
    global SORT_BY_AVG
    global SORT_BY_N
    SORT_BY_TOTAL = False
    SORT_BY_AVG = True
    SORT_BY_N = False
    return redirect('/mark/RE;FR;ESH')

@app.route("/n_flag/", methods=["GET"])
def n_sort():
    global SORT_BY_TOTAL
    global SORT_BY_AVG
    global SORT_BY_N
    SORT_BY_TOTAL = False
    SORT_BY_AVG = False
    SORT_BY_N = True
    return redirect('/mark/RE;FR;ESH')

@app.route('/image')
def prepare_random_image():
    img = Image.open(random.choice(RANDOM_BACKGORUNDS))
    image_io = io.BytesIO()
    img.save(image_io, format='PNG')
    image_io.seek(0)
    return send_file(
        image_io,
        as_attachment=False,
        mimetype='image/png'
    )


@app.route("/save/", methods=["GET"])
def save():
    global daily_loaded
    global daily_stack_activities
    global daily_stack_cycles
    #  global daily_marked
    #  global daily_rest
    
    report = {}
    report["daily_loaded"] = daily_loaded
    report["daily_stack_activities"] = daily_stack_activities
    report["daily_stack_cycles"] = daily_stack_cycles

    with open("report.json", "w") as outfile:
        json.dump(report, outfile, indent=2)

    current_day = STTM(OPTIMAL_WAKE)
    daily_name = TMTSR(current_day)
    with open(os.path.join(os.getcwd(), "reports", daily_name+".json"), "w") as outfile:
        json.dump(report, outfile, indent=2)
    return redirect("/mu/")

@app.route("/load/", methods=["GET"])
def load():
    global daily_loaded
    global daily_stack_activities
    global daily_stack_cycles
    #  global daily_marked
    #  global daily_rest
    
    with open("report.json") as outfile:
        report = json.load(outfile)
        daily_loaded = report["daily_loaded"]
        daily_stack_activities = report["daily_stack_activities"]
        daily_stack_cycles = report["daily_stack_cycles"]
        #  daily_marked = report["daily_marked"]
        #  daily_rest = report["daily_rest"]

    return redirect('/mark/RE;FR;ESH')

if __name__ == '__main__':
    app.secret_key = 'test app secret key'
    app.run(host='0.0.0.0')
