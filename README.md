# homework_bot

### Описание
Телеграм бот для отправки уведомлений об изменении статуса ревью кода.

### Технологии
- Python 3.10
- Bot API 6.1 for Telegram


# API для проекта YaMDb
## Спринт 7 — homework_bot

### Описание
Телеграм бот для отправки уведомлений в Телеграм чат об изменении статуса ревью программного кода на Яндекс Практикум.
Текущий статус ревью проверяется каждые 10 минут при помощи запроса на следующий эндпоинт: 
```
https://practicum.yandex.ru/api/user_api/homework_statuses/
```
Доступ к эндпоинту ограничен токеном, который можно получить по [ссылке](https://oauth.yandex.ru/authorizeresponse_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a "ссылке").

Возможные варианты статуса ревью:
- работа принята на проверку;
- работа возвращена для исправления ошибок;
- работа принята.

### Технологии
- Python 3.10
- Bot API 6.1 for Telegram

### Запуск проекта в dev-режиме
Клонируем проект:
```
git clone https://github.com/AnthonyHol/homework_bot.git
```

Переходим в папку с проектом и устанавливаем виртуальное окружение:

```
python -m venv venv
```

Активируем виртуальное окружение:
```
source venv/Scripts/activate
```

Устанавливаем зависимости:
```
python -m pip install --upgrade pip
```
```
pip install -r requirements.txt
```

В папку, где находится файл settings.py, добавляем файл .env, куда прописываем секретный ключ следующим образом:
```
PRACTICUM_TOKEN='Токен'
TELEGRAM_TOKEN='Токен'
TELEGRAM_CHAT_ID='ID'
```

Запускаем телеграм бота:
```
python homework.py
```

Автор: [Холкин Антон](https://github.com/AnthonyHol/ "Холкин Антон")
