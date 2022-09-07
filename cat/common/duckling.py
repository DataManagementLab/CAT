import requests
import logging
import json
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta
from typing import Tuple
from enum import IntEnum

logger = logging.getLogger('duckling')

GRAIN_SECOND = 'second'
GRAIN_MINUTE = 'minute'
GRAIN_HOUR = 'hour'
GRAIN_DAY = 'day'
GRAIN_WEEK = 'week'
GRAIN_MONTH = 'month'
GRAIN_QUARTER = 'quarter'
GRAIN_YEAR = 'year'


class Grain(IntEnum):
    second = 0
    minute = 1
    hour = 2
    day = 3
    week = 4
    month = 5
    quarter = 6
    year = 7


class Duckling:

    def __init__(self, host='localhost', port=8000, https=False, locale='en_US', timezone='Europe/Berlin'):
        protocol = 'https' if https else 'http'
        self.base_url = f'{protocol}://{host}:{port}'
        self.__test_connection__()
        self.locale = locale
        self.timezone = timezone

    def __test_connection__(self):
        try:
            requests.post(f'{self.base_url}/parse', data={'text': 'tomorrow'})
        except requests.exceptions.ConnectionError:
            raise Exception(f'Duckling connection error: could not connect to {self.base_url}')
        else:
            logger.info(f'Duckling server is up at {self.base_url}')

    def parse(self, text):
        payload = {
            'text': text,
            'locale': self.locale,
            'tz': self.timezone
        }
        try:
            r = requests.post(f'{self.base_url}/parse', data=payload)
        except requests.exceptions.ConnectionError:
            logger.debug(f'Connection error: could not connect to {self.base_url}')

        if r.status_code != 200:
            logger.error(f'Error parsing text: {r}')
            return None
        results = json.loads(r.text)
        return results

    def parse_datetime(self, text) -> Tuple[datetime, datetime]:
        results = self.parse(text)
        time_results = list(filter(lambda r: r['dim'] == 'time', results))
        if len(time_results) == 0:
            return None, None
        times = time_results[0]['value']
        value_type = times['type']
        if value_type == 'interval':
            datetime_from = datetime.fromisoformat(times['from']['value']) if 'from' in times.keys() else None
            datetime_to = datetime.fromisoformat(times['to']['value']) if 'to' in times.keys() else None
            return datetime_from, datetime_to
        else:
            datetime_value = datetime.fromisoformat(times['value'])
            grain = Grain[times['grain']]
            if grain <= Grain.day:
                return datetime_value, datetime_value
            if grain == Grain.week:
                datetime_to = datetime_value + relativedelta(days=+7)
            elif grain == Grain.month:
                datetime_to = datetime_value + relativedelta(months=+1)
            elif grain == Grain.quarter:
                datetime_to = datetime_value + relativedelta(months=+3)
            elif grain == Grain.year:
                datetime_to = datetime_value + relativedelta(years=+1)
            return datetime_value, datetime_to

    def parse_date(self, text) -> Tuple[date, date]:
        datetime_from, datetime_to = self.parse_datetime(text)
        return datetime_from.date() if datetime_from else None, datetime_to.date() if datetime_to else None

    def parse_time(self, text) -> Tuple[time, time]:
        datetime_from, datetime_to = self.parse_datetime(text)
        return datetime_from.time() if datetime_from else None, datetime_to.time() if datetime_to else None

    def parse_numeric(self, text) -> float:
        result = self.parse(text)
        numeric_results = list(filter(lambda r: r['dim'] in ['number', 'amount-of-money'], result))
        if len(numeric_results) == 0:
            return None, None
        numbers = numeric_results[0]['value']
        value_type = numbers['type']
        if value_type == 'interval':
            number_from = float(numbers['from']['value']) if 'from' in numbers.keys() else None
            number_to = float(numbers['to']['value']) if 'to' in numbers.keys() else None
            return number_from, number_to
        else:
            number = float(numbers['value'])
            return number, number
