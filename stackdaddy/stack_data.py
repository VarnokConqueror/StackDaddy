# stack_data.py

import json
import os

STACK_DATA_FILE = "stack_data.json"

def load_stack_data():
    if os.path.exists(STACK_DATA_FILE):
        with open(STACK_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_stack_data(data):
    with open(STACK_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_user_stack(user_id):
    data = load_stack_data()
    return data.get(str(user_id), [])

def add_supplement_to_stack(user_id, supplement):
    data = load_stack_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = []
    data[uid].append(supplement)
    save_stack_data(data)

def clear_user_stack(user_id):
    data = load_stack_data()
    uid = str(user_id)
    if uid in data:
        data[uid] = []
        save_stack_data(data)

def format_stack(stack):
    if not stack:
        return "Your stack is currently empty."
    return "\n".join(f"💊 {supplement}" for supplement in stack)
