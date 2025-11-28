import json
import random
import logging
from environs import env


logger = logging.getLogger(__name__)


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
        return []


def get_random_question(questions):
    if not questions:
        raise Exception("Вопросы не загружены.")
    return random.choice(questions)
