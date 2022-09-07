from typing import List, Dict

from jinja2 import Environment, FileSystemLoader

from cat.simulation.common.actions import *
from cat.simulation.common.constants import *
from cat.simulation.common.persistence import Persistor
from cat.simulation.interaction.frames import TransactionFrame
from cat.simulation.nlg.engine import NlgEngine

JINJA_TEMPLATE_DIR = 'templates'


class ResponseGenerator:
    def __init__(self,
                 frames: List[TransactionFrame],
                 persistor: Persistor,
                 response_templates: Dict,
                 schema: Dict,
                 schema_name: str):
        self.frames = frames
        self.persistor = persistor
        self.response_templates = response_templates
        self.schema_name = schema_name
        self.schema = schema
        self.responses = []
        self.actions = []

    def generate_responses_actions(self):
        self._extract_responses()
        self._extract_actions()
        self._generate_action_code()
        return self.responses, self.actions

    def _extract_responses(self):
        if UTTER_ASK_HOWCANHELP in self.response_templates.keys():
            self._add_response(UtterGreet(templates=self.response_templates[UTTER_ASK_HOWCANHELP]))
        else:
            self._add_response(UtterGreet())

        if UTTER_BYE in self.response_templates.keys():
            self._add_response(UtterBye(templates=self.response_templates[UTTER_BYE]))
        else:
            self.responses.append(UtterBye())

        if UTTER_ASK_REPHRASE in self.response_templates.keys():
            self._add_response(UtterAskRephrase(templates=self.response_templates[UTTER_ASK_REPHRASE]))
        else:
            self._add_response(UtterAskRephrase())

        if UTTER_ASK_NEXT_TASK in self.response_templates.keys():
            self._add_response(UtterAskNextTask(templates=self.response_templates[UTTER_ASK_NEXT_TASK]))
        else:
            self._add_response(UtterAskNextTask())

        for frame in self.frames:
            if isinstance(frame, TransactionFrame):
                self._add_response(UtterProposeBeginTransaction(frame, templates=self.response_templates[
                    f'utter_propose_begin_transaction_{frame.name}'], init_templates=True))
                for slot in frame.slots:
                    self._add_response(UtterAskParameter(slot, templates=self.response_templates[
                        f'utter_ask_parameter_{slot.name}'
                    ], init_templates=True))
            for subframe in frame.subframes:
                if isinstance(subframe, SelectFrame):
                    for slot in [s for s in subframe.slots if s.requestable]:
                        self._add_response(UtterRequestForm(slot.name, subframe,
                                                            templates=self.response_templates[
                                                                f'utter_ask_{slot.name}'], init_templates=True))
                if isinstance(subframe, ChoiceFrame):
                    self._add_response(UtterRequestChoice(subframe, templates=self.response_templates[
                        f'utter_ask_{subframe.get_slot().name}'], init_templates=True))
                    self._add_response(UtterProposeChoice(subframe, templates=self.response_templates[
                        f'utter_propose_{subframe.get_slot().name}'], init_templates=True))

    def _extract_actions(self):
        for frame in self.frames:
            self._add_action(ActionProposeTransaction(frame, templates=self.response_templates[
                f'utter_propose_transaction_{frame.name}'], init_templates=True))
            self._add_action(ActionExecuteTransaction(frame))
            self._add_action(ActionFailedTransaction(frame, templates=self.response_templates[
                f'utter_failed_transaction_{frame.name}'
            ], init_templates=True))
            self._add_action(ActionSuccessfulTransaction(frame, templates=self.response_templates[
                f'utter_success_transaction_{frame.name}'
            ], init_templates=True))
            for subframe in frame.subframes:
                self._add_action(ActionTransferSlot(subframe, frame))
                if isinstance(subframe, SelectFrame):
                    self._add_action(ActionSelect(subframe))
                    self._add_action(ActionProposeForm(subframe, templates=self.response_templates[
                        f'utter_propose_{subframe.table_name}'], init_templates=True))
                    self._add_action(ActionSaveOption(subframe))
                if isinstance(subframe, ChoiceFrame):
                    slot = subframe.get_slot()
                    if slot.data_type == 'bool':
                        self._add_action(ActionSetBoolChoice(subframe, slot.name, True))
                        self._add_action(ActionSetBoolChoice(subframe, slot.name, False))
                    else:
                        self._add_action(ActionValidateChoice(subframe, slot.name, None))
                self._add_action(ActionClear(subframe))

    def _generate_action_code(self):
        env = Environment(loader=FileSystemLoader('templates'), autoescape=True)
        action_template = env.get_template('actions.j2')
        template_objects = {
            'db': {
                'name': 'tcb',
                'host': 'localhost',
                'port': 5432,
                'schema': self.schema_name,
                'user': 'tcb',
                'password': 'tcb'
            },
            'formActions': [],
            'proposeActions': [],
            'saveOptionActions': [],
            'clearActions': [],
            'transferActions': [],
            'boolActions': [],
            'validationActions': [],
            'proposeTransactionActions': [],
            'executeTransactionActions': [],
            'successTransactionActions': [],
            'failedTransactionActions': [],
            'customActions': []
        }
        for action in self.actions:
            if isinstance(action, ActionSelect):
                template_objects['formActions'].append(action.template_object())
            elif isinstance(action, ActionProposeForm):
                template_objects['proposeActions'].append(action.template_object())
            elif isinstance(action, ActionSaveOption):
                template_objects['saveOptionActions'].append(action.template_object())
            elif isinstance(action, ActionTransferSlot):
                template_objects['transferActions'].append(action.template_object())
            elif isinstance(action, ActionSetBoolChoice):
                template_objects['boolActions'].append(action.template_object())
            elif isinstance(action, ActionValidateChoice):
                template_objects['validationActions'].append(action.template_object())
            elif isinstance(action, ActionClear):
                template_objects['clearActions'].append(action.template_object())
            elif isinstance(action, ActionProposeTransaction):
                template_objects['proposeTransactionActions'].append(action.template_object())
            elif isinstance(action, ActionExecuteTransaction):
                template_objects['executeTransactionActions'].append(action.template_object())
            elif isinstance(action, ActionSuccessfulTransaction):
                template_objects['successTransactionActions'].append(action.template_object(self.schema))
            elif isinstance(action, ActionFailedTransaction):
                template_objects['failedTransactionActions'].append(action.template_object())
            else:
                template_objects['customActions'].append(action.template_object())
        actions_code = action_template.render(template_objects)
        self.persistor.persist_action_code(actions_code)

    def _add_response(self, action: UtteranceAction):
        if action not in self.responses:
            self.responses.append(action)

    def _add_action(self, action: CustomAction):
        if action not in self.actions:
            self.actions.append(action)


class IntentGenerator:
    def __init__(self,
                 frames: List[TransactionFrame],
                 intent_templates: Dict,
                 persistor: Persistor,
                 paraphrasers: List[str] = [],
                 pivot_languages: List[str] = []):
        self.frames = frames
        self.persistor = persistor
        self.intent_templates = intent_templates
        self.nlg_engine = NlgEngine(intent_templates=intent_templates,
                                    paraphraser_names=paraphrasers,
                                    pivot_languages=pivot_languages)

    def generate_intents(self, num_samples):
        self._phrase_intents(num_samples)
        self.persistor.persist_nlu_data(self.nlg_engine.nlu_data, self.nlg_engine.lookup_tables)
        return self.nlg_engine.intents

    def _phrase_intents(self, num_samples):
        logger.info('Phrasing intents')
        self.nlg_engine.phrase_default_intents()
        self.nlg_engine.phrase_options_intents()
        for frame in self.frames:
            self.nlg_engine.phrase_transaction_intent(frame, num_samples)
            for subframe in frame.subframes:
                if isinstance(subframe, ChoiceFrame):
                    slot = subframe.get_slot()
                    if slot.data_type == 'bool':
                        self.nlg_engine.phrase_inform_bool_intents(slot)
                    else:
                        self.nlg_engine.phrase_inform_choice_intents(slot, num_samples)
                if isinstance(subframe, SelectFrame):
                    for slot in subframe.slots:
                        if slot.requestable:
                            self.nlg_engine.add_form_slot(slot)
                    self.nlg_engine.phrase_inform_form_intents(subframe, num_samples)
