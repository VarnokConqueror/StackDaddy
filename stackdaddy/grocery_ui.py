# grocery_ui.py

import os
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from utils_mealplan import get_all_ingredients_flat

GROCERY_FILE = "grocery_checklist.json"

def load_checklist():
    if os.path.exists(GROCERY_FILE):
        with open(GROCERY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_checklist(data):
    with open(GROCERY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_user_checklist(user_id):
    return load_checklist().get(str(user_id), {})

def toggle_item(user_id, item):
    data = load_checklist()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {}
    data[uid][item] = not data[uid].get(item, False)
    save_checklist(data)

def clear_checklist(user_id):
    data = load_checklist()
    uid = str(user_id)
    data[uid] = {}
    save_checklist(data)

def populate_checklist_from_mealplan(user_id):
    ingredients = get_all_ingredients_flat()
    data = load_checklist()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {}
    for item in ingredients:
        if item not in data[uid]:
            data[uid][item] = False
    save_checklist(data)

def build_checklist_keyboard(user_id):
    checklist = get_user_checklist(user_id)
    if not checklist:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📥 Load from Meal Plan", callback_data="populate_checklist")]
        ])

    keyboard = []
    for item in sorted(checklist):
        status = "✅" if checklist[item] else "⬜"
        keyboard.append([InlineKeyboardButton(f"{status} {item}", callback_data=f"toggle_{item}")])

    keyboard.append([
        InlineKeyboardButton("📥 Reload from Meal Plan", callback_data="populate_checklist"),
        InlineKeyboardButton("🗑 Clear All", callback_data="clear_checklist")
    ])

    return InlineKeyboardMarkup(keyboard)

async def show_grocery_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query or update.message
    user_id = update.effective_user.id

    if query.message:
        await query.reply_text(
            "🛒 Grocery Checklist:\n\nTap an item to check or uncheck it.",
            reply_markup=build_checklist_keyboard(user_id)
        )
    else:
        await query.answer()
        await query.edit_message_text(
            "🛒 Grocery Checklist:\n\nTap an item to check or uncheck it.",
            reply_markup=build_checklist_keyboard(user_id)
        )

async def handle_toggle_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    item = query.data.replace("toggle_", "")
    toggle_item(user_id, item)
    await query.answer()
    await query.edit_message_reply_markup(reply_markup=build_checklist_keyboard(user_id))

async def handle_special_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    action = query.data

    if action == "populate_checklist":
        populate_checklist_from_mealplan(user_id)
        await query.answer("Checklist updated from meal plan!")
    elif action == "clear_checklist":
        clear_checklist(user_id)
        await query.answer("Checklist cleared!")

    await query.edit_message_reply_markup(reply_markup=build_checklist_keyboard(user_id))
