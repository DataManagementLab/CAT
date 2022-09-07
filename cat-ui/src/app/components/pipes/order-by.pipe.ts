import {Pipe, PipeTransform} from '@angular/core';

@Pipe({
  name: 'orderBy'
})
export class OrderByPipe implements PipeTransform {

  transform(value: any[], key?: string, reverse?: boolean): any[] {
    if (!value) {
      return value;
    }

    let sorted = value;
    if (!key) {
      sorted = value.sort();
    } else {
      sorted = value.sort((a, b) => {
        if (a[key] >= b[key]) {
          return 1;
        }
        return -1;
      });
    }
    if (reverse) {
      return sorted.reverse();
    }
    return sorted;
  }

}
