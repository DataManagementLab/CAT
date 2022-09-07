import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'nl'
})
export class NlPipe implements PipeTransform {

  transform(value: string, divider?: string): any {
    const regExp = new RegExp(divider ? divider : '_', 'g');
    return value.replace(regExp, ' ');
  }

}
