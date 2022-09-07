import os
import json
from bson import json_util
import random
import yaml
import re
from enum import Enum
from rasa_sdk.events import EventType, SlotSet

from .db.database import *
from .duckling import *
import datetime

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

SCHEMA_CONFIG_FILE = 'schema_config.json'

OPERATION_SELECT = 'select'
OPERATION_CALL = 'call'

INTENT_DONT_CARE = 'dont_care'
INTENT_AFFIRM = 'affirm'
INTENT_DENY = 'deny'
INTENT_ASK_OPTIONS = 'ask_options'
INTENT_MORE_OPTIONS = 'ask_more_options'
INTENT_PREVIOUS_OPTIONS = 'ask_previous_options'
INTENT_SELECT_OPTION = 'select_option'
INTENT_RESTART = 'restart'

UTTER_ASK_REPHRASE = 'utter_ask_rephrase'

RESULT_SLOT = 'options_results'
RESULT_OFFSET_SLOT = 'options_offset'
RESULT_CHOICE_SLOT = 'options_choice'
VALIDATION_RESULT_SLOT = 'is_choice_valid'
TRANSACTION_RESULT_SLOT = 'transaction_result'
TRANSACTION_ERROR_SLOT = 'transaction_error'

ENDPOINTS_FILE = f'{os.path.dirname(os.path.abspath(__file__))}/endpoints.yml'
DATABASE_ENDPOINT_KEY = 'database_endpoint'
DUCKLING_ENDPOINT_KEY = 'duckling_endpoint'
MAX_PROPOSE_OPTIONS = 5

INTERMEDIATE_RESULTS_TABLE = 'matches'


class DateTypeEnum(Enum):
    date = 1
    time = 2
    datetime = 3


# RASA specific operations
def get_latest_intent(tracker: "Tracker"):
    return tracker.latest_message['intent']['name']


def update_constraints(old_constraints, new_constraints: Dict[str, Dict[str, List[Dict[str, any]]]]):
    for table_name, column_constraints in new_constraints.items():
        old_constraints[table_name].update(new_constraints[table_name])


def has_non_dont_care_constraints(constraints: Dict[str, Dict[str, List[Dict[str, any]]]]):
    return any([any([c['values'] != [DONT_CARE] for c in constr])
                for table, column_constraints in constraints.items()
                for column, constr in column_constraints.items()])


# NL tools
def get_transaction_nl(transaction_name):
    procedure = list(filter(lambda p: p['name'] == transaction_name, SCHEMA_CONFIG['procedures']))[0]
    return procedure['nl']


def get_table_nl(table_name):
    table = list(filter(lambda t: t['name'] == table_name, SCHEMA_CONFIG['tables']))[0]
    return random.choice(table['nl'])


def get_column_nl(table_name, column_name):
    table = list(filter(lambda t: t['name'] == table_name, SCHEMA_CONFIG['tables']))[0]
    column = list(filter(lambda c: c['name'] == column_name, table['columns']))[0]
    return random.choice(column['nl'])


# JSON tools
def set_serialized_slot(slot: str, value: any) -> EventType:
    return SlotSet(slot, json_serialize(value))


def get_deserialized_slot(tracker, slot) -> any:
    return json_deserialize(tracker.get_slot(slot))


def custom_json_serializer(obj, json_options=json_util.DEFAULT_JSON_OPTIONS):
    if isinstance(obj, datetime.date):
        return {"$date.date": "%s" % obj.isoformat()}
    if isinstance(obj, datetime.time):
        return {"$date.time": "%s" % obj.isoformat()}
    return json_util.default(obj, json_options=json_options)


def custom_json_object_hook(dct, json_options=json_util.DEFAULT_JSON_OPTIONS):
    if "$date.date" in dct:
        return datetime.date.fromisoformat(dct["$date.date"])
    if "$date.time" in dct:
        return datetime.time.fromisoformat(dct["$date.time"])
    return json_util.object_hook(dct, json_options=json_options)


def json_serialize(obj: any):
    return json.dumps(obj, default=custom_json_serializer)


def json_deserialize(s: str):
    return json.loads(s, object_hook=custom_json_object_hook)


def load_json(filepath):
    json_path = os.path.join(PROJECT_ROOT, filepath)
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(e)


def get_placeholders(template: str):
    return re.findall('{(.+?)}', template)


def to_human_readable(obj: any):
    if isinstance(obj, datetime.datetime):
        return obj.strftime('%dth %B %Y %H:%M:%S')
    if isinstance(obj, datetime.date):
        return obj.strftime('%dth %B %Y')
    if isinstance(obj, datetime.time):
        return obj.strftime('%H:%M:%S')
    if isinstance(obj, bool):
        return "yes" if obj else "no"
    return str(obj)


def normalize_choice(choice: str, target_data_type: str, duckling: Duckling):
    normalized = None
    if target_data_type == 'string':
        return choice
    elif target_data_type == 'date':
        normalized, _ = duckling.parse_date(choice)
        return normalized
    elif target_data_type == 'datetime':
        normalized, _ = duckling.parse_datetime(choice)
        return normalized
    elif target_data_type == 'time':
        normalized, _ = duckling.parse_time(choice)
        return normalized
    elif target_data_type == 'integer':
        normalized, _ = duckling.parse_numeric(choice)
        return int(normalized)
    elif target_data_type == 'float':
        normalized, _ = duckling.parse_numeric(choice)
        return float(normalized)
    return normalized


def clean_error(text: str):
    error_start = text.find(':') + 1
    return text[error_start:].strip()


SCHEMA_CONFIG = load_json(SCHEMA_CONFIG_FILE)
