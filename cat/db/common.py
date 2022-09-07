OPERATION_SELECT = 'select'
OPERATION_CALL = 'call'
COUNT = 'count'
COUNT_ALL = 'count(*)'
DONT_CARE = '__DONT_CARE__'

OPERATOR_EQUAL = '='
OPERATOR_IN = 'IN'
OPERATOR_GT = '>'
OPERATOR_LT = '<'
OPERATOR_GTE = '>='
OPERATOR_LTE = '<='


def slot_to_table_column_with_join_table_column(slot: str):
    s = slot.split('___')
    if len(s) == 2:
        return tuple([*s[0].split('__'), *s[1].split('__')])
    else:
        return tuple([None, None, *s[0].split('__')])


def table_with_fk(join_table, join_column, table):
    if join_table and join_column:
        return f'{join_table}__{join_column}___{table}'
    else:
        return table


def table_to_fk_and_table(table_alias):
    s = table_alias.split('___')
    if len(s) == 2:
        return s[0], s[1]
    else:
        return None, s[0]


def table_with_fk_to_table(table_alias):
    s = table_alias.split('___')
    if len(s) == 2:
        return s[1]
    else:
        return s[0]


def table_with_fk_to_fk(table_name_with_fk):
    s = table_name_with_fk.split('___')
    if len(s) == 2:
        return s[0]
    else:
        return None


def slot_to_table_column_with_fk(slot):
    s = slot.split('___')
    if len(s) == 2:
        table, column = s[1].split('__')
        return f'{s[0]}___{table}', column
    else:
        return s[0].split('__')


def slot_to_table_column(slot):
    s = slot.split('___')
    if len(s) == 2:
        return s[1].split('__')
    else:
        return s[0].split('__')


def slot_to_column(slot):
    return slot_to_table_column(slot)[1]


def slot_to_table(slot: str):
    return slot_to_table_column(slot)[0]


def slot_to_table_with_fk(slot: str):
    fk_table, fk_column, table, column = slot_to_table_column_with_join_table_column(slot)
    return table_with_fk(fk_table, fk_column, table)


def slot_to_proc_name(slot):
    return slot.split('__')[0]


def slot_to_proc_arg(slot):
    return slot.split('__')[1]


def proc_arg_to_slot(proc_name, arg_name):
    return f'{proc_name}__{arg_name}'


def column_to_slot(table_name, column_name):
    return f'{table_name}__{column_name}'


def is_value(v):
    return v and v != DONT_CARE
