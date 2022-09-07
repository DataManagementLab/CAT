from cat.simulation.interaction.frames import TransactionFrame, ChoiceFrame, SelectFrame

from cat.simulation.nlg.common import *
from datetime import datetime, timedelta

from cat.simulation.nlg.paraphrasing import PPDBParaphraser, GooglePivotParaphraser, AbstractParaphraser

logger = logging.getLogger('nlg')


class NlgEngine:

    def __init__(self, intent_templates: Dict[str, str] = {}, lookup_table_dir='data/lookup_tables/',
                 paraphraser_names: List[str] = [], pivot_languages: List[str] = []):
        self.db: PostgreSQLDatabase = PostgreSQLDatabase.get_instance()
        self.nlu_data = NLU_DATA_TEMPLATE
        self.intents = []
        self.form_slots = []
        self.form_slot_names = []
        self.intent_templates = dict(DEFAULT_INTENT_TEMPLATES)
        self.intent_templates.update(intent_templates)
        self.lookup_tables = []
        self.lookup_table_dir = lookup_table_dir
        self.paraphrasers: List[AbstractParaphraser] = [p for p in [self._get_paraphraser(n, pivot_languages) for n in paraphraser_names] if p]
        if self.paraphrasers:
            self._paraphrase_templates()

    def _get_paraphraser(self, name, languages=[]):
        if name == 'p':
            return PPDBParaphraser()
        if name == 'g':
            if len(set(languages)) < 2:
                logger.error(f'Expected at least 2 langauges for pivot paraphrasing but got {languages}')
                return None
            if languages[0] != languages[-1]:
                languages.append(languages[0])
            return GooglePivotParaphraser(languages=languages)
        return None

    def _paraphrase_templates(self):
        for key, templates in self.intent_templates.items():
            paraphrased = []
            for template in templates:
                for p in self.paraphrasers:
                    paraphrase = p.paraphrase_sentence(template)
                    if paraphrase and paraphrase not in templates and paraphrase not in paraphrased:
                        paraphrased.append(paraphrase)
            logger.info(f'Generated {len(paraphrased)} paraphrases for intent {key}')
            self.intent_templates[key] += paraphrased

    def _add_intent(self, intent_name: str):
        if intent_name not in self.intents:
            self.intents.append(intent_name)

    def add_form_slot(self, slot: Slot):
        if slot.name not in self.form_slot_names:
            self.form_slot_names.append(slot.name)
            self.form_slots.append(slot)

    def phrase_default_intents(self):
        logger.info('Phrasing default intents')
        for intent in DEFAULT_INTENTS:
            self._phrase_intent(intent)

    def phrase_options_intents(self, num_phrases=5):
        logger.info('Phrasing option selection intents')
        for intent in [AskMoreOptions(), AskPreviousOptions(), AskOptions()]:
            self._phrase_intent(intent)

        # the select option intents have a choice slot
        select_option_intent = SelectOption("dummy")
        self._add_intent(INTENT_SELECT_OPTION)
        for template in self.intent_templates[INTENT_SELECT_OPTION]:
            for i in range(num_phrases):
                choice_number = random.randint(1, MAX_RESULTS)
                choice = rephrase_integer(choice_number, to_ordinal=random.choice([True, False]))
                phrasing = template.format(choice=choice)
                entity_start, entity_end = find_string_start_end(phrasing, choice)
                entity = get_entity_example(entity_start, entity_end, OPTION_CHOICE_SLOT, choice)
                example = get_common_example(select_option_intent.name, phrasing, [entity])
                self._add_common_example(example)

    def _phrase_intent(self, intent: Intent):
        logger.debug(f'Found {len(self.intent_templates[intent.name])} examples for intent {intent.name}')
        self._add_intent(intent.name)
        for phrasing in self.intent_templates[intent.name]:
            example = get_common_example(intent.name, phrasing)
            self._add_common_example(example)

    def phrase_transaction_intent(self, frame: TransactionFrame, num_samples_per_template=100):
        logger.info(f'Phrasing transaction intent {frame.name} with {num_samples_per_template} samples')
        intent = Transaction(frame.name)
        intent_name = intent.name
        if intent_name not in self.intents:
            self._add_intent(intent_name)
            select_frame_slots = [slot for subframe in frame.subframes if isinstance(subframe, SelectFrame) for slot in
                                  subframe.slots if slot.requestable]
            choice_frame_slots = [slot for subframe in frame.subframes if isinstance(subframe, ChoiceFrame) for slot in
                                  subframe.slots if slot.requestable]
            all_slots = select_frame_slots + choice_frame_slots
            key = intent_name if intent_name in self.intent_templates.keys() else 'begin_transaction'
            num_templates = len(self.intent_templates[key])
            ti = 0
            for phrasing in self.intent_templates[key]:
                ti += 1
                logger.debug(f'Template {ti}/{num_templates}')
                required_form_slots = get_template_slots(phrasing, select_frame_slots)
                required_choice_slots = get_template_slots(phrasing, choice_frame_slots)
                required_nl_slots, required_table_nl_slots = get_nl_slots(phrasing, all_slots)
                # only phrase one sample if no entity slots
                num_phrasings = num_samples_per_template if len(required_form_slots) + len(
                    required_choice_slots) > 0 else 1

                # generate phrasing for each predicate/argument pair
                if is_predicate_argument_template(phrasing):
                    for predicate, argument in frame.task.nl:
                        format_values = {'predicate': predicate, 'argument': argument}
                        for i in range(num_phrasings):
                            formatted_phrasing, entities = self._phrase_slotted_template(phrasing, required_form_slots,
                                                                                         required_choice_slots,
                                                                                         required_nl_slots,
                                                                                         required_table_nl_slots,
                                                                                         format_values)
                            example = get_common_example(intent_name, formatted_phrasing, entities)
                            self._add_common_example(example)
                else:
                    for i in range(num_phrasings):
                        formatted_phrasing, entities = self._phrase_slotted_template(phrasing, required_form_slots,
                                                                                     required_choice_slots,
                                                                                     required_nl_slots,
                                                                                     required_table_nl_slots)
                        example = get_common_example(intent_name, formatted_phrasing, entities)
                        self._add_common_example(example)

    def phrase_inform_form_intents(self, frame: SelectFrame, num_samples_per_template=100):
        logger.info(
            f'Phrasing form inform intents for table {frame.table_name} with each {num_samples_per_template} samples')
        self._add_intent(INTENT_INFORM)
        for slot in [s for s in self.form_slots if s.requestable]:
            if len(slot.lookup_table) > 0:
                self._add_lookup_table(slot.name, slot.lookup_table)
            for value, synonyms in slot.entity_synonyms.items():
                self._add_entity_synonym(value, synonyms)
            if slot.regex:
                self._add_regex_feature(slot.name, slot.regex)

        key = f'inform_form_{frame.table_name}'
        if key not in self.intent_templates.keys():
            logger.debug(f'Cannot find templates for intent {key}, using default templates')
            key = 'inform_form'
        num_templates = len(self.intent_templates[key])
        ti = 0
        for template in self.intent_templates[key]:
            ti += 1
            logger.debug(f'Template {ti}/{num_templates}')
            for i in range(num_samples_per_template):
                required_slots = get_template_slots(template, self.form_slots)
                required_nl_slots, required_table_nl_slots = get_nl_slots(template, self.form_slots)
                phrasing, entities = self._phrase_slotted_template(template, required_slots, [], required_nl_slots,
                                                                   required_table_nl_slots)
                example = get_common_example(INTENT_INFORM, phrasing, entities)
                self._add_common_example(example)

        for slot in [slot for slot in self.form_slots if slot.data_type == 'bool']:
            self.phrase_inform_bool_intents(slot)

    def phrase_inform_choice_intents(self, slot: Slot, num_samples_per_template=100):
        key = f'inform_{slot.name}'
        logger.info(f'Phrasing inform templates for intent {key} with {num_samples_per_template} samples')
        if key not in self.intent_templates.keys():
            logger.debug(f'Cannot find templates for intent {key}, using default templates')
            key = 'inform_choice'
        num_templates = len(self.intent_templates[key])
        ti = 0
        for template in self.intent_templates[key]:
            ti += 1
            logger.debug(f'Template {ti}/{num_templates}')
            choice_template = template.format(slot_name='{slot_name}', choice=f'{{{slot.name}}}')
            for i in range(num_samples_per_template):
                format_values = {
                    SLOT_NAME: random.choice(slot.column_nl),
                    slot.name: self._get_sample_choice_value(slot)
                }
                phrasing, entities = self._phrase_slotted_template(choice_template, in_format_values=format_values)
                example = get_common_example('inform', phrasing, entities)
                self._add_common_example(example)

    def phrase_inform_bool_intents(self, slot: Slot):
        intent_name = f'inform_bool_{slot.name}_true'
        self._add_intent(intent_name)
        key = intent_name
        logger.info(f'Phrasing positive inform boolean templates for {key}')
        if key not in self.intent_templates.keys():
            logger.debug(f'Cannot find positive templates for intent {key}, using default templates')
            key = 'inform_bool_true'
        num_templates = len(self.intent_templates[key])
        ti = 0
        for template in self.intent_templates[key]:
            ti += 1
            logger.debug(f'Template {ti}/{num_templates}')
            if '{slot_name}' in template:
                for slot_nl in slot.column_nl:
                    phrasing = template.format(slot_name=slot_nl)
                    example = get_common_example(intent_name, phrasing, [])
                    self._add_common_example(example)
            else:
                example = get_common_example(intent_name, template, [])
                self._add_common_example(example)

        intent_name = f'inform_bool_{slot.name}_false'
        self._add_intent(intent_name)
        key = intent_name
        logger.info(f'Phrasing negative inform boolean templates for {key}')
        if key not in self.intent_templates.keys():
            logger.debug(f'Cannot find negative templates for intent {key}, using default templates')
            key = 'inform_bool_false'
        num_templates = len(self.intent_templates[key])
        ti = 0
        for template in self.intent_templates[key]:
            ti += 1
            logger.debug(f'Template {ti}/{num_templates}')
            if '{slot_name}' in template:
                for slot_nl in slot.column_nl:
                    phrasing = template.format(slot_name=slot_nl)
                    example = get_common_example(intent_name, phrasing, [])
                    self._add_common_example(example)
            else:
                example = get_common_example(intent_name, template, [])
                self._add_common_example(example)

    def _phrase_slotted_template(self, template: str, form_slots=[], choice_slots=[], nl_slots=[], table_nl_slots=[],
                                 in_format_values={},
                                 numeric_operator_ratio=0.5):
        format_values = dict(in_format_values)
        for slot in form_slots:
            data_type = self.db.get_python_datatype(slot.data_type)
            if data_type in ['integer', 'float'] and random.uniform(0.0, 1.0) < numeric_operator_ratio:
                operator, operator_phrasing = phrase_numeric_operator()
                if operator == '>=<':
                    format_values[slot.name] = f'{operator_phrasing}'.format(
                        value1=str(self._get_sample_form_value(slot)),
                        value2=str(self._get_sample_form_value(slot)))
                else:
                    format_values[slot.name] = f'{operator_phrasing} {str(self._get_sample_form_value(slot))}'
            else:
                format_values[slot.name] = self._get_sample_form_value(slot)
        for slot in choice_slots:
            format_values[slot.name] = self._get_sample_choice_value(slot)
        for slot in nl_slots:
            format_values[f'{slot.name}_nl'] = random.choice(slot.column_nl)
        for slot in table_nl_slots:
            format_values[f'{slot_to_table(slot.name)}_nl'] = random.choice(slot.table_nl) if len(
                slot.table_nl) > 0 else None
        return get_phrasing_entities(template, format_values)

    def _get_sample_form_value(self, slot: Slot, operator_ratio=0.5):
        table_name, column_name = slot_to_table_column(slot.name)
        sample_value = self.db.get_column_sample(table_name, column_name)
        if not sample_value:
            return self._get_sample_choice_value(slot)
        return self._rephrase_value(self.db.get_python_datatype(slot.data_type), sample_value[column_name])

    def _get_sample_choice_value(self, slot: Slot):
        sample_value = None
        data_type = self.db.get_python_datatype(slot.data_type)
        if data_type == 'bool':
            sample_value = random.choice([True, False])
        elif data_type in ['date', 'time', 'datetime']:
            sample_value = datetime.now() + timedelta(days=random.randint(-100, 100), hours=random.randint(0, 23),
                                                      minutes=random.randint(0, 59), seconds=random.randint(0, 59))
        elif data_type == 'integer':
            sample_value = random.randint(0, 100)
        elif data_type == 'float':
            sample_value = round(random.uniform(0.5, 10.0), 2)
        else:
            logger.error(f'Cannot sample datatype {data_type}')
        return self._rephrase_value(data_type, sample_value)

    def _rephrase_value(self, data_type: str, value: any):
        if data_type == 'date':
            return rephrase_date(value)
        if data_type == 'time':
            return rephrase_time(value)
        if data_type == 'datetime':
            return rephrase_datetime(value)
        if data_type == 'string':
            return rephrase_string(value)
        if data_type == 'integer':
            return rephrase_integer(value)
        if data_type == 'float':
            return rephrase_float(value)
        if data_type == 'bool':
            return rephrase_bool(value)
        return str(value) if random.choice([True, False]) else str(value).lower()

    def _add_common_example(self, example):
        self.nlu_data[RASA_NLU_DATA_KEY][COMMON_EXAMPLES_KEY].append(example)

    def _add_entity_synonym(self, entity: str, synonyms: List[str]):
        if entity not in [s['value'] for s in self.nlu_data[RASA_NLU_DATA_KEY][ENTITY_SYNONYMS_KEY]]:
            self.nlu_data[RASA_NLU_DATA_KEY][ENTITY_SYNONYMS_KEY].append({
                'value': entity,
                'synonyms': synonyms
            })

    def _add_lookup_table(self, name: str, elements: List[str]):
        if name not in [lt['name'] for lt in self.nlu_data[RASA_NLU_DATA_KEY][LOOKUP_TABLES_KEY]]:
            lookup_file_name = f'{name}.txt'
            relative_lookup_dir = f'{self.lookup_table_dir}{lookup_file_name}'
            self.lookup_tables.append({
                'name': name,
                'elements': elements,
                'file': lookup_file_name
            })

            self.nlu_data[RASA_NLU_DATA_KEY][LOOKUP_TABLES_KEY].append({
                'name': name,
                'elements': relative_lookup_dir
            })

    def _add_regex_feature(self, entity: str, regex: str):
        if entity not in [rf['name'] for rf in self.nlu_data[RASA_NLU_DATA_KEY][REGEX_FEATURES_KEY]]:
            self.nlu_data[RASA_NLU_DATA_KEY][REGEX_FEATURES_KEY].append({
                'name': entity,
                'pattern': regex
            })
