import json
import os
from datetime import datetime, timedelta

MEALS_FILE = "data/meals.json"
GROCERY_LIST_FILE = "data/grocery_list.json"
MAX_WEEKS = 4

def ensure_data_folder():
    if not os.path.exists("data"):
        os.makedirs("data")

def load_meals():
    ensure_data_folder()
    if os.path.exists(MEALS_FILE):
        with open(MEALS_FILE, "r") as f:
            return json.load(f)
    return {"weeks": [], "current_index": 0}

def save_meals(data):
    ensure_data_folder()
    with open(MEALS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_meals(week_meals):
    data = load_meals()
    if len(data["weeks"]) >= MAX_WEEKS:
        data["weeks"].pop(0)
    data["weeks"].append(week_meals)
    save_meals(data)

def rotate_weekly_meals():
    data = load_meals()
    if not data["weeks"]:
        return None  # No meals available
    data["current_index"] = (data["current_index"] + 1) % len(data["weeks"])
    save_meals(data)
    return data["weeks"][data["current_index"]]

def get_current_week_meals():
    data = load_meals()
    if not data["weeks"]:
        return []
    return data["weeks"][data["current_index"]]

def generate_flat_grocery_list():
    meals = get_current_week_meals()
    ingredients = set()
    for meal in meals:
        for item in meal.get("ingredients", []):
            ingredients.add(item.strip())
    return sorted(list(ingredients))

def save_grocery_list():
    ensure_data_folder()
    grocery_items = generate_flat_grocery_list()
    checklist = [{"item": i, "checked": False} for i in grocery_items]
    with open(GROCERY_LIST_FILE, "w") as f:
        json.dump(checklist, f, indent=2)

def load_grocery_list():
    ensure_data_folder()
    if os.path.exists(GROCERY_LIST_FILE):
        with open(GROCERY_LIST_FILE, "r") as f:
            return json.load(f)
    return []
