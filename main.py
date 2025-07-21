from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters,
)
import sys
import datetime
import re
import os
import json


from datetime import timedelta

import datetime

AUTO_CHAT_ID = ""  # Set your chat/user ID here, or detect from first /start
TODAY_SENT_LOG = "today_sent.log"

def has_sent_today_auto():
    today_str = datetime.date.today().isoformat()
    if os.path.exists(TODAY_SENT_LOG):
        with open(TODAY_SENT_LOG, "r") as f:
            dates = [line.strip() for line in f.readlines()]
            return today_str in dates
    return False

def mark_sent_today_auto():
    today_str = datetime.date.today().isoformat()
    with open(TODAY_SENT_LOG, "a") as f:
        f.write(today_str + "\n")

async def auto_send_today_workout(context: ContextTypes.DEFAULT_TYPE):
    #if has_sent_today_auto():
    #    return  # Already sent
    
    current_date = datetime.date.today()
    days_since_start = (current_date - PLAN_START_DATE).days
    day = days_since_start % 28
    workout = get_workout_for_day(day)
    
    chat_id = AUTO_CHAT_ID  # Replace with your Telegram user/chat ID

    if chat_id:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"📅 Auto Today's Workout (Cycle Day {day + 1}/28, {current_date.strftime('%A')}): {workout}"
        )
        mark_sent_today_auto()

PLAN_START_DATE = datetime.date(2025, 7, 20)  # Starting Sunday, July 20, 2025

WORKOUT_FILE = "workout_plan.txt"
TIME_LOG_FILE = "workout_times.log"
STATS_FILE = "stats.json"

# Initialize stats data
DEFAULT_STATS = {
    "5K": 0.0,
    "FTP": 0
}

# Convert seconds to mm:ss format
def seconds_to_mmss(seconds):
    minutes = int(seconds) // 60
    secs = int(round(seconds % 60))
    return f"{minutes}:{secs:02d}"

def mmss_to_seconds(mmss):
    parts = mmss.split(':')
    if len(parts) != 2:
        raise ValueError("Invalid mm:ss format")
    minutes = int(parts[0])
    seconds = int(parts[1])
    return minutes * 60 + seconds

def format_printable(line):

    stats_data = load_stats()  # Ensure this function returns a dictionary with keys "FTP" and "5K"
    # For example: stats_data = {"FTP": 180, "5K": 420}  # 5K pace = 7:00 min/mile

    ftp_tags = {
        "FTP65":  stats_data["FTP"] * 0.65,
        "FTP75":  stats_data["FTP"] * 0.75,
        "FTP90":  stats_data["FTP"] * 0.90,
        "FTP95":  stats_data["FTP"] * 0.95,
        "FTP100": stats_data["FTP"] * 1.00,
        "FTP105": stats_data["FTP"] * 1.05
    }

    run_tags = {
        "5K95":   stats_data["5K"] * 0.95,
        "5K97":   stats_data["5K"] * 0.97,
        "5K98":   stats_data["5K"] * 0.98,
        "5K100":  stats_data["5K"] * 1.00,
        "5K107":  stats_data["5K"] * 1.07,
        "10KP":   stats_data["5K"] * 1.03,
        "TEMPO":  stats_data["5K"] * 1.05
    }


    # Replace run tags
    for tag, sec_val in run_tags.items():
        formatted_val = seconds_to_mmss(sec_val)
        line = line.replace(tag, formatted_val)

    # Replace FTP tags
    for tag, power_val in ftp_tags.items():
        formatted_val = f"{int(round(power_val))}W"
        line = line.replace(tag, formatted_val)

    return line

def load_stats():
    if not os.path.exists(STATS_FILE):
        save_stats(DEFAULT_STATS)
    try:
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_STATS

def save_stats(data):
    with open(STATS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_workout_plan():
    if not os.path.exists(WORKOUT_FILE):
        return ["No workout plan found. Please create workout_plan.txt."]
    
    with open(WORKOUT_FILE, "r") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    return lines

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Chat =", update.effective_chat.id)
    await update.message.reply_text(
        "👋 Welcome!\nUse /today or /tomorrow to view your workout.\n"
        "Use /set5k <time_in_minutes> and /setftp <number> to update stats.\n"
        "Use /stats to view current 5K and FTP stats."
    )

def get_workout_for_day(day_index: int) -> str:
    plan = load_workout_plan()

    return format_printable(plan[day_index])  # <-- Always format before returning


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_date = datetime.date.today()
    days_since_start = (current_date - PLAN_START_DATE).days
    day = days_since_start % 28
    workout = get_workout_for_day(day)
    await update.message.reply_text(
        f"📅 Today's Workout (Cycle Day {day + 1}/28, {current_date.strftime('%A')}): {workout}"
    )




async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
        
    current_date = datetime.date.today() + timedelta(days=1)
    days_since_start = (current_date - PLAN_START_DATE).days
    day = days_since_start % 28
    workout = get_workout_for_day(day)
    await update.message.reply_text(
        f"📅 Tomorrow's Workout (Cycle Day {day + 1}/28, {current_date.strftime('%A')}): {workout}"
    )


def log_times_from_message(message_text: str):
    times = re.findall(r'\b([01]?\d|2[0-3]):[0-5]\d\b', message_text)
    if times:
        with open(TIME_LOG_FILE, "a") as f:
            for time_str in times:
                f.write(f"{datetime.datetime.now().isoformat()}: {time_str}\n")
    return times

async def catch_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    times_found = log_times_from_message(text)
    if times_found:
        await update.message.reply_text(f"✅ Logged time(s): {', '.join(times_found)}")

# ---- Commands to Get / Set 5K & ftp ----

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats_data = load_stats()
    msg = f"📊 Current Stats:\n" \
          f"• 5K: {seconds_to_mmss(stats_data.get('5K'))} minutes/mile\n" \
          f"• FTP: {stats_data.get('FTP')} watts\n"
    await update.message.reply_text(msg)

async def set5k(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /set5k <time_in_mm:ss>")
        return
    
    try:
        value = mmss_to_seconds(context.args[0])
        if value < 0:
            raise ValueError("Time cannot be negative.")
        stats_data = load_stats()
        stats_data["5K"] = value
        save_stats(stats_data)
        await update.message.reply_text(f"✅ 5K time updated to {seconds_to_mmss(value)} minutes.")
    except ValueError:
        await update.message.reply_text("⚠️ Invalid value. Please enter a number.")

async def setftp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /setftp <number>")
        return
    
    try:
        value = int(context.args[0])
        stats_data = load_stats()
        stats_data["FTP"] = value
        save_stats(stats_data)
        await update.message.reply_text(f"✅ FTP updated to {value}.")
    except ValueError:
        await update.message.reply_text("⚠️ Invalid value. Please enter an integer.")

async def auto_run_today(application, chat_id):
    if has_sent_today_auto():
        return
    # Fake a minimal Update/Context for today()
    class AutoContext:
        chat_id = AUTO_CHAT_ID
    from types import SimpleNamespace
    # Build a minimal Update-like object
    update = SimpleNamespace(
        effective_chat=SimpleNamespace(id=chat_id),
        message=SimpleNamespace(
            reply_text=lambda msg: application.bot.send_message(chat_id=chat_id, text=msg)
        ),
    )
    context = SimpleNamespace()
    await today(update, context)
    mark_sent_today_auto()

def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python main.py <TOKEN> <CHATID>")
        sys.exit(1)

    token = sys.argv[1]
    AUTO_CHAT_ID = sys.argv[2]
    application = Application.builder().token(token).build()

    # Workouts
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("today", today))
    application.add_handler(CommandHandler("tomorrow", tomorrow))

    # Stats commands
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("set5k", set5k))
    application.add_handler(CommandHandler("setftp", setftp))

    # Free-text time logger
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, catch_all))

    async def post_init_hook(app):
        await auto_run_today(app, AUTO_CHAT_ID)

    application.post_init = post_init_hook
    application.run_polling()


if __name__ == "__main__":
    main()
