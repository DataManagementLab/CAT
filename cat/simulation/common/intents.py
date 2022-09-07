from cat.simulation.common.constants import *


class Intent:

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def name(self):
        return self.name

    @staticmethod
    def do_log():
        return True


class Greet(Intent):

    def __init__(self):
        Intent.__init__(self, INTENT_GREET)


class Bye(Intent):

    def __init__(self):
        Intent.__init__(self, INTENT_BYE)


class Affirm(Intent):

    def __init__(self, entity=None):
        self.entity = entity
        Intent.__init__(self, INTENT_AFFIRM)


class Deny(Intent):

    def __init__(self, entity=None):
        self.entity = entity
        Intent.__init__(self, INTENT_DENY)


class Restart(Intent):

    def __init__(self):
        Intent.__init__(self, INTENT_RESTART)


class OutOfScope(Intent):

    def __init__(self):
        Intent.__init__(self, INTENT_OOS)


class AskOptions(Intent):
    def __init__(self):
        Intent.__init__(self, INTENT_ASK_OPTIONS)


class AskPreviousOptions(Intent):

    def __init__(self):
        Intent.__init__(self, INTENT_ASK_PREV_OPTIONS)


class AskMoreOptions(Intent):

    def __init__(self):
        Intent.__init__(self, INTENT_ASK_MORE_OPTIONS)


class Transaction(Intent):

    def __init__(self, transaction, entity_values={}):
        name = f'begin_{transaction}'
        self.transaction = transaction
        self.data = entity_values
        Intent.__init__(self, name)

    def __str__(self):
        base_name = super(Transaction, self).__str__()
        if len(self.data.items()) > 0:
            informed_values = ', '.join([f'"{slot}": "{value}"' for slot, value in self.data.items()])
            return f'{base_name}{{{informed_values}}}'
        return base_name


class Inform(Intent):

    def __init__(self, values):
        self.values = values
        Intent.__init__(self, INTENT_INFORM)

    def __str__(self):
        informs = ', '.join([f'"{entity}": "{value}"' for entity, value in self.values.items()])
        return f'inform{{{informs}}}'


class SelectOption(Intent):

    def __init__(self, value: int):
        self.entity = OPTION_CHOICE_SLOT
        self.value = value
        Intent.__init__(self, INTENT_SELECT_OPTION)

    def __str__(self):
        return f'{INTENT_SELECT_OPTION}{{"{OPTION_CHOICE_SLOT}": {self.value}}}'


class InformBool(Intent):

    def __init__(self, entity, value):
        self.entity = entity
        self.value = value
        Intent.__init__(self, entity)

    def __str__(self):
        return f'inform_bool_{self.entity}_{str(self.value).lower()}'


class InformForm(Inform):

    @staticmethod
    def do_log():
        return False


class DontCare(Intent):

    def __init__(self):
        Intent.__init__(self, INTENT_DONT_CARE)


class Done(Intent):

    def __init__(self):
        Intent.__init__(self, INTENT_DONE)


class GiveUp(Intent):

    def __init__(self):
        Intent.__init__(self, INTENT_GIVE_UP)
