import {Table} from './table';
import {Procedure} from './procedure';

export interface Configuration {
  tables: Table[];
  procedures: Procedure[];
}
