# stackdaddy_bot.py

import asyncio
import logging
import os
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from handlers import start, handle_buttons, handle_meal_logging
from grocery_ui import (
    show_grocery_checklist,
    handle_toggle_item,
    handle_special_actions,
)
from scheduler import setup_reminders
from utils_inventory import (
    handle_inventory_actions,
    show_inventory_ui
)

# Load env variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def main():
    application = ApplicationBuilder().token(TOKEN).build()

    # Command Handlers
    application.add_handler(CommandHandler("start", start))

    # Inline Button Handlers
    application.add_handler(CallbackQueryHandler(handle_buttons, pattern="^(taken_|inventory)$"))
    application.add_handler(CallbackQueryHandler(show_grocery_checklist, pattern="^show_grocery$"))
    application.add_handler(CallbackQueryHandler(handle_toggle_item, pattern="^toggle_"))
    application.add_handler(CallbackQueryHandler(handle_special_actions, pattern="^(populate_checklist|clear_checklist)$"))

    # Inventory Visual UI Handlers
    application.add_handler(CallbackQueryHandler(handle_inventory_actions, pattern="^(inc_|dec_|restock_low)$"))
    application.add_handler(CallbackQueryHandler(show_inventory_ui, pattern="^show_inventory$"))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_meal_logging))

    # Setup weekly reminders (and potentially weekly checklist auto-refresh)
    setup_reminders(application)

    print("StackDaddy is running...")
    await application.run_polling()

if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
