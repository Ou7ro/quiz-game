import json
import random
import logging

logger = logging.getLogger(__name__)


def load_questions(questions_path):
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
