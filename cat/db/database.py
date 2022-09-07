import copy
import logging
from .graph import *
from .common import *
from .schema import *
from typing import List, Dict, Tuple, Union

import psycopg2 as pg
import psycopg2.errors as errors
from psycopg2.extras import RealDictCursor, RealDictRow
import psycopg2.extensions as pgx
from numpy import random

DEC2FLOAT = pgx.new_type(pgx.DECIMAL.values, 'DEC2FLOAT',
                         lambda value, curs: float(value) if value is not None else None)
pgx.register_type(DEC2FLOAT)

logger = logging.getLogger('db')
logging.basicConfig(level=logging.DEBUG)


# noinspection SqlResolve,SqlResolve,SqlNoDataSourceInspection
class PostgreSQLDatabase:
    _instance = None

    def __init__(self, db_name: str, schema_name: str, user: str, password: str, host: str, port: int, cache=True):
        if PostgreSQLDatabase._instance:
            raise Exception('PostgreSQLDatabase is a singleton, use get_instance() to get the database instance')
        else:
            self.db_name = db_name
            self.schema_name = schema_name
            self.user = user
            self.password = password
            self.host = host
            self.port = port

            self._metaschema: MetaSchema = None
            self._informativity_cache = None
            self._dependencies = None
            self._connection = None
            PostgreSQLDatabase._instance = self
            self._connect(cache=cache)

    @staticmethod
    def get_instance(db_name=None, schema_name=None, user=None, password=None, host=None, port=None):
        if not PostgreSQLDatabase._instance:
            if not (db_name and schema_name and user and password and host and port):
                raise Exception('Not all connection parameters specified, although no database instance is in place.')
            PostgreSQLDatabase(db_name, schema_name, user, password, host, port)
        elif db_name and schema_name and user and password and host and port:
            logger.debug('Instance in place but parameters specified. Setting instance to new parameters')
            if PostgreSQLDatabase._instance._check_connection():
                PostgreSQLDatabase._instance.disconnect()
            PostgreSQLDatabase._instance = None
            PostgreSQLDatabase(db_name, schema_name, user, password, host, port)
        return PostgreSQLDatabase._instance

    def _connect(self, cache=False):
        if not self._check_connection():
            try:
                logger.debug(
                    f'Connecting to database postgres://{self.user}@{self.host}:{self.port}/{self.db_name}, schema: {self.schema_name}')
                self._connection = pg.connect(
                    f"dbname={self.db_name} user={self.user} password={self.password} host={self.host} port={self.port} options='-c search_path={self.schema_name}'",
                    cursor_factory=RealDictCursor)
                schema = self.__query_one(
                    'SELECT nspname FROM pg_catalog.pg_namespace WHERE nspname=%(schema)s', {
                        'schema': self.schema_name
                    })
                if not schema:
                    existing_schemas = [s['nspname'] for s in
                                        self.__query_all(
                                            'SELECT nspname FROM pg_catalog.pg_namespace')]
                    self.disconnect()
                    raise Exception(
                        f'Schema {self.schema_name} does not exist. Available Schemas:\n {", ".join(existing_schemas)}')
                # todo remove, for convenience remove matches table on startup
                self.__execute('DROP TABLE IF EXISTS matches;')
                self.__generate_metaschema()
                if cache:
                    self.__build_informativity_cache()
            except pg.Error as e:
                error = f'Unable to connect to database: postgresql://{self.user}@{self.host}:{self.port}/{self.db_name}' \
                        f', Schema: {self.schema_name}\n' \
                        f'{e}'
                self.disconnect()
                logger.error(error)
                logger.error(e)
                raise Exception(error)
        else:
            logger.warning('Already having a database connection established.')

    def disconnect(self):
        if self._check_connection():
            logger.debug('Closing database connection.')
            self._connection.close()
        else:
            logger.warning('No connection to close')
        self._connection = None

    def get_metaschema(self):
        return self._metaschema

    def select(self,
               target_table_alias: str,
               additional_tables: List[str] = [],
               constraints: Dict[str, Dict[str, List[Dict[str, any]]]] = {},
               distinct_on_target=None,
               select_dict={},
               order: Tuple[any, str] = (1, 'ASC'),
               limit: int = None) -> List[RealDictRow]:

        query, params = self._get_select_query(target_table_alias=target_table_alias,
                                               additional_tables=additional_tables,
                                               constraints=constraints,
                                               select_dict=select_dict,
                                               distinct_on_target=distinct_on_target,
                                               order=order)

        if limit:
            if limit == 1:
                row = self.__query_one(query, params)
                if row:
                    return row
                return None
            return self.__query_many(query, params, limit)
        return self.__query_all(query, params)

    def select_into_table(self,
                          target_table_alias: str,
                          additional_tables: List[str] = [],
                          constraints={},
                          select_dict={},
                          distinct_on_target: str = None,
                          result_table='matches',
                          order: Tuple[any, str] = None,
                          analyze=False):
        # drop current results
        delete_temp = f'DROP TABLE IF EXISTS {result_table}'
        self.__execute(delete_temp)
        create_temp = f'CREATE UNLOGGED TABLE IF NOT EXISTS {result_table} AS '

        query, params = self._get_select_query(target_table_alias, additional_tables, constraints, select_dict,
                                               distinct_on_target, order)

        create_temp += query
        self.__execute(create_temp, params)
        if analyze:
            self.__execute(f'ANALYZE {result_table}')
        return result_table

    def _get_select_query(self,
                          target_table_alias: str,
                          additional_tables: List[str] = [],
                          constraints={},
                          select_dict={},
                          distinct_on_target: str = None,
                          order: Tuple[any, str] = (1, 'ASC')) -> str:
        # the tables to join are either ones that have constraints or are explicitly asked to join
        constraint_tables = [table for table, column_constraints in constraints.items() if column_constraints]
        join_aliases = list(set(constraint_tables).union(set(additional_tables)))
        alias_to_table_name_dict = self._metaschema.get_alias_to_table_name_dict(
            set(join_aliases + [target_table_alias]))
        ordered_join_aliases = self._get_ordered_join_aliases(target_table_alias, join_aliases,
                                                              alias_to_table_name_dict)
        alias_to_table_dict = self._metaschema.get_alias_to_table_dict(ordered_join_aliases)

        if not select_dict:
            # select target values
            select_clause = 'SELECT '
            if distinct_on_target:
                target_table_name = alias_to_table_name_dict[target_table_alias]
                select_clause += f'DISTINCT ON ({target_table_name}.{distinct_on_target}) {target_table_name}.{distinct_on_target} AS {target_table_alias}__{distinct_on_target} '
                other_columns = [column for column in alias_to_table_dict[target_table_alias].columns if
                                 column.name != distinct_on_target]
                if len(other_columns) > 0:
                    select_clause += ', '
                select_clause += ', '.join(
                    [f'{target_table_name}.{column.name} AS {target_table_alias}__{column.name}' for column in
                     other_columns])
            else:
                select_clause += ', '.join([
                    f'{alias_to_table_name_dict[target_table_alias]}.{column.name} AS {target_table_alias}__{column.name}'
                    for column in alias_to_table_dict[target_table_alias].columns])
        else:
            select_clause = 'SELECT ' + \
                            ', '.join(
                                [f'{select_table}.{select_column} AS {select_table}__{select_column}' for
                                 select_table, select_columns in select_dict.items() for select_column in
                                 select_columns])

        from_clause, successfully_joined = self._get_from_clause(ordered_join_aliases, alias_to_table_dict)

        if not select_dict:
            # select values of joined tables
            if len(set(successfully_joined) - set([target_table_alias])) > 0:
                select_clause += ', '
            select_clause += ', '.join(
                [f'{table_name}.{column.name} AS {table_name}__{column.name}' for table_name in successfully_joined
                 for column in alias_to_table_dict[table_name].columns if table_name != target_table_alias]
            )

        where_clause = 'WHERE 1=1 '

        params = {}
        param_num = 0

        select_constraints = dict([(table_alias, constr) for table_alias, constr in constraints.items() if constr])
        select_constraint_where_conditions, params, param_num = self._get_where_conditions(select_constraints, params,
                                                                                           param_num)

        where_clause += select_constraint_where_conditions

        query = f'{select_clause} {from_clause} {where_clause}'
        if order:
            query += f" ORDER BY {order[0]} {order[1]} "
        return query, params

    def insert(self):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError

    def call_procedure(self, name, operation, arguments):
        if operation.lower() not in [OPERATION_SELECT, OPERATION_CALL]:
            raise Exception(f'No operation {operation} to call procedure {name}. Use "select" or "call"')
        arg_names = list(arguments.keys())
        matching_procs = [proc for proc in self._metaschema.procedures
                          if proc.name.lower() == name.lower()
                          and len(arg_names) == len(proc.parameters)
                          and all([arg_name.lower()
                                   in [arg.name.lower() for arg in proc.parameters] for arg_name in arg_names])
                          ]
        if len(matching_procs) == 0:
            raise Exception(f'No stored procedure with name {name} and arguments {", ".join(arg_names)}')
        proc = matching_procs[0]
        proc_params = tuple([arguments[param_name] for param_name in proc.parameter_names()])
        if self._check_connection():
            with self._connection.cursor() as curs:
                try:
                    if operation == OPERATION_SELECT:
                        curs.callproc(name, proc_params)
                        self._connection.commit()
                        result = curs.fetchall()
                        return result, None
                    else:
                        query = f'CALL {proc.name}('
                        query += ', '.join([f'%({param_name})s' for param_name in proc.parameter_names()])
                        query += ')'
                        params = dict([(param_name, arguments[param_name]) for param_name in proc.parameter_names()])
                        curs.execute(query, params)
                        self._connection.commit()
                        return None, None
                except (errors.RaiseException, errors.InFailedSqlTransaction) as e:
                    self._connection.rollback()
                    return None, e.args[0].split('\n')[0]
        raise Exception('No active connection to database')

    def should_join_next_table(self, target_table_name, joined_tables=[], constraints={}, requestable_columns={}):
        # if we only have the target table, join with another table
        if len(joined_tables + [t for t, c in constraints.items() if c and t != target_table_name]) == 0:
            return True

        # check if any of the target columns that can be requested are not filled yet
        informed_target_columns = constraints[target_table_name]
        remaining_target_columns = list(set(requestable_columns[target_table_name]) - set(informed_target_columns))

        # then check which columns of the join tables are already constraint
        informed_join_columns = dict([(table, constraints[table]) for table in joined_tables if constraints[table]])
        requestable_join_columns = dict(
            [(table, requestable_columns[table]) for table in joined_tables])
        remaining_join_columns = dict([(table, list(
            set(columns) - (set(informed_join_columns[table]) if table in informed_join_columns.keys() else set()))) for
                                       table, columns in requestable_join_columns.items()])
        num_remaining_join_columns = sum([len(columns) for table, columns in remaining_join_columns.items()])

        # if no target column nor a join column is missing a requestable constraint, join another table
        if len(remaining_target_columns) + num_remaining_join_columns == 0:
            return True
        return False

    def get_best_join_table(self, target_table_name, joined_tables=[], constraints={}, requestable_columns={},
                            limit_check=None):

        used_tables = list(set([target_table_name] +
                               joined_tables +
                               [table for table, column_constr in self.get_real_constraints(constraints).items()]))
        join_candidates = self._dependencies.get_join_candidates(used_tables, self._metaschema.mapping_tables)

        informativity_table = {}
        # do not join if our result is not limited at all
        if len(used_tables) == 1:
            for candidate_table_alias in join_candidates:
                candidate_table = table_with_fk_to_table(candidate_table_alias)
                candidate_columns = [c for c in requestable_columns[candidate_table_alias]]
                for candidate_column in candidate_columns:
                    col_infs = self._informativity_cache.get(candidate_table, {})
                    inf = col_infs.get(candidate_column, None)
                    if inf:
                        informativity_table[column_to_slot(candidate_table_alias, candidate_column)] = inf
            return self._get_best_informativity(informativity_table)

        if limit_check:
            join_candidates = join_candidates[:min(limit_check, len(join_candidates))]

        for candidate in join_candidates:
            new_join_tables = joined_tables + [candidate]
            result_table_name = f'joined_{candidate}'
            select_columns = {
                candidate: requestable_columns[candidate]
            }
            logger.debug(f'Checking join selectivity on table {candidate}')
            self.select_into_table(target_table_name, new_join_tables, constraints=constraints,
                                   result_table=result_table_name, select_dict=select_columns)
            informativity_columns = [f'{candidate}__{column}' for column in requestable_columns[candidate]]
            informativity_table.update(self.get_column_entropies(result_table_name, informativity_columns))
            self.__execute(f'DROP TABLE IF EXISTS {result_table_name}')
        # return the table name with the highest informativity
        if informativity_table:
            best_slot, informativity = max(informativity_table.items(), key=lambda pair: pair[1])
            best_table, best_column = slot_to_table_column_with_fk(best_slot)
            return best_table
        return None

    def get_join_tables(self, table_name, directed=True):
        return self._dependencies.get_join_candidates([table_name], self._metaschema.mapping_tables, directed=directed)

    def get_column_entropies(self, table_name, columns):
        entropy_table = {}
        for column in columns:
            params = {
                'tablename': table_name,
                'attname': column
            }
            row = self.__query_one('SELECT public.normalized_entropy(%(tablename)s, %(attname)s)', params)
            entropy_table[column] = row['normalized_entropy']
        return entropy_table

    def get_column_selectivities(self, table_name, candidate, requestable_columns):
        query = f'SELECT attname AS table_column, n_distinct AS selectivity FROM pg_stats \
        WHERE tablename = %(join_table)s AND attname IN %(attributes)s'

        attributes = [f'{candidate}__{column}' for column in requestable_columns[candidate]]
        params = {
            'join_table': table_name,
            'attributes': tuple(attributes)
        }
        selectivities = self.__query_all(query, params)
        return selectivities

    def _get_best_informativity(self, informativity_table):
        if informativity_table:
            best_slot, informativity = max(informativity_table.items(), key=lambda pair: pair[1])
            best_table, best_column = slot_to_table_column_with_fk(best_slot)
            return best_table
        return None

    def _get_ordered_join_aliases(self, target_table_alias, join_aliases, alias_to_table_name_dict):
        join_paths = [self._dependencies.get_best_dependency_path(target_table_alias, alias_to_table_name_dict[t]) for t
                      in join_aliases]
        ordered_join_aliases = []
        for alias, path in zip(join_aliases, join_paths):
            prefix = table_with_fk_to_fk(alias)
            prefix_table, prefix_column = slot_to_table_column(prefix) if prefix else (None, None)
            do_prefix = False
            for t in path:
                prefixed = table_with_fk(prefix_table, prefix_column, t) if do_prefix else t
                if prefixed not in alias_to_table_name_dict.keys():
                    alias_to_table_name_dict.update({prefixed: self._metaschema.get_alias_table(prefixed)})
                    join_aliases.append(prefixed)
                if prefixed not in ordered_join_aliases:
                    ordered_join_aliases.append(prefixed)
                if prefix_table == t:
                    do_prefix = True
        if not ordered_join_aliases:
            return [target_table_alias]
        return ordered_join_aliases

    def _get_from_clause(self, ordered_join_aliases: List[str], tables_dict: Dict[str, Table]):
        from_clause = 'FROM '
        fact_aliases = []
        successfully_joined = []
        for i, alias in enumerate(ordered_join_aliases):
            table = tables_dict[alias]
            # first table needs no join condition, acts as our base
            if i == 0:
                from_clause += f' {table.name} AS {alias}'
                successfully_joined.append(alias)
                continue
            # if it is a mapping table look back and ahead for join tables
            if self._metaschema.is_mapping_table(table.name):
                fact_join_clause = self._get_fact_clause(tables_dict, alias, successfully_joined)
                if fact_join_clause:
                    from_clause += fact_join_clause
                    successfully_joined.append(alias)
                    fact_aliases.append(alias)
                continue
            # if it is a dimension table see if it needs to be joined 1:n or with fact table
            else:
                fk_join_clause = self._get_foreign_key_join_clause(tables_dict, alias, successfully_joined)
                if fk_join_clause:
                    from_clause += fk_join_clause
                    successfully_joined.append(alias)
                    continue
                dim_join_clause = self._get_dim_join_clause(tables_dict, alias, fact_aliases)
                if dim_join_clause:
                    from_clause += dim_join_clause
                    successfully_joined.append(alias)
                    continue
        return from_clause, successfully_joined

    def _get_foreign_key_join_clause(self, tables_dict: Dict[str, Table], dim_alias: str, joined_tables=[]) -> str:
        alias_prefix = table_with_fk_to_fk(dim_alias)
        fk_ref = [(alias, table, column)
                  for alias, table in tables_dict.items()
                  for column in table.columns if
                  alias in joined_tables and
                  column.table_reference == table_with_fk_to_table(dim_alias) and
                  (alias_prefix is None or (
                          table.name == slot_to_table(alias_prefix) and column.name == slot_to_column(alias_prefix)))
                  ]
        if fk_ref:
            a, t, c = fk_ref[0]
            return f' LEFT JOIN {tables_dict[dim_alias].name} AS {dim_alias} ON {a}.{c.name} = {dim_alias}.{c.column_reference}'
        return None

    def _get_fact_clause(self, know_tables_dict: Dict[str, Table], fact_alias: str, previous_aliases: List[str]) -> str:
        # join the table as its alias
        alias_prefix = table_with_fk_to_fk(fact_alias)
        fact_table = know_tables_dict[fact_alias]
        join_clause = f' LEFT JOIN {fact_table.name} AS {fact_alias}'

        # find the mapping column that refers to a previous table alias
        fact_reference_tables = [column.table_reference for column in fact_table.columns if
                                 column.name in fact_table.primary_key]
        join_on_dim_alias = [alias for alias in previous_aliases
                             if table_with_fk_to_fk(alias) == alias_prefix
                             and know_tables_dict[alias].name in fact_reference_tables
                             ][0]
        join_on_dim_table = know_tables_dict[join_on_dim_alias]
        join_column = [column for column in fact_table.columns
                       if column.name in fact_table.primary_key
                       and column.table_reference == join_on_dim_table.name][0]
        join_clause += f' ON {fact_alias}.{join_column.name} = {join_on_dim_alias}.{join_column.column_reference}'
        return join_clause

    def _get_dim_join_clause(self, known_tables_dict: Dict[str, Table], dim_alias: str, fact_aliases) -> str:
        alias_prefix = table_with_fk_to_fk(dim_alias)
        dim_table = known_tables_dict[dim_alias]

        join_clause = f' LEFT JOIN {dim_table.name} AS {dim_alias}'

        # find a fact table that refers to this alias
        fact_aliases = [alias for alias in fact_aliases if table_with_fk_to_fk(alias) == alias_prefix]
        if not fact_aliases:
            return None
        fact_alias = fact_aliases[0]
        fact_table = known_tables_dict[fact_alias]
        join_column = [column for column in fact_table.columns
                       if column.name in fact_table.primary_key
                       and column.table_reference == dim_table.name][0]
        join_clause += f' ON {dim_alias}.{join_column.column_reference} = {fact_alias}.{join_column.name}'
        return join_clause

    def select_all(self, table_name='matches'):
        return self.__query_all(f'SELECT * FROM {table_name}')

    def select_distinct(self, table_name: str, column_name: str, count=False, limit: int = None):
        query = f'SELECT '
        if count:
            query += 'COUNT('
        query += f'DISTINCT {column_name}'
        if count:
            query += ')'
        query += f' FROM {table_name}'
        if limit and limit > 0:
            if limit == 1:
                return self.__query_one(query)
            else:
                return self.__query_many(query)
        return self.__query_all(query)

    def get_next_slot(self, target_table, joined_tables=[], constraints={}, requestable_columns={},
                      result_table='matches', as_table_column=False):
        requestable_tables = list(set(
            [target_table] + joined_tables + [table for table, column_constr in constraints.items() if column_constr]))
        known_columns = [f'{table}__{column}' for table, column_constr in constraints.items() for column in
                         column_constr.keys() if column_constr]
        column_options = [f'{table}__{column}' for table in requestable_tables for column in requestable_columns[table]
                          if f'{table}__{column}' not in known_columns]
        if len(column_options) == 0:
            logger.debug('No column options found')
            return (None, None) if as_table_column else None

        # use cached base tables nothing is joined or no constraints are set
        if self._informativity_cache and len(joined_tables) == 0 or len(
                self.get_real_constraints(constraints).items()) == 0:
            # filter column options
            informativity_table = dict(
                [(column_to_slot(table, c), e)
                 for table, ce in self._informativity_cache.items()
                 for c, e in ce.items()
                 if column_to_slot(table, c) in column_options]
            )
        else:
            informativity_table = self.get_column_entropies(result_table, column_options)
        if not informativity_table:
            logger.debug('Informativity table is empty')
            return (None, None) if as_table_column else None
        best_informativity = max(informativity_table.values())
        best_slots = [slot for slot, informativity in informativity_table.items() if
                      informativity == best_informativity]
        next_slot = random.choice(best_slots)
        if not next_slot:
            logger.debug('No next slot found')
            return (None, None) if as_table_column else None
        if not as_table_column:
            logger.debug(f'Found next slot {next_slot}')
            return next_slot
        logger.debug(f'Transforming next slot to table/column tuple: {next_slot}')
        fk_table, fk_column, table, column = slot_to_table_column_with_join_table_column(next_slot)
        return table_with_fk(fk_table, fk_column, table), column

    @staticmethod
    def get_real_constraints(constraints):
        return dict([(table, column_constr) for table, column_constr in constraints.items()
                     if column_constr and
                     any([is_value(val) for col, constrs in column_constr.items()
                          for constr in constrs
                          for val in constr['values']])])

    @staticmethod
    def build_constraint(values: List[any], operator: str = OPERATOR_EQUAL, is_reference: bool = False):
        """
        Returns a Dict with a constraint.
        :param values: A list of values to compare
        :param operator: An SQL operator for comparison (e.g. IN, =, >, <, NOT)
        :param is_reference: Wheater the constraint operand (values) is a reference to another column or an actual value
        :return:
        """
        return {
            'values': values,
            'operator': operator
        }

    @staticmethod
    def _get_where_conditions(constraints, params={}, param_num=0):
        where_clause = ''
        filtered_constraints = dict([(table, col_constr) for table, col_constr in constraints.items() if col_constr])
        for table_alias, column_constraints in filtered_constraints.items():
            for column_name, col_constraints in column_constraints.items():
                for c in col_constraints:
                    values = c['values']
                    operator = c['operator']
                    # skip dont care conditions
                    if len(values) == 1 and values[0] == DONT_CARE:
                        continue
                    where_clause += f" AND {table_alias}.{column_name} {operator} "
                    param_name = f'param{param_num}'
                    if operator == OPERATOR_IN or len(values) > 1:
                        params[param_name] = tuple(values)
                    elif len(values) > 1:
                        params[param_name] = values
                    else:
                        params[param_name] = values[0]
                    param_num += 1
                    where_clause += f'%({param_name})s'
        return where_clause, params, param_num

    def get_similar_string_values(self, table: str, column: str, value: str, gt_threshold: float = 0):
        max_query = f'(SELECT max(public.SIMILARITY({column}, %(value)s)) AS max_sim FROM {table}' \
                    f' WHERE public.SIMILARITY({column}, %(value)s::TEXT) > %(gt_threshold)s) max_sims'

        query = f'SELECT ' \
                f'{column}, public.SIMILARITY({column}, %(value)s) AS similarity' \
                f' FROM {table}' \
                f' INNER JOIN {max_query}' \
                f' ON public.SIMILARITY({column}, %(value)s) = max_sim' \
                f' GROUP BY {column}'
        params = {
            'value': value,
            'gt_threshold': gt_threshold
        }
        result = self.__query_all(query, params)
        if len(result) == 0:
            return None, 0
        return [row[column] for row in result], result[0]['similarity']

    def get_column_type(self, table_name, column_name):
        table_matches = list(filter(lambda t: t.name == table_name, self._metaschema.tables))
        if len(table_matches) == 0:
            logger.error(f'Schema has no table {table_name}')
            return None
        table = table_matches[0]
        column_matches = list(filter(lambda c: c.name == column_name, table.columns))
        if len(column_matches) == 0:
            logger.error(f'Table {table_name} has no column {column_name}')
            return None
        column = column_matches[0]
        return self.get_python_datatype(column.data_type)

    def get_python_datatype(self, data_type: str):
        category = self.type_categories[data_type]
        if category == 'S':
            return 'string'
        if category == 'N':
            if data_type.startswith('int'):
                return 'integer'
            return 'float'
        if category == 'B':
            return 'bool'
        if category == 'D':
            if data_type == 'date':
                return 'date'
            if data_type in ['time', 'timetz']:
                return 'time'
            return 'datetime'
        return 'string'  # default

    def get_sample(self, table_names, column_names={}, constraints={}):
        if isinstance(table_names, str):
            column_names = {table_names: [column_names] if isinstance(column_names, str) else column_names}
            table_names = [table_names]
        return self.select(table_names, column_names, constraints, order=('random()', 'ASC'), limit=1)

    def get_column_sample(self, table_name, column_name):
        return self.__query_one(
            f'SELECT {column_name} FROM {table_name} WHERE {column_name} NOTNULL ORDER BY random() LIMIT 1')

    def can_cast_datatype(self, value, datatype) -> bool:
        params = {
            'value': value
        }
        try:
            result = self.__query_one(f'SELECT %(value)s::{datatype}', params)
            # logger.debug(f'Datatype validation successfull: {value}::{datatype}={result[datatype]}')
            return True
        except errors.RaiseException as e:
            logger.error(f'Datatype validation failed: {value}::{datatype}')
            logger.error(e)
            return False

    def _check_connection(self):
        return self._connection and not self._connection.closed

    def __query_one(self, sql, data={}):
        if self._check_connection():

            with self._connection.cursor() as curs:
                curs.execute(sql, data)
                return curs.fetchone()
        else:
            logger.error('Could not execute query. Not database connection established.')
            return {}

    def __query_many(self, sql: str, data={}, num=100):
        if self._check_connection():
            with self._connection.cursor() as curs:
                curs.execute(sql, data)
                return curs.fetchmany(num)
        else:
            logger.error('Could not execute query. Not database connection established.')
            return []

    def __query_all(self, sql: str, data={}):
        if self._check_connection():
            with self._connection.cursor() as curs:
                curs.execute(sql, data)
                return curs.fetchall()
        else:
            logger.error('Could not execute query. Not database connection established.')
            return []

    def __execute(self, sql: str, data={}):
        if self._check_connection():
            with self._connection.cursor() as curs:
                curs.execute(sql, data)
                self._connection.commit()
        else:
            logger.error('Could not execute query. Not database connection established.')

    def __generate_metaschema(self):
        self._metaschema = MetaSchema(name=self.schema_name)
        if self._check_connection():
            logger.debug('Generating schema for current database connection...')
            self.__get_data_types()
            self._metaschema.tables = self.__generate_schema_tables(self.schema_name)
            self._metaschema.procedures = self.__generate_schema_procedures(self.schema_name)
            self._dependencies = self.__generate_dependency_graph(self._metaschema.table_names())
            self._metaschema.mapping_tables = [table.name for table in self._metaschema.tables if
                                               self._metaschema._is_mapping_table(table)]
        else:
            logger.error('Could not generate schema. No database connection established.')

    def __get_data_types(self):
        # get postgres types dictory - pg_proc only reveales type ids
        result = self.__query_all(
            "SELECT t.oid, t.typname, t.typcategory \
            FROM    pg_catalog.pg_type t;"
        )
        self.types = dict([(t['oid'], t['typname']) for t in result])
        self.type_categories = dict([(t['typname'], t['typcategory']) for t in result])

    def __generate_schema_tables(self, schema_name) -> List[Table]:
        tables = []
        table_names = [t['table_name'] for t in self.__query_all(
            "SELECT table_name FROM information_schema.tables \
            WHERE table_schema=%(table_schema)s \
            AND table_type='BASE TABLE';", {'table_schema': schema_name})]
        for table_name in table_names:
            # primary keys
            primary_key_rows = self.__query_all(
                "SELECT column_name FROM information_schema.table_constraints t \
                LEFT JOIN information_schema.key_column_usage k \
                ON t.constraint_name = k.constraint_name AND t.table_name = k.table_name \
                WHERE k.constraint_schema =%(schema_name)s AND k.table_name = %(table_name)s \
                AND t.constraint_type = 'PRIMARY KEY'",
                {'schema_name': schema_name,
                 'table_name': table_name
                 })
            primary_key = []
            if primary_key_rows:
                primary_key = [primary_key_row['column_name'] for primary_key_row in
                               primary_key_rows]
            table = Table(name=table_name, primary_key=primary_key)

            # columns
            columns_data = [c for c in self.__query_all(
                # column_name, data_type, is_nullable
                "SELECT column_name, udt_name As data_type, is_nullable FROM information_schema.columns \
                WHERE table_schema = %(schema_name)s AND table_name = %(table_name)s",
                {'schema_name': schema_name,
                 'table_name': table_name})]

            columns = []
            for c in columns_data:
                column_name = c['column_name']
                data_type = c['data_type']
                nullable = c['is_nullable']
                is_nullable = True if nullable == 'YES' else False
                column = Column(name=column_name, data_type=data_type, nullable=is_nullable)

                foreign_key_row = self.__query_one(
                    "SELECT	rel_kcu.table_name AS foreign_table_name, rel_kcu.column_name AS foreign_column_name \
                    FROM information_schema.table_constraints tco \
                    JOIN information_schema.key_column_usage kcu ON \
                    tco.constraint_schema = kcu.constraint_schema \
                    AND tco.constraint_name = kcu.constraint_name \
                    JOIN information_schema.referential_constraints rco \
                    ON tco.constraint_name = rco.constraint_name \
                    AND tco.constraint_schema = rco.constraint_schema \
                    JOIN information_schema.key_column_usage rel_kcu \
                    ON rco.unique_constraint_schema = rel_kcu.constraint_schema \
                    AND rco.unique_constraint_name = rel_kcu.constraint_name \
                    AND kcu.ordinal_position = rel_kcu.ordinal_position \
                    AND rco.constraint_name = tco.constraint_name \
                    WHERE kcu.constraint_schema = %(schema_name)s AND kcu.table_name = %(table_name)s AND\
                    kcu.column_name = %(column_name)s AND tco.constraint_type = 'FOREIGN KEY'",
                    {
                        'schema_name': schema_name,
                        'table_name': table_name,
                        'column_name': column_name
                    })
                if foreign_key_row:
                    column.table_reference = foreign_key_row['foreign_table_name']
                    column.column_reference = foreign_key_row['foreign_column_name']
                columns += [column]
            table.columns = columns
            tables += [table]
        logger.debug(f'Found {len(tables)} tables.')
        return tables

    def __generate_schema_procedures(self, schema_name) -> List[Procedure]:
        procedures_data = self.__query_all(
            "SELECT n.nspname, p.proname, p.proargnames, p.proargtypes, p.prorettype, p.prosrc, p.prokind, p.proallargtypes, p.proargmodes FROM pg_catalog.pg_namespace n JOIN pg_catalog.pg_proc p ON p.pronamespace = n.oid WHERE p.prokind = 'f' AND n.nspname = 'public' AND proargmodes IS NOT NULL;",
            {}
        )

        procedures = []
        for p in procedures_data:
            procedure_name = p['proname']
            procedure_operation = OPERATION_SELECT if p['prokind'] == 'f' else OPERATION_CALL
            # zip argument names (list) with looked up argument types (only provided as string by catalog)
            parameters = []
            # only input arguments in proargtypes (output/table arguments in proallargtypes)
            in_arg_types = p['proargtypes']
            for arg in zip(p['proargnames'][:len(in_arg_types)],
                           [self.types[int(typeid_str)] for typeid_str in in_arg_types.split()]):
                parameter_name = arg[0]
                type_name = arg[1]
                data_type = type_name.strip('_')
                is_list = type_name.startswith('_')
                parameter = Parameter(name=parameter_name, data_type=data_type, is_list=is_list)
                parameters += [parameter]

            # filter return types if return is via OUT or a table (record is returned)
            return_record = None
            return_values = []

            if procedure_operation == 'select':
                return_type = self.types[int(p['prorettype'])]
                return_modes = [m for m in p['proargmodes'] if m != 'i']
                return_record = ReturnRecord(name=procedure_name, is_list=all([m == 't' for m in return_modes]))
                all_names = p['proargnames']
                all_types = p['proallargtypes']
                all_modes = p['proargmodes']
                # only look at OUT (o) or TABLE (t) args
                for name, arg_type, mode in [(n, t, m) for n, t, m in zip(all_names, all_types, all_modes) if
                                             m != 'i']:
                    type_name = self.types[int(arg_type)]
                    data_type = type_name.strip('_')
                    is_list = type_name.startswith('_')
                    return_value = ReturnValue(name=name, data_type=data_type, is_list=is_list)
                    return_values += [return_value]
                return_record.values = return_values

            procedure = Procedure(name=procedure_name,
                                  operation=procedure_operation,
                                  parameters=parameters,
                                  return_record=return_record,
                                  body=p['prosrc'])
            procedures += [procedure]
        logger.debug(f'Found {len(procedures)} stored procedures.')
        return procedures

    def __generate_dependency_graph(self, table_names):
        graph = DependencyGraph()
        for table_name in table_names:
            vertices, edges = self.__get_table_vertices_edges(graph, table_name)
            for v in vertices:
                graph.add_vertex(v)
            for e in edges:
                graph.add_edge(e)
        return graph

    def __build_informativity_cache(self, use_primary_keys=False):
        logger.debug('Building cache for base table informativity')
        informativity_table = {}
        for table in self._metaschema.tables:
            logger.debug(f'Caching table {table.name}')
            column_names = [column.name for column in table.columns if
                            use_primary_keys or column.name not in table.primary_key]
            informativity_table[table.name] = self.get_column_entropies(table.name, column_names)
        self._informativity_cache = informativity_table

    def __get_table_vertices_edges(self, graph, table_alias):
        table_prefix, table_name = table_to_fk_and_table(table_alias)
        table_vertex = DependencyVertex(table_name=table_name,
                                        table_alias=table_alias)  # , table_alias=table_alias)
        if table_vertex in graph.vertices:
            return [], []
        table = self._metaschema.get_table(table_name)
        vertices = []
        edges = []
        vertices.append(table_vertex)
        fk_columns = [column for column in table.columns if column.table_reference and column.column_reference]
        for column in fk_columns:
            reference_table = column.table_reference
            referenced_column = column.column_reference
            to_table_alias = reference_table
            edges.append(DependencyEdge(from_table=table_name, to_table=reference_table,
                                        from_alias=table_alias, to_alias=to_table_alias,
                                        from_column=column.name, to_column=referenced_column))
            if column.table_reference == table_name:
                continue
            rec_vertices, rec_edges = self.__get_table_vertices_edges(graph, to_table_alias)
            for e in rec_edges:
                edges.append(e)
            for v in rec_vertices:
                vertices.append(v)
        return vertices, edges
