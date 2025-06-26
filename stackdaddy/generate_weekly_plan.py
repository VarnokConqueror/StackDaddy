import json
import random
import os

MEAL_FILE = "vegetarian_meal_plan.json"
WEEKLY_PLAN_FILE = "weekly_meal_plan.json"
GROCERY_LIST_FILE = "weekly_grocery_list.json"
CHECKLIST_FILE = "grocery_checklist.json"

def load_meals():
    if not os.path.exists(MEAL_FILE):
        raise FileNotFoundError("Meal file not found.")
    with open(MEAL_FILE, "r") as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

def generate_plan(meals):
    chosen = random.sample(meals, 5)
    week_plan = [
        chosen[0],  # Mon
        chosen[1],  # Tue
        {"name": f"Leftovers: {chosen[0]['name']}", "ingredients": []},  # Wed
        chosen[2],  # Thu
        chosen[3],  # Fri
        {"name": f"Leftovers: {chosen[2]['name']}", "ingredients": []},  # Sat
        chosen[4],  # Sun
    ]
    return week_plan

def extract_ingredients(plan):
    ingredients = set()
    for meal in plan:
        ingredients.update(meal.get("ingredients", []))
    return sorted(list(ingredients))

def build_checklist(ingredients):
    return {item: False for item in ingredients}

def main():
    meals = load_meals()
    plan = generate_plan(meals)
    ingredients = extract_ingredients(plan)
    checklist = build_checklist(ingredients)

    save_json(WEEKLY_PLAN_FILE, plan)
    save_json(GROCERY_LIST_FILE, ingredients)
    save_json(CHECKLIST_FILE, checklist)

    print("✅ Weekly meal plan, grocery list, and checklist saved.")

if __name__ == "__main__":
    main()
