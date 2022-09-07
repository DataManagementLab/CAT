import {LookupEntry} from './lookup-entry';

export interface Column {
  name: string;
  nlExpressions: string[];
  dataType: string;
  tableReference: string;
  columnReference: string;
  nullable: boolean;
  requestable: boolean;
  displayable: boolean;
  resolveDependency: boolean;
  regex: string;
  lookupTable: LookupEntry[];
}
