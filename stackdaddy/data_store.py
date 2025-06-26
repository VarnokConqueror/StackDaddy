# data_store.py

import json
import os

DATA_FOLDER = "data"
MEALPLAN_FILE = os.path.join(DATA_FOLDER, "mealplan.json")
INVENTORY_FILE = os.path.join(DATA_FOLDER, "supplement_inventory.json")
DOSELOG_FILE = os.path.join(DATA_FOLDER, "dose_log.json")

def ensure_data_folder():
    os.makedirs(DATA_FOLDER, exist_ok=True)

def save_json(data, path):
    ensure_data_folder()
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def load_json(path, fallback=None):
    if not os.path.exists(path):
        return fallback if fallback is not None else {}
    with open(path, "r") as f:
        return json.load(f)

def get_mealplan():
    return load_json(MEALPLAN_FILE, fallback={"breakfast": "", "lunch": "", "dinner": ""})

def save_mealplan(plan):
    save_json(plan, MEALPLAN_FILE)

def get_inventory():
    return load_json(INVENTORY_FILE, fallback={})

def save_inventory(inventory):
    save_json(inventory, INVENTORY_FILE)

def get_dose_log():
    return load_json(DOSELOG_FILE, fallback={"AM": False, "PM": False})

def save_dose_log(log):
    save_json(log, DOSELOG_FILE)
