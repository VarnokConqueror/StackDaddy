from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from utils_stackdaddy import (
    get_time_period,
    get_stack,
    format_stack,
    mark_stack_taken,
    get_color_coded_inventory,
    decrement_stack_inventory,
    save_chat_id
)
from utils_mealplan import format_mealplan, get_user_mealplan, add_meal_to_plan

# Handle free-text meal logging
async def handle_meal_logging(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()

    if "," not in text:
        await update.message.reply_text("⚠️ Please separate the meal name and ingredients with commas.")
        return

    parts = [p.strip() for p in text.split(",")]
    meal_name = parts[0]
    ingredients = parts[1:]

    if not ingredients:
        await update.message.reply_text("⚠️ You need to list at least one ingredient.")
        return

    # Store the meal
    add_meal_to_plan(user.id, {"name": meal_name, "ingredients": ingredients})
    await update.message.reply_text(f"✅ Logged '{meal_name}' with ingredients: {', '.join(ingredients)}")


# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    save_chat_id(chat_id)  # Store user’s chat ID for reminders

    period = get_time_period()
    stack = get_stack(period)
    meals = get_user_mealplan(user.id)

    stack_text = f"🔥 Hey {user.first_name}, here’s your {period} stack:\n\n{format_stack(stack)}"
    meal_text = f"\n\n🍽 Today's Meal Plan:\n{format_mealplan(meals)}"

    keyboard = [
        [InlineKeyboardButton("✅ Mark Taken", callback_data=f"taken_{period}")],
        [InlineKeyboardButton("📦 Inventory", callback_data="inventory")],
        [InlineKeyboardButton("🧾 Grocery Checklist", callback_data="show_grocery")],
        [InlineKeyboardButton("🍽 Log a Meal", callback_data="log_meal")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(stack_text + meal_text, reply_markup=reply_markup)

# Button interaction handler
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("taken_"):
        period = data.split("_")[1]
        response = mark_stack_taken(period)
        decrement_stack_inventory(period)
        await query.edit_message_text(text=response)

    elif data == "inventory":
        inventory = get_color_coded_inventory()
        await query.edit_message_text(text=f"📦 Supplement Inventory:\n\n{inventory}")

    elif data == "toggle_grocery_ui":
        from grocery_ui import show_grocery_checklist
        await show_grocery_checklist(update, context)

    elif data == "log_meal":
        await query.edit_message_text(
            text="🍽 Please send me the meal name and ingredients separated by commas.\nExample:\nGrilled Cheese & Tomato Soup, bread, cheese, butter, tomato soup"
        )
        return  # Exit to wait for their next message

    else:
        await query.edit_message_text(text="❓ Unknown action.")
