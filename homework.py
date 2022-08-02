import logging
import os
import sys
import time
from http import HTTPStatus
from typing import Any, Dict, List, Optional

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


PRACTICUM_TOKEN: Optional[str] = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN: Optional[str] = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")

RETRY_TIME: int = 600
ENDPOINT: str = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS: dict[str, str] = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}


HOMEWORK_STATUSES: dict[str, str] = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


def check_tokens() -> bool:
    """Ф-я проверки токенов."""
    logger.info('Запущена функция "check_tokens"')
    tokens: tuple[str, str, str] = (
        "PRACTICUM_TOKEN",
        "TELEGRAM_TOKEN",
        "TELEGRAM_CHAT_ID",
    )

    for name in tokens:
        if not globals()[name]:
            logger.critical(f"Не задано значение для {name}")

    return bool(PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID)


def get_bot():
    """Ф-я получения бота."""
    logger.info('Запущена функция "get_bot"')
    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)

        logger.debug("Подключение к боту успешно")
        return bot
    except Exception as error:
        logger.error(f"Не удалось подключиться к боту. Ошибка: {error}")


def get_api_answer(
    current_timestamp: int,
) -> Dict[str, str]:
    """Ф-я получения ответа API.

    Принимает текущий timestamp, возвращает словарь с результатом запроса.
    """
    logger.info('Запущена функция "get_api_answer"')

    timestamp: int = current_timestamp or int(time.time())
    params: dict[str, int] = {"from_date": timestamp}

    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if not homework_statuses.status_code == HTTPStatus.OK:
        logger.error(
            (
                f"Запрос вернул неверный статус-код:"
                f"{homework_statuses.status_code}."
            )
        )
        send_message(
            get_bot(),
            (
                f"Запрос вернул неверный статус-код:"
                f"{homework_statuses.status_code}."
            ),
        )
        raise IncorrectStatusResponseCode(homework_statuses.status_code)

    return homework_statuses.json()


def check_response(response) -> List[Any]:
    """Ф-я проверки корректности ответа на запрос.

    Принимает результат запроса. Возвращает список домашних работ.
    """
    sum_message: str = ""
    message: str = ""

    logger.info('Запущена функция "check_response"')
    if not isinstance(response, Dict):
        message = f"Запрос вернул результат типа не Dict, а {type(response)}."
        sum_message = f"{sum_message}\n {message}"
        logging.error(message)
        raise TypeError(message)

    if "homeworks" not in response.keys():
        message = 'Ответ не содержит ключа "homeworks".'
        sum_message = f"{sum_message}\n {message}"
        logging.error(message)
        raise KeyError(message)

    if not isinstance(response.get("homeworks"), List):
        message = '"homeworks" не является списком.'
        sum_message = f"{sum_message}\n {message}"
        logging.error(message)
        raise TypeError(message)

    if sum_message.replace("\n", ""):
        send_message(get_bot(), sum_message)

    result: Optional[list] = response.get("homeworks")
    if not result:
        result = []

    return result


def parse_status(homework: dict[str, str]) -> str:
    """Ф-я извлечения из информации о конкретной домашней работе ее статуса.

    Принимает один элемент из списка домашних работ.
    Возвращает строку с вердиктом.
    """
    logger.info('Запущена функция "parse_status"')

    for key in ("homework_name", "status"):
        if key not in homework:
            logger.error(f"Отсутствует ожидаемый ключ {key}")
            raise KeyError(f"Отсутствует ожидаемый ключ {key}")

    homework_name: str = homework["homework_name"]
    homework_status: str = homework["status"]
    try:
        verdict: str = HOMEWORK_STATUSES[homework_status]
    except Exception as error:
        logger.error(f"Недокументированный статус домашней работы({error})")
        raise IncorrectHomeworkStatus(error)
    else:
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot: telegram.bot.Bot, message: str) -> None:
    """Ф-я отправки сообщения ботом в Телеграм.

    Принимает бота и сообщение.
    """
    try:
        logger.debug(f"Попытка обращения к чату ={TELEGRAM_CHAT_ID}=")
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
        logger.debug("Токены прошли проверку.")
        bot = get_bot()
        current_timestamp: int = int(time.time())

        while True:
            response: Dict[str, str] = get_api_answer(current_timestamp)
            logger.debug(f'Ф-я "get_api_answer" вернула: \n{response}\n')
            try:
                homeworks: List[Any] = check_response(response)
                if len(homeworks) != 0:
                    current_status: str = parse_status(homeworks[0])
                    send_message(bot, current_status)
                    logger.debug(
                        f'Ф-я "parse_status" вернула "{current_status}"'
                    )
                else:
                    logger.debug("Ничего нового...")

            except Exception as error:
                logger.error(f"Сбой в работе программы: {error}")
                time.sleep(RETRY_TIME)
            else:
                continue
    else:
        logger.critical("Были переданы не все требуемые переменные окружения")
        raise NoExistToken()


if __name__ == "__main__":
    main()
