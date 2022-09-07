import { Task } from './task';

export interface Simulation {
  botName: string;
  tasks: Task[];
  dialogs: number;
}
