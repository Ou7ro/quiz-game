import json
import random
import logging

logger = logging.getLogger(__name__)

try:
    with open("questions.json", "r", encoding="KOI8-R") as file:
        ALL_QUESTIONS = json.load(file)
    logger.info(f"Загружено {len(ALL_QUESTIONS)} вопросов")
except Exception as e:
    logger.error(f"Ошибка загрузки вопросов: {e}")
    ALL_QUESTIONS = []


def get_random_question():
    return random.choice(ALL_QUESTIONS)
