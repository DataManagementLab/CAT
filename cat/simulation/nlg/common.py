from cat.simulation.common.intents import *
from cat.simulation.common.model import Slot
import copy
import re
from num2words import num2words
from cat.db.database import *
from typing import List, Dict
from numpy import random
from datetime import datetime


RASA_NLU_DATA_KEY = 'rasa_nlu_data'
COMMON_EXAMPLES_KEY = 'common_examples'
REGEX_FEATURES_KEY = 'regex_features'
LOOKUP_TABLES_KEY = 'lookup_tables'
ENTITY_SYNONYMS_KEY = 'entity_synonyms'

NLU_DATA_TEMPLATE = {
    RASA_NLU_DATA_KEY: {
        COMMON_EXAMPLES_KEY: [],
        REGEX_FEATURES_KEY: [],
        LOOKUP_TABLES_KEY: [],
        ENTITY_SYNONYMS_KEY: []
    }
}

INTENT_TEMPLATE = {
    'text': None,
    'intent': None,
    'entities': []
}

ENTITY_TEMPLATE = {
    'start': None,
    'end': None,
    'value': None,
    'entity': None
}

DEFAULT_INTENT_TEMPLATES = {
    'begin_transaction': ['I want to {predicate} {argument}', 'Can you {predicate} {argument}',
                          'I would like to {predicate} {argument}', 'I''d like to {predicate} {argument}'],
    'greeting': ['Hey', 'Hello', 'Hi', 'Hi!', 'Hola', 'Hi there'],
    'goodbye': ['Bye', 'Goodbye'],
    'affirm': ['Ok', 'Okay', 'Yes', 'That''s fine', 'Fine', 'Alright', 'Yes please'],
    'deny': ['No', 'That''s wrong', 'Nope', 'Nah'],
    'ask_options': ['What are my options?', 'What are the current results?'],
    'ask_more_options': ['Can you show me more options?', 'Show me more'],
    'ask_previous_options': ['Can you scroll back?', 'Can you go back?', 'Can you show me the previous options?'],
    'select_option': ['Ill go for option {choice}', 'I want option {choice}'],
    'dont_care': ['I don''t know', 'Dont''t know', 'I don''t care', 'Dont care'],
    'done': ['Thats it', 'No I''m done', 'Done', 'That''s it thanks', 'That''s it thank you'],
    'give_up': ['That''s not what I wanted', 'You can''t help me'],
    'out_of_scope': [],
    'restart': ['Restart', 'Start over', 'Lets start again', 'Please restart'],
    'inform_form': [],
    'inform_choice': ['Set {slot_name} to {choice}', 'I want {choice} {slot_name}', 'I want {choice}', '{choice}'],
    'select_option': ['Give me option {choice}', 'I want the {choice} option', 'Choose the {choice}'],
    'inform_bool_true': ['I want {slot_name}'],
    'inform_bool_false': ['I do not want want {slot_name}']
}

DEFAULT_INTENTS = [Greet(), Bye(), Affirm(), Deny(), DontCare(), Done(), GiveUp(), Restart(), OutOfScope()]
OPTIONS_INTENTS = [AskOptions(), AskPreviousOptions(), AskMoreOptions()]

PREDICATE = 'predicate'
ARGUMENT = 'argument'
SLOT_NAME = 'slot_name'
CHOICE = 'choice'
NL_SUFFIX = '_nl'

RELATIVE_DATE_OPERATORS = ['before', 'after', 'from', 'until', 'to', 'til', 'starting', 'ending', '']
RELATIVE_DATE_DESCRIPTORS = ['last', 'next', 'this', '']
RELATIVE_DATE_PHRASINGS = ['today', 'tomorrow', 'yesterday', 'the day after tomorrow', 'week', 'month',
                           'year', 'day', 'after', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Saturday', 'Sunday',
                           'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
                           'October', 'November', 'December']
DATE_STRING_FORMATS = ['%A the %wth', '%d %B', '%A the %w of %B', '%d/%m', '%d.%m.', '%d.%m.%y', '%d/%m/%y',
                       '%d.%m.%Y', '%x', '%A %B %d %Y']
TIME_STRING_FORMATS = ['%I%p', '%I %p', '%H:%M', '%I:%M', '%H:%M:%S', '%H.%M', '%H.%M.%S', '%H:%M%p', '%H:%M %p', '%X']

NUMERIC_OPERATORS = {
    '<': ['less than', 'fewer than', 'below'],
    '>': ['more than', 'over', 'above', 'bigger than', 'greater than'],
    '<=': ['tops', 'not more than', 'no more than', 'maximum of', 'at most'],
    '>=': ['at least', 'minimum', 'minimal', 'not fewer than'],
    '>=<': ['between {value1} and {value2}', 'from {value1} to {value2}']
}

TRUE_PHRASINGS = ['Yes', 'Yas', 'True', 'Yep']
FALSE_PHRASINGS = ['No', 'Nope', 'Nah']

SPECIAL_CHARACTERS_REGEX = re.compile('[()\[\]/\\\]+')


def get_template_slots(template: str, slots: List[Slot]):
    required_slots = []
    for slot in slots:
        if f'{{{slot.name}}}' in template:
            required_slots.append(slot)
    return required_slots


def get_nl_slots(template: str, slots: List[Slot]):
    nl_slots = []
    table_nl_slots = []
    for slot in slots:
        if f'{{{slot.name}_nl}}' in template:
            nl_slots.append(slot)
        if f'{{{slot_to_table(slot.name)}_nl}}' in template:
            table_nl_slots.append(slot)
    return nl_slots, table_nl_slots


def is_predicate_argument_template(template: str):
    return '{predicate}' in template or '{argument}' in template


def is_slotted_template(template: str):
    return len(re.findall('{(.+?)}', template)) > 0


def get_template_placeholders(template: str):
    return re.findall('{(.+?)}', template)


def num_to_word(num: int, to_ordinal=False):
    if to_ordinal:
        return num2words(num, to='ordinal')
    return num2words(num)


def replace_special_characters(value: str):
    return re.sub(SPECIAL_CHARACTERS_REGEX, '', value).strip()


def rephrase_date(value, relative_quota=0.5):
    if random.uniform(0.0, 1.0) < relative_quota:
        operator = random.choice(RELATIVE_DATE_OPERATORS)
        descriptor = random.choice(RELATIVE_DATE_DESCRIPTORS)
        phrasing = random.choice(RELATIVE_DATE_PHRASINGS)
        return f'{operator} {descriptor} {phrasing}'.strip().replace('  ', ' ')
    else:
        format = random.choice(DATE_STRING_FORMATS)
        if value.year <= 1900:
            value = datetime.now().date()
        return value.strftime(format=format)


def rephrase_time(value):
    return value.strftime(random.choice(TIME_STRING_FORMATS))


def rephrase_datetime(value, use_connector=0.5):
    s = rephrase_date(value)
    if random.uniform(0.0, 1.0) > use_connector:
        s += ' at'
    s += f' {rephrase_time(value)}'
    return s


def rephrase_string(value: str, obfuscation_quota=0.3):
    value = value = replace_special_characters(value)
    # lower
    if random.choice([True, False]):
        value = value.lower()
    tokens = value.split(' ')
    if len(tokens) < 2:
        return value.strip()
    # strip last token
    if random.uniform(0.0, 1.0) < obfuscation_quota:
        # drop one token at the end
        return replace_special_characters(' '.join(tokens[:-1])).strip()
    return value.strip()


def rephrase_integer(value: int, word_quota=0.3, to_ordinal=False):
    if random.uniform(0.0, 1.0) < word_quota:
        return num_to_word(value, to_ordinal)
    return str(value).strip()


def rephrase_float(value: float, comma_quota=0.5):
    # if random.uniform(0.0, 1.0) < comma_quota:
    #    return str(value).replace('.', ',')
    return value


def rephrase_bool(value: bool):
    if value:
        return random.choice(TRUE_PHRASINGS)
    return random.choice(FALSE_PHRASINGS)


def phrase_numeric_operator():
    operator = random.choice(list(NUMERIC_OPERATORS.keys()))
    return operator, random.choice(NUMERIC_OPERATORS[operator])


def find_string_start_end(text, s):
    try:
        match = re.search(r'\b({s})(?:\s|$|\b|\.|\?|,)'.format(s=s), text)
    except Exception as e:
        logger.error(e)
        return None, None
    if not match:
        return None, None
    start = match.start(1)
    return start, start + len(s)


def get_phrasing_entities(template, format_values):
    entities = []
    phrasing = template.format(**format_values)
    last_end = 0
    # sort items by occurence in the template so we can use the "last_end" for identifying the index
    try:
        sorted_format_values = sorted(filter(lambda p: p[0] in template, format_values.items()),
                                      key=lambda t: template.index(f'{{{t[0]}}}'))
    except ValueError:
        logger.error(f'Placeholder not found in template')
    for placeholder, value in sorted_format_values:
        if placeholder in ['predicate', 'argument', 'slot_name'] or placeholder.endswith(NL_SUFFIX):
            continue
        str_value = str(value)
        try:
            start, end = find_string_start_end(phrasing[last_end:], str_value)
            if start is None:
                logger.error(f'Could not find "{str_value}" in "{phrasing}')
                continue
            entity_start = last_end + start
            entity_end = entity_start + len(str_value)
            last_end = entity_end
            entity = get_entity_example(start=entity_start, end=entity_end, entity_name=placeholder,
                                        value=str_value)
            entities.append(entity)
        except ValueError:
            logger.error(f'"{str_value}" not found in phrasing "{phrasing}"')
    return phrasing, entities

def get_entity_example(start: int, end: int, entity_name: str, value: str) -> Dict[str, str]:
    entity_example = copy.deepcopy(ENTITY_TEMPLATE)
    entity_example['start'] = start
    entity_example['end'] = end
    entity_example['entity'] = entity_name
    entity_example['value'] = value
    return entity_example


def get_common_example(intent: str, text: str, entities: List[Dict] = []):
    intent_example = copy.deepcopy(INTENT_TEMPLATE)
    intent_example['intent'] = intent
    intent_example['text'] = text
    intent_example['entities'] = entities
    return intent_example
