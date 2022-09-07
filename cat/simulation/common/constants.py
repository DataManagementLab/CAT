# intent names
INTENT_GREET = 'greeting'
INTENT_BYE = 'goodbye'
INTENT_AFFIRM = 'affirm'
INTENT_DENY = 'deny'
INTENT_RESTART = 'restart'
INTENT_OOS = 'out_of_scope'
INTENT_ASK_OPTIONS = 'ask_options'
INTENT_ASK_PREV_OPTIONS = 'ask_previous_options'
INTENT_ASK_MORE_OPTIONS = 'ask_more_options'
INTENT_INFORM = 'inform'
INTENT_SELECT_OPTION = 'select_option'
INTENT_DONT_CARE = 'dont_care'
INTENT_DONE = 'done'
INTENT_GIVE_UP = 'give_up'

# simple utterances
UTTER_ASK_HOWCANHELP = 'utter_ask_howcanhelp'
UTTER_BYE = 'utter_bye'
UTTER_ASK_REPHRASE = 'utter_ask_rephrase'
UTTER_ASK_NEXT_TASK = 'utter_ask_next_task'

# slots
REQUESTED_SLOT = 'requested_slot'
OPTION_CHOICE_SLOT = 'options_choice'
OPTION_RESULTS_SLOT = 'options_results'
OPTION_OFFSET_SLOT = 'options_offset'

VALIDATION_RESULT_SLOT = 'is_choice_valid'
TRANSACTION_RESULT_SLOT = 'transaction_result'
TRANSACTION_ERROR_SLOT = 'transaction_error'

# slot types
LIST_SLOT_TYPE = 'list'
TEXT_SLOT_TYPE = 'text'
BOOL_SLOT_TYPE = 'bool'
UNFEATURIZED_SLOT_TYPE = 'unfeaturized'

# constants
MAX_RESULTS = 5

# slot and db specific values
DUMMY_VALUE = 'dummy'
OPERATION_SELECT = 'select'
OPERATION_CALL = 'call'