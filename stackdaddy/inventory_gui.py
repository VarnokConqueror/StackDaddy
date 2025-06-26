from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import json
import os

INVENTORY_FILE = "inventory.json"
EXPIRATION_DAYS_WARNING = 30  # Days before expiration to trigger warning color

# Load inventory from file
def load_inventory():
    if not os.path.exists(INVENTORY_FILE):
        return {}
    with open(INVENTORY_FILE, "r") as f:
        return json.load(f)

# Save inventory to file
def save_inventory(inventory):
    with open(INVENTORY_FILE, "w") as f:
        json.dump(inventory, f, indent=2)

# Create inventory GUI as inline keyboard
def build_inventory_gui():
    inventory = load_inventory()
    buttons = []

    for item, info in inventory.items():
        stock = info.get("stock", 0)
        expires_in = info.get("expires_in", 999)
        label = f"{item}: {stock}"

        # Expiration icons
        if expires_in <= 0:
            label += " 🔥"
        elif expires_in <= EXPIRATION_DAYS_WARNING:
            label += " 🟠"

        # Stock level color icons
        if stock < 3:
            label += " 🔴"
        elif stock <= 10:
            label += " ⚠️"
        else:
            label += " ✅"

        buttons.append([
            InlineKeyboardButton(f"➖ {label}", callback_data=f"dec_{item}"),
            InlineKeyboardButton(f"➕", callback_data=f"inc_{item}")
        ])

    buttons.append([InlineKeyboardButton("♻️ Restock All Low Items", callback_data="restock_low")])

    return InlineKeyboardMarkup(buttons)

def change_inventory_stock(item, delta):
    inventory = load_inventory()
    if item not in inventory:
        inventory[item] = {"stock": 0, "expires_in": 999}
    inventory[item]["stock"] += delta
    inventory[item]["stock"] = max(inventory[item]["stock"], 0)
    save_inventory(inventory)

def restock_low_items(threshold=3, new_stock=10):
    inventory = load_inventory()
    for item, info in inventory.items():
        if info["stock"] < threshold:
            inventory[item]["stock"] = new_stock
    save_inventory(inventory)

def get_inventory():
    inventory = load_inventory()
    lines = []
    for item, info in inventory.items():
        stock = info.get("stock", 0)
        expires = info.get("expires_in", "N/A")
        lines.append(f"{item}: {stock} left, expires in {expires} days")
    return "\n".join(lines)

def decrement_stack_inventory(period):
    from utils_stackdaddy import get_stack  # avoid circular import
    inventory = load_inventory()
    stack = get_stack(period)
    for item in stack:
        if item in inventory:
            inventory[item]["stock"] = max(inventory[item]["stock"] - 1, 0)
    save_inventory(inventory)
