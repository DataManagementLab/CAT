import {Injectable} from '@angular/core';
import {Configuration} from '../model/configuration';
import {Observable, of} from 'rxjs';
import {Task} from '../model/task';
import {Argument} from '../model/argument';
import {Slot} from '../model/slot';
import {Table} from '../model/table';
import {Subtask} from '../model/subtask';
import {Column} from '../model/column';

@Injectable({providedIn: 'root'})
export class TaskService {

  constructor() {
  }

  exportTasks(tasks: Task[]) {
    return JSON.stringify(tasks, null, '\t');
  }

  generateTasks(configuration: Configuration): Observable<Task[]> {
    const tasks: Task[] = [];
    const tables = configuration.tables;
    const procedures = configuration.procedures;

    procedures.forEach(proc => {
      const taskName = proc.name;
      const taskOperation = proc.operation;
      const taskNl = proc.nlPairs;
      const taskSlots = this.getTaskSlots(proc.name, proc.parameters);
      const returnRecordNl = proc.operation === 'call' ? [] : proc.returns.nlExpressions;
      const taskReturnSlots = proc.operation === 'call' ? [] : this.getReturnSlots(proc.name, proc.returns.values);
      const taskSubTasks = this.getSubtasks(taskSlots, tables);
      tasks.push({
        name: taskName,
        operation: taskOperation,
        nl: taskNl,
        slots: taskSlots,
        returnNl: returnRecordNl,
        returnSlots: taskReturnSlots,
        subtasks: taskSubTasks
      });
    });

    return of(tasks);
  }

  private getTaskSlots(taskName: string, parameters: Argument[]): Slot[] {
    return parameters.map(p => (
      this.valueToSlot(taskName, p)
    ));
  }

  private getReturnSlots(taskName: string, returnValues: Argument[]): Slot[] {
    return returnValues.map(rv => this.valueToSlot(taskName, rv));
  }

  private valueToSlot(prefix: string, value: Argument): Slot {
    return {
      name: `${prefix}__${value.name}`,
      entityNl: [],
      nl: value.nlExpressions,
      dataType: value.dataType,
      list: value.list,
      requestable: false,
      displayable: true,
      tableReference: value.tableReference,
      columnReference: value.columnReference,
      regex: null,
      lookupTable: []
    };
  }

  private getSubtasks(parentSlots: Slot[], tables: Table[]): Subtask[] {
    const subtasks = [];
    parentSlots.forEach(parentSlot => {
      const isSelectTask = parentSlot.tableReference && parentSlot.columnReference;
      if (isSelectTask) {
        let targetTable = tables.find(t => t.name === parentSlot.tableReference);
        let targetColumn = targetTable.columns.find(c => c.name === parentSlot.columnReference);
        let prefix;
        // If this is a foreign key reference, resolve it and use the referenced table to resolve slots
        if (targetTable.primaryKey.indexOf(parentSlot.columnReference) === -1) {
          const fkColumn = targetTable.columns.find(c => c.name === parentSlot.columnReference);
          targetTable = tables.find(t => t.name === fkColumn.tableReference);
          targetColumn = targetTable.columns.find(c => c.name === fkColumn.columnReference);
          prefix = `${parentSlot.tableReference}__${parentSlot.columnReference}`;
        }
        subtasks.push({
          targetSlot: parentSlot.name,
          targetDataType: parentSlot.dataType,
          targetList: parentSlot.list,
          targetTable: targetTable.name,
          targetTableNl: targetTable.nlExpressions,
          targetColumn: targetColumn.name,
          targetTableRepresentation: targetTable.representation,
          operation: 'select',
          slots: this.getSubtaskSlots(targetTable, tables, prefix)
        });
      } else {
        subtasks.push({
          targetSlot: parentSlot.name,
          targetDataType: parentSlot.dataType,
          targetList: parentSlot.list,
          targetTable: undefined,
          targetTableNl: [],
          targetColumn: undefined,
          targetTableRepresentation: '',
          operation: 'choose',
          slots: this.getChoiceSubtaskSlots(parentSlot)
        });
      }

    });
    return subtasks;
  }

  private getChoiceSubtaskSlots(parentSlot: Slot) {
    return [{
      name: `choice_${parentSlot.name}`,
      entityNl: [],
      nl: parentSlot.nl,
      dataType: parentSlot.dataType,
      list: parentSlot.list,
      requestable: true,
      displayable: true,
      tableReference: null,
      columnReference: null,
      regex: null,
      lookupTable: []
    }];
  }

  private getSubtaskSlots(targetTable: Table, tables: Table[], prefix?: string): Slot[] {
    return this.getJointTableColumnSlots(targetTable, tables, targetTable.resolveDepth, 0, prefix);
  }

  getJointTableColumnSlots(targetTable: Table, tables: Table[], maxDepth: number = 1, recursion: number = 0, prefix?: string): Slot[] {
    const slots = [];
    // Table slots
    this.getTableSlots(targetTable, prefix)
      .forEach(slot => {
        const slotNames = slots.map(s => s.name);
        if (slotNames.indexOf(slot.name) === -1) {
          slots.push(slot);
        }
      });

    // Return if max recursion is reached
    if (recursion === maxDepth) {
      return Array.from(slots.values());
    }

    // FK table slots
    const fkColumns = targetTable.columns.filter(col => {
      return col.resolveDependency && col.tableReference !== null || col.columnReference !== null;
    });
    [].concat(...fkColumns.map(col => {
      const needsPrefix = fkColumns.some(c => c.name !== col.name && c.tableReference === col.tableReference && c.columnReference === col.columnReference)
      const refTable = tables.find(t => t.name === col.tableReference);
      if (needsPrefix) {
        return this.getJointTableColumnSlots(refTable, tables, maxDepth, recursion + 1, `${targetTable.name}__${col.name}`);
      }
      return this.getJointTableColumnSlots(refTable, tables, maxDepth, recursion + 1, prefix);
    })).forEach(slot => {
      const slotNames = slots.map(s => s.name);
      if (slotNames.indexOf(slot.name) === -1) {
        slots.push(slot);
      }
    });

    // Slots of all mapping tables
    const mappingTables = this.getMappingTables(targetTable, tables);
    [].concat(...mappingTables.map(mt => {
      return this.getTableSlots(mt, prefix);
    })).forEach(slot => {
      const slotNames = slots.map(s => s.name);
      if (slotNames.indexOf(slot.name) === -1) {
        slots.push(slot);
      }
    });

    // FK relations of the mapping table other than the source
    const mappingTableFkColumns = [].concat(...mappingTables.map(mt => {
      return mt.columns.filter(col => {
        return col.resolveDependency && col.tableReference !== null && col.tableReference !== targetTable.name;
      });
    }));
    [].concat(...mappingTableFkColumns.map(col => {
      const refTable = tables.find(t => t.name === col.tableReference);
      return this.getJointTableColumnSlots(refTable, tables, maxDepth, recursion + 1, prefix);
    })).forEach(slot => {
      const slotNames = slots.map(s => s.name);
      if (slotNames.indexOf(slot.name) === -1) {
        slots.push(slot);
      }
    });
    return slots;
  }

  getMappingTables(referencedTable: Table, tables: Table[]): Table[] {
    const mappingTables = [];
    referencedTable.columns.forEach(referencedColumn => {
      tables.filter(t => {
        return t.name !== referencedTable.name &&               // Is not the referenced
          t.primaryKey.length > 1 &&                            // Has composite key
          // Column with reference is part of the primary key
          t.columns.filter(c => {
            return c.tableReference === referencedTable.name &&
              c.columnReference === referencedColumn.name &&
              // Column must be part of the primary key
              t.primaryKey.indexOf(c.name) > -1;
          }).length > 0 &&
          // the primary key components have references
          t.columns.filter(c => {
            return t.primaryKey.indexOf(c.name) > -1 && c.tableReference && c.columnReference;
          }).length > 1;
      }).forEach(t => {
        mappingTables.push(t);
      });
    });
    return mappingTables;
  }

  getTableSlots(table: Table, prefix?: string): Slot[] {
    return table.columns.map(col => {
      return {
        name: prefix ? `${prefix}___${table.name}__${col.name}` : `${table.name}__${col.name}`,
        entityNl: table.nlExpressions,
        nl: col.nlExpressions,
        dataType: col.dataType,
        list: false,
        requestable: col.requestable,
        displayable: col.displayable,
        tableReference: col.tableReference,
        columnReference: col.columnReference,
        regex: col.regex,
        lookupTable: col.lookupTable
      } as Slot;
    });
  }
}
