import json
import random
import logging
from environs import env
logger = logging.getLogger(__name__)

_questions = None


def load_questions():
    global _questions
    env.read_env()
    questions_path = env.str('QUESTION_PATH', 'questions.json')
    try:
        with open(questions_path, "r", encoding="KOI8-R") as file:
            _questions = json.load(file)
        logger.info("Вопросы загружены")
        return True
    except Exception as e:
        logger.error(f"Ошибка загрузки вопросов: {e}")
        _questions = []
        return False


def get_random_question():
    if _questions is None:
        raise Exception("Вопросы не загружены.")
    return random.choice(_questions)
