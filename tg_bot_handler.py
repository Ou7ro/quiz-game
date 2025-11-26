import logging
from environs import env
import redis
from enum import Enum
from quiz_quiestions import get_random_question

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler,
)


logger = logging.getLogger(__name__)

redis_client = None


class BotState(Enum):
    MENU = 0
    WAITING_FOR_ANSWER = 1


def start(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    custom_keyboard = [['Новый вопрос', 'Сдаться'],
                       ['Мой счет']]

    reply_markup = ReplyKeyboardMarkup(custom_keyboard)

    update.message.reply_text(
        'Привет! Я бот для викторины. Давай сыграем!',
        reply_markup=reply_markup,
    )

    redis_client.set(f"user_{user_id}_score", 0)
    return BotState.MENU.value


def handle_new_question_request(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    question_data = get_random_question()
    question_text = question_data['question']

    redis_client.set(f"user_{user_id}_current_question", question_text)
    redis_client.set(f"user_{user_id}_current_answer", question_data['answer'])

    update.message.reply_text(question_text)
    return BotState.WAITING_FOR_ANSWER.value


def handle_solution_attempt(update: Update, context: CallbackContext) -> int:
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
        return BotState.MENU.value
    else:
        update.message.reply_text('Неправильно. Попробуйте еще раз.')
        return BotState.WAITING_FOR_ANSWER.value


def handle_surrender(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id

    correct_answer = redis_client.get(f"user_{user_id}_current_answer")
    if correct_answer:
        update.message.reply_text(f"Правильный ответ: {correct_answer}")
    else:
        update.message.reply_text("Нет активного вопроса")

    return BotState.MENU.value


def handle_show_score(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id

    user_score = redis_client.get(f"user_{user_id}_score")
    if not user_score:
        user_score = 0

    update.message.reply_text(f"Ваш счет: {user_score}")

    current_question = redis_client.get(f"user_{user_id}_current_question")
    if current_question:
        return BotState.WAITING_FOR_ANSWER.value
    else:
        return BotState.MENU.value


def main() -> None:
    global redis_client
    env.read_env()
    tg_bot_token = env.str('TG_BOT_TOKEN')

    redis_client = redis.Redis(
        host=env.str('REDIS_HOST', 'localhost'),
        port=env.int('REDIS_PORT', 6379),
        db=env.int('REDIS_DB', 0),
        decode_responses=True,
        password=env.str('REDIS_PASSWOR', '')
    )

    try:
        redis_client.ping()
        logger.info("Redis подключен успешно")
    except redis.ConnectionError:
        logger.error("Ошибка подключения к Redis")
        return

    updater = Updater(tg_bot_token)

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                BotState.MENU.value: [
                    MessageHandler(Filters.regex('^Новый вопрос$'), handle_new_question_request),
                    MessageHandler(Filters.regex('^Мой счет$'), handle_show_score),
                ],
                BotState.WAITING_FOR_ANSWER.value: [
                    MessageHandler(Filters.regex('^Сдаться$'), handle_surrender),
                    MessageHandler(Filters.regex('^Мой счет$'), handle_show_score),
                    MessageHandler(Filters.text & ~Filters.command, handle_solution_attempt),
                ],
            },
            fallbacks=[],
        )

    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
    )

    main()
