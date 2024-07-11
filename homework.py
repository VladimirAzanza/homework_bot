import logging
import os
import time

import requests
from telebot import TeleBot, types
from dotenv import load_dotenv

from constants import (
    ENDPOINT,
    ENV_VARIABLES_LIST,
    HEADERS,
    HOMEWORK_VERDICTS,
    PRACTICUM_TOKEN,
    RETRY_PERIOD,
    TELEGRAM_CHAT_ID,
    TELEGRAM_TOKEN,
)
from exceptions import (
    NoneValueException
)

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
    filemode='w'
)


def check_tokens():
    if not all(ENV_VARIABLES_LIST):
        raise NoneValueException(
            'Required environment variables are missing.'
            'Check for the availability of tokens'
        )


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
    homework_name = homework['homework_name']
    verdict = homework['status']
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
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
