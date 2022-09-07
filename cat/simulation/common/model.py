from typing import List, Tuple, Dict


class Slot:

    def __init__(self, name: str, data_type: str, table_reference: str, column_reference: str,
                 column_nl: List[str] = [], table_nl: List[str] = [], is_list: bool = False,
                 lookup_table: List[str] = [], entity_synonyms: Dict[str, str] = {}, regex: str = None, requestable: bool = True, displayable: bool = True):
        self.name = name
        self.column_nl = column_nl
        self.table_nl = table_nl
        self.data_type = data_type
        self.table_reference = table_reference
        self.column_reference = column_reference
        self.is_list = is_list
        self.requestable = requestable
        self.displayble = displayable
        self.lookup_table = lookup_table
        self.entity_synonyms = entity_synonyms
        self.regex = regex

    def __eq__(self, other):
        return isinstance(other, Slot) and self.name == other.name and self.data_type == other.data_type


class Subtask:
    def __init__(self, target_slot: str, operation: str, target_data_type: str, target_table: str, target_column: str,
                 target_table_nl: List[str] = [], target_table_representation: str = [],
                 target_is_list: bool = False, slots: List[Slot] = []):
        self.target_slot = target_slot
        self.operation = operation
        self.target_data_type = target_data_type
        self.target_table = target_table
        self.target_table_nl = target_table_nl
        self.target_table_representation = target_table_representation
        self.target_column = target_column
        self.target_is_list = target_is_list
        self.slots = slots

    def add_slot(self, slot: Slot):
        self.slots.append(slot)


class Task:

    def __init__(self, name: str, operation: str, nl: List[Tuple[str, str]],
                 slots: List[Slot] = [], return_nl: List[str] = [], return_slots: List[Slot] = [],
                 subtasks: List[Subtask] = []):
        self.name = name
        self.operation = operation
        self.nl = nl
        self.slots = slots
        self.return_nl = return_nl
        self.return_slots = return_slots
        self.subtasks = subtasks

    def add_subtask(self, subtask: Subtask):
        self.subtasks = self.subtasks.append(subtask)

    def add_slot(self, slot: Slot):
        self.slots.append(slot)
