import logging
from cat.simulation.common.actions import *
from cat.simulation.common.intents import *
from cat.simulation.common.constants import *
from cat.simulation.common.persistence import Persistor
from cat.simulation.interaction.frames import TransactionFrame, SelectFrame

DOMAIN_SESSION_CONFIG_KEY = 'session_config'
DOMAIN_SESSION_CONFIG_EXPIRATION_KEY = 'session_expiration_time'
DOMAIN_SESSION_CONFIG_CARRY_OVER_KEY = 'carry_over_slots_to_new_session'
DOMAIN_ACTIONS_KEY = 'actions'
DOMAIN_ENTITIES_KEY = 'entities'
DOMAIN_INTENTS_KEY = 'intents'
DOMAIN_SLOTS_KEY = 'slots'
DOMAIN_TEMPLATES_KEY = 'responses'

DOMAIN_TEMPLATE = {
    DOMAIN_SESSION_CONFIG_KEY: {
        DOMAIN_SESSION_CONFIG_EXPIRATION_KEY: 60,
        DOMAIN_SESSION_CONFIG_CARRY_OVER_KEY: False
    },
    DOMAIN_ENTITIES_KEY: [],
    DOMAIN_INTENTS_KEY: [],
    DOMAIN_ACTIONS_KEY: [],
    DOMAIN_SLOTS_KEY: {},
    DOMAIN_TEMPLATES_KEY: {}
}

DEFAULT_POLICIES = [
    {'name': 'FormPolicy'},
    {'batch_strategy': 'balanced',
     'random_seed': 200, 'epochs': 30,
     'batch_size': 5,
     'max_training_samples': 500,
     'featurizer': [{
         'name': 'FullDialogueTrackerFeaturizer',
         'state_featurizer': [{
             'name': 'BinarySingleStateFeaturizer'
         }],
     }],
     'early_stopping': {
         'monitor': 'acc',
         'mode': 'max',
         'min_delta': 0.005,
         'verbose': 1,
         'patience': 5
     },
     'name': 'policies.TEDEarlyStoppingPolicy'
     },
    {'max_history': 3, 'name': 'MemoizationPolicy'},
    {'name': 'MappingPolicy'},
    {'nlu_threshold': 0.6,
     'ambiguity_threshold': 0.1,
     'name': 'TwoStageFallbackPolicy'
     }
]

# Default "supervised_embeddings" pipeline
DEFAULT_NLU_PIPELINE = [
    {'name': 'HFTransformersNLP',
     'model_name': 'bert'
     },
    {'name': 'LanguageModelTokenizer',
     'intent_tokenization_flag': False,
     'intent_split_symbol': '_'
     },
    {'name': 'LanguageModelFeaturizer'},
    {'epochs': 100,
     'name': 'DIETClassifier'
     }
]

logger = logging.getLogger('rasa-builder')


class RasaBuilder:
    def __init__(self,
                 frames: List[TransactionFrame],
                 intents: Intent,
                 responses: List[UtteranceAction],
                 actions: List[AbstractAction],
                 schema_name: str,
                 persistor: Persistor):
        self.persistor = persistor
        self.frames = frames
        self.domain = copy.deepcopy(DOMAIN_TEMPLATE)
        self.endpoints = {}
        self.config = {}
        self.credentials = {}
        self.intents = intents
        self.responses = responses
        self.actions = actions
        self.schema_name = schema_name

    def build_files(self):
        logger.info('Building domain')
        self._build_domain()
        logger.info('Building endpoints')
        self._build_endpoints()
        logger.info('Building config')
        self._build_config()
        logger.info('Building credentials')
        self._build_credentials()
        self.domain[DOMAIN_INTENTS_KEY] = self.intents

    def persist(self):
        self.persistor.persist_domain(self.domain)
        self.persistor.persist_config(self.config)
        self.persistor.persist_endpoints(self.endpoints)
        self.persistor.persist_credentials(self.credentials)
        self.persistor.copy_utils()

    def _add_slot_to_domain(self, slot_name, slot_type=LIST_SLOT_TYPE, is_entity=True):
        if slot_name not in self.domain[DOMAIN_SLOTS_KEY].keys():
            self.domain[DOMAIN_SLOTS_KEY][slot_name] = {'type': slot_type}
        if is_entity and slot_name not in self.domain[DOMAIN_ENTITIES_KEY]:
            self.domain[DOMAIN_ENTITIES_KEY].append(slot_name)

    def _add_action_to_domain(self, action: AbstractAction):
        action_name = str(action)
        if action_name not in self.domain[DOMAIN_ACTIONS_KEY]:
            self.domain[DOMAIN_ACTIONS_KEY].append(action_name)
            self.domain[DOMAIN_TEMPLATES_KEY][action_name] = [{'text': f'{t}'} for t in action.templates]

    def _build_domain(self):
        self._extract_slots_and_entities()
        self._add_default_actions()
        self._add_responses()
        self._add_actions()

    def _extract_slots_and_entities(self):
        # slots for user option selection
        self._add_slot_to_domain(OPTION_CHOICE_SLOT, slot_type=TEXT_SLOT_TYPE, is_entity=True)
        self._add_slot_to_domain(OPTION_RESULTS_SLOT, slot_type=TEXT_SLOT_TYPE, is_entity=False)
        self._add_slot_to_domain(OPTION_OFFSET_SLOT, slot_type=TEXT_SLOT_TYPE, is_entity=False)
        # slot for choice validation
        self._add_slot_to_domain(VALIDATION_RESULT_SLOT, slot_type=BOOL_SLOT_TYPE, is_entity=False)
        # slot for transaction results and errors
        self._add_slot_to_domain(TRANSACTION_RESULT_SLOT, slot_type=TEXT_SLOT_TYPE, is_entity=False)
        self._add_slot_to_domain(TRANSACTION_ERROR_SLOT, slot_type=TEXT_SLOT_TYPE, is_entity=False)

        # frame based slots
        for frame in self.frames:
            self._add_slot_to_domain(f'transaction_error_{frame.name}', is_entity=False)
            for return_slot in frame.return_slot_names:
                self._add_slot_to_domain(return_slot, TEXT_SLOT_TYPE, False)
            for slot in frame.slots:
                slot_type = BOOL_SLOT_TYPE if slot.data_type == 'bool' else TEXT_SLOT_TYPE
                self._add_slot_to_domain(slot.name, slot_type)
            for subframe in frame.subframes:
                if isinstance(subframe, SelectFrame):
                    # form requires a 'requested_slot'
                    self._add_slot_to_domain(slot_name=REQUESTED_SLOT, slot_type=UNFEATURIZED_SLOT_TYPE,
                                             is_entity=False)
                for slot in subframe.slots:
                    # select uses FormAction that requires unfeaturized slots
                    if isinstance(subframe, SelectFrame):
                        self._add_slot_to_domain(slot.name, UNFEATURIZED_SLOT_TYPE)
                    elif slot.data_type == 'bool':
                        self._add_slot_to_domain(slot.name, BOOL_SLOT_TYPE)
                    else:
                        self._add_slot_to_domain(slot.name, TEXT_SLOT_TYPE)

    def _add_default_actions(self):
        self._add_action_to_domain(ActionRestartConversation())
        self._add_action_to_domain(ActionDeactivateSelectForm())

    def _add_responses(self):
        for action in self.responses:
            self._add_action_to_domain(action)

    def _add_actions(self):
        for action in self.actions:
            self._add_action_to_domain(action)

    def _build_endpoints(self):
        # default: provide action server
        self.endpoints['action_endpoint'] = {'url': 'http://localhost:5055/webhook'}
        self.endpoints['duckling_endpoint'] = {
            'host': 'localhost',
            'port': 8000,
            'https': False
        }
        self.endpoints['database_endpoint'] = {
            'host': 'localhost',
            'port': 5432,
            'name': 'tcb',
            'schema': self.schema_name,
            'user': 'tcb',
            'password': 'tcb'
        }

    def _build_config(self, language='en', embeddings=DEFAULT_NLU_PIPELINE, policies=DEFAULT_POLICIES):
        self.config['language'] = language
        self.config['pipeline'] = embeddings
        self.config['policies'] = policies

    def _build_credentials(self):
        return
