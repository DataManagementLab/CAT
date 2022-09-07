import {NaturalLanguagePair} from './nl-pair';
import {Slot} from './slot';
import {Subtask} from './subtask';

export interface Task {
  name: string;
  operation: string;
  nl: NaturalLanguagePair[];
  slots: Slot[];
  returnNl: string[];
  returnSlots: Slot[];
  subtasks: Subtask[];
}
