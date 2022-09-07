import {Pipe, PipeTransform} from '@angular/core';

@Pipe({
  name: 'filter'
})
export class FilterPipe implements PipeTransform {

  transform(value: any[], key: string, equals: any): any[] {
    return value.filter((v) => v[key] === equals);
  }

}
