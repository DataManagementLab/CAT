import {Component, EventEmitter, Input, isDevMode, OnInit, Output, ViewChild} from '@angular/core';
import {Database} from '../../../model/database';
import {MatDialog, MatVerticalStepper} from '@angular/material';
import {Task} from 'src/app/model/task';
import {TaskService} from '../../../services/task.service';
import {NotificationService} from '../../../services/notification.service';
import {ViewDialogComponent} from '../../dialogs/view-dialog/view-dialog.component';
import {SimulationService, SimulationState, SimulationStatus} from '../../../services/simulation.service';
import {FormBuilder, FormGroup, Validators} from '@angular/forms';
import {Simulation} from '../../../model/simulation';
import {Procedure} from '../../../model/procedure';
import {Table} from '../../../model/table';

@Component({
  selector: 'app-simulation-step',
  templateUrl: './simulation-step.component.html',
  styleUrls: ['./simulation-step.component.css']
})
export class SimulationStepComponent implements OnInit {

  @Input() database: Database;
  @Input() tables: Table[];
  @Input() procedures: Procedure[];

  @Input() tasks: Task[];
  @Output() finished = new EventEmitter();

  simulationConfiguration: FormGroup;

  simulationStatusTitle: string;
  simulationStatus: SimulationStatus;
  simulationMode: 'indeterminate' | 'determinate' | 'buffer' | 'query' = 'determinate';

  @ViewChild(MatVerticalStepper, {static: false}) stepper: MatVerticalStepper;

  constructor(private notificationService: NotificationService,
              private simulationService: SimulationService,
              private formBuilder: FormBuilder
  ) {
  }

  ngOnInit() {
    this.simulationConfiguration = this.formBuilder.group({
      botName: ['', [Validators.required]],
      selectedTasks: ['', Validators.required],
      numDialogs: ['', [Validators.required, Validators.min(1)]]
    });
    this.simulationStatusTitle = 'No simulation in progress';
    this.simulationStatus = {
      state: SimulationState.Unknown,
      currentDialog: 0,
      totalDialogs: 0,
      message: 'Press run to start a simulation'
    };
  }

  startSimulation() {
    this.simulationService.connect();
    const simulation: Simulation = {
      botName: this.simulationConfiguration.controls.botName.value,
      tasks: this.simulationConfiguration.controls.selectedTasks.value,
      dialogs: this.simulationConfiguration.controls.numDialogs.value
    };

    this.simulationService.startSimulation(simulation, {tables: this.tables, procedures: this.procedures});
    this.simulationService.getSimulationStatus()
      .subscribe(response => {
        this.simulationStatus = response;
        this.updateSimulationStatus();
      });
  }

  stopSimulation() {
    this.simulationService.stopSimulation();
    this.finished.emit(false);
  }

  private updateSimulationStatus() {
    this.simulationMode = 'determinate';
    switch (this.simulationStatus.state) {
      case SimulationState.Started:
        this.simulationStatusTitle = 'Simulation started';
        this.finished.emit(false);
        break;
      case SimulationState.Running:
        this.simulationStatusTitle = 'Simulation running';
        this.finished.emit(false);
        break;
      case SimulationState.Finished:
        this.simulationStatusTitle = 'Simulation finished';
        this.finished.emit(true);
        this.simulationService.disconnect();
        break;
      case SimulationState.Stopped:
        this.simulationStatusTitle = 'Simulation stopped';
        this.finished.emit(false);
        this.simulationService.disconnect();
        break;
      case SimulationState.Dumping:
        this.simulationStatusTitle = 'Processing';
        this.simulationMode = 'indeterminate';
        this.finished.emit(false);
        break;
      case SimulationState.Unknown:
        this.simulationStatusTitle = 'Press run to start a simulation';
        this.finished.emit(false);
        this.simulationService.disconnect();
        break;
      default:
        this.simulationStatusTitle = 'Press run to start a simulation';
        this.finished.emit(false);
        break;
    }
  }

}
