import {Pipe, PipeTransform} from '@angular/core';
import * as moment from 'moment';
import {Moment} from 'moment';

@Pipe({
  name: 'moment'
})
export class MomentPipe implements PipeTransform {

  transform(value: number, truncDate?: boolean): Moment {
    if (truncDate) {
      const date = moment(value * 1000);
      date.millisecond(0);
      date.second(0);
      date.minute(0);
      date.hour(0);
      return date;
    }
    return moment(value * 1000);
  }

}
