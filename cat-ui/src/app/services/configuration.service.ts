import {Injectable, isDevMode} from '@angular/core';
import {Configuration} from '../model/configuration';
import {Table} from '../model/table';
import {Procedure} from '../model/procedure';
import {Observable, of} from 'rxjs';
import {JsonService} from './json.service';

export interface ConfigurationImport {
  configuration: Configuration;
  warnings: string[];
}

@Injectable({providedIn: 'root'})
export class ConfigurationService {

  constructor(private jsonService: JsonService) {
  }

  exportConfiguration(configTables: Table[], configProcedures: Procedure[]) {
    const exportConfig: Configuration = {
      tables: configTables,
      procedures: configProcedures
    };
    return this.jsonService.toJson(exportConfig);
  }

  importConfiguration(file: File, matchTables: Table[], matchProcedures: Procedure[]): Observable<ConfigurationImport> {
    return new Observable<ConfigurationImport>((sub) => {
      this.jsonService.readTextFile(file)
        .subscribe(text => {
          this.jsonService.parseJSON(text)
            .subscribe(json => {
              const config = json as Configuration;
              if (!config.tables || !config.procedures) {
                sub.error(`Could not parse configuration file. Missing tables or procedures.`);
              }
              return this.validateConfiguration(json, matchTables, matchProcedures)
                .subscribe(configImport => {
                  sub.next(configImport);
                  sub.complete();
                }, error => {
                  sub.error(error);
                });
            }, error => {
              sub.error(`Error parsing JSON: ${error}`);
            });
        }, error => {
          sub.error(`Error reading file ${file.name}: ${error}`);
        });
    });
  }

  private validateConfiguration(config: any, matchTables: Table[], matchProcedures: Procedure[]): Observable<ConfigurationImport> {
    return new Observable<ConfigurationImport>(sub => {
      const warn: string[] = [];
      const validTablesResult = this.validateTables(config, matchTables);
      validTablesResult.warnings.forEach(err => warn.push(err));
      const validColumnResult = this.validateColumns(validTablesResult.configuration, matchTables);
      validColumnResult.warnings.forEach(err => warn.push(err));
      const validProceduresResult = this.validateProcedures(validColumnResult.configuration, matchProcedures);
      validProceduresResult.warnings.forEach(err => warn.push(err));
      sub.next({
        configuration: validProceduresResult.configuration,
        warnings: warn
      });
      sub.complete();
    });
  }

  private validateTables(config: Configuration, matchTables: Table[]): ConfigurationImport {
    const warn = [];
    // Missing tables
    const missingTables = matchTables.filter(matchTable => {
      return config.tables.map(t => t.name).indexOf(matchTable.name) < 0;
    });
    if (missingTables.length > 0) {
      const missingTableNames = missingTables.map(t => t.name);
      warn.push(`Configuration misses the following tables: ${missingTableNames.join(', ')}.`);
      const backupTables = matchTables.filter(t => missingTableNames.indexOf(t.name) > -1);
      backupTables.forEach(table => {
        config.tables.push(table);
      });
    }
    // Tables that are not in the database
    const additionalTables = config.tables.filter(table => {
      return matchTables.map(t => t.name).indexOf(table.name) < 0;
    });
    if (additionalTables.length > 0) {
      const additionalTableNames = additionalTables.map(t => t.name);
      warn.push(`Configuration has unknown tables: ${additionalTableNames.join(', ')}. Skipping tables.`);
      additionalTableNames.forEach(tableName => {
        const index = config.tables.map(t => t.name).indexOf(tableName);
        config.tables.splice(index, 1);
      });
    }
    // Validate table pk
    config.tables.forEach(table => {
      const pk = table.primaryKey;
      const matchTable = matchTables.find(t => t.name === table.name);
      // equal if no, pk, same components of the primary. same length => check only one direction
      const pkEqual = (!pk && !matchTable.primaryKey) || (
        pk && matchTable.primaryKey &&
        pk.length === matchTable.primaryKey.length &&
        pk.every(col => matchTable.primaryKey.indexOf(col) > -1)
      );
      if (!pkEqual) {
        warn.push(`Primary key of configuration table '${table.name}' '${table.primaryKey.join(', ')}' does not match \
                  '${matchTable.primaryKey.join(', ')}'. Using existing configuration.`);
        table.primaryKey = matchTable.primaryKey;
      }
    });
    // Validate NL expressions
    config.tables.forEach(table => {
      const matchTable = matchTables.find(t => t.name === table.name);
      const representation = table.nlExpressions;
      if (representation === undefined) {
        warn.push(`NL Expressions of table '${table.name}' are missing, using existing configuration`);
        table.representation = matchTable.representation;
      }
    });
    // Validate representation
    config.tables.forEach(table => {
      const matchTable = matchTables.find(t => t.name === table.name);
      const representation = table.representation;
      if (representation === undefined) {
        warn.push(`Representation of table '${table.name}' are missing, using existing configuration`);
        table.representation = matchTable.representation;
      }
    });
    // Validate resolveDepth
    // Validate representation
    config.tables.forEach(table => {
      const matchTable = matchTables.find(t => t.name === table.name);
      const resolveDepth = table.resolveDepth;
      if (!resolveDepth) {
        warn.push(`Resolve depth of table '${table.name}' is missing, using existing configuration`);
        table.resolveDepth = matchTable.resolveDepth;
      }
    });
    return {
      configuration: config,
      warnings: warn
    };
  }

  private validateColumns(config: Configuration, matchTables: Table[]): ConfigurationImport {
    const warn = [];
    config.tables.forEach(table => {
      const matchTable = matchTables.find(t => t.name === table.name);
      matchTable.columns.forEach(matchCol => {
        // Find missing columns
        const col = table.columns.find(c => c.name === matchCol.name);
        if (!col) {
          warn.push(`Configuration table '${table.name}' has missing column '${matchCol.name}'. Adding column.`);
          table.columns.push(matchCol);
        } else {
          const index = table.columns.map(c => c.name).indexOf(col.name);
          // Match data types
          if (matchCol.dataType !== col.dataType) {
            warn.push(`Configuration column '${table.name}.${col.name}' data type \
            '${col.dataType}' does not match '${matchCol.dataType}'. Updating value.`);
            table.columns[index].dataType = matchCol.dataType;
          }
          // Match FK relation
          if (matchCol.tableReference !== col.tableReference || matchCol.columnReference !== col.columnReference) {
            warn.push(`Configuration column '${table.name}.${col.name}' foreign key relation \
            '${col.tableReference}.${col.columnReference}' does not match \
            '${matchCol.tableReference}.${matchCol.columnReference}'. Updating value.`);
            table.columns[index].tableReference = matchCol.tableReference;
            table.columns[index].columnReference = matchCol.columnReference;
          }
          if (!col.nlExpressions) {
            warn.push(`Configuration column '${table.name}.${col.name}' misses natural language expressions. Using existing configuration`);
            table.columns[index].nlExpressions = matchCol.nlExpressions;
          }
          // Validate options
          if (col.requestable === undefined) {
            warn.push(`Configuration column '${table.name}.${col.name}' misses option 'requestable'. Using existing configuration`);
            col.requestable = matchCol.requestable;
          }
          if (col.displayable === undefined) {
            warn.push(`Configuration column '${table.name}.${col.name}' misses option 'displayable'. Using existing configuration`);
            col.displayable = matchCol.displayable;
          }
          if (col.resolveDependency === undefined) {
            warn.push(`Configuration column '${table.name}.${col.name}' misses option 'resolveDependency'. Using existing configuration`);
            col.resolveDependency = matchCol.resolveDependency;
          }
          if (col.lookupTable === undefined) {
            warn.push(`Configuration column '${table.name}.${col.name}' misses option 'lookupTable'. Using existing configuration`);
            col.lookupTable = matchCol.lookupTable;
          }
          if (col.regex === undefined) {
            warn.push(`Configuration column '${table.name}.${col.name}' misses option 'regex'. Using existing configuration`);
            col.regex = matchCol.regex;
          }
        }
        // Find unexpected columns
        const additionalColumns = table.columns.filter(column => {
          return matchTable.columns.map(c => c.name).indexOf(column.name) < 0;
        });
        const additionalColumnNames = additionalColumns.map(c => c.name);
        if (additionalColumnNames.length > 0) {
          warn.push(`Configuration has unknown columns in table '${table.name}': ${additionalColumnNames.join(', ')}. Ignoring columns.`);
          additionalColumnNames.forEach(colName => {
            const index = table.columns.map(c => c.name).indexOf(colName);
            table.columns.splice(index, 1);
          });
        }
      });
    });
    return {
      configuration: config,
      warnings: warn
    };
  }

  private validateProcedures(config: Configuration, matchProcedures: Procedure[]): ConfigurationImport {
    const warn = [];
    // Missing procedures
    const missingProcedures = matchProcedures.filter(matchProcedure => {
      return config.procedures.map(p => p.name).indexOf(matchProcedure.name) < 0;
    });
    if (missingProcedures.length > 0) {
      const missingProcedureNames = missingProcedures.map(p => p.name);
      warn.push(`Configuration misses the following procedures: ${missingProcedureNames.join(', ')}.`);
      const backupProcedures = matchProcedures.filter(p => missingProcedureNames.indexOf(p.name) > -1);
      backupProcedures.forEach(procedure => {
        config.procedures.push(procedure);
      });
    }
    // Procedures that are not in the database
    const additionalProcedures = config.procedures.filter(procedure => {
      return matchProcedures.map(p => p.name).indexOf(procedure.name) < 0;
    });
    if (additionalProcedures.length > 0) {
      const additionalProcedureNames = additionalProcedures.map(p => p.name);
      warn.push(`Configuration has unknown procedures: ${additionalProcedureNames.join(', ')}. Skipping procedures.`);
      additionalProcedureNames.forEach(procedureName => {
        const index = config.procedures.map(p => p.name).indexOf(procedureName);
        config.procedures.splice(index, 1);
      });
    }
    config.procedures.forEach(procedure => {
      const matchProcedure = matchProcedures.find(p => p.name === procedure.name);

      // Validate sampling
      if (!procedure.nlSample) {
        warn.push(`Configuration procedure '${procedure.name}' has missing nl sample. Adding empty sample.`);
        procedure.nlSample = {
          parameterName: null,
          predicates: [],
          tableName: null,
          columnName: null
        };
      }

      // Validate procedure params
      matchProcedure.parameters.forEach(param => {
        // Find missing parameters
        const matchParam = procedure.parameters.find(p => p.name === param.name);
        if (!matchParam) {
          warn.push(`Configuration procedure '${procedure.name}' has missing parameter '${param.name}'. Adding parameter.`);
          procedure.parameters.push(param);
        } else {
          const index = procedure.parameters.map(p => p.name).indexOf(param.name);
          // Match data types
          if (param.dataType !== procedure.parameters[index].dataType) {
            warn.push(`Configuration parameter '${procedure.name}.${param.name}' data type \
            '${procedure.parameters[index].dataType}' does not match '${param.dataType}'. Updating value.`);
            procedure.parameters[index].dataType = param.dataType;
          }
          if (param.list !== procedure.parameters[index].list) {
            if (param.list) {
              warn.push(`Configuration procedure '${procedure.name}' parameter '${param.name}' type is a list. Updating value.`);
              procedure.parameters[index].list = true;
            } else {
              warn.push(`Configuration procedure '${procedure.name}' parameter '${param.name} is not a list. Updating value.`);
              procedure.parameters[index].list = false;
            }
          }
        }
        // Find unexpected parameters
        const additionalParameters = procedure.parameters.filter(parameter => {
          return matchProcedure.parameters.map(p => p.name).indexOf(parameter.name) < 0;
        });
        const additionalParameterNames = additionalParameters.map(p => p.name);
        if (additionalParameterNames.length > 0) {
          warn.push(`Configuration has unknown parameters in procedure '${procedure.name}': ${additionalParameterNames.join(', ')}. Ignoring parameters.`);
          additionalParameterNames.forEach(colName => {
            const index = procedure.parameters.map(p => p.name).indexOf(colName);
            procedure.parameters.splice(index, 1);
          });
        }
      });

      // Validate procedure return values
      if (matchProcedure.returns) {
        matchProcedure.returns.values.forEach(returnValue => {
          // Find missing return values
          const matchReturnValue = procedure.returns.values.find(r => r.name === returnValue.name);
          if (!matchReturnValue) {
            warn.push(`Configuration procedure '${procedure.name}' has missing return value '${returnValue.name}'. Adding value.`);
            procedure.returns.values.push(returnValue);
          } else {
            const index = procedure.returns.values.map(r => r.name).indexOf(returnValue.name);
            // Match data types
            if (returnValue.dataType !== procedure.returns.values[index].dataType) {
              warn.push(`Configuration return value '${procedure.name}.${returnValue.name}' data type \
            '${procedure.returns.values[index].dataType}' does not match '${returnValue.dataType}'. Updating value.`);
              procedure.returns.values[index].dataType = returnValue.dataType;
            }
            if (returnValue.list !== procedure.returns.values[index].list) {
              if (returnValue.list) {
                warn.push(`Configuration procedure '${procedure.name}' return value '${returnValue.name}' type is a list. Updating value.`);
                procedure.returns.values[index].list = true;
              } else {
                warn.push(`Configuration procedure '${procedure.name}' return value '${returnValue.name} is not a list. Updating value.`);
                procedure.returns.values[index].list = false;
              }
            }
          }
          // Find unexpected return values
          const additionalReturnValues = procedure.returns.values.filter(retVal => {
            return matchProcedure.returns.values.map(r => r.name).indexOf(retVal.name) < 0;
          });
          const additionalReturnValueNames = additionalReturnValues.map(r => r.name);
          if (additionalReturnValueNames.length > 0) {
            warn.push(`Configuration has unknown return values in procedure '${procedure.name}': ${additionalReturnValueNames.join(', ')}. Ignoring values.`);
            additionalReturnValueNames.forEach(retVal => {
              const index = procedure.returns.values.map(r => r.name).indexOf(retVal);
              procedure.returns.values.splice(index, 1);
            });
          }
        });
      }
      if (matchProcedure.body !== procedure.body) {
        warn.push(`The body of '${procedure.name}' has changed. Updating to new body.`);
        procedure.body = matchProcedure.body;
      }
    });
    return {
      configuration: config,
      warnings: warn
    };
  }

}
