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
BUDGET = "budget/"
TODO = "todo/"
DIET = "diet/"

def load_spent():
    if not os.path.exists(BUDGET + "budget.txt"):
        return {}
    
    budget_data = {}
    with open(BUDGET + "budget.txt", "r") as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) == 2:
                budget_data[parts[0].strip()] = float(parts[1].strip())
    
    return budget_data

def save_spent(budget_data):
    with open(BUDGET + "budget.txt", "w") as f:
        for category, amount in budget_data.items():
            f.write(f"{category},{amount}\n")

async def add_spent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /add_spent <category> <amount>")
        return
    
    category = context.args[0].strip()
    try:
        amount = float(context.args[1].strip())
    except ValueError:
        await update.message.reply_text("⚠️ Invalid amount. Please enter a number.")
        return
    
    budget_data = load_spent()
    
    if category in budget_data:
        budget_data[category] += amount
    else:
        budget_data[category] = amount
    
    save_spent(budget_data)
    await update.message.reply_text(f"✅ Added {amount} to {category}.")

async def show_spent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    budget_data = load_spent()
    if not budget_data:
        await update.message.reply_text("No budget data found.")
        return
    
    msg = "📊 Budget Spent:\n"
    for category, amount in budget_data.items():
        msg += f"• {category}: ${amount:.2f}\n"
    
    await update.message.reply_text(msg)

def load_todo():
    if not os.path.exists(TODO + "todo.txt"):
        return []
    
    with open(TODO + "todo.txt", "r") as f:
        todos = [line.strip() for line in f.readlines() if line.strip()]
    
    return todos

def save_todo(todos):
    with open(TODO + "todo.txt", "w") as f:
        for todo in todos:
            f.write(todo.strip() + "\n")

async def add_todo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /add_todo <task>")
        return
    
    todo_item = " ".join(context.args)
    todos = load_todo()
    
    if todo_item not in todos:
        todos.append(todo_item)
        save_todo(todos)
        await update.message.reply_text(f"✅ Added todo item: {todo_item}")
    else:
        await update.message.reply_text(f"❌ Todo item '{todo_item}' already exists.")

async def finish_todo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /finish_todo <task number>")
        return
    
    try:
        task_number = int(context.args[0]) - 1
        todos = load_todo()
        
        if 0 <= task_number < len(todos):
            removed_item = todos.pop(task_number)
            save_todo(todos)
            await update.message.reply_text(f"✅ Removed todo item: {removed_item}")
        else:
            await update.message.reply_text("❌ Invalid task number.")
    except ValueError:
        await update.message.reply_text("⚠️ Please provide a valid task number.")

async def show_todos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    todos = load_todo()
    if not todos:
        await update.message.reply_text("No todo items found.")
    else:
        msg = "📝 Todo List:\n" + "\n".join(f"{i + 1}. {todo}" for i, todo in enumerate(todos))
        await update.message.reply_text(msg)

def get_week_label():
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())  # Monday of the current week
    end_of_week = start_of_week + datetime.timedelta(days=6)  # Sunday of the current week
    return f"{start_of_week.isoformat()}_to_{end_of_week.isoformat()}"

def load_diet():
    week_label = get_week_label()
    diet_file = DIET + f"diet_{week_label}.txt"
    if not os.path.exists(diet_file):
        return {}
    
    diet_items = {}
    with open(diet_file, "r") as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) == 2:
                item, count = parts[0].strip(), int(parts[1].strip())
                diet_items[item] = count
    
    return diet_items

def save_diet(diet_items):
    week_label = get_week_label()
    diet_file = DIET + f"diet_{week_label}.txt"
    with open(diet_file, "w") as f:
        for item, count in diet_items.items():
            f.write(f"{item},{count}\n")

def last_week_label():
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday() + 7)  # Monday of the last week
    end_of_week = start_of_week + datetime.timedelta(days=6)  # Sunday of the last week
    return f"{start_of_week.isoformat()}_to_{end_of_week.isoformat()}"

def load_last_week_diet():
    week_label = last_week_label()
    diet_file = DIET + f"diet_{week_label}.txt"
    if not os.path.exists(diet_file):
        return []
    
    with open(diet_file, "r") as f:
        diet_items = [line.strip() for line in f.readlines() if line.strip()]
    
    return diet_items

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
        "👋 Welcome!\n"
        "Use /today or /tomorrow to view your workout.\n"
        "Use /set5k <time_in_mm:ss> and /setftp <number> to update stats.\n"
        "Use /stats to view current 5K and FTP stats.\n"
        "Use /guju to get today's Gujarati words and practice prompts.\n"
        "Use /vocab to view learned Gujarati words.\n"
        "Use /add_diet <item>, /remove_diet <item>, and /get_diet to manage your diet.\n"
        "Use /add_spent <category> <amount> and /show_spent to manage your budget.\n"
        "Use /add_todo <task>, /finish_todo <task number>, and /show_todos to manage your todo list."
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

def stow_words(words):
    with open(GUJU_PATH + "learned.txt", "a") as f:
        for word in words:
            f.write(word.strip() + "\n")

def get_todays_words(unlearned, count=2, offset = 0):
    random.seed(5)
    
    unlearned = list(unlearned)
    
    random.shuffle(unlearned)
    
    start_index = ((datetime.date.today() - PLAN_START_DATE).days + offset) % len(unlearned)
    selected_words = [unlearned[(start_index + i) % len(unlearned)] for i in range(min(count, len(unlearned)))]
    
    wrds = [f"{word.strip()}" for word in selected_words]

    return wrds

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
    words = "Today:\n" + "\n".join(get_todays_words(unl, 2)) #todays words

    for i in range(1, 7):
        words += "\n" + f"\nDays ago: {i}\n" 
        words += "\n".join(get_todays_words(unl, 2, offset = -i))  # words from the last week

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

async def get_diet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    diet_items = load_diet()
    if not diet_items:
        await update.message.reply_text("No diet items added for this week.")
    else:
        msg = "Diet Items for this week:\n" + "\n".join([f"{item}: {count}" for item, count in diet_items.items()])
        await update.message.reply_text(msg)

async def add_diet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /add_diet <item>")
        return

    diet_item = " ".join(context.args)
    diet_items = load_diet()

    if not diet_items:
        diet_items = {}

    if diet_item not in diet_items:
        diet_items[diet_item] = 1
    else:
        diet_items[diet_item] += 1

    save_diet(diet_items)
    await update.message.reply_text(f"✅ Added diet item: {diet_item}")

async def remove_diet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /remove_diet <item>")
        return

    diet_item = " ".join(context.args)
    diet_items = load_diet()

    if diet_item in diet_items:
        del diet_items[diet_item]
        save_diet(diet_items)
        await update.message.reply_text(f"✅ Removed diet item: {diet_item}")
    else:
        await update.message.reply_text(f"❌ Diet item '{diet_item}' not found.")



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
    application.add_handler(CommandHandler("today", today))
    application.add_handler(CommandHandler("tomorrow", tomorrow))
    # Learned words command
    application.add_handler(CommandHandler("vocab", learned_guju))
    application.add_handler(CommandHandler("guju", get_today_guju))

    # Budget commands
    
    application.add_handler(CommandHandler("show_spent", show_spent))
    application.add_handler(CommandHandler("add_spent", add_spent))

    # Diet commands
    application.add_handler(CommandHandler("get_diet", get_diet))
    application.add_handler(CommandHandler("add_diet", add_diet))
    application.add_handler(CommandHandler("remove_diet", remove_diet))

    # Todo commands
    application.add_handler(CommandHandler("add_todo", add_todo))
    application.add_handler(CommandHandler("finish_todo", finish_todo))
    application.add_handler(CommandHandler("show_todos", show_todos))

    # Free-text time logger
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, catch_all))

    application.run_polling()



if __name__ == "__main__":

    main()
