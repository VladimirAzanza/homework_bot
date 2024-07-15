import logging
import time

from dotenv import load_dotenv
from http import HTTPStatus
import requests
from telebot import TeleBot, types

from constants import (
    ENDPOINT,
    ENV_TOKENS_LIST,
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


logger = logging.getLogger(__name__)


def check_tokens():
    """Checks for the avalability of environment variables and tokens.

    Returns:
        missing_tokens (list): A list with the missing variables or tokens.
    """
    missing_tokens = [
        token_name for token, token_name in ENV_TOKENS_LIST if not token
    ]
    return missing_tokens


def send_message(bot, message):
    """Function that sends a message to the user through a bot.

    Arguments:
        bot (telebot.Telebot): Telegram bot instance.
        message (str):  Message to be sent to the user.
    """
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            reply_markup=types.ReplyKeyboardRemove()
        )
        logger.debug(
            f'Message succesfully sent to {TELEGRAM_CHAT_ID}: {message}'
        )
    except Exception as error:
        logger.error(
            f'Failed to send message: {error}'
        )


def get_api_answer(timestamp):
    """Function that gets a request to the Yandex Practicum API.

    Arguments:
        timestamp (int): A timestamp representing the actual time.

    Raises:
        StatusCodeException: Exception if request code status is not 200.

    Returns:
        dict: API response converted to Python data type.
    """
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
        if response.status_code != HTTPStatus.OK:
            logger.error('Program crash')
            raise StatusCodeException('Not 200 Http status code.')
        return response.json()
    except requests.RequestException as error:
        logger.error(f'Program crash: {error}')


def check_response(response):
    """Function that checks for the API response.

    Arguments:
        response (dict): API response converted to Python data type.

    Raises:
        TypeError: Exception for non correct type.
        KeyError: Exception for no key.

    Returns:
        list: The list of homeworks from the response.
    """
    if not isinstance(response, dict):
        raise TypeError('Response must be a dictionary type')
    if 'homeworks' not in response:
        raise KeyError('Not homeworks key at response')
    homeworks = response.get('homeworks')
    if not homeworks:
        logger.debug('No new homework status')
    elif not isinstance(homeworks, list):
        raise TypeError('Homeworks must be a list')
    else:
        return homeworks


def parse_status(homework):
    """Parse the status of a homework and returns a message with the status.

    Arguments:
        homework (dict): Dictionary with the information of the homework.

    Raises:
        TypeError: Exception for non correct type.
        KeyError: Exception for no key.
        UndefinedStatusException: Exception for no expected status.

    Returns:
        str: Message with the status of the homework.
    """
    if not isinstance(homework, dict):
        raise TypeError('Homework must be a dictionary type')
    if 'homework_name' not in homework:
        raise KeyError('No "homework_name" at homework keys')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS[homework_status]
    else:
        raise UndefinedStatusException(
            f'Unkown status: {homework_status}'
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
    handler = logging.StreamHandler()
    logger.addHandler(handler)

    if check_tokens():
        logger.critical(
            f'Check for existence of environment varibles/tokens:'
            f'{", ".join(check_tokens())}'
        )
        raise NoneValueException(
            f'Check for existence of environment varibles/tokens:'
            f'{", ".join(check_tokens())}'
        )

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - (8640 * 2)
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
            message = f'Program crash: {error}'
            logging.warning(message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
