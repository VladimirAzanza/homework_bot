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
    SendMessageFailedException,
    UndefinedStatusException
)


def check_tokens():
    if not all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        logging.critical(
            'Check that the environment varibles/tokens are not missing'
        )
        raise NoneValueException(
            'Check that the environment varibles/tokens are not missing'
        )


def send_message(bot, message):
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logging.debug(
            f'Message succesfully sent to {TELEGRAM_CHAT_ID}:{message}'
        )
    except SendMessageFailedException:
        logging.error(
            f'Failed to send message to {TELEGRAM_CHAT_ID}:{message}'
        )


def get_api_answer(timestamp):
    try:
        homeworks = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        ).json().get('homeworks')
        if homeworks == []:
            return {}
        else:
            return homeworks[0]
    except requests.RequestException as error:
        logging.error(f'Program crash: {error}')


def check_response(response):
    homeworks = response.get('homeworks')
    if not homeworks:
        logging.debug('No new homework status')
    for homework in homeworks:
        if not isinstance(homework, dict):
            raise TypeError('Homework must be a dictionary type')
        return parse_status(homework)


def parse_status(homework):
    if 'homework_name' not in homework:
        raise KeyError('У словарья нет ключа "homework_name"')
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
    load_dotenv()

    logging.basicConfig(
        level=logging.DEBUG,
        filename='program.log',
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
    )

    check_tokens()

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            get_api_answer(timestamp)
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
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
