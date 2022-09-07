import {Column} from './column';

export interface Table {
  name: string;
  primaryKey: string[];
  nlExpressions: string[];
  representation: string;
  columns: Column[];
  resolveDepth: number;
}
