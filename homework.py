import logging
import os
import time

from dotenv import load_dotenv
import requests
from telebot import TeleBot, types
from http import HTTPStatus

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
    StatusCodeException,
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
            f'Message succesfully sent to {TELEGRAM_CHAT_ID}: {message}'
        )
    except SendMessageFailedException as e:
        logging.error(
            f'Failed to send message: {e}'
        )


def get_api_answer(timestamp):
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
        if response.status_code != HTTPStatus.OK:
            logging.error('Program crash')
            raise StatusCodeException('Not 200 Http status code.')
        return response.json()
    except requests.RequestException as error:
        logging.error(f'Program crash: {error}')


def check_response(response):
    if not isinstance(response, dict):
        raise TypeError('Response must be a dictionary type')
    if 'homeworks' not in response:
        raise KeyError('Not homeworks key at response')
    homeworks = response.get('homeworks')
    if not homeworks:
        logging.debug('No new homework status')
    else:
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
    message = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            new_message = check_response(response)
            if new_message != message and message:
                message = new_message
                send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.warning(message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
