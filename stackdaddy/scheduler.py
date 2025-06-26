from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot
from dotenv import load_dotenv
import os
import asyncio

from utils_stackdaddy import (
    get_time_period,
    get_stack,
    format_stack,
    get_saved_chat_ids
)
from grocery_ui import populate_checklist_from_mealplan, build_checklist_keyboard

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

async def send_daily_reminder(bot: Bot):
    for chat_id in get_saved_chat_ids():
        try:
            period = get_time_period()
            stack = get_stack(period)
            message = f"⏰ Daily {period} Stack Reminder:\n\n{format_stack(stack)}"
            await bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            print(f"Failed to send daily reminder to {chat_id}: {e}")

async def auto_refresh_grocery(bot: Bot):
    for chat_id in get_saved_chat_ids():
        try:
            populate_checklist_from_mealplan(chat_id)
            keyboard = build_checklist_keyboard(chat_id)
            await bot.send_message(
                chat_id=chat_id,
                text="🛒 Your grocery checklist has been refreshed for the week!",
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Failed to refresh grocery list for {chat_id}: {e}")

def setup_reminders(application):
    scheduler = AsyncIOScheduler(timezone="America/New_York")

    # Daily Stack Reminder (every day at 9am)
    scheduler.add_job(
        send_daily_reminder,
        CronTrigger(hour=9, minute=0),
        args=[application.bot],
        name="Daily Supplement Reminder"
    )

    # Weekly Grocery Refresh (Sundays at 9am)
    scheduler.add_job(
        auto_refresh_grocery,
        CronTrigger(day_of_week="sun", hour=9, minute=0),
        args=[application.bot],
        name="Weekly Grocery Checklist Auto-Refresh"
    )

    scheduler.start()
