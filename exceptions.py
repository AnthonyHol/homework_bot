class NoExistToken(Exception):
    """Исключение, когда не задано значения для токена."""

    def __init__(self, *args):
        """Инициализирует NoExistToken."""
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        """Формирует строковое представление IncorrectStatusResponseCode."""
        if self.message:
            return f"Не задано значение для {self.message}."
        else:
            return "Передены не все значения для токенов."


class IncorrectStatusResponseCode(Exception):
    """Исключение, когда запрос вернул неверный статус-код."""

    def __init__(self, *args):
        """Инициализирует IncorrectStatusResponseCode."""
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        """Формирует строковое представление IncorrectStatusResponseCode."""
        if self.message:
            return f"Запрос вернул неверный статус-код: {self.message}."
        else:
            return "Запрос вернул неверный статус-код."


class IncorrectHomeworkStatus(Exception):
    """Исключение недокументированного статуса домашней работы."""

    def __init__(self, *args):
        """Инициализирует IncorrectHomeworkStatus."""
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        """Формирует строковое представление IncorrectStatusResponseCode."""
        if self.message:
            return (
                f"Недокументированный статус домашней работы: {self.message}."
            )
        else:
            return "Недокументированный статус домашней работы."


class IncorrectResponse(Exception):
    """Исключение неверного результата запроса."""
