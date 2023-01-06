import logging
import os

from dotenv import load_dotenv
import telegram
import requests
import time
from datetime import datetime

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
CURRENT_DATE = 1549962000 - 30

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG)


class CheckAPIError(Exception):
    """Custom API Error."""
    pass


def check_tokens():
    """Проверка доступности переменных окружения."""
    if (PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID
            and RETRY_PERIOD and ENDPOINT and HEADERS and HOMEWORK_VERDICTS):
        return True
    logging.critical('The app has been stopped, check tokens')
    return False


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        log_info = f'Message has been sent: {message}'
        logging.debug(log_info)
    except Exception as error:
        log_info = f'Message has NOT been sent: {error}'
        logging.error(log_info)


def get_api_answer(timestamp):
    """Создание запроса к эндпоинту API-сервиса."""
    payload = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(ENDPOINT,
                                         headers=HEADERS,
                                         params=payload)
        if homework_statuses.status_code != 200:
            homework_statuses.raise_for_status()
        return homework_statuses.json()
    except requests.RequestException as error:
        logging.error(f'{error} has occured, '
                      f'API answer failed, '
                      f'{ENDPOINT} is not available.')
        return False


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError
    if 'homeworks' not in response or 'current_date' not in response:
        raise KeyError
    if not isinstance(response.get('homeworks'), list):
        raise TypeError
    return True


def parse_status(homework):
    """Извлечение статуса домашней работы."""
    homework_name = homework.get('homework_name')
    if not homework_name:
        logging.error(f'KeyError has occured: '
                      f'homework_name: {homework_name}.')
        raise KeyError
    status = homework.get('status')
    if not status:
        logging.error(f'KeyError has occured: '
                      f'status: {status}.')
        raise KeyError
    if status not in HOMEWORK_VERDICTS:
        logging.error(f'Unknown status: {status}.')
        raise ValueError
    verdict = HOMEWORK_VERDICTS[status]
    return (f'Изменился статус проверки работы "{homework_name}". {verdict}')


def main():
    """Основная логика работы бота."""
    failure_msg = ''
    if not check_tokens():
        raise Exception('Variables error.')
    logging.debug('Tokens available.')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    logging.debug(f'timestamp: {timestamp}')
    while True:
        try:
            response = get_api_answer(0)
            logging.debug('response received')
            logging.debug(f'timestamp 1: {timestamp}')
            if not check_response(response):
                logging.error('Data from API can not be used.')
            homeworks = response.get('homeworks')
            homework = homeworks[0]
            logging.debug('List of works received')
            if len(homework) > 0:
                logging.debug('New homework')
                upd_time = datetime.timestamp(
                    datetime.strptime(homework.get('date_updated'),
                                      '%Y-%m-%dT%H:%M:%SZ')
                )
                if int(upd_time) > timestamp:
                    logging.debug('upd_time > timestamp')
                    message = parse_status(homework)
                    send_message(bot, message)
                    timestamp = int(upd_time)
                    failure_msg = ''
                    logging.debug(f'timestamp 2: {timestamp}')
                logging.debug('Same status, no msg has been sent.')
            logging.debug('No new homework')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if message != failure_msg:
                send_message(bot, message)
                failure_msg = message
            logging.debug(f'timestamp 3: {timestamp}')
            logging.debug(f'failure_msg: {failure_msg}')
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
