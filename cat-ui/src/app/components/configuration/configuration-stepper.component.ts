import {Component, Input, isDevMode, OnInit, ViewChild} from '@angular/core';

import {MatHorizontalStepper} from '@angular/material';
import {Procedure} from '../../model/procedure';
import {Table} from '../../model/table';
import {Database} from '../../model/database';
import {environment} from '../../../environments/environment';
import {Task} from 'src/app/model/task';

@Component({
  selector: 'app-configuration-stepper',
  templateUrl: './configuration-stepper.component.html',
  styleUrls: ['./configuration-stepper.component.css'],
})
export class ConfigurationStepperComponent implements OnInit {

  @ViewChild(MatHorizontalStepper, {static: true}) stepper: MatHorizontalStepper;

  database: Database = new Database();
  @Input() tables: Table[];
  @Input() procedures: Procedure[];
  @Input() tasks: Task[];

  databaseStepCompleted = false;
  templatingStepCompleted = false;
  // simulationStepCompleted = false;

  configChanged = false;

  constructor() {
  }

  ngOnInit() {
    if (isDevMode()) {
      this.database.hostname = environment.dbHost;
      this.database.port = environment.dbPort;
      this.database.username = environment.dbUsername;
      this.database.password = environment.dbPassword;
      this.database.databaseName = environment.dbName;
      this.database.schemaName = environment.dbSchema;
    }
  }

  onDatabaseConnected(isConnected) {
    this.databaseStepCompleted = isConnected;
    // Step forward automatically
    if (isDevMode() && isConnected) {
      // Apparently async propagation of component "completed" to "step" completed
      // Hence cannot step forward before step is completed
      setTimeout(() => {
        this.stepper.next();
      }, 500);
    }
  }

  onConfigurationChanged(hasChanged) {
    this.configChanged = hasChanged;
    setTimeout(() => {
      this.configChanged = false;
    }, 1000);
  }

  onTasksFinished(isFinished) {
    this.templatingStepCompleted = isFinished;
  }

  /*onSimulationFinished(isFinished) {
    this.simulationStepCompleted = isFinished;
  }*/
}
