import {LookupEntry} from './lookup-entry';

export interface Slot {
  name: string;
  entityNl: string[];
  nl: string[];
  dataType: string;
  list: boolean;
  requestable: boolean;
  displayable: boolean;
  tableReference: string;
  columnReference: string;
  regex: string;
  lookupTable: LookupEntry[];
}
