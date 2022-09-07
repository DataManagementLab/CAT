import {Injectable} from '@angular/core';
import {Observable} from 'rxjs';
import {Simulation} from '../model/simulation';
import {Configuration} from '../model/configuration';
import {SocketIOService} from './socket-io.service';


export enum SimulationState {
  Started = 'started',
  Running = 'running',
  Stopped = 'stopped',
  Finished = 'finished',
  Dumping = 'dumping',
  Unknown = 'unknown'
}

export interface SimulationStatus {
  state: SimulationState;
  currentDialog: number;
  totalDialogs: number;
  message: string;
}

@Injectable({
  providedIn: 'root'
})
export class SimulationService {

  private namespace = 'simulation';
  private socket: SocketIOClient.Socket;
  private simulation: Simulation;

  constructor(private socketService: SocketIOService) {
  }

  connect() {
    this.socket = this.socketService.connect(this.namespace);
  }

  disconnect() {
    this.socketService.disconnect(this.socket);
  }

  startSimulation(simulation: Simulation, config: Configuration) {
    this.simulation = simulation;
    this.socket.emit('start_simulation', simulation, config);
  }

  stopSimulation() {
    this.socket.emit('stop_simulation');
  }

  getSimulationStatus(): Observable<SimulationStatus> {
    return new Observable<SimulationStatus>(sub => {
      this.socket.on('simulation_started', response => {
        const state = {
          state: SimulationState.Started,
          currentDialog: 0,
          totalDialogs: this.simulation.dialogs,
          message: response.message
        };
        sub.next(state);
      });
      this.socket.on('simulation_progress', response => {
        const state = {
          state: SimulationState.Running,
          currentDialog: response.dialog,
          totalDialogs: response.total_dialogs,
          message: response.message
        };
        sub.next(state);
      });
      this.socket.on('simulation_dumping', response => {
        const state = {
          state: SimulationState.Dumping,
          currentDialog: response.dialog,
          totalDialogs: response.total_dialogs,
          message: response.message
        };
        sub.next(state);
      });
      this.socket.on('simulation_finished', response => {
        const state = {
          state: SimulationState.Finished,
          currentDialog: response.dialog,
          totalDialogs: response.total_dialogs,
          message: response.message
        };
        sub.next(state);
        sub.complete();
      });
      this.socket.on('simulation_stopped', response => {
        const state = {
          state: SimulationState.Stopped,
          currentDialog: response.dialog,
          totalDialogs: response.total_dialogs,
          message: response.message
        };
        sub.next(state);
        sub.complete();
      });
    });
  }
}
