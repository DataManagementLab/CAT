import {Component, EventEmitter, Input, OnChanges, Output, SimpleChange, SimpleChanges} from '@angular/core';
import {MatDialog, MatHorizontalStepper} from '@angular/material';
import {DatabaseService} from '../../../services/database.service';
import {Table} from '../../../model/table';
import {Procedure} from '../../../model/procedure';
import {ConfigurationImport, ConfigurationService} from '../../../services/configuration.service';
import {NotificationService} from '../../../services/notification.service';
import {WarningDialogComponent} from '../../dialogs/warning-dialog/warning-dialog.component';

@Component({
  selector: 'app-configuration-step',
  templateUrl: './configuration-step.component.html',
  styleUrls: ['./configuration-step.component.css']
})
export class ConfigurationStepComponent implements OnChanges {
  @Input() stepper: MatHorizontalStepper;
  @Input() canLoadData: boolean;

  tableStep = 0;
  procedureStep = -1;

  @Input() tables: Table[];
  @Output() tablesChange = new EventEmitter();
  @Input() procedures: Procedure[];
  @Output() proceduresChange = new EventEmitter();

  @Output() configChange = new EventEmitter();

  constructor(private databaseService: DatabaseService,
              private notificationService: NotificationService,
              private configurationService: ConfigurationService,
              private dialog: MatDialog) {
  }

  ngOnChanges(changes: SimpleChanges) {
    // Can only load table/procedure data after database connection step is completed
    const canLoadData: SimpleChange = changes.canLoadData;
    if (canLoadData && canLoadData.currentValue === true) {
      this.initTables();
      this.initProcedures();
      this.tableStep = 0;
      this.procedureStep = -1;
      this.configChange.emit(true);
    }
  }

  resetConfiguration() {
    const dialogRef = this.dialog.open(WarningDialogComponent, {
      width: '500px',
      data: {
        title: 'Reset configuration',
        question: 'This will reset all tables and procedures to the factory default and discard any changes. Do you want to continue?'
      }
    });
    dialogRef.afterClosed().subscribe(doReset => {
      if (doReset) {
        this.initTables();
        this.initProcedures();
        this.notificationService.success(`Reset configuration to factory default.`, 3000);
        this.configChange.emit(true);
      } else {
        this.notificationService.error(`Canceled configuration reset`, 3000);
      }
    });
  }

  initTables() {
    this.databaseService.getTables().subscribe(tables => {
      this.tables = tables;
      this.tablesChange.emit(this.tables);
    });
  }

  initProcedures() {
    this.databaseService.getProcedures().subscribe(procedures => {
      this.procedures = procedures;
      this.proceduresChange.emit(this.procedures);
    });
  }

  tableStepChanged(tableStep: number) {
    // Jump to procedures
    if (tableStep > this.tables.length - 1) {
      this.procedureStep = 0;
    }
  }

  importConfigFile(files: FileList) {
    if (!files || files.length === 0) {
      return;
    }
    const configFile = files[0];
    this.configurationService.importConfiguration(configFile, this.tables, this.procedures)
      .subscribe(configurationImport => {
        if (configurationImport.warnings.length > 0) {
          const dialogRef = this.dialog.open(WarningDialogComponent, {
            width: '500px',
            data: {
              title: 'Configuration import finished with warnings',
              contents: configurationImport.warnings,
              question: 'Do you still want to import the new configuration?'
            }
          });
          dialogRef.afterClosed().subscribe(doImport => {
            if (doImport) {
              this.doImportConfiguration(configurationImport, configFile.name);
            } else {
              this.notificationService.error(`Canceled configuration import due to warnings`, 3000);
            }
          });
        } else {
          this.doImportConfiguration(configurationImport, configFile.name);
        }
      }, error => {
        this.notificationService.error(`Could not import configuration: ${error}`);
      });
  }

  doImportConfiguration(configImport: ConfigurationImport, filename: string) {
    this.tables = configImport.configuration.tables;
    this.procedures = configImport.configuration.procedures;
    this.tablesChange.emit(this.tables);
    this.proceduresChange.emit(this.procedures);
    this.notificationService.success(`Imported configuration from file ${filename}`, 3000);
    this.configChange.emit(true);
  }

  getJSONConfig() {
    return this.configurationService.exportConfiguration(this.tables, this.procedures);
  }

}
