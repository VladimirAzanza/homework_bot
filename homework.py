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
    return requests.get(
        ENDPOINT,
        headers=HEADERS,
        params={'from_date': timestamp}
    ).json()


def check_response(response):
    ...


def parse_status(homework):
    ...

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            get_api_answer(timestamp)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        ...


if __name__ == '__main__':
    main()
