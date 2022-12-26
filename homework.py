import logging
import os

from dotenv import load_dotenv
from telegram.ext import CommandHandler, Updater
import telegram
import requests
import time
from pprint import pprint

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
CURRENT_DATE = 1549962000 - 30

RETRY_PERIOD = 10 #600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
LAST_RESPONSE = []

#def check_tokens():
    #"""Проверка доступности переменных окружения."""
    

def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    text = message
    bot.send_message(TELEGRAM_CHAT_ID, text)
    time.sleep(RETRY_PERIOD)
    main()



def get_api_answer(timestamp):
    """Создание запроса к эндпоинту API-сервиса."""
    payload = {'from_date': CURRENT_DATE}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    return homework_statuses.json().get('homeworks')
    

def check_response(response):
    """Проверка ответа API на соответствие документации."""
    global LAST_RESPONSE
    if response == []:
        time.sleep(RETRY_PERIOD)
        main()
    elif response == LAST_RESPONSE:
        time.sleep(RETRY_PERIOD)
        main()
    LAST_RESPONSE = response
    return response


def parse_status(homework):
    """Извлечение статуса домашней работы"""
    homework_name = homework[0].get('homework_name')
    status = homework[0].get('status')
    if status in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    

#...
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
#...
    response = get_api_answer(timestamp)
    homework = check_response(response)
    message = parse_status(homework)  
    send_message(bot, message)

    #while True:
    #    try:

    #        ...

    #    except Exception as error:
    #        message = f'Сбой в работе программы: {error}'
    #        ...
    #    ...

if __name__ == '__main__':
    main()
