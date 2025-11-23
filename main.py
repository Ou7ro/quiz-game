import logging
from environs import env
import json
import random
import redis

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

redis_client = None


def get_random_question():
    with open("questions.json", "r", encoding="KOI8-R") as file:
        questions = json.load(file)
        question = random.choice(questions)
    return (question)


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user_id = update.effective_user.id
    custom_keyboard = [['Новый вопрос', 'Сдаться'],
                       ['Мой счет']]

    reply_markup = ReplyKeyboardMarkup(custom_keyboard)

    update.message.reply_text(
        'Привет! Я бот для викторины. Давай сыграем!',
        reply_markup=reply_markup,
    )

    redis_client.set(f"user_{user_id}_score", 0)


def new_question(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    question_data = get_random_question()
    question_text = question_data['question']

    redis_client.set(f"user_{user_id}_current_question", question_text)
    redis_client.set(f"user_{user_id}_current_answer", question_data['answer'])

    update.message.reply_text(question_text)


def handle_answer(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_answer = update.message.text.strip().lower().rstrip('.')

    correct_answer = redis_client.get(f"user_{user_id}_current_answer")
    if correct_answer:
        correct_answer = correct_answer.strip().lower().rstrip('.')

    if user_answer == correct_answer:
        current_score = redis_client.get(f"user_{user_id}_score")
        new_score = int(current_score) + 1 if current_score else 1
        redis_client.set(f"user_{user_id}_score", new_score)
        update.message.reply_text('Правильно!')
    else:
        update.message.reply_text('Неправильно. Попробуйте еще раз.')


def surrender(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    correct_answer = redis_client.get(f"user_{user_id}_current_answer")
    if correct_answer:
        update.message.reply_text(f"Правильный ответ: {correct_answer}")
    else:
        update.message.reply_text("Нет активного вопроса")


def show_score(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    user_score = redis_client.get(f"user_{user_id}_score")
    if not user_score:
        user_score = 0

    update.message.reply_text(f"Ваш счет: {user_score}")


def main() -> None:
    """Start the bot."""
    global redis_client
    env.read_env()
    tg_bot_token = env.str('TG_BOT_TOKEN')

    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=True
    )

    try:
        redis_client.ping()
        logger.info("Redis подключен успешно")
    except redis.ConnectionError:
        logger.error("Ошибка подключения к Redis")
        return

    updater = Updater(tg_bot_token)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))

    dispatcher.add_handler(MessageHandler(Filters.regex('^Новый вопрос$'), new_question))
    dispatcher.add_handler(MessageHandler(Filters.regex('^Сдаться$'), surrender))
    dispatcher.add_handler(MessageHandler(Filters.regex('^Мой счет$'), show_score))

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_answer))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
