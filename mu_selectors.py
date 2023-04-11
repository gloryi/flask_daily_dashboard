import wikipediaapi
import json
import os

wiki_wiki = wikipediaapi.Wikipedia('en')


def extract_links(page, urlify):
    links = page.links
    links_titles_list = []
    for title in sorted(links.keys()):
        if not urlify:
            links_titles_list.append(title)
        else:
            links_titles_list.append(f"https://en.wikipedia.org/wiki/{title}")
    return links_titles_list


def validate_page(page):
    categories = page.categories
    for title in sorted(categories.keys()):
        if "music" in title.lower():
            return True
    return False


def parse_in_depth(index_page):
    title_pages = extract_links(wiki_wiki.page(index_page), urlify=False)

    resulting = {"offlist": []}

    for title_page in title_pages:
        page_references = extract_links(
            wiki_wiki.page(title_page), urlify=False)

        lists_found = False

        for reference in page_references:
            if "list of" in reference.lower() and "/" not in reference:
                lists_found = True
                resulting_list = parse_wiki_list(reference, urlify=False)
                if not resulting_list:
                    continue
                resulting[f"{title_page} | {reference}"] = resulting_list

        if not lists_found:
            resulting["offlist"].append(
                f"https://en.wikipedia.org/wiki/{title_page}")
    return resulting


def parse_wiki_list(page_name, urlify=False, validate=True):
    composers_id = page_name
    cache_file = os.path.join(os.getcwd(), "mu", composers_id + ".json")

    page_composers = ""

    if not os.path.exists(cache_file):
        page_composers = wiki_wiki.page(composers_id)
        if validate and not validate_page(page_composers):
            return None

        target_list = extract_links(page_composers, urlify)

        with open(cache_file, "w", encoding="UTF-8") as dumpfile:
            json.dump({"list": target_list}, dumpfile)

    with open(cache_file, "r", encoding="UTF-8") as dumpfile:
        target_list = json.load(dumpfile)

    return target_list["list"]


def from_directory(dir_path):
    parsed_dict = {}
    for _r, _d, _f in os.walk(dir_path):
        for f in _f:
            if ".json" in f:
                full_path = os.path.join(_r, f)
                with open(full_path) as mufile:
                    genre_id = f.replace(".json", "")
                    loaded = json.load(mufile)["list"]
                    mulist = [_ for _ in loaded if "List of" not in _]
                    if mulist:
                        parsed_dict[genre_id] = mulist
        return parsed_dict
