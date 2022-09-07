import {NaturalLanguagePair} from './nl-pair';
import {ReturnRecord} from './return-record';
import {EntitySample} from './entity-sample';
import {Argument} from './argument';

export interface Procedure {
  name: string;
  nlPairs: NaturalLanguagePair[];
  nlSample: EntitySample;
  operation: string;
  parameters: Argument[];
  returns: ReturnRecord;
  body: string;
}
