from typing import List, Dict

from cat.simulation.common.model import Task, Subtask, Slot


def transform_tasks(tasks_data) -> List[Task]:
    tasks = []
    for task_data in tasks_data:
        task_name = task_data['name']
        task_operation = task_data['operation']
        task_nl = [(nl['predicate'], nl['argument']) for nl in task_data['nl']]
        subtasks = transform_subtasks(task_data['subtasks'])
        slots = transform_slots(task_data['slots'])
        return_nl = task_data['returnNl']
        return_slots = transform_slots(task_data['returnSlots'])
        task = Task(name=task_name, operation=task_operation, nl=task_nl,
                    subtasks=subtasks, slots=slots, return_nl=return_nl, return_slots=return_slots)
        tasks.append(task)
    return tasks


def transform_subtasks(subtasks_data) -> List[Subtask]:
    subtasks = []
    for subtask_data in subtasks_data:
        subtask_target = subtask_data['targetSlot']
        subtask_data_type = subtask_data['targetDataType']
        subtask_is_list = subtask_data['targetList']
        subtask_table_reference = subtask_data.get('targetTable', None)
        subtask_table_nl = subtask_data['targetTableNl']
        subtask_table_representation = subtask_data['targetTableRepresentation']
        subtask_column_reference = subtask_data.get('targetColumn', None)
        subtask_operation = subtask_data['operation']
        subtask_slots = transform_slots(subtask_data['slots'])
        subtask = Subtask(target_slot=subtask_target, operation=subtask_operation,
                          target_data_type=subtask_data_type, target_is_list=subtask_is_list,
                          target_table=subtask_table_reference, target_table_nl=subtask_table_nl,
                          target_table_representation=subtask_table_representation,
                          target_column=subtask_column_reference, slots=subtask_slots)
        subtasks.append(subtask)
    return subtasks


def transform_slots(slots_data) -> List[Slot]:
    slots = []
    for slot_data in slots_data:
        slot_name = slot_data['name']
        table_nl = slot_data['entityNl']
        column_nl = slot_data['nl']
        slot_data_type = slot_data['dataType']
        slot_is_list = slot_data['list']
        slot_requestable = slot_data['requestable']
        slot_displayable = slot_data['displayable']
        slot_table_reference = slot_data['tableReference']
        slot_column_reference = slot_data['columnReference']
        slot_lookup_table, slot_entity_synonyms = transform_lookup_table(slot_data['lookupTable'])
        slot_regex = slot_data['regex']
        slot = Slot(name=slot_name, column_nl=column_nl, table_nl=table_nl, data_type=slot_data_type,
                    is_list=slot_is_list,
                    table_reference=slot_table_reference, column_reference=slot_column_reference,
                    lookup_table=slot_lookup_table, entity_synonyms=slot_entity_synonyms, regex=slot_regex,
                    requestable=slot_requestable, displayable=slot_displayable)
        slots.append(slot)
    return slots


def transform_lookup_table(lookup):
    if len(lookup) == 0:
        return [], {}
    lookup_values = [entry['value'] for entry in lookup]
    entity_synonyms = dict(
        [(entry['value'], [synonym for synonym in entry['synonyms'] if not synonym == entry['value']]) for entry in
         lookup])
    return lookup_values, entity_synonyms


def transform_config(configuration: Dict) -> Dict:
    return {
        'tables': transform_table_config(configuration['tables']),
        'procedures': transform_procedure_config(configuration['procedures'])
    }


def transform_templates(configuration: Dict) -> Dict:
    response_templates = dict([(response['id'], response['templates']) for response in configuration['responses']])
    intent_templates = dict([(intent['id'], intent['templates']) for intent in configuration['intents']])
    return response_templates, intent_templates


def transform_table_config(tables: List) -> List:
    return [{
        'name': table['name'],
        'pk': table['primaryKey'],
        'nl': table['nlExpressions'],
        'table_representation': table['representation'],
        'resolve_depth': table['resolveDepth'],
        'columns': [transform_column_config(column) for column in table['columns']]
    } for table in tables]


def transform_column_config(column: Dict) -> Dict:
    return {
        'name': column['name'],
        'nl': column['nlExpressions'],
        'data_type': column['dataType'],
        'table_reference': column['tableReference'],
        'column_reference': column['columnReference'],
        'nullable': column['nullable'],
        'requestable': column['requestable'],
        'displayable': column['displayable'],
        'resolve_dependency': column['resolveDependency']
    }


def transform_procedure_config(procedures: List):
    return [{
        'name': procedure['name'],
        'nl': procedure['nlPairs'],
        'operation': procedure['operation'],
        'parameters': [transform_parameter_config(param) for param in procedure['parameters']],
        'returns': transform_return_record_config(procedure['returns']) if procedure['returns'] else None,
    } for procedure in procedures]


def transform_parameter_config(param: Dict):
    return {
        'name': param['name']
    }


def transform_return_record_config(return_record: Dict):
    return {
        'name': return_record['name'],
        'nl': return_record['nlExpressions'],
        'values': [transform_return_value_config(value) for value in return_record['values']]
    }


def transform_return_value_config(return_value: Dict):
    return {
        'name': return_value['name'],
        'nl': return_value['nlExpressions'],
        'data_type': return_value['dataType'],
        'is_list': return_value['list'],
        'table_reference': return_value['tableReference'],
        'column_reference': return_value['columnReference'],
    }
