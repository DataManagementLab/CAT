from cat.db.database import *
from cat.simulation.common.model import Slot, Task, Subtask
from typing import List


class Frame:

    def __init__(self, slots: List[Slot]):
        self.slots = slots
        self.slot_names = [s.name for s in slots]
        self.data = dict.fromkeys(self.slot_names)
        self.history = []
        self.affirmed = False

    def get_slot(self, slot_name) -> Slot:
        slots = [slot for slot in self.slots if slot.name == slot_name]
        if len(slots) > 0:
            return slots[0]
        return None

    def clear(self, unaffirm=True):
        self.data = dict.fromkeys(self.slot_names)
        self.history = []
        if unaffirm:
            self.affirmed = False

    def update_data(self, values: Dict[str, str]):
        self.snapshot()
        for slot, value in values.items():
            if slot in self.slot_names:
                self.data[slot] = value

    def snapshot(self):
        self.history.append(self.data)

    def rewind(self):
        self.data = self.history.pop()

    def is_filled(self):
        return all([self.data[slot] is not None for slot in self.slot_names])

    def is_empty(self):
        return all([self.data[slot] is None for slot in self.slot_names])

    def is_affirmed(self):
        return self.affirmed

    def get_informed_slot_names(self) -> List[Slot]:
        return [slot for slot in self.slot_names if self.data[slot] is not None]

    def get_informable_slot_names(self, informed_names=[]) -> List[str]:
        return list(set([slot.name for slot in self.slots if self.data[slot.name] is None and slot.requestable]) -
                    set(informed_names))

    def get_empty_slot_names(self) -> List[str]:
        return [slot for slot in self.slot_names if self.data[slot] is None]

    def affirm(self):
        self.affirmed = True


class TransactionFrame(Frame):

    def __init__(self, task: Task):
        self.task = task
        self.name = task.name
        self.operation = task.operation
        self.return_slots = task.return_slots
        self.return_slot_names = [s.name for s in self.return_slots]
        self.return_data = dict.fromkeys(self.return_slot_names)
        self.return_references = dict(
            [(s.name, column_to_slot(s.table_reference, s.column_reference) if s.table_reference else None) for s in
             task.return_slots]
        )
        self.error = None
        self.subframes = [SelectFrame(self.name, subtask) if subtask.operation == 'select' else
                          ChoiceFrame(self.name, subtask)
                          for subtask in task.subtasks]
        Frame.__init__(self, task.slots)

    def add_subframe(self, frame):
        self.subframes.append(frame)

    def clear(self, clear_subframe: bool = True, unaffirm: bool = True):
        self.return_data = dict.fromkeys(self.return_slot_names)
        self.error = None
        if clear_subframe:
            for frame in self.subframes:
                frame.clear()
        Frame.clear(self, unaffirm=unaffirm)

    def __eq__(self, other):
        return isinstance(other, TransactionFrame) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def update_data(self, values: Dict[str, str]):
        super(TransactionFrame, self).update_data(values)
        for frame in self.subframes:
            frame.update_data(values)


class SubFrame(Frame):
    def __init__(self, parent_task_name: str, subtask: Subtask):
        self.task = subtask
        self.transaction_name = parent_task_name
        self.reference = subtask.target_slot
        Frame.__init__(self, subtask.slots)

    def __eq__(self, other):
        return isinstance(other, SubFrame) and self.reference == other.reference and self.data_type == other.data

    def __hash__(self):
        return hash(self.reference)


class SelectFrame(SubFrame):

    def __init__(self, parent_task_name: str, subtask: Subtask):
        self.table_name = subtask.target_table
        self.representation = subtask.target_table_representation
        self.column_name = subtask.target_column
        self.target_slot_name = f'{subtask.target_table}__{subtask.target_column}'
        self.tables = set([slot_to_table(slot.name) for slot in subtask.slots])
        self.requested_slot: Slot = None
        self.single_result = False
        SubFrame.__init__(self, parent_task_name, subtask)

    def is_filled(self):
        return self.data[self.target_slot_name] is not None

    def get_constraints(self):
        constraints = dict((table, {}) for table in self.tables)
        for filled_slot in self.get_informed_slots():
            table, column = slot_to_table_column(filled_slot)
            constraints[table][column] = {
                'value': self.data[filled_slot],
                'similar': False
            }
        return constraints

    def get_requestable_columns(self):
        column_dict = dict([(table, []) for table in self.tables])
        for slot in self.slots:
            if slot.requestable:
                table, column = slot_to_table_column(slot.name)
                column_dict[table].append(column)
        return column_dict

    def __str__(self):
        return f'select_{self.table_name}_frame'


class ChoiceFrame(SubFrame):
    def __init__(self, parent_task_name: str, subtask: Subtask):
        self.data_type = subtask.target_data_type
        self.valid = False
        SubFrame.__init__(self, parent_task_name, subtask)

    def get_slot(self):
        return self.slots[0]

    def __str__(self):
        return f'choice_{self.transaction_name}_{self.get_slot()}_frame'