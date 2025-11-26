from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from quiz_quiestions import get_random_question
from environs import env
import vk_api as vk
import logging
import random
import redis


logger = logging.getLogger(__name__)

redis_client = None


class BotState:
    MENU = 0
    WAITING_FOR_ANSWER = 1


def create_keyboard():
    keyboard = VkKeyboard(one_time=False)

    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)

    keyboard.add_line()

    keyboard.add_button('Мой счет', color=VkKeyboardColor.SECONDARY)

    return keyboard.get_keyboard()


def start(user_id, vk_api):
    redis_client.set(f"vk_user_{user_id}_score", 0)
    redis_client.set(f"vk_user_{user_id}_state", BotState.MENU)

    vk_api.messages.send(
        user_id=user_id,
        message='Привет! Я бот для викторины. Давай сыграем!',
        keyboard=create_keyboard(),
        random_id=random.randint(1, 1000)
    )


def handle_new_question_request(user_id, vk_api):
    question_data = get_random_question()
    question_text = question_data['question']

    redis_client.set(f"vk_user_{user_id}_current_question", question_text)
    redis_client.set(f"vk_user_{user_id}_current_answer", question_data['answer'])
    redis_client.set(f"vk_user_{user_id}_state", BotState.WAITING_FOR_ANSWER)

    vk_api.messages.send(
        user_id=user_id,
        message=question_text,
        keyboard=create_keyboard(),
        random_id=random.randint(1, 1000)
    )


def handle_solution_attempt(user_id, user_answer, vk_api):
    user_answer_clean = user_answer.strip().lower().rstrip('.')

    correct_answer = redis_client.get(f"vk_user_{user_id}_current_answer")
    if correct_answer:
        correct_answer_clean = correct_answer.strip().lower().rstrip('.')

    if user_answer_clean == correct_answer_clean:
        current_score = redis_client.get(f"vk_user_{user_id}_score")
        new_score = int(current_score) + 1 if current_score else 1
        redis_client.set(f"vk_user_{user_id}_score", new_score)
        redis_client.set(f"vk_user_{user_id}_state", BotState.MENU)

        vk_api.messages.send(
            user_id=user_id,
            message='Правильно!',
            keyboard=create_keyboard(),
            random_id=random.randint(1, 1000)
        )
    else:
        vk_api.messages.send(
            user_id=user_id,
            message='Неправильно. Попробуйте еще раз.',
            keyboard=create_keyboard(),
            random_id=random.randint(1, 1000)
        )


def handle_surrender(user_id, vk_api):
    correct_answer = redis_client.get(f"vk_user_{user_id}_current_answer")

    if correct_answer:
        message = f"Правильный ответ: {correct_answer}"
    else:
        message = "Нет активного вопроса"

    redis_client.set(f"vk_user_{user_id}_state", BotState.MENU)

    vk_api.messages.send(
        user_id=user_id,
        message=message,
        keyboard=create_keyboard(),
        random_id=random.randint(1, 1000)
    )
    handle_new_question_request(user_id, vk_api)


def handle_show_score(user_id, vk_api):
    user_score = redis_client.get(f"vk_user_{user_id}_score")
    if not user_score:
        user_score = 0

    current_state = redis_client.get(f"vk_user_{user_id}_state")

    message = f"Ваш счет: {user_score}"

    current_question = redis_client.get(f"vk_user_{user_id}_current_question")
    if current_question and current_state == str(BotState.WAITING_FOR_ANSWER):
        message += f"\n\nУ вас есть активный вопрос:\n{current_question}"

    vk_api.messages.send(
        user_id=user_id,
        message=message,
        keyboard=create_keyboard(),
        random_id=random.randint(1, 1000)
    )


def handle_message(event, vk_api):
    user_id = event.user_id
    user_message = event.text

    current_state = redis_client.get(f"vk_user_{user_id}_state")

    if current_state is None:
        start(user_id, vk_api)
        return

    if user_message == 'Новый вопрос':
        handle_new_question_request(user_id, vk_api)

    elif user_message == 'Сдаться':
        handle_surrender(user_id, vk_api)

    elif user_message == 'Мой счет':
        handle_show_score(user_id, vk_api)

    elif current_state == str(BotState.WAITING_FOR_ANSWER):
        handle_solution_attempt(user_id, user_message, vk_api)

    else:
        vk_api.messages.send(
            user_id=user_id,
            message='Пожалуйста, используйте кнопки клавиатуры для взаимодействия',
            keyboard=create_keyboard(),
            random_id=random.randint(1, 1000)
        )


def run_vk_bot():
    global redis_client

    logger.info('Запуск VK бота')
    vk_token = env.str('VK_BOT_TOKEN')

    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=True
    )

    try:
        redis_client.ping()
        logger.info("Redis подключен успешно для VK бота")
    except redis.ConnectionError:
        logger.error("Ошибка подключения к Redis для VK бота")
        return

    vk_session = vk.VkApi(token=vk_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    try:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                handle_message(event, vk_api)
    except Exception as e:
        logger.error(f'VK bot error: {e}')


def main():
    env.read_env()
    run_vk_bot()


if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
    )
    main()
