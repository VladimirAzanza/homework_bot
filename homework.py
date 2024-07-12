import logging
import time

from dotenv import load_dotenv
from http import HTTPStatus
import requests
from telebot import TeleBot, types

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
    StatusCodeException,
    UndefinedStatusException
)


def check_tokens():
    """_summary_

    Raises:
        NoneValueException: _description_
    """
    if not all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        logging.critical(
            'Check that the environment varibles/tokens are not missing'
        )
        raise NoneValueException(
            'Check that the environment varibles/tokens are not missing'
        )


def send_message(bot, message):
    """_summary_

    Arguments:
        bot -- _description_
        message -- _description_
    """
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            reply_markup=types.ReplyKeyboardRemove()
        )
        logging.debug(
            f'Message succesfully sent to {TELEGRAM_CHAT_ID}: {message}'
        )
    except Exception as error:
        logging.error(
            f'Failed to send message: {error}'
        )


def get_api_answer(timestamp):
    """_summary_

    Arguments:
        timestamp -- _description_

    Raises:
        StatusCodeException: _description_

    Returns:
        _description_
    """
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
    """_summary_

    Arguments:
        response -- _description_

    Raises:
        TypeError: _description_
        KeyError: _description_
        TypeError: _description_

    Returns:
        _description_
    """
    if not isinstance(response, dict):
        raise TypeError('Response must be a dictionary type')
    if 'homeworks' not in response:
        raise KeyError('Not homeworks key at response')
    homeworks = response.get('homeworks')
    if not homeworks:
        logging.debug('No new homework status')
    elif not isinstance(homeworks, list):
        raise TypeError('Homeworks must be a list')
    else:
        return homeworks


def parse_status(homework):
    """_summary_

    Arguments:
        homework -- _description_

    Raises:
        TypeError: _description_
        KeyError: _description_
        UndefinedStatusException: _description_

    Returns:
        _description_
    """
    if not isinstance(homework, dict):
        raise TypeError('Homework must be a dictionary type')
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
    last_message = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                new_message = parse_status(homeworks[0])
                if new_message != last_message and new_message:
                    last_message = new_message
                    send_message(bot, last_message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.warning(message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
