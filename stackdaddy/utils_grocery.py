# utils_grocery.py

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from utils_mealplan import load_mealplan_data

GROCERY_FILE = "grocery_checklist.json"
INGREDIENTS_DB = "ingredients_by_meal.json"  # Maps meals to ingredients

# Load mapping of meals to ingredients
def load_meal_ingredients():
    if os.path.exists(INGREDIENTS_DB):
        with open(INGREDIENTS_DB, "r") as f:
            return json.load(f)
    return {}

# Get current week's date range
def get_current_week_dates():
    today = datetime.now()
    start = today - timedelta(days=today.weekday())  # Monday
    return [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

# Build grocery list from meals scheduled for the current week
def get_weekly_grocery_list(user_id):
    mealplan = load_mealplan_data()
    meal_ingredients = load_meal_ingredients()
    user_id = str(user_id)
    week_dates = get_current_week_dates()

    ingredients = defaultdict(int)

    if user_id in mealplan:
        for date in week_dates:
            meals = mealplan[user_id].get(date, [])
            for meal in meals:
                for ingredient in meal_ingredients.get(meal, []):
                    ingredients[ingredient] += 1

    return sorted(ingredients.keys())

# File-based toggle and tracking
def load_checked_status(user_id):
    if os.path.exists(GROCERY_FILE):
        with open(GROCERY_FILE, "r") as f:
            data = json.load(f)
            return data.get(str(user_id), {})
    return {}

def save_checked_status(user_id, status):
    data = {}
    if os.path.exists(GROCERY_FILE):
        with open(GROCERY_FILE, "r") as f:
            data = json.load(f)
    data[str(user_id)] = status
    with open(GROCERY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def toggle_item_checked(user_id, item):
    user_id = str(user_id)
    status = load_checked_status(user_id)
    status[item] = not status.get(item, False)
    save_checked_status(user_id, status)
