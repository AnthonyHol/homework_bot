import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (
    IncorrectHomeworkStatus,
    IncorrectStatusResponseCode,
    NoExistToken,
)

load_dotenv()

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
handler.setFormatter(formatter)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TELEGRAM_RETRY_TIME = 600

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
PRACTICUM_ENDPOINT = (
    'https://practicum.yandex.ru/api/user_api/homework_statuses/'
)
PRACTICUM_HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}


def check_tokens():
    """Ф-я проверки токенов."""
    logger.info('Запущена функция "check_tokens"')
    tokens = (
        'PRACTICUM_TOKEN',
        'TELEGRAM_TOKEN',
        'TELEGRAM_CHAT_ID',
    )

    for name in tokens:
        if not globals()[name]:
            logger.critical(f'Не задано значение для {name}')

    return bool(PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID)


def get_bot():
    """Ф-я получения бота."""
    logger.info('Запущена функция "get_bot"')
    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)

        logger.debug('Подключение к боту успешно')
        return bot
    except Exception as error:
        logger.error(f'Не удалось подключиться к боту. Ошибка: {error}')


def get_api_answer(
    current_timestamp,
):
    """Ф-я получения ответа API.

    Принимает текущий timestamp, возвращает словарь с результатом запроса.
    """
    logger.info('Запущена функция "get_api_answer"')

    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    homework_statuses = requests.get(
        PRACTICUM_ENDPOINT, headers=PRACTICUM_HEADERS, params=params
    )
    if not homework_statuses.status_code == HTTPStatus.OK:
        logger.error(
            (
                f'Запрос вернул неверный статус-код:'
                f'{homework_statuses.status_code}.'
            )
        )
        send_message(
            get_bot(),
            (
                f'Запрос вернул неверный статус-код:'
                f'{homework_statuses.status_code}.'
            ),
        )
        raise IncorrectStatusResponseCode(homework_statuses.status_code)

    return homework_statuses.json()


def check_response(response):
    """Ф-я проверки корректности ответа на запрос.

    Принимает результат запроса. Возвращает список домашних работ.
    """
    sum_message = ''
    message = ''

    logger.info('Запущена функция "check_response"')
    if not isinstance(response, dict):
        message = f'Запрос вернул результат типа не Dict, а {type(response)}.'
        sum_message = f'{sum_message}\n {message}'
        logging.error(message)
        raise TypeError(message)

    if 'homeworks' not in response.keys():
        message = 'Ответ не содержит ключа "homeworks".'
        sum_message = f'{sum_message}\n {message}'
        logging.error(message)
        raise KeyError(message)

    if not isinstance(response.get("homeworks"), list):
        message = '"homeworks" не является списком.'
        sum_message = f'{sum_message}\n {message}'
        logging.error(message)
        raise TypeError(message)

    if sum_message.replace('\n', ''):
        send_message(get_bot(), sum_message)

    result = response.get('homeworks')
    if not result:
        result = []

    return result


def parse_status(homework):
    """Ф-я извлечения из информации о конкретной домашней работе ее статуса.

    Принимает один элемент из списка домашних работ.
    Возвращает строку с вердиктом.
    """
    logger.info('Запущена функция "parse_status"')

    for key in ('homework_name', 'status'):
        if key not in homework:
            logger.error(f'Отсутствует ожидаемый ключ {key}')
            raise KeyError(f'Отсутствует ожидаемый ключ {key}')

    homework_name = homework['homework_name']
    homework_status = homework['status']
    try:
        verdict = HOMEWORK_STATUSES[homework_status]
    except Exception as error:
        logger.error(f'Недокументированный статус домашней работы({error})')
        raise IncorrectHomeworkStatus(error)
    else:
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, message):
    """Ф-я отправки сообщения ботом в Телеграм.

    Принимает бота и сообщение.
    """
    try:
        logger.debug(f'Попытка обращения к чату "{TELEGRAM_CHAT_ID}"')
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        logger.error(
            f'Не удалось отправить сообщение "{message}".' f'Ошибка:"{error}"',
            exc_info=True,
        )
    else:
        logger.info(f'Успешно отправлено сообщение: "{message}"')


def main() -> None:
    """Основная логика работы бота."""
    if check_tokens():
        logger.debug('Токены прошли проверку.')
        bot = get_bot()
        current_timestamp = int(time.time())

        while True:
            response = get_api_answer(current_timestamp)
            logger.debug(f'Ф-я "get_api_answer" вернула: \n{response}\n')
            try:
                homeworks = check_response(response)
                if len(homeworks) != 0:
                    current_status: str = parse_status(homeworks[0])
                    send_message(bot, current_status)
                    logger.debug(
                        f'Ф-я "parse_status" вернула "{current_status}"'
                    )
                else:
                    logger.debug('Ничего нового...')

            except Exception as error:
                logger.error(f'Сбой в работе программы: {error}')
                time.sleep(TELEGRAM_RETRY_TIME)
            else:
                continue
    else:
        logger.critical('Были переданы не все требуемые переменные окружения')
        raise NoExistToken()


if __name__ == '__main__':
    main()
