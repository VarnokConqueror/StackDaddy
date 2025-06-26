# grocery_checklist.py

import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

GROCERY_FILE = "grocery_checklist.json"

def load_grocery_data():
    if os.path.exists(GROCERY_FILE):
        with open(GROCERY_FILE, "r") as f:
            return json.load(f)
    return {"items": []}

def save_grocery_data(data):
    with open(GROCERY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def generate_checklist_from_meals(meal_data):
    all_ingredients = set()
    for meal in meal_data.values():
        for item in meal["ingredients"]:
            all_ingredients.add(item)
    checklist = [{"item": i, "checked": False} for i in sorted(all_ingredients)]
    save_grocery_data({"items": checklist})

def format_checklist():
    data = load_grocery_data()
    if not data["items"]:
        return "No items in your grocery list."
    return "\n".join(
        f"[{'✅' if item['checked'] else '❌'}] {item['item']}" for item in data["items"]
    )

def build_checklist_buttons():
    data = load_grocery_data()
    buttons = []
    for i, item in enumerate(data["items"]):
        label = f"{'✅' if item['checked'] else '❌'} {item['item']}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"toggle_{i}")])
    return InlineKeyboardMarkup(buttons)

async def show_grocery_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛒 Grocery Checklist:\n\n" + format_checklist(),
        reply_markup=build_checklist_buttons()
    )

async def toggle_checklist_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    index = int(query.data.replace("toggle_", ""))
    data = load_grocery_data()
    if 0 <= index < len(data["items"]):
        data["items"][index]["checked"] = not data["items"][index]["checked"]
        save_grocery_data(data)
        await query.edit_message_text(
            text="🛒 Grocery Checklist:\n\n" + format_checklist(),
            reply_markup=build_checklist_buttons()
        )
