import {Argument} from './argument';

export interface ReturnRecord {
  name: string;
  nlExpressions: string[];
  values: Argument[];
}
