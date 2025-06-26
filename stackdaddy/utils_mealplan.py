# utils_mealplan.py

import json
import os
from datetime import datetime

MEALPLAN_FILE = "mealplan_data.json"

def load_mealplan_data():
    if os.path.exists(MEALPLAN_FILE):
        with open(MEALPLAN_FILE, "r") as f:
            return json.load(f)
    return {}

def save_mealplan_data(data):
    with open(MEALPLAN_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_today():
    return datetime.now().strftime("%Y-%m-%d")

def get_user_mealplan(user_id):
    data = load_mealplan_data()
    return data.get(str(user_id), {}).get(get_today(), [])

def add_meal_to_plan(user_id, meal_name, ingredients):
    data = load_mealplan_data()
    uid = str(user_id)
    today = get_today()

    if uid not in data:
        data[uid] = {}
    if today not in data[uid]:
        data[uid][today] = []

    meal_entry = {
        "name": meal_name,
        "ingredients": ingredients
    }

    data[uid][today].append(meal_entry)
    save_mealplan_data(data)

def clear_today_meals(user_id):
    data = load_mealplan_data()
    uid = str(user_id)
    today = get_today()
    if uid in data and today in data[uid]:
        data[uid][today] = []
        save_mealplan_data(data)

def format_mealplan(meals):
    if not meals:
        return "No meals logged today."

    lines = []
    for meal in meals:
        name = meal["name"]
        ingredients = ", ".join(meal["ingredients"])
        lines.append(f"🍽 {name} ({ingredients})")

    return "\n".join(lines)

def get_all_ingredients_flat():
    data = load_mealplan_data()
    ingredients = set()

    for user_meals in data.values():
        for day_meals in user_meals.values():
            for meal in day_meals:
                if isinstance(meal, dict) and "ingredients" in meal:
                    ingredients.update(meal["ingredients"])

    return sorted(ingredients)
