# utils_stackdaddy.py

import json
import os
from datetime import datetime

INVENTORY_FILE = "data/inventory.json"
MEALPLAN_FILE = "data/mealplan.json"

def load_json(filepath, default):
    if not os.path.exists(filepath):
        return default
    with open(filepath, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return default

def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

def get_inventory():
    return load_json(INVENTORY_FILE, {})

def update_inventory(supplement, amount):
    inventory = get_inventory()
    inventory[supplement] = inventory.get(supplement, 0) + amount
    save_json(INVENTORY_FILE, inventory)

def get_meal_plan():
    return load_json(MEALPLAN_FILE, {
        "breakfast": [],
        "lunch": [],
        "dinner": []
    })

def update_meal_plan(meal, items):
    plan = get_meal_plan()
    plan[meal] = items
    save_json(MEALPLAN_FILE, plan)

def generate_shopping_list():
    plan = get_meal_plan()
    inventory = get_inventory()
    shopping_list = {}

    all_items = plan["breakfast"] + plan["lunch"] + plan["dinner"]
    for item in all_items:
        if inventory.get(item, 0) <= 0:
            shopping_list[item] = shopping_list.get(item, 0) + 1

    return shopping_list

def send_daily_reminder(context):
    job = context.job
    context.bot.send_message(
        chat_id=job.chat_id,
        text="🕘 Time for your daily supplements! Tap below to log them.",
        reply_markup=main_menu_keyboard()
    )

# Imported late to prevent circular import
from keyboard import main_menu_keyboard
