import json
import random
import logging
from environs import env
logger = logging.getLogger(__name__)

_questions = None


def load_questions():
    env.read_env()
    questions_path = env.str('QUESTION_PATH', 'questions.json')
    try:
        with open(questions_path, "r", encoding="KOI8-R") as file:
            questions = json.load(file)
        logger.info("Вопросы загружены")
        return questions
    except Exception as e:
        logger.error(f"Ошибка загрузки вопросов: {e}")
        return None


def get_random_question():
    questions = load_questions()
    if not questions:
        raise Exception("Вопросы не загружены.")
    return random.choice(questions)
