from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import json
import os

INVENTORY_FILE = "inventory.json"
EXPIRATION_WARNING_DAYS = 30  # Show orange icon when expiring within 30 days
LOW_STOCK_THRESHOLD = 3
RESTOCK_AMOUNT = 10

# Load and save helpers
def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        with open(INVENTORY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_inventory(data):
    with open(INVENTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Build inventory UI
def build_inventory_keyboard():
    inventory = load_inventory()
    buttons = []

    for item, info in inventory.items():
        stock = info.get("stock", 0)
        expires_in = info.get("expires_in", 999)
        label = f"{item}: {stock}"

        # Expiration warnings
        if expires_in <= 0:
            label += " 🔥"
        elif expires_in <= EXPIRATION_WARNING_DAYS:
            label += " 🟠"

        # Stock level warnings
        if stock < LOW_STOCK_THRESHOLD:
            label += " 🔴"
        elif stock <= 10:
            label += " ⚠️"
        else:
            label += " ✅"

        buttons.append([
            InlineKeyboardButton(f"➖ {label}", callback_data=f"dec_{item}"),
            InlineKeyboardButton(f"➕", callback_data=f"inc_{item}")
        ])

    buttons.append([InlineKeyboardButton("♻️ Restock Low Stock", callback_data="restock_low")])

    return InlineKeyboardMarkup(buttons)

# Send full inventory UI
async def show_inventory_ui(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    markup = build_inventory_keyboard()
    await query.edit_message_text(
        "📦 Supplement Inventory:\n\nManage stock levels below:",
        reply_markup=markup
    )

# Handle button interactions
async def handle_inventory_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    inventory = load_inventory()

    if data.startswith("inc_"):
        item = data.replace("inc_", "")
        if item in inventory:
            inventory[item]["stock"] += 1

    elif data.startswith("dec_"):
        item = data.replace("dec_", "")
        if item in inventory and inventory[item]["stock"] > 0:
            inventory[item]["stock"] -= 1

    elif data == "restock_low":
        for item, info in inventory.items():
            if info.get("stock", 0) < LOW_STOCK_THRESHOLD:
                inventory[item]["stock"] = RESTOCK_AMOUNT

    save_inventory(inventory)
    markup = build_inventory_keyboard()
    await query.edit_message_reply_markup(reply_markup=markup)
