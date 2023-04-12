import os
from collections import OrderedDict
from copy import deepcopy
DAY_MIN = 16*60


def load_planning_json(json_path):
    with open(json_path) as infile:
        planning_dict = json.load(infile) 

    return planning_dict

def validate_planning_json(planning):

    if "known_activities" not in planning:
        print("No activities records")
        return False
    activities = len(planning["known_activities"].keys())
    print(f"Activities: {activities}")

    if "cycles" not in planning:
        print("Cycles are not defined")
        return False
    cycles = len(planning["cycles"].keys())
    print(f"Cycles: {cycles}")

    for cycle in planning["cycles"]:
        for action in planning["cycles"][cycle]:
            if action not in planning["known_activities"]:
                print(f"Action {action} are not known")
                return False

    return True

def traverse_cycle(planning, cycle_name):
    for activity in planning["cycles"][cycle_name]:
        yield activity

def cycle_estimation(planning, cycle_name):
    total_time = 0
    for activity in traverse_cycle(planning, cycle_name):
        total_time += planning["known_activities"][activity]["time_estem"]
    return total_time

def produce_daily_list_by_schema(planning_dict, daily_schema):
    #daily_list = []
    daily_list = OrderedDict()
    for i, cycle in enumerate(daily_schema):
        for activity in planning_dict["cycles"][cycle]:
            cycle_index = str(i).rjust(2, "0") + cycle

            if cycle_index not in daily_list:
                daily_list[cycle_index] = []

            daily_list[cycle_index].append([activity, deepcopy(planning_dict["known_activities"][activity])])
    return daily_list

