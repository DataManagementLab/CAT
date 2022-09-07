import logging
from collections import defaultdict

import json
from abc import ABC

from cat.simulation.nlg.common import *
from cat.simulation.interaction.frames import TransactionFrame, SubFrame, SelectFrame, ChoiceFrame
from cat.simulation.common.model import Slot
from cat.simulation.common.intents import *
from cat.db.common import slot_to_table, column_to_slot, slot_to_table_with_fk, DONT_CARE

logger: logging.Logger = logging.getLogger('actions')


# base class
class AbstractAction(ABC):

    def __init__(self, name: str, templates: List[str] = [], init_templates=False):
        self.name = name
        self.templates = templates
        self.init_templates = init_templates

    def __str__(self):
        return 'action_' + self.name

    def to_natural_language(self):
        pass

    def do_log(self):
        return True

    def __eq__(self, other):
        return isinstance(other, AbstractAction) and self.name == other.name


class ActionUtteranceReverted(AbstractAction):
    def __init__(self):
        AbstractAction.__init__(self, 'back')


class ActionReverted(AbstractAction):
    def __init__(self):
        AbstractAction.__init__(self, 'undo')


class ActionRestartConversation(AbstractAction):
    def __init__(self):
        AbstractAction.__init__(self, 'restart')


class ActionSetSlot(AbstractAction):
    def __init__(self, slot: str, value: any, log: bool = False):
        self.slot = slot
        self.value = value
        self.log = log
        if self.value is not None:
            name = f'slot{{"{self.slot}": {json.dumps(value)}}}'
        else:
            name = f'slot{{"{self.slot}": null}}'
        AbstractAction.__init__(self, name)

    def __str__(self):
        return self.name

    def do_log(self):
        return self.log


class UtteranceAction(AbstractAction):
    def __init__(self, name, templates=[]):
        AbstractAction.__init__(self, name, templates)

    def __str__(self):
        return self.name


# Default actions/utterances
class UtterGreet(UtteranceAction):

    def __init__(self, templates=['Hey, how can i help you?', 'What can I do for you?']):
        UtteranceAction.__init__(self, UTTER_ASK_HOWCANHELP, templates)


class UtterBye(UtteranceAction):

    def __init__(self, templates=['Goodbye', 'Bye']):
        UtteranceAction.__init__(self, UTTER_BYE, templates)


class UtterAskNextTask(UtteranceAction):

    def __init__(self, templates=['Is there anything else i can help you with?']):
        UtteranceAction.__init__(self, UTTER_ASK_NEXT_TASK, templates)


class UtterAskRephrase(UtteranceAction):

    def __init__(self, templates=['Can you rephrase that', 'Sorry i didnt get that can you repeat that?']):
        UtteranceAction.__init__(self, UTTER_ASK_REPHRASE, templates)


class UtterAskParameter(UtteranceAction):

    def __init__(self, param_slot: Slot, templates=['Therefor need the {param_nl}'], init_templates=False):
        self.param_slot = param_slot
        request_templates = []
        if init_templates:
            for t in templates:
                if 'param_nl' in get_template_placeholders(t):
                    for param_nl in self.param_slot.column_nl:
                        request_templates.append(t.format(param_nl=param_nl))
                else:
                    request_templates.append(t)
        UtteranceAction.__init__(self, f'utter_ask_param_{param_slot.name}', request_templates)


class UtterRequestForm(UtteranceAction):
    def __init__(self, slot_name: str, frame: SelectFrame,
                 templates=['Can you please tell me the {table_nl}s {column_nl}',
                            'Alright can you provide me the {table_nl}s {column_nl}'], init_templates=False):
        self.frame = frame
        self.slot = frame.get_slot(slot_name)
        request_templates = []
        if init_templates:
            for t in templates:
                placeholders = get_template_placeholders(t)
                if 'table_nl' in placeholders:
                    for t_nl in self.slot.table_nl:
                        if 'column_nl' in placeholders:
                            for c_nl in self.slot.column_nl:
                                request_templates.append(t.format(table_nl=t_nl, column_nl=c_nl))
                        else:
                            request_templates.append(t.format(table_nl=t_nl))
                else:
                    request_templates.append(t)
        UtteranceAction.__init__(self, f'utter_ask_{slot_name}', request_templates)


class UtterRequestChoice(UtteranceAction):

    def __init__(self, frame: ChoiceFrame,
                 templates=['Can you please tell me the {slot_nl}?', 'Alright, can you provide me the {slot_nl}?'],
                 init_templates=False):
        self.frame = frame
        self.slot = frame.get_slot()
        request_templates = []
        if init_templates:
            for t in templates:
                if '{slot_nl}' not in t:
                    request_templates.append(t)
                else:
                    for nl in self.slot.column_nl:
                        request_templates.append(t.format(slot_nl=nl))
        UtteranceAction.__init__(self, f'utter_ask_{self.slot.name}', request_templates)


class UtterProposeChoice(UtteranceAction):

    def __init__(self, choose_frame: ChoiceFrame,
                 templates=['Alright is {choice} the correct {slot_nl}?', 'Is {choice} the correct choice?'],
                 init_templates=False):
        self.frame = choose_frame
        slot = self.frame.get_slot()
        name = f'utter_propose_{slot.name}'
        propose_templates = []
        if init_templates:
            for t in templates:
                placeholders = get_template_placeholders(t)
                if 'slot_nl' in placeholders:
                    for c_nl in slot.column_nl:
                        propose_templates.append(t.format(slot_nl=c_nl, choice=f'{{{slot.name}}}'))
                else:
                    propose_templates.append(t.format(choice=f'{{{slot.name}}}'))
        UtteranceAction.__init__(self, name, propose_templates)


class UtterProposeBeginTransaction(UtteranceAction):

    def __init__(self, frame: TransactionFrame, templates=['So you want to {predicate} {argument}?'],
                 init_templates=False):
        self.frame = frame
        name = f'utter_propose_begin_transaction_{frame.name}'
        propose_templates = []
        if init_templates:
            for t in templates:
                for predicate, argument in frame.task.nl:
                    propose_templates.append(t.format(predicate=predicate, argument=argument))
        UtteranceAction.__init__(self, name, propose_templates)


# Names of subclasses of this abstract class are logged as is
class AbstractFormAction(AbstractAction):
    def __init__(self, name: str):
        AbstractAction.__init__(self, name)


class ActionStartSelectForm(AbstractFormAction):
    def __init__(self, frame: SelectFrame):
        name = f'select_{frame.table_name}_form'
        AbstractFormAction.__init__(self, name)


class ActionActivateSelectForm(AbstractFormAction):
    def __init__(self, frame: SelectFrame):
        name = f'form{{"name": "action_select_{frame.table_name}_form"}}'
        AbstractFormAction.__init__(self, name)

    def __str__(self):
        return self.name


class ActionDeactivateSelectForm(AbstractAction):

    def __init__(self):
        AbstractAction.__init__(self, name='deactivate_form', templates=[])


class ActionQuitSelectForm(AbstractFormAction):

    def __init__(self):
        name = 'form{\"name\": null}'
        AbstractFormAction.__init__(self, name)

    def __str__(self):
        return self.name


# Custom actions that generate code
class CustomAction(AbstractAction):

    def __init__(self, name, templates=[]):
        AbstractAction.__init__(self, name=name, templates=templates)

    def run(self):
        return self

    def template_object(self):
        pass


class ActionSelect(CustomAction):

    def __init__(self, frame: SelectFrame):
        self.frame = frame
        self.updated_slots = []
        name = f'select_{frame.table_name}'
        CustomAction.__init__(self, name)

    def __str__(self):
        return 'action_' + self.name + '_form'

    def run(self):
        informable_slots = self.frame.get_informable_slot_names(self.frame.get_informed_slot_names())
        # if we cant request anything, assume the frame is filled
        if len(informable_slots) == 0:
            values = {self.frame.target_slot_name: DUMMY_VALUE}
            self.frame.update_data(values)
            return self
        if not self.frame.is_filled():
            next_slot = random.choice(informable_slots)
            self.frame.requested_slot = self.frame.get_slot(next_slot)
            self.updated_slots.append(next_slot)
            self.updated_slots.append(REQUESTED_SLOT)
            return self
        return self

    def _revert(self):
        for slot_name in self.updated_slots:
            self.frame.data[slot_name] = None

    def template_object(self):
        requestable_slots = [slot.name for slot in self.frame.slots if slot.requestable]
        join_tables = list(set([slot_to_table_with_fk(slot_name) for slot_name in requestable_slots]))
        # todo might have multiple target slots (pk)? reuse instead of clearing form --> training
        target_slot = column_to_slot(self.frame.table_name, self.frame.column_name)
        slot_mappings = defaultdict(list)
        for slot in self.frame.slots:
            if not slot.requestable:
                continue
            if slot.data_type == 'bool':
                slot_mappings[slot.name].append(
                    f"self.from_intent(intent='{str(InformBool(slot.name, True))}', value=True)")
                slot_mappings[slot.name].append(
                    f"self.from_intent(intent='{str(InformBool(slot.name, False))}', value=False)")
                slot_mappings[slot.name].append(f"self.from_intent(intent='{INTENT_AFFIRM}', value=True)")
                slot_mappings[slot.name].append(f"self.from_intent(intent='{INTENT_DENY}', value=False)")
                slot_mappings[slot.name].append(f"self.from_intent(intent='{INTENT_DONT_CARE}', value='{DONT_CARE}')")
            else:
                slot_mappings[slot.name].append(f"self.from_entity(entity='{slot.name}')")
                slot_mappings[slot.name].append(f"self.from_text(intent=['{INTENT_INFORM}'])")
        return {
            'className': ''.join([s.capitalize() for s in self.name.split('_')]),
            'actionName': self.name,
            'targetSlots': [target_slot],
            'requiredSlots': requestable_slots,
            'targetTable': self.frame.table_name,
            'targetColumn': self.frame.column_name,
            'targetSlot': target_slot,
            'joinTables': join_tables,
            'slotMappings': [{'slotName': slot, 'slotMappings': mappings} for slot, mappings in slot_mappings.items()]
        }

    def do_log(self):
        return False


class ActionProposeForm(CustomAction):

    def __init__(self, frame: SelectFrame, templates=[], init_templates=False):
        name = f'propose_{frame.table_name}'
        self.frame = frame

        propose_templates = []
        if init_templates:
            slots = [s for s in frame.slots if s.displayble]
            template_values = dict(
                [(f'{slot.name}_nl', slot.column_nl[0]) for slot in slots] + [(f'{slot.name}', f'{{{slot.name}}}') for
                                                                              slot
                                                                              in slots] + [
                    ('table_nl', frame.table_name)])
            for t in templates:
                propose_templates.append(t.format(**template_values))
        CustomAction.__init__(self, name, propose_templates)

    def template_object(self):
        display_slots = [s.name for s in self.frame.slots if s.displayble]
        return {
            'className': ''.join([s.capitalize() for s in self.name.split('_')]),
            'actionName': self.name,
            'displaySlots': display_slots,
            'targetTable': self.frame.table_name,
            'representation': self.frame.representation
        }


class ActionSaveOption(CustomAction):
    def __init__(self, frame: SelectFrame):
        name = f'save_option_{frame.table_name}'
        self.frame = frame
        CustomAction.__init__(self, name)

    def template_object(self):
        display_slots = [s.name for s in self.frame.slots if s.displayble]
        target_slot = column_to_slot(self.frame.table_name, self.frame.column_name)
        set_slots = [s.name for s in self.frame.slots if s.requestable]
        return {
            'className': ''.join([s.capitalize() for s in self.name.split('_')]),
            'actionName': self.name,
            'displaySlots': display_slots,
            'targetSlot': target_slot,
            'targetTable': self.frame.table_name,
            'setSlots': set_slots,
            'representation': self.frame.representation
        }


class ActionClear(CustomAction):
    def __init__(self, frame: SubFrame):
        self.frame = frame
        if isinstance(frame, SelectFrame):
            name = f'clear_{self.frame.table_name}'
        elif isinstance(frame, ChoiceFrame):
            name = f'clear_{self.frame.get_slot().name}'
        CustomAction.__init__(self, name)

    def run(self, unaffirm=False):
        self.frame.clear(unaffirm)
        return self

    def template_object(self):
        return {
            'className': ''.join([s.capitalize() for s in self.name.split('_')]),
            'actionName': self.name,
            'clearedSlots': self.frame.slot_names
        }


class ActionSetBoolChoice(CustomAction):
    def __init__(self, frame: ChoiceFrame, entity: str, value: bool):
        self.frame = frame
        self.entity = entity
        self.value = value
        name = f'set_bool_{self.entity}_{str(value).lower()}'
        CustomAction.__init__(self, name)

    def run(self):
        self.frame.data[self.entity] = self.value
        return self

    def template_object(self):
        return {
            'className': ''.join([s.capitalize() for s in self.name.split('_')]),
            'actionName': self.name,
            'targetSlot': self.entity,
            'value': self.value
        }


class ActionValidateChoice(CustomAction):
    def __init__(self, frame: ChoiceFrame, entity: str, value: str, failure_ratio=0.1):
        self.frame = frame
        self.slot = frame.get_slot()
        self.entity = entity
        self.value = value
        self.failure_ratio = failure_ratio
        name = f'validate_{self.slot.name}'
        CustomAction.__init__(self, name)

    def run(self):
        self.frame.valid = random.uniform(0.0, 1.0) > self.failure_ratio
        return self

    def template_object(self):
        return {
            'className': ''.join([s.capitalize() for s in self.name.split('_')]),
            'actionName': self.name,
            'validationSlot': self.slot.name,
            'dataType': self.slot.data_type
        }


class ActionTransferSlot(CustomAction):

    def __init__(self, subframe: SubFrame, transaction_frame: TransactionFrame):
        self.transaction_frame = transaction_frame
        self.subframe = subframe
        self.updated_slots = []
        if isinstance(subframe, SelectFrame):
            self.source_name = f'{subframe.table_name}__{subframe.column_name}'
        if isinstance(subframe, ChoiceFrame):
            self.source_name = f'{subframe.get_slot().name}'

        name = f'transfer_slot_{self.source_name}_to_{subframe.reference}'
        CustomAction.__init__(self, name)

    def run(self):
        self.updated_slots = []
        if isinstance(self.subframe, SelectFrame):
            source_slot_name = column_to_slot(self.subframe.table_name, self.subframe.column_name)
        elif isinstance(self.subframe, ChoiceFrame):
            source_slot_name = self.subframe.get_slot().name
        target_slot_name = self.subframe.reference
        self.transaction_frame.update_data(target_slot_name, self.subframe.data[source_slot_name])
        self.updated_slots.append(target_slot_name)
        return self

    def template_object(self):
        return {
            'className': ''.join([s.capitalize() for s in self.name.split('_')]),
            'actionName': self.name,
            'sourceSlot': self.source_name,
            'targetSlot': self.subframe.reference
        }


# Actions that refer to the top level progress of the dialog
class TransactionAction(CustomAction):

    def __init__(self, name, frame: TransactionFrame, templates=[]):
        self.frame = frame
        CustomAction.__init__(self, name, templates)

    def template_object(self):
        pass


class ActionProposeTransaction(TransactionAction):

    def __init__(self, frame: TransactionFrame,
                 templates=['Alright im gonna {predicate} {argument} with the following information:'],
                 init_templates=False):
        name = f'propose_transaction_{frame.name}'
        self.frame = frame
        select_subframes = [frame for frame in self.frame.subframes if isinstance(frame, SelectFrame)]

        propose_templates = []

        if init_templates:
            # translate nl placeholders that can occur in the template to natural language phrasings of the slot
            # slot value placeholders are just replaced by the placeholders again and filled during runtime
            replacement_values = [(f'{slot.name}_nl', slot.column_nl[0]) for slot in frame.slots]
            replacement_values += [(f'{slot.name}', f'{{{slot.name}}}') for slot in frame.slots]
            for subframe in select_subframes:
                replacement_values += [(f'{slot.name}_nl', f'{{{slot.column_nl[0]}}}') for slot in subframe.slots]
                replacement_values += [(f'{slot.name}', f'{{{slot.name}}}') for slot in subframe.slots]
            for t in templates:
                if is_predicate_argument_template(t):
                    for predicate, argument in frame.task.nl:
                        template_values = dict(
                            replacement_values +
                            [('predicate', predicate), ('argument', argument)]
                        )
                        propose_templates.append(t.format(**template_values))
                else:
                    propose_templates.append(t.format(**dict(replacement_values)))
        TransactionAction.__init__(self, name, frame, propose_templates)

    def template_object(self):
        return {
            'className': ''.join([s.capitalize() for s in self.name.split('_')]),
            'actionName': self.name,
            'transactionName': self.frame.name,
            'asIsSlots': [frame.reference for frame in self.frame.subframes],
            'resolveSlots': dict([(frame.reference, column_to_slot(frame.table_name, frame.column_name)) for frame in
                                  self.frame.subframes if isinstance(frame, SelectFrame)])
        }


class ActionExecuteTransaction(TransactionAction):

    def __init__(self, frame: TransactionFrame, failure_ratio=0.5):
        self.failure_ratio = failure_ratio
        name = f'execute_transaction_{frame.name}'
        TransactionAction.__init__(self, name, frame)

    def run(self):
        self.frame.clear(clear_subframe=False, unaffirm=False)
        success = random.uniform(0.0, 1.0) > self.failure_ratio
        if not success:
            self.frame.error = DUMMY_VALUE
        elif self.frame.operation == OPERATION_SELECT:
            for key in self.frame.return_slot_names:
                self.frame.return_data[key] = DUMMY_VALUE
        return self

    def template_object(self):
        return {
            'className': ''.join([s.capitalize() for s in self.name.split('_')]),
            'actionName': self.name,
            'operation': self.frame.operation,
            'transactionName': self.frame.name,
            'argumentSlots': self.frame.slot_names,
            'returnSlots': self.frame.return_slot_names
        }


class ActionFailedTransaction(TransactionAction):

    def __init__(self, frame: TransactionFrame, templates=[], init_templates=False):
        name = f'failed_transaction_{frame.name}'
        failure_templates = []
        if init_templates:
            for t in templates:
                # dictionary with all placeholders that stay in place
                placeholders = get_template_placeholders(t)
                replacement_values = dict([(placeholder, f'{{{placeholder}}}') for placeholder in placeholders])
                if is_predicate_argument_template(t):
                    for predicate, argument in frame.task.nl:
                        # only update predicate argument placeholders
                        pa_replacement = copy.deepcopy(replacement_values)
                        pa_replacement.update(dict([('predicate', predicate), ('argument', argument)]))
                        failure_templates.append(t.format(**pa_replacement))
                else:
                    failure_templates.append(t.format(**replacement_values))
        TransactionAction.__init__(self, name, frame, failure_templates)

    def template_object(self):
        return {
            'className': ''.join([s.capitalize() for s in self.name.split('_')]),
            'actionName': self.name,
            'transactionName': self.frame.name
        }


class ActionSuccessfulTransaction(TransactionAction):

    def __init__(self, frame: TransactionFrame, templates=[], init_templates=False):
        name = f'success_transaction_{frame.name}'
        self.result = None
        success_templates = []

        if init_templates:
            for t in templates:
                # dictionary with all placeholders that stay in place
                placeholders = get_template_placeholders(t)
                replacement_values = dict([(placeholder, f'{{{placeholder}}}') for placeholder in placeholders])
                if is_predicate_argument_template(t):
                    for predicate, argument in frame.task.nl:
                        # only update predicate argument placeholders
                        pa_replacement = copy.deepcopy(replacement_values)
                        pa_replacement.update(dict([('predicate', predicate), ('argument', argument)]))
                        success_templates.append(t.format(**pa_replacement))
                else:
                    success_templates.append(t.format(**replacement_values))
        TransactionAction.__init__(self, name, frame, success_templates)

    def template_object(self, schema):
        return {
            'className': ''.join([s.capitalize() for s in self.name.split('_')]),
            'actionName': self.name,
            'operation': self.frame.operation,
            'transactionName': self.frame.name,
            'returnSlots': self.frame.return_slot_names,
            'returnReferences': self.frame.return_references,
            'resultTables': self._get_result_tables(
                [slot_to_table(reference) for reference in self.frame.return_references.values() if reference],
                schema
            )
        }

    def _get_result_tables(self, table_names: List[str] = [], schema: Dict = {}):
        tables = [t for t in schema['tables'] if t['name'] in table_names]
        for table in tables:
            for column in table['columns']:
                has_reference = column['table_reference'] is not None and column['column_reference'] is not None
                if has_reference:
                    ref_table_name = column['table_reference']
                    if ref_table_name not in table_names:
                        for t in self._get_result_tables([ref_table_name], schema):
                            if t not in table_names:
                                table_names.append(t)
        return table_names
