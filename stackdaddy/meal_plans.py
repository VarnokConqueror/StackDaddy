# meal_plans.py

meal_plan = {
    "Monday": {
        "Breakfast": "Greek yogurt with honey and almonds",
        "Lunch": "Grilled cheese and tomato soup",
        "Dinner": "Vegetarian chili with brown rice"
    },
    "Tuesday": {
        "Breakfast": "Oatmeal with banana and peanut butter",
        "Lunch": "Avocado and egg sandwich",
        "Dinner": "Stir-fried tofu and vegetables with noodles"
    },
    "Wednesday": {
        "Breakfast": "Scrambled eggs and toast",
        "Lunch": "Veggie wrap with hummus",
        "Dinner": "Whole wheat pasta with marinara and roasted veggies"
    },
    "Thursday": {
        "Breakfast": "Fruit smoothie with protein powder",
        "Lunch": "Chickpea salad",
        "Dinner": "Stuffed bell peppers"
    },
    "Friday": {
        "Breakfast": "Cottage cheese with pineapple",
        "Lunch": "Spinach and cheese quesadilla",
        "Dinner": "Homemade veggie pizza"
    },
    "Saturday": {
        "Breakfast": "Pancakes with maple syrup",
        "Lunch": "Leftover chili",
        "Dinner": "Vegetable curry with jasmine rice"
    },
    "Sunday": {
        "Breakfast": "Bagel with cream cheese",
        "Lunch": "Quinoa salad with cucumbers and feta",
        "Dinner": "Baked ziti with garlic bread"
    }
}

def get_meal_plan_for_day(day):
    return meal_plan.get(day, {})
