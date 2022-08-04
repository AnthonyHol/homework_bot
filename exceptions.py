class NoExistToken(Exception):
    """Возникает, когда не задано значения для токена."""

    def __init__(self, *args) -> None:
        """Инициализирует NoExistToken."""
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self) -> str:
        """Формирует строковое представление IncorrectStatusResponseCode."""
        if self.message:
            return f"Не задано значение для {self.message}."
        else:
            return "Передены не все значения для токенов."


class IncorrectStatusResponseCode(Exception):
    """Возникает, когда запрос вернул неверный статус-код."""

    def __init__(self, *args) -> None:
        """Инициализирует IncorrectStatusResponseCode."""
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self) -> str:
        """Формирует строковое представление IncorrectStatusResponseCode."""
        if self.message:
            return f"Запрос вернул неверный статус-код: {self.message}."
        else:
            return "Запрос вернул неверный статус-код."


class IncorrectHomeworkStatus(Exception):
    """Возникает для недокументированного статуса домашней работы."""

    def __init__(self, *args) -> None:
        """Инициализирует IncorrectHomeworkStatus."""
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self) -> str:
        """Формирует строковое представление IncorrectStatusResponseCode."""
        if self.message:
            return f"Недокументированный статус домашней работы: {self.message}."
        else:
            return "Недокументированный статус домашней работы."


class APIRequestException(Exception):
    """Возникает при ошибке при запросе к API."""

    def __init__(self, *args) -> None:
        """Инициализирует APIRequestError."""
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self) -> str:
        """Формирует строковое представление APIRequestError."""
        if self.message:
            return f"Ошибка при обработке запросе к API. Запрос: {self.message}."
        else:
            return "Ошибка при обработке запроса к API."


class JSONDecodeException(Exception):
    """Возникает при ошибке при преобразовании JSON."""

    def __init__(self, *args) -> None:
        """Инициализирует JSONDecodeException."""
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self) -> str:
        """Формирует строковое представление JSONDecodeException."""
        if self.message:
            return f"Ошибка при преобразовании JSON из: {self.message}."
        else:
            return "Ошибка при преобразовании JSON."
