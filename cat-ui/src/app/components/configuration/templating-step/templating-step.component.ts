import {
  Component,
  EventEmitter,
  Input,
  isDevMode,
  OnChanges,
  OnInit,
  Output,
  SimpleChange,
  SimpleChanges,
  ViewChild
} from '@angular/core';
import {Table} from '../../../model/table';
import {Procedure} from '../../../model/procedure';
import {Task} from '../../../model/task';
import {TaskService} from '../../../services/task.service';
import {ViewDialogComponent} from '../../dialogs/view-dialog/view-dialog.component';
import {MatDialog, MatVerticalStepper} from '@angular/material';
import {NotificationService} from '../../../services/notification.service';
import {TemplateImport, TemplateService} from '../../../services/template.service';
import {WarningDialogComponent} from '../../dialogs/warning-dialog/warning-dialog.component';
import {Templateable} from '../../../model/templateable';
import {DataFile} from '../../../model/data-file';
import {ConfigurationService} from '../../../services/configuration.service';

@Component({
  selector: 'app-templating-step',
  templateUrl: './templating-step.component.html',
  styleUrls: ['./templating-step.component.css']
})
export class TemplatingStepComponent implements OnInit, OnChanges {

  @ViewChild(MatVerticalStepper, {static: true}) stepper: MatVerticalStepper;

  @Input() tables: Table[];
  @Input() procedures: Procedure[];

  @Input() tasks: Task[];
  @Output() tasksChange = new EventEmitter();
  @Output() finished = new EventEmitter();
  @Input() tasksComplete = false;

  @Input() configChanged;

  actionStep = -1;
  @Input() responses: Templateable[];

  intentStep = -1;
  @Input() intents: Templateable[];

  constructor(private taskService: TaskService,
              private templateService: TemplateService,
              private configurationService: ConfigurationService,
              private notificationService: NotificationService,
              private dialog: MatDialog) {
  }

  ngOnInit() {
    this.tasksComplete = false;
    this.responses = [];
    this.intents = [];
  }

  ngOnChanges(changes: SimpleChanges): void {
    const configChanged = changes.configChanged;
    if (configChanged && configChanged.currentValue) {
      this.ngOnInit();
      this.stepper.reset();
    }
  }

  generateTasks() {
    this.tasksComplete = false;
    this.taskService.generateTasks({tables: this.tables, procedures: this.procedures})
      .subscribe(tasks => {
        this.tasks = tasks;
        this.tasksChange.emit(this.tasks);
        this.finished.emit(true);
        this.tasksComplete = true;
        this.notificationService.success(`Generated ${this.tasks.length} tasks.`);
        this.onTasksChange(true);
      }, err => {
        this.tasks = [];
        this.tasksChange.emit(this.tasks);
        this.finished.emit(false);
        this.notificationService.error(`Could not generate tasks: ${err}`);
        this.onTasksChange(false);
      });
  }

  openTasks() {
    this.dialog.open(ViewDialogComponent, {
      width: '800px',
      data: {
        title: 'Task configuration',
        data: this.getJSONTasks()
      }
    });
  }

  getJSONTasks() {
    return this.taskService.exportTasks(this.tasks);
  }

  getJSONTemplates() {
    return this.templateService.exportTemplates(this.responses, this.intents);
  }

  getJSONConfig() {
    return this.configurationService.exportConfiguration(this.tables, this.procedures);
  }

  importTemplatesFile(files: FileList) {
    if (!files || files.length === 0) {
      return;
    }
    const configFile = files[0];
    this.templateService.importTemplates(configFile, this.responses, this.intents)
      .subscribe(templateImport => {
        if (templateImport.warnings.length > 0) {
          const dialogRef = this.dialog.open(WarningDialogComponent, {
            width: '500px',
            data: {
              title: 'Template import finished with warnings',
              contents: templateImport.warnings,
              question: 'Do you still want to import the new templates?'
            }
          });
          dialogRef.afterClosed().subscribe(doImport => {
            if (doImport) {
              this.doImportTemplates(templateImport, configFile.name);
            } else {
              this.notificationService.error(`Canceled template import due to warnings`, 3000);
            }
          });
        } else {
          this.doImportTemplates(templateImport, configFile.name);
        }
      }, error => {
        this.notificationService.error(`Could not import templates: ${error}`);
      });
  }

  doImportTemplates(templateImport: TemplateImport, filename: string) {
    this.responses = templateImport.templates.responses;
    this.intents = templateImport.templates.intents;
    this.notificationService.success(`Imported templates from file ${filename}`, 3000);
  }

  onTasksChange(generateTemplates: boolean) {
    if (generateTemplates) {
      this.responses = this.templateService.generateResponseTemplates(this.tasks, this.tables);
      this.intents = this.templateService.generateIntents(this.tasks);
    } else {
      this.responses = [];
      this.intents = [];
    }
  }

  getConfigs(): DataFile[] {
    return [{
      filename: 'tasks',
      extension: 'json',
      data: this.getJSONTasks()
    }, {
      filename: 'templates',
      extension: 'json',
      data: this.getJSONTemplates()
    }, {
      filename: 'config',
      extension: 'json',
      data: this.getJSONConfig(),
    }] as DataFile[];
  }

}
