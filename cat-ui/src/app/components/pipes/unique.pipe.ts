import {Pipe, PipeTransform} from '@angular/core';

@Pipe({
  name: 'unique'
})
export class UniquePipe implements PipeTransform {

  private static unique(value: any, index: number, list: any[]) {
    return list.indexOf(value) === index;
  }

  transform(value: any[]): any[] {
    return value.filter(UniquePipe.unique);
  }

}
