import logging
import os

from dotenv import load_dotenv
import telegram
import requests
import time

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

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


def check_tokens():
    """Проверка доступности переменных окружения."""
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
            RETRY_PERIOD, ENDPOINT, HEADERS, HOMEWORK_VERDICTS]):
        return True
    logging.critical('The app has been stopped, check tokens')


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        log_info = f'Message has been sent: {message}'
        logging.debug(log_info)
        return message
    except Exception as error:
        log_info = f'Message has NOT been sent: {error}'
        logging.error(log_info)
        return log_info


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
        logging.error(f'TypeError has occured: '
                      f'response is not dict.'
                      f'response: {response}.')
        raise TypeError
    if 'homeworks' not in response or 'current_date' not in response:
        logging.error(f'KeyError has occured: '
                      f'no homeworks or current_date in response.'
                      f'response: {response}.')
        raise KeyError
    if not isinstance(response.get('homeworks'), list):
        homeworks = response.get('homeworks')
        logging.error(f'TypeError has occured: '
                      f'homeworks is not list.'
                      f'homeworks: {homeworks}.')
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
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    failure_msg = ''
    success_msg = ''
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
            message = parse_status(homework)
            if message != success_msg:
                result = send_message(bot, message)
                failure_msg = ''
                success_msg = result
                logging.debug(f'Final report: {success_msg}')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if message != failure_msg:
                send_message(bot, message)
                failure_msg = message
            logging.error(f'failure_msg: {failure_msg}')
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
