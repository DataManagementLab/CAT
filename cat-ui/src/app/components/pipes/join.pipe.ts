import { Pipe, PipeTransform } from '@angular/core';
import {Argument} from '../../model/argument';

@Pipe({
  name: 'join'
})
export class JoinPipe implements PipeTransform {

  transform(values: any[], mapAttribute?: string, joinSeparator: string = ', '): any {
    if (mapAttribute) {
      return values.map(v => v[mapAttribute]).join(joinSeparator);
    }
    return values.join(joinSeparator);
  }

}
