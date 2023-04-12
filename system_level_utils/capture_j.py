import pyautogui as pya
#import pyperclip
import os
import csv
import time
from tkinter import Tk

TARGET = "EXTRACT"

def save_buffer(data):
    target_path = os.path.join("/mnt/X/WORKSHOP/Scripts/dash/system_level_utils", TARGET+".csv")

    with open(target_path, "a") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(["***"])
        for line in data.split("\n"):
            writer.writerow([line])

def copy_clipboard():
    root = Tk()
    root.withdraw()
    #pya.hotkey('ctrl', 'c')
    #time.sleep(.2)
    return root.clipboard_get() 

var = copy_clipboard()
save_buffer(var)
