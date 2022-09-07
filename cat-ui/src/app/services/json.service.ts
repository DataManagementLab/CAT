import { Injectable } from '@angular/core';
import {Observable} from 'rxjs';
import {NotificationService} from './notification.service';

@Injectable({
  providedIn: 'root'
})
export class JsonService {

  constructor(private notificationService: NotificationService) { }

  toJson(object: any, replacer = null, space = '\t' ): string {
    return JSON.stringify(object, replacer, space);
  }

  readTextFile(file: File): Observable<string> {
    return new Observable((sub) => {
      const reader = new FileReader();
      reader.onerror = _ => sub.error(reader.error.message);
      reader.onabort = _ => sub.error(reader.error.message);
      reader.onload = _ => {
        sub.next(reader.result.toString());
        sub.complete();
      };
      reader.readAsText(file);
    });
  }

  parseJSON(text: string): Observable<any> {
    return new Observable((sub) => {
      try {
        const obj = JSON.parse(text);
        sub.next(obj);
        sub.complete();
      } catch (e) {
        sub.error(e.message);
      }
    });
  }
}
