import os
from flask import request
from flask_restplus import Resource, Namespace, fields
from flask_jwt_extended import jwt_required
from flask_restplus.inputs import boolean
from cat.db.database import *
from cat.db.schema import Table as DBTable, Column as DBColumn, Procedure as DBProcedure, Parameter as DBParameter, \
    ReturnRecord as DBReturnRecord, ReturnValue as DBReturnValue

# allow disabling JWT by overriding default
if not boolean(os.getenv('JWT_ON', False)):
    jwt_required = lambda fn: fn

api = Namespace('database', description='Database related operations')

connect_data = api.model('Connect_database_data', {
    'hostname': fields.String('Hostname', required=True),
    'port': fields.Integer('Port', required=True),
    'username': fields.String('Username', required=True),
    'password': fields.String('Password', required=True),
    'databaseName': fields.String('Database name', required=True),
    'schemaName': fields.String('Schema name', required=True)
})


@api.route('/connect')
class DatabaseConnect(Resource):
    @api.doc('connect_database')
    @api.expect(connect_data)
    @jwt_required
    def post(self):
        connect_dict = request.json
        missing = [key for key in connect_data.keys() if not connect_dict or key not in connect_dict.keys()]
        if len(missing) > 0:
            api.abort(400, f'Missing parameters: {", ".join(missing)}')
        try:
            PostgreSQLDatabase.get_instance(host=connect_dict['hostname'],
                                            port=connect_dict['port'],
                                            user=connect_dict['username'],
                                            password=connect_dict['password'],
                                            db_name=connect_dict['databaseName'],
                                            schema_name=connect_dict['schemaName'])
            return True, 200
        except Exception as e:
            api.abort(400, e)


@api.route('/tables')
class TableList(Resource):
    @api.doc('list_tables')
    @jwt_required
    def get(self):
        db = try_database(api)
        tables = [transform_table(table) for table in db.get_metaschema().tables]
        return tables, 200


table_data = api.model('Table', {
    'name': fields.String(readonly=True, description='The unique name of the table')
})


@api.route('/tables/<name>')
class Table(Resource):
    @api.doc('table')
    @api.expect(table_data)
    @jwt_required
    def get(self, name):
        db = try_database(api)
        tables = [table for table in db.get_metaschema().tables if table.name == name]
        if len(tables) == 1:
            return transform_table(tables[0]), 200
        api.abort(404, f'Table {name} not found')


@api.route('/tables/<name>/columns')
class ColumnList(Resource):
    @api.doc('list_columns')
    @api.expect(table_data)
    @jwt_required
    def get(self, name):
        db = try_database(api)
        tables = [table for table in db.get_metaschema().name if table.name == name]
        if len(tables) == 1:
            return [transform_column(column, tables[0]) for column in tables[0].columns], 200
        api.abort(404, f'Column {name} not found')


column_data = api.model('Column', {
    'table_name': fields.String(readonly=True, description='The unique name of the table'),
    'column_name': fields.String(readonly=True, description='The unique name of the column')
})


@api.route('/tables/<table_name>/columns/<column_name>')
class Column(Resource):
    @api.doc('column')
    @api.expect(column_data)
    @jwt_required
    def get(self, table_name, column_name):
        db = try_database(api)
        tables = [table for table in db.get_metaschema().tables if table.name == table_name]
        if len(tables) == 1:
            columns = [column for column in tables[0].columns if column.name == column_name]
            if len(columns) == 1:
                return transform_column(columns[0], tables[0]), 200
        api.abort(404, f'Column {column_name} not found')


@api.route('/tables/<table_name>/columns/<column_name>/values')
class Column(Resource):
    @api.doc('colum_values')
    @api.expect(column_data)
    @jwt_required
    def get(self, table_name, column_name):
        db = try_database(api)
        tables = [table for table in db.get_metaschema().tables if table.name == table_name]
        if len(tables) == 1:
            columns = [column for column in tables[0].columns if column.name == column_name]
            if len(columns) == 1:
                result = db.select_distinct(table_name, column_name)
                return [value for row in result for column, value in row.items()], 200
        api.abort(404, f'Column {table_name}.{column_name} not found')


@api.route('/procedures')
class ProcedureList(Resource):
    @api.doc('list_procedures')
    @jwt_required
    def get(self):
        db = try_database(api)
        procedures = [transform_procedure(procedure) for procedure in db.get_metaschema().procedures]
        return procedures, 200


def transform_table(table: DBTable):
    return {
        'name': table.name,
        'primaryKey': table.primary_key,
        'nlExpressions': [table.name.lower().replace('_', ' ').strip()],
        'columns': [transform_column(column, table) for column in table.columns],
        'resolveDepth': 1,
        'representation': ''
    }


def transform_column(column: DBColumn, table: DBTable):
    is_reference_column = column.table_reference and column.column_reference
    return {
        'name': column.name,
        'nlExpressions': [column.name.lower().replace('_', ' ').strip()],
        'dataType': column.data_type,
        'tableReference': column.table_reference,
        'columnReference': column.column_reference,
        'nullable': column.nullable,
        'requestable': False if column.name in table.primary_key or is_reference_column else True,
        'displayable': False if column.name in table.primary_key or is_reference_column else True,
        'resolveDependency': is_reference_column,
        'regex': None,
        'lookupTable': []
    }


def transform_procedure(procedure: DBProcedure):
    return {
        'name': procedure.name,
        'nlPairs': [],
        'nlSample': {'parameterName': None, 'predicates': [], 'tableName': None, 'columnName': None},
        'operation': procedure.operation,
        'parameters': [transform_parameter(param) for param in procedure.parameters],
        'returns': transform_return_record(procedure.return_record) if procedure.return_record else None,
        'body': procedure.body
    }


def transform_parameter(param: DBParameter):
    return {
        'name': param.name,
        'nlExpressions': [param.name.lower().replace('_', ' ').strip()],
        'dataType': param.data_type,
        'list': param.is_list,
        'sampleWith': None,
        'tableReference': None,
        'columnReference': None
    }


def transform_return_record(return_type: DBReturnRecord):
    return {
        'name': return_type.name,
        'nlExpressions': [return_type.name.lower().replace('_', ' ').strip()],
        'values': [transform_return_value(return_value) for return_value in return_type.values]
    }


def transform_return_value(return_value: DBReturnValue):
    return {
        'name': return_value.name.lower(),
        'nlExpressions': [return_value.name.lower().replace('_', ' ').strip()],
        'dataType': return_value.data_type,
        'list': return_value.is_list,
        'tableReference': None,
        'columnReference': None
    }


def try_database(api_handle) -> PostgreSQLDatabase:
    try:
        return PostgreSQLDatabase.get_instance()
    except Exception as e:
        api_handle.abort(400, e)
