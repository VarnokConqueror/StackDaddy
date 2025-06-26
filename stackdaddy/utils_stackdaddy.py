import os
import json
from datetime import datetime

# File paths
STACK_FILE = "stack_status.json"
INVENTORY_FILE = "inventory.json"
CHAT_ID_FILE = "chat_ids.json"

# Time-based stack period
def get_time_period():
    hour = datetime.now().hour
    if hour < 12:
        return "morning"
    elif hour < 18:
        return "afternoon"
    else:
        return "evening"

# Define the supplement stacks
STACKS = {
    "morning": ["Lion’s Mane", "Omega-3", "Vitamin D3 + K2"],
    "afternoon": ["Acetyl L-Carnitine", "Alpha Lipoic Acid"],
    "evening": ["Magnesium Glycinate", "Vitamin B12"]
}

def get_stack(period):
    return STACKS.get(period, [])

def format_stack(stack):
    return "\n".join(f"• {item}" for item in stack)

# Load and save stack status
def load_stack_status():
    if os.path.exists(STACK_FILE):
        with open(STACK_FILE, "r") as f:
            return json.load(f)
    return {}

def save_stack_status(status):
    with open(STACK_FILE, "w") as f:
        json.dump(status, f)

def mark_stack_taken(period):
    status = load_stack_status()
    date = datetime.now().strftime("%Y-%m-%d")
    if date not in status:
        status[date] = {}
    status[date][period] = True
    save_stack_status(status)
    return f"✅ Marked your {period} stack as taken!"

# Inventory logic
def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        with open(INVENTORY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_inventory(data):
    with open(INVENTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def decrement_stack_inventory(period):
    inventory = load_inventory()
    changed = False
    for item in STACKS.get(period, []):
        if item in inventory and inventory[item] > 0:
            inventory[item] -= 1
            changed = True
    if changed:
        save_inventory(inventory)

def get_inventory():
    inventory = load_inventory()
    if not inventory:
        return "No inventory data found."

    result = []
    for item, qty in inventory.items():
        if qty <= 5:
            icon = "🔴"
        elif qty <= 10:
            icon = "🟡"
        else:
            icon = "🟢"
        result.append(f"{icon} {item}: {qty}")
    return "\n".join(result)

def restock_item(item_name, amount):
    inventory = load_inventory()
    if item_name in inventory:
        inventory[item_name] += amount
    else:
        inventory[item_name] = amount
    save_inventory(inventory)

# Chat ID management
def save_chat_id(chat_id):
    chat_id = str(chat_id)
    ids = get_saved_chat_ids()
    if chat_id not in ids:
        ids.append(chat_id)
        with open(CHAT_ID_FILE, "w") as f:
            json.dump(ids, f)

def get_saved_chat_ids():
    if os.path.exists(CHAT_ID_FILE):
        with open(CHAT_ID_FILE, "r") as f:
            return json.load(f)
    return []

# Color-coded inventory display
def get_color_coded_inventory():
    inventory = load_inventory()
    lines = []
    for item, qty in inventory.items():
        if qty <= 2:
            color = "🔴"  # Low stock
        elif qty <= 5:
            color = "🟠"  # Moderate
        else:
            color = "🟢"  # Healthy
        lines.append(f"{color} {item}: {qty}")
    return "\n".join(lines)
