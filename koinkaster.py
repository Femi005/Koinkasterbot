from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonCommands
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
import asyncio
import json
import os
from datetime import datetime, timedelta

TOKEN = '8382867932:AAFXD6HyU8JB_FgHV-UxY0Q4PbcBMHCjn4E'
DATA_FILE = 'koinkaster_data.json'

CPA_LINKS = [
    "https://is.gd/bdX9KY",
    "https://is.gd/URGBYu",
    "https://is.gd/2C2YMX",
    "https://is.gd/f2pTMc",
    "https://is.gd/CbpeDj",
    "https://is.gd/VwF9nG",
    "https://is.gd/208AHs",
    "https://is.gd/a4xYCn",
    "https://is.gd/IgLgU0",
    "https://is.gd/208AHs"
]

# Load or initialize user data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        users = json.load(f)
else:
    users = {}

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(users, f)

def get_user(user_id):
    if str(user_id) not in users:
        users[str(user_id)] = {
            "coins": 0,
            "referral_earnings": 0,
            "referrer": None,
            "started": False,
            "current_link_index": 0,
            "last_mine_time": None,
            "pending_task": None
        }
    return users[str(user_id)]

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    args = context.args
    u = get_user(user_id)

    if not u["started"]:
        if args:
            referrer_id = args[0]
            if referrer_id != str(user_id) and referrer_id in users:
                u["referrer"] = referrer_id
                ref_user = get_user(referrer_id)
                ref_bonus = 0.1 * 0.07
                ref_user["referral_earnings"] += round(ref_bonus, 4)
                ref_user["coins"] += round(ref_bonus, 4)
        u["coins"] += 0.1
        u["started"] = True
        save_data()

    welcome_msg = (
        f"Welcome {user.first_name} to Koinkaster\n\n"
        "Earn Koinkaster Coins every 20 seconds by completing offers\n"
        "Click the task link, complete it, then confirm to get coins\n\n"
        "Join our [Telegram Channel](https://t.me/koinkaster) for updates"
    )
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

# /earn command
async def earn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    u = get_user(user_id)

    now = datetime.utcnow()
    last_mine_time = (
        datetime.strptime(u["last_mine_time"], "%Y-%m-%d %H:%M:%S")
        if u["last_mine_time"] else None
    )

    if last_mine_time and now - last_mine_time < timedelta(seconds=20):
        await update.message.reply_text("⏳ Please wait 20 seconds before starting another task")
        return

    # Get the next CPA link
    index = u["current_link_index"]
    link = CPA_LINKS[index]
    u["pending_task"] = link

    # Build the confirmation button
    keyboard = [
        [InlineKeyboardButton("✅ I Have Completed the Task", callback_data="task_done")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    save_data()

    msg = (
        f"Click the link below and complete the task to earn 0.1 Koinkaster Coins\n\n"
        f"[Start Task]({link})"
    )
    await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=reply_markup)

# Button press handler
async def task_done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    u = get_user(user_id)

    now = datetime.utcnow()
    last_mine_time = (
        datetime.strptime(u["last_mine_time"], "%Y-%m-%d %H:%M:%S")
        if u["last_mine_time"] else None
    )

    if last_mine_time and now - last_mine_time < timedelta(seconds=20):
        await query.edit_message_text("⏳ Please wait 20 seconds before mining again")
        return

    if not u["pending_task"]:
        await query.edit_message_text("❌ No pending task found. Use /earn to start one.")
        return

    # Reward the user
    u["coins"] += 0.1
    u["last_mine_time"] = now.strftime("%Y-%m-%d %H:%M:%S")
    u["pending_task"] = None

    # Move to next link
    u["current_link_index"] = (u["current_link_index"] + 1) % len(CPA_LINKS)

    save_data()

    await query.edit_message_text("✅ Task completed! You earned 0.1 Koinkaster Coins")

# /reffer command
async def reffer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    referral_link = f"https://t.me/KoinkasterBot?start={user_id}"

    msg = (
        "Invite and Earn\n\n"
        "Earn 7% of your referral's mining earnings automatically\n"
        f"Your referral link:\n{referral_link}"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

# /balance command
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    u = get_user(user_id)

    msg = (
        "Your Wallet Summary\n\n"
        f"Total Coins: {round(u['coins'], 4)}\n"
        f"Referral Earnings: {round(u['referral_earnings'], 4)}"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

# Main entry point
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("earn", earn))
    app.add_handler(CallbackQueryHandler(task_done_callback, pattern="task_done"))
    app.add_handler(CommandHandler("reffer", reffer))
    app.add_handler(CommandHandler("balance", balance))

    await app.bot.set_my_commands([
        ("start", "Start your Koinkaster journey"),
        ("earn", "Start a mining task"),
        ("balance", "Check your Koinkaster wallet"),
        ("reffer", "Referral link and earnings")
    ])
    await app.bot.set_chat_menu_button(menu_button=MenuButtonCommands())

    print("Koinkaster Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
