import {Slot} from './slot';

export interface Subtask {
  targetSlot: string;
  targetDataType: string;
  targetList: string;
  targetTable: string;
  targetColumn: string;
  targetTableRepresentation: string;
  operation: string;
  slots: Slot[];
}
