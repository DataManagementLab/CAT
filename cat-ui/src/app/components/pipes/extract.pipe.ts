import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'extract'
})
export class ExtractPipe implements PipeTransform {

  transform(value: any[], key: string): any[] {
    return value.map((v: any) => v[key]);
  }

}
