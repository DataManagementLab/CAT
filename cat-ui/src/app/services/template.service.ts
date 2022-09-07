import {Injectable} from '@angular/core';
import {Task} from '../model/task';
import {
  Templateable,
  BEGIN_TRANSACTION_TEMPLATE,
  DEFAULT_INTENTS,
  ASK_CHOICE_TEMPLATE,
  ASK_SELECT_TEMPLATE,
  DEFAULT_RESPONSES,
  PROPOSE_CHOICE_TEMPLATE,
  PROPOSE_SELECTION_TEMPLATE,
  PROPOSE_TASK_TEMPLATE,
  PROPOSE_TRANSACTION_TEMPLATE,
  INFORM_CHOICE_TEMPLATE,
  INFORM_SELECTION_TEMPLATE,
  ASK_PARAMETER_TEMPLATE,
  INFORM_TRUE_BOOL_CHOICE_TEMPLATE,
  INFORM_FALSE_BOOL_CHOICE_TEMPLATE,
  SUCCESS_TRANSACTION_TEMPLATE, FAILED_TRANSACTION_TEMPLATE
} from '../model/templateable';
import {Subtask} from '../model/subtask';
import {Observable} from 'rxjs';
import {JsonService} from './json.service';
import {Slot} from '../model/slot';
import {Table} from '../model/table';
import {TaskService} from './task.service';

export interface TemplateImport {
  templates: {
    responses: Templateable[];
    intents: Templateable[];
  };
  warnings: string[];
}

@Injectable({
  providedIn: 'root'
})
export class TemplateService {

  constructor(private jsonService: JsonService, private taskService: TaskService) {
  }

  exportTemplates(exportActions: Templateable[], exportIntents: Templateable[]) {
    return this.jsonService.toJson({
      responses: exportActions,
      intents: exportIntents
    });
  }

  importTemplates(file: File, matchActions: Templateable[], matchIntents): Observable<TemplateImport> {
    return new Observable<TemplateImport>((sub) => {
      this.jsonService.readTextFile(file)
        .subscribe(text => {
          this.jsonService.parseJSON(text)
            .subscribe(json => {
              const templateImport = {
                templates: json,
                warnings: []
              } as TemplateImport;

              matchActions.forEach(responseTemplate => {
                if (templateImport.templates.responses.map(a => a.id).indexOf(responseTemplate.id) === -1) {
                  templateImport.templates.responses.push(responseTemplate);
                  templateImport.warnings.push(`Added default template for missing response ${responseTemplate.name}`);
                }
              });
              matchIntents.forEach(intentTemplate => {
                if (templateImport.templates.intents.map(i => i.id).indexOf(intentTemplate.id) === -1) {
                  templateImport.templates.intents.push(intentTemplate);
                  templateImport.warnings.push(`Added default template for missing intent ${intentTemplate.name}`);
                }
              });

              templateImport.templates.responses.forEach(importTemplate => {
                if (matchActions.map(a => a.id).indexOf(importTemplate.id) === -1) {
                  const index = templateImport.templates.responses.map(a => a.id).indexOf(importTemplate.id);
                  templateImport.warnings.push(`Unknown template for response with key ${importTemplate.id}. Ignoring template.`);
                  templateImport.templates.responses.splice(index, 1);
                }
              });

              templateImport.templates.intents.forEach(importTemplate => {
                if (matchIntents.map(a => a.id).indexOf(importTemplate.id) === -1) {
                  const index = templateImport.templates.intents.map(a => a.id).indexOf(importTemplate.id);
                  templateImport.warnings.push(`Unknown template for intent with key ${importTemplate.id}. Ignoring template.`);
                  templateImport.templates.intents.splice(index, 1);
                }
              });

              sub.next(templateImport);
              sub.complete();
            }, error => {
              sub.error(`Error parsing JSON: ${error}`);
            });
        }, error => {
          sub.error(`Error reading file ${file.name}: ${error}`);
        });
    });
  }

  generateResponseTemplates(tasks: Task[], tables: Table[]): Templateable[] {
    const responses = [...DEFAULT_RESPONSES];
    tasks.forEach(task => {
      const proposeTaskAction = this.generateTaskProposalTemplates(task);
      responses.push(proposeTaskAction);
      const askParameterActions = this.generateAskParameterTemplates(task);
      askParameterActions.forEach(askAction => {
        if (responses.map(a => a.id).indexOf(askAction.id) === -1) {
          responses.push(askAction);
        }
      });

      task.subtasks.forEach(subtask => {
        let response: Templateable;
        let askResponses: Templateable[];
        if (subtask.operation === 'select') {
          response = this.generateSelectionProposalTemplates(subtask);
          askResponses = this.generateAskSelectSlotTemplates(subtask);
        } else if (subtask.operation === 'choose') {
          response = this.generateChoiceProposalTemplates(subtask);
          askResponses = this.generateAskChoiceSlotTemplates(subtask);
        }
        if (responses.map(a => a.id).indexOf(response.id) === -1) {
          responses.push(response);
        }
        askResponses.forEach(askAction => {
          if (responses.map(a => a.id).indexOf(askAction.id) === -1) {
            responses.push(askAction);
          }
        });
        const successResponses = this.generateSuccessTransactionTemplates(task, tables);
        successResponses.forEach(successAction => {
          if (responses.map(a => a.id).indexOf(successAction.id) === -1) {
            responses.push(successAction);
          }
        });
        const failureResponses = this.generateFailedTransactionTemplates(task);
        failureResponses.forEach(failureResponse => {
          if (responses.map(a => a.id).indexOf(failureResponse.id) === -1) {
            responses.push(failureResponse);
          }
        });
      });
      const proposeTransactionResponse = this.generateTransactionProposalTemplates(task);
      responses.push(proposeTransactionResponse);
    });
    return responses;
  }

  generateTaskProposalTemplates(task: Task): Templateable {
    const proposeTask = {...PROPOSE_TASK_TEMPLATE};
    proposeTask.id += `${task.name}`;
    proposeTask.name = `Propose Task ${this.getDisplayName(task.name)}`;
    proposeTask.placeholders = [...PROPOSE_TASK_TEMPLATE.placeholders];
    proposeTask.templates = [...PROPOSE_TASK_TEMPLATE.templates];
    return proposeTask;
  }

  generateSelectionProposalTemplates(task: Subtask): Templateable {
    const proposeSelection = {...PROPOSE_SELECTION_TEMPLATE};
    proposeSelection.id += `${task.targetTable}`;
    proposeSelection.name = `Propose ${this.getDisplayName(task.targetTable)} Selection`;
    // All displayable slots, the respective columns NL phrasing and the tables NL phrasing
    proposeSelection.placeholders = [].concat(...task.slots.filter(s => s.displayable).map(s => [s.name, `${s.name}_nl`]));
    proposeSelection.placeholders.push('table_nl');
    proposeSelection.templates = proposeSelection.templates.map(t => {
      let template = t + '';
      task.slots.filter(s => s.displayable).map(s => s.name).forEach(placeholder => {
        template += `\n- {${placeholder}_nl}: {${placeholder}}`;
      });
      return template;
    });
    return proposeSelection;
  }

  generateChoiceProposalTemplates(task: Subtask): Templateable {
    const proposeChoice = {...PROPOSE_CHOICE_TEMPLATE};
    proposeChoice.id += `_${task.targetSlot}`;
    const targetTaskAndSlot = task.targetSlot.split('__');
    proposeChoice.name += `${this.getDisplayName(targetTaskAndSlot[1])} (${this.getDisplayName(targetTaskAndSlot[0])})`;
    proposeChoice.templates = [...PROPOSE_CHOICE_TEMPLATE.templates];
    proposeChoice.placeholders = [...PROPOSE_CHOICE_TEMPLATE.placeholders];
    return proposeChoice;
  }

  generateTransactionProposalTemplates(task: Task): Templateable {
    const proposeTransaction = {...PROPOSE_TRANSACTION_TEMPLATE};
    proposeTransaction.id += `_${task.name}`;
    proposeTransaction.name += `${this.getDisplayName(task.name)}`;
    proposeTransaction.templates = proposeTransaction.templates.map(t => {
      let template = t + '';
      task.slots.map(s => s.name).forEach(placeholder => {
        template += `\n- {${placeholder}_nl}: {${placeholder}}`;
      });
      return template;
    });
    proposeTransaction.placeholders = [].concat(
      proposeTransaction.placeholders,
      task.slots.map(s => s.name),
      // Resolve transaction slot table references and add displayable slots
      [].concat(
        ...task.subtasks
          .filter(st => st.targetTable)
          .map(st => {
            return [].concat(...st.slots
              .filter(s => s.displayable)
              .map(s => [s.name, `${s.name}_nl`])
            );
          })
      )
    );
    return proposeTransaction;
  }

  generateAskParameterTemplates(task: Task): Templateable[] {
    return task.slots.map(slot => {
      const askParameterTemplate = {...ASK_PARAMETER_TEMPLATE};
      askParameterTemplate.id += `${slot.name}`;
      askParameterTemplate.name += `${this.getDisplayName(slot.name)}`;
      askParameterTemplate.placeholders = [...ASK_PARAMETER_TEMPLATE.placeholders];
      askParameterTemplate.templates = [...ASK_PARAMETER_TEMPLATE.templates];
      return askParameterTemplate;
    });
  }

  generateAskSelectSlotTemplates(subtask: Subtask): Templateable[] {
    return subtask.slots.filter(s => s.requestable)
      .map(slot => {
        const askSlotTemplate = {...ASK_SELECT_TEMPLATE};
        askSlotTemplate.id += `${slot.name}`;
        askSlotTemplate.name += `${this.getDisplayName(slot.name)}`;
        askSlotTemplate.placeholders = [...ASK_SELECT_TEMPLATE.placeholders];
        askSlotTemplate.templates = [...ASK_SELECT_TEMPLATE.templates];
        return askSlotTemplate;
      });
  }

  generateAskChoiceSlotTemplates(subtask: Subtask): Templateable[] {
    const askChoiceSlot = {...ASK_CHOICE_TEMPLATE};
    askChoiceSlot.id += `${subtask.targetSlot}`;
    askChoiceSlot.name += `${this.getDisplayName(subtask.targetSlot)}`;
    askChoiceSlot.placeholders = [...ASK_CHOICE_TEMPLATE.placeholders];
    askChoiceSlot.templates = [...ASK_CHOICE_TEMPLATE.templates];
    return [askChoiceSlot];
  }

  generateSuccessTransactionTemplates(task: Task, tables: Table[]): Templateable[] {
    const success = {...SUCCESS_TRANSACTION_TEMPLATE};
    success.id += task.name;
    success.name += `${this.getDisplayName(task.name)}`;
    success.placeholders = [...SUCCESS_TRANSACTION_TEMPLATE.placeholders].concat(task.returnSlots.map(s => s.name));
    // If a result column is a table reference we want to resolve all joint column to display the human readble result
    task.returnSlots.filter(s => s.tableReference)
      .forEach(slot => {
          const refTable = tables.find(t => t.name === slot.tableReference);
          const displayableSlots = this.taskService.getJointTableColumnSlots(refTable, tables);
          displayableSlots.forEach(s => {
            if (s.displayable && success.placeholders.indexOf(s.name) === -1) {
              success.placeholders.push(s.name);
            }
          });
        }
      );
    success.templates = [...SUCCESS_TRANSACTION_TEMPLATE.templates];
    return [success];
  }


  generateFailedTransactionTemplates(task: Task): Templateable[] {
    const failure = {...FAILED_TRANSACTION_TEMPLATE};
    failure.id += task.name;
    failure.name += `${this.getDisplayName(task.name)}`;
    failure.placeholders = [...FAILED_TRANSACTION_TEMPLATE.placeholders];
    failure.templates = [...FAILED_TRANSACTION_TEMPLATE.templates];
    return [failure];
  }

  generateIntents(tasks: Task[]): Templateable[] {
    const intents = [...DEFAULT_INTENTS];
    tasks.forEach(task => {
      const taskIntentTemplate = this.generateBeginTaskIntentTemplate(task);
      intents.push(taskIntentTemplate);
      // One intent "inform form" per selection
      const informFormTemplates = this.generateInformFormTemplates(task);
      informFormTemplates.forEach(informFormTemplate => {
        if (intents.map(i => i.id).indexOf(informFormTemplate.id) === -1) {
          intents.push(informFormTemplate);
        }
      });
      const informChoiceTemplates = this.generateInformChoiceTemplates(task);
      informChoiceTemplates.forEach(t => {
        intents.push(t);
      });
    });
    return intents;
  }

  generateBeginTaskIntentTemplate(task: Task): Templateable {
    const beginTaskIntent = {...BEGIN_TRANSACTION_TEMPLATE};
    beginTaskIntent.id += task.name;
    beginTaskIntent.name += this.getDisplayName(task.name);
    beginTaskIntent.placeholders = [].concat(
      ...beginTaskIntent.placeholders,
      ...task.subtasks
        // .filter(st => st.targetTable)
        .map(st => {
          return [].concat(...st.slots
            .filter(s => s.displayable)
            .map(s => [s.name, `${s.name}_nl`])
          );
        })
    );
    beginTaskIntent.templates = [].concat(...beginTaskIntent.templates);
    return beginTaskIntent;
  }

  generateInformFormTemplates(task: Task): Templateable[] {
    const templateables = [];
    const selectTasks = task.subtasks.filter(st => st.operation === 'select');
    selectTasks.forEach(subtask => {
      // handle non-boolean slots
      const inform = {...INFORM_SELECTION_TEMPLATE};
      inform.id += `${subtask.targetTable}`;
      inform.name += this.getDisplayName(subtask.targetTable);
      inform.placeholders = [...INFORM_SELECTION_TEMPLATE.placeholders];
      const defaultTemplates = [...inform.templates];
      const templates = [];
      subtask.slots.filter(s => s.requestable && s.dataType !== 'bool').forEach(s => {
        const slotTable = s.name.split('__')[0];
        const slotTablePlaceholder = `${slotTable}_nl`;
        if (inform.placeholders.indexOf(slotTablePlaceholder) === -1) {
          inform.placeholders.push(slotTablePlaceholder);
        }
        if (inform.placeholders.indexOf(s.name) === -1) {
          inform.placeholders.push(s.name);
          inform.placeholders.push(`${s.name}_nl`);
        }
        defaultTemplates.forEach(t => {
          const template = t.replace('{table_nl}', `{${slotTablePlaceholder}}`)
            .replace('{column_nl}', `{${s.name}_nl}`)
            .replace('{value}', `{${s.name}}`);
          templates.push(template);
        });
      });
      inform.templates = templates;
      templateables.push(inform);
      // handle boolean slots
      subtask.slots.filter(s => s.requestable && s.dataType === 'bool').forEach(s => {
        const informPos = {...INFORM_TRUE_BOOL_CHOICE_TEMPLATE};
        informPos.id += (s.name + '_true');
        informPos.name += ` ${this.getDisplayName(s.name)}`;
        informPos.placeholders = [...INFORM_TRUE_BOOL_CHOICE_TEMPLATE.placeholders];
        informPos.templates = [...INFORM_TRUE_BOOL_CHOICE_TEMPLATE.templates];
        templateables.push(informPos);

        const informNeg = {...INFORM_FALSE_BOOL_CHOICE_TEMPLATE};
        informNeg.id += (s.name + '_false');
        informNeg.name += ` ${this.getDisplayName(s.name)}`;
        informNeg.placeholders = [...INFORM_FALSE_BOOL_CHOICE_TEMPLATE.placeholders];
        informNeg.templates = [...INFORM_FALSE_BOOL_CHOICE_TEMPLATE.templates];
        templateables.push(informNeg);
      });
    });
    return templateables;
  }

  generateInformChoiceTemplates(task: Task): Templateable[] {
    const choiceSlots = [].concat(...task.subtasks
      .filter(st => st.operation === 'choose')
      .map(st => st.slots)
    ) as Slot[];
    const choiceTemplates = [];
    choiceSlots.forEach(s => {
      if (s.dataType === 'bool') {
        const informPos = {...INFORM_TRUE_BOOL_CHOICE_TEMPLATE};
        informPos.id += (s.name + '_true');
        informPos.name += this.getDisplayName(s.name.replace('choose ', ''));
        informPos.placeholders = [...INFORM_TRUE_BOOL_CHOICE_TEMPLATE.placeholders];
        informPos.templates = [...INFORM_TRUE_BOOL_CHOICE_TEMPLATE.templates];
        choiceTemplates.push(informPos);

        const informNeg = {...INFORM_FALSE_BOOL_CHOICE_TEMPLATE};
        informNeg.id += (s.name + '_false');
        informNeg.name += this.getDisplayName(s.name.replace('choose ', ''));
        informNeg.placeholders = [...INFORM_FALSE_BOOL_CHOICE_TEMPLATE.placeholders];
        informNeg.templates = [...INFORM_FALSE_BOOL_CHOICE_TEMPLATE.templates];
        choiceTemplates.push(informNeg);
      } else {
        const inform = {...INFORM_CHOICE_TEMPLATE};
        inform.id += s.name;
        inform.name += this.getDisplayName(s.name.replace('choose ', ''));
        inform.placeholders = [...INFORM_CHOICE_TEMPLATE.placeholders];
        inform.templates = [...INFORM_CHOICE_TEMPLATE.templates];
        choiceTemplates.push(inform);
      }
    });
    return choiceTemplates;
  }

  getDisplayName(id: string) {
    return id.split('_')
      .filter(part => part.length > 0)
      .map(part => part[0].toUpperCase() + part.slice(1))
      .join(' ');
  }

  /*private getJointTableColumnSlots(targetTableName: string, tables: Table[], maxDepth: number = 1, recursion: number = 0): Slot[] {
    const slots = [];
    const targetTable = tables.find(t => t.name === targetTableName);
    // Table slots
    this.getTableSlots(targetTable)
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
      return this.getJointTableColumnSlots(col.tableReference, tables, maxDepth, recursion + 1);
    })).forEach(slot => {
      const slotNames = slots.map(s => s.name);
      if (slotNames.indexOf(slot.name) === -1) {
        slots.push(slot);
      }
    });

    // Slots of all mapping tables
    const mappingTables = this.getMappingTables(targetTable, tables);
    [].concat(...mappingTables.map(mt => {
      return this.getTableSlots(mt);
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
      return this.getJointTableColumnSlots(col.tableReference, tables, maxDepth, recursion + 1);
    })).forEach(slot => {
      const slotNames = slots.map(s => s.name);
      if (slotNames.indexOf(slot.name) === -1) {
        slots.push(slot);
      }
    });
    return slots;
  }

  private getMappingTables(referencedTable: Table, tables: Table[]): Table[] {
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

  private getTableSlots(table: Table): Slot[] {
    return table.columns.map(col => {
      return {
        name: `${table.name}__${col.name}`,
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
  }*/
}
