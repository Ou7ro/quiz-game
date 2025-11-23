from vk_api.longpoll import VkLongPoll, VkEventType
from environs import env
import vk_api as vk
import logging
import random


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def echo(event, vk_api):
    vk_api.messages.send(
        user_id=event.user_id,
        message=event.text,
        random_id=random.randint(1,1000)
    )


def run_vk_bot():
    logger.info('Запуск VK бота')
    vk_token = env.str('VK_TOKEN_BOT')

    vk_session = vk.VkApi(token=vk_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    try:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                echo(event, vk_api)
    except Exception as e:
        logger.error(f'VK bot error: {e}')


def main():
    env.read_env()
    run_vk_bot()


if __name__ == "__main__":
    main()
