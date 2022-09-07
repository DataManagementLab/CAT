from typing import List
from .graph import DependencyGraph
from .common import *


class Column:
    def __init__(self, name: str, data_type: str, table_reference: str = None, column_reference: str = None,
                 nullable: bool = False):
        self.name = name
        self.data_type = data_type
        self.table_reference = table_reference
        self.column_reference = column_reference
        self.nullable = nullable

    def __str__(self):
        return self.name if not self.table_reference else f'{self.name} ({self.table_reference}.{self.column_reference})'

    def is_reference(self):
        return self.table_reference and self.column_reference

    def get_reference(self):
        return self.table_reference, self.column_reference


class Parameter:
    def __init__(self, name: str, data_type: str, is_list: bool = False, table_reference: str = None,
                 column_reference: str = None):
        self.name = name
        self.data_type = data_type
        self.is_list = is_list
        self.table_reference = table_reference
        self.column_reference = column_reference

    def __str__(self):
        return f'{self.name} ({self.data_type})'


class ReturnValue:
    def __init__(self, name: str, data_type: str, table_reference: str = None, column_reference: str = None,
                 is_list: bool = False):
        self.name = name
        self.data_type = data_type
        self.table_reference = table_reference
        self.column_reference = column_reference
        self.is_list = is_list

    def __str__(self):
        return f'{self.name} ({self.data_type})'


class ReturnRecord:
    def __init__(self, name: str, is_list=False, values: List[ReturnValue] = []):
        self.name = name
        self.is_list = is_list
        self.values = values

    def __str__(self):
        return f'{self.name}({", ".join([str(val) for val in self.values])}'


class Procedure:
    def __init__(self, name: str,
                 operation: str,
                 parameters: List[Parameter] = [],
                 return_record: ReturnRecord = None,
                 body: str = None):
        self.name = name
        self.operation = operation
        self.parameters = parameters
        self.return_record = return_record
        self.body = body

    def __str__(self):
        return f"{self.name}({', '.join(self.parameter_names())})"

    def parameter_names(self):
        return [parameter.name for parameter in self.parameters]


class Table:
    def __init__(self, name: str, primary_key: List[str] = [], columns: List[Column] = []):
        self.name = name
        self.primary_key = primary_key
        self.columns = columns

    def __str__(self):
        return self.name

    def column_names(self):
        return [column.name for column in self.columns]


class MetaSchema:
    def __init__(self, name: str,
                 tables: List[Table] = [],
                 procedures: List[Procedure] = [],
                 mapping_tables: List[str] = [],
                 join_graph: DependencyGraph = None):
        self.name = name
        self.tables = tables
        self.procedures = procedures
        self.mapping_tables = mapping_tables
        self.join_graph = join_graph

    def table_names(self):
        return [table.name for table in self.tables]

    def procedure_names(self):
        return [procedure.name for procedure in self.procedures]

    def get_table(self, table_name):
        return [table for table in self.tables if table.name == table_name][0]

    def get_alias_table(self, table_alias):
        return table_with_fk_to_table(table_alias)

    def get_alias_to_table_name_dict(self, aliases):
        return dict(
            [(table_name_with_fk, self.get_alias_table(table_name_with_fk)) for table_name_with_fk in aliases])

    def get_alias_to_table_dict(self, aliases: List[str]):
        alias_dict = self.get_alias_to_table_name_dict(aliases)
        return dict([(table_alias, self.get_table(alias_dict[table_alias])) for table_alias in alias_dict.keys()])

    def is_mapping_table(self, table_name: str):
        return table_name in self.mapping_tables

    def _is_mapping_table(self, table: Table):
        if len(table.primary_key) < 2:
            return False
        return all([column.table_reference for column in table.columns if column.name in table.primary_key])
