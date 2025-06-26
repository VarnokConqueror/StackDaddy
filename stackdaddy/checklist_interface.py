# checklist_interface.py

import json
import os

CHECKLIST_FILE = "checklist_data.json"

def load_checklist():
    if os.path.exists(CHECKLIST_FILE):
        with open(CHECKLIST_FILE, "r") as f:
            return json.load(f)
    return {}

def save_checklist(data):
    with open(CHECKLIST_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_user_checklist(user_id):
    data = load_checklist()
    return data.get(str(user_id), {})

def toggle_checklist_item(user_id, item):
    data = load_checklist()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {}
    user_checklist = data[uid]
    if item in user_checklist:
        user_checklist[item] = not user_checklist[item]
    else:
        user_checklist[item] = True
    save_checklist(data)

def format_checklist(user_id):
    checklist = get_user_checklist(user_id)
    if not checklist:
        return "Your checklist is empty. Add items using /addcheck [item]"
    lines = []
    for item, checked in checklist.items():
        checkmark = "✅" if checked else "⬜️"
        lines.append(f"{checkmark} {item}")
    return "\n".join(lines)

def remove_checklist_item(user_id, item):
    data = load_checklist()
    uid = str(user_id)
    if uid in data and item in data[uid]:
        del data[uid][item]
        save_checklist(data)
