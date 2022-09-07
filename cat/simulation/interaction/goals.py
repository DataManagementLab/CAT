from cat.simulation.common.actions import *
from cat.simulation.interaction.frames import *
from typing import List


class Goal:
    def __init__(self, slots: List[Slot]):
        self.satisfied = False
        self.db = PostgreSQLDatabase.get_instance()
        self.slots = slots
        self.slot_names = [s.name for s in slots]
        self.constraints = dict.fromkeys(self.slot_names)

    def update(self, last_action):
        pass

    def resample(self, exclude=[], constrain_on={}):
        self.satisfied = False

    def get_slot(self, slot_name) -> Slot:
        slots = [slot for slot in self.slots if slot.name == slot_name]
        if len(slots) > 0:
            return slots[0]
        return None

    def get_informable_slot_names(self) -> List[str]:
        pass


class TransactionGoal(Goal):

    def __init__(self, task: Task):
        self.transaction_name = task.name
        self.operation = task.operation
        self.slot_references = dict([
            (slot.name, (slot.table_reference, slot.column_reference)
            if (slot.table_reference and slot.column_reference) else None)
            for slot in task.slots])
        self.subgoals: List[SubGoal] = [SelectGoal(self.transaction_name, subtask) if subtask.operation == 'select'
                                        else ChooseGoal(self.transaction_name, subtask)
                                        for subtask in task.subtasks]

        Goal.__init__(self, task.slots)

    def update(self, last_action):
        self.satisfied = isinstance(last_action, ActionSuccessfulTransaction)

    def get_informable_slot_names(self):
        return [slot_name for subgoal in self.subgoals for slot_name in subgoal.get_informable_slot_names()]


class SubGoal(Goal):
    def __init__(self, parent_task_name: str, subtask: Subtask):
        self.task = subtask
        self.transaction_name = parent_task_name
        self.transaction_slot = subtask.target_slot
        Goal.__init__(self, subtask.slots)

    def __eq__(self, other):
        return isinstance(other, ChoiceFrame) \
               and self.transaction_slot == other.transaction_slot \
               and self.transaction_name == other.transaction_name

    def __hash__(self):
        return hash(self.transaction_name) + hash(self.transaction_slot)

    def update(self, last_action):
        self.satisfied = isinstance(last_action, ActionTransferSlot)

    def get_informable_slot_names(self) -> List[str]:
        return [slot.name for slot in self.slots if slot.requestable]


class SelectGoal(SubGoal):

    def __init__(self, parent_task_name: str, subtask: Subtask):
        self.table_name = subtask.target_table
        self.column_name = subtask.target_column
        SubGoal.__init__(self, parent_task_name, subtask)


class ChooseGoal(SubGoal):
    def __init__(self, parent_task_name: str, subtask: Subtask):
        self.data_type = subtask.slots[0].data_type
        SubGoal.__init__(self, parent_task_name, subtask)
