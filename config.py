import os
#  DAILY_PLAN = ["morning", "midday", "evening"]
#  PLANNING_SCHEMA = "__daily_example.json"

DAILY_PLAN = ["morning", "working", "working", "learning",
                "learning", "midday", "learning", "learning",
                "learning", "evening"]
DAILY_PLAN = ["morning", "special", "special", "special",
                "midday", "special", "special",
                "special", "special", "evening", "unplanned"]
PLANNING_SCHEMA = "daily.json"


def list_images(target_directory):
    selected_files = []
    for _r, _d, _f in os.walk(target_directory):
        for f in _f:
            selected_files.append(os.path.join(_r, f))
    return selected_files


IMAGES_MINOR_DIR = os.path.join("/home/gloryi/Pictures/Lightning")
RANDOM_BACKGORUNDS = list_images(IMAGES_MINOR_DIR)
