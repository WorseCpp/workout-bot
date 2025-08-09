from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters,
)
import sys
import datetime
import re
import os
import json
import random

from datetime import timedelta

import datetime

AUTO_CHAT_ID = ""  # Set your chat/user ID here, or detect from first /start
TODAY_SENT_LOG = "today_sent.log"

GUJU_PATH = 'guju/'

def load_vocab():
    if not os.path.exists(GUJU_PATH + "vocab.txt"):
        return set()
    
    words = open(GUJU_PATH + "vocab.txt", "r").readlines()
        
    return set(words)

def load_learned():
    if not os.path.exists(GUJU_PATH + "learned.txt"):
        return set()

    return set(open(GUJU_PATH + "learned.txt", "r").readlines())

def append_to_learned(new_words):
    with open("learned.txt", "a") as f:
        for word in new_words:
            f.write(f"{word['english']},{word['gujarati']}\n")


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

def get_todays_words(unlearned, count=2):
    random.seed(datetime.date.today().isoformat())
    selected_words = random.sample(sorted(unlearned), min(2, len(unlearned)))
    wrds = [f"{word.strip()}" for word in selected_words]
    
    with open(GUJU_PATH + "learned.txt", "a") as f:
        for word in selected_words:
            f.write(word.strip() + "\n")

    words_msg = "\n".join(wrds)
    return words_msg

def get_todays_practice_words(learned, count=3):
    random.seed(datetime.date.today().isoformat())
    learned_list = list(learned)
    practice_words = random.sample(sorted(learned_list), min(count, len(learned_list)))
    practice_prompts = []
    for entry in practice_words:
        parts = entry.strip().split(' - ')
        if len(parts) != 2:
            continue
        if random.randint(0, 1) == 0:
            practice_prompts.append(f"Translate to Gujarati: {parts[0].strip()}")
        else:
            practice_prompts.append(f"Translate to English: {parts[1].strip()}")
    return practice_prompts

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

    voc = load_vocab()
    lrn = load_learned()
    unl = voc - lrn

    if not unl:
        await update.message.reply_text("✅ All words learned! No new words to practice today.")
        return
    
    # Randomly select 2 unlearned words *seed based on the current date*
    
    words = get_todays_words(unl, 2)
    
    await update.message.reply_text(
        f"📚 Today's Gujarati words to learn:\n{words}\n\n"
    )

    learned_list = list(lrn)

    if learned_list:
        
        practice_prompts = get_todays_practice_words(learned_list, 3)

        if practice_prompts:
            await update.message.reply_text(
                "🔄 Word Practice:\n" + "\n".join(practice_prompts)
            )

    if datetime.date.today().weekday() == 5:
        try:
            with open(GUJU_PATH + "grammar.txt", "r") as gf:
                grammar_lesson = gf.read()
        except FileNotFoundError:
            grammar_lesson = "Grammar lesson file not found."

        grammar_lesson = grammar_lesson.split("\n\n")

        grammar_lesson = random.choice(grammar_lesson).strip()

        await update.message.reply_text(f"📖 {grammar_lesson}")

async def learned_guju(update: Update, context: ContextTypes.DEFAULT_TYPE):
    learned_words = load_learned()
    if not learned_words:
        await update.message.reply_text("No learned words found.")
    else:
        msg = "Learned Gujarati Words:\n" + "\n".join(sorted(learned_words))
        await update.message.reply_text(msg)

async def get_today_guju(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voc = load_vocab()
    lrn = load_learned()
    unl = voc - lrn

    if not unl:
        await update.message.reply_text("✅ All words learned! No new words to practice today.")
        return
    
    # Randomly select 2 unlearned words *seed based on the current date*
    words = get_todays_words(unl, 2)
    
    await update.message.reply_text(
        f"📚 Today's Gujarati words to learn:\n{words}\n\n"
    )

    learned_list = list(lrn)

    if learned_list:
        
        practice_prompts = get_todays_practice_words(learned_list, 3)

        if practice_prompts:
            await update.message.reply_text(
                "🔄 Word Practice:\n" + "\n".join(practice_prompts)
            )

def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python main.py <TOKEN> <CHATID>")
        sys.exit(1)

    token = sys.argv[1]
    AUTO_CHAT_ID = sys.argv[2]
    application = Application.builder().token(token).build()

    # Workouts
    application.add_handler(CommandHandler("start", start))
    # Stats commands
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("set5k", set5k))
    application.add_handler(CommandHandler("setftp", setftp))
    # Learned words command
    application.add_handler(CommandHandler("learned", learned_guju))
    application.add_handler(CommandHandler("guju", get_today_guju))

    # Free-text time logger
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, catch_all))

    async def post_init_hook(app):
        await auto_run_today(app, AUTO_CHAT_ID)

    application.post_init = post_init_hook
    application.run_polling()


if __name__ == "__main__":

    main()
