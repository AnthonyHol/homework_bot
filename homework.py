import json as simplejson
import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from requests import RequestException

from exceptions import (
    APIRequestException,
    IncorrectHomeworkStatus,
    IncorrectStatusResponseCode,
    JSONDecodeException,
    NoExistToken,
)

load_dotenv()

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
handler.setFormatter(formatter)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_RETRY_TIME = 600

PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
PRACTICUM_ENDPOINT = (
    "https://practicum.yandex.ru/api/user_api/homework_statuses/"
)
PRACTICUM_HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}

HOMEWORK_STATUSES = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


def check_tokens() -> bool:
    """Ф-я проверки токенов."""
    logger.info('Запущена функция "check_tokens"')
    tokens = (
        "PRACTICUM_TOKEN",
        "TELEGRAM_TOKEN",
        "TELEGRAM_CHAT_ID",
    )
    no_valid_tokens = []

    for name in tokens:
        if not globals()[name]:
            no_valid_tokens.append(name)

    if no_valid_tokens:
        logger.critical(f'Не задано значение для {", ".join(no_valid_tokens)}')

    return PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID


def get_api_answer(current_timestamp: int) -> dict:
    """Ф-я получения ответа API.

    Args:
        current_timestamp (:obj:`int`): текущая временная метка

    Returns:
        :obj:`dict`: словарь с результатом запроса.
    """
    logger.info('Запущена функция "get_api_answer"')

    timestamp = current_timestamp or int(time.time())
    params = {"from_date": timestamp}

    try:
        homework_statuses = requests.get(
            PRACTICUM_ENDPOINT, headers=PRACTICUM_HEADERS, params=params
        )

    except RequestException as exc:
        raise APIRequestException("Не удалось получить ответ от API.") from exc

    try:
        if homework_statuses.status_code != HTTPStatus.OK:
            raise IncorrectStatusResponseCode(homework_statuses.status_code)

        return homework_statuses.json()

    except simplejson.JSONDecodeError as exc:
        raise JSONDecodeException(homework_statuses) from exc


def check_response(response: dict) -> list:
    """Ф-я проверки корректности ответа на запрос.

    Args:
        response (:obj:`dict`): результат запроса

    Returns:
        :obj:`list`: список домашних работ.
    """
    logger.info('Запущена функция "check_response"')

    if not isinstance(response, dict):
        message = f"Запрос вернул результат типа не Dict, а {type(response)}."
        logging.error(message)
        raise TypeError(message)

    if "homeworks" not in response:
        message = 'Ответ не содержит ключа "homeworks".'
        logging.error(message)
        raise KeyError(message)

    result = response.get("homeworks")

    if not isinstance(result, list):
        message = '"homeworks" не является списком.'
        logging.error(message)
        raise TypeError(message)

    if len(result) == 0:
        logging.debug('Список "homeworks" пуст.')

    return result


def parse_status(homework: dict) -> str:
    """Ф-я извлечения из информации о конкретной домашней работе ее статуса.

    Args:
        response (:obj:`dict`): один элемент из списка домашних работ

    Returns:
        :obj:`str`: строка с вердиктом.
    """
    logger.info('Запущена функция "parse_status"')

    for key in ("homework_name", "status"):
        if key not in homework:
            logger.error(f'Отсутствует ожидаемый ключ "{key}".')
            raise KeyError(f'Отсутствует ожидаемый ключ "{key}".')

    homework_name: str = homework["homework_name"]
    homework_status: str = homework["status"]

    if homework_status in HOMEWORK_STATUSES:
        verdict: str = HOMEWORK_STATUSES[homework_status]
    else:
        logger.error(
            f"Недокументированный статус домашней работы({homework_status})"
        )
        raise IncorrectHomeworkStatus(homework_status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot: telegram.Bot, message: str) -> None:
    """Ф-я отправки сообщения ботом в Телеграм.

    Args:
        response (:obj:`telegram.Bot`): объект бот
        message (:obj:`str`): сообщение для отправления.
    """
    logger.info('Запущена функция "send_message"')

    try:
        logger.debug(f'Попытка обращения к чату "{TELEGRAM_CHAT_ID}"')
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

    except telegram.error.TelegramError as error:
        logger.exception(
            f'Не удалось отправить сообщение "{message}".\n Ошибка:"{error}"',
            exc_info=True,
        )

    else:
        logger.info(f'Успешно отправлено сообщение: "{message}"')


def get_bot() -> telegram.Bot:
    """Ф-я создания бота.

    Returns:
        :obj:`telegram.Bot`: объект бот.
    """
    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        logger.debug("Подключение к боту успешно")
        return bot

    except telegram.error.TelegramError as error:
        logger.exception(f"Не удалось подключиться к боту. Ошибка: {error}.")


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical("Были переданы не все требуемые переменные окружения")
        raise NoExistToken()

    logger.debug("Токены прошли проверку.")

    bot = get_bot()

    current_timestamp: int = int(time.time())
    last_status: str = ""

    hw_last_error_associations: dict = {}
    cur_hw_name: str = ""

    while True:
        try:
            response = get_api_answer(current_timestamp)
            logger.debug(f'Ф-я "get_api_answer" вернула: \n{response}\n')
            homeworks = check_response(response)

            if len(homeworks) != 0:
                current_status: str = parse_status(homeworks[0])
                cur_hw_name = current_status[46 : current_status.find(".zip")]

                if current_status != last_status:
                    send_message(bot, current_status)
                    logger.debug(
                        f'Ф-я "parse_status" вернула "{current_status}"'
                    )
                last_status = current_status
                current_timestamp = int(time.time())
            else:
                logger.debug("Ничего нового...")

        except Exception as error:
            if cur_hw_name:
                if hw_last_error_associations[cur_hw_name] != error:
                    logger.exception(error)
                    send_message(bot, error)
                    hw_last_error_associations[cur_hw_name] = error
                    logger.debug(hw_last_error_associations)
            else:
                logger.exception(error)
                send_message(bot, error)

        else:
            time.sleep(TELEGRAM_RETRY_TIME)


if __name__ == "__main__":
    main()
