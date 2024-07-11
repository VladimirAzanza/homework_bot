import logging
import os
import time

import requests
from telebot import TeleBot, types
from dotenv import load_dotenv

from constants import (
    ENDPOINT,
    HEADERS,
    HOMEWORK_VERDICTS,
    PRACTICUM_TOKEN,
    RETRY_PERIOD,
    TELEGRAM_CHAT_ID,
    TELEGRAM_TOKEN,
)
from exceptions import (
    NoneValueException,
    UndefinedStatusException
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    filename='program.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
)
logger = logging.getLogger(__name__)


def check_tokens():
    for token in [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]:
        if token is None:
            logger.critical(
                'Required environment variable {token} is missing.'
            )
            raise NoneValueException('hjsda')


def send_message(bot, message):
    bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message
    )


def get_api_answer(timestamp):
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
        return dict(response.json().get('homeworks'))
    except requests.RequestException as error:
        print(f'Сбой в работе программы: {error}')


def check_response(response):
    homework = response.get('homeworks')
    return parse_status(homework)


def parse_status(homework):
    if 'homework_name' not in homework:
        raise KeyError('У словарья нет клоча "homework_name"')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS[homework_status]
    else:
        raise UndefinedStatusException(
            f'Статус не известный: {homework_status}'
        )
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    check_tokens()
    get_api_answer(timestamp)

    while True:
        try:
            check_response(
                requests.get(
                    ENDPOINT,
                    headers=HEADERS,
                    params={'from_date': timestamp}
                ).json()
            )
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        bot.polling()
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
