import {Injectable} from '@angular/core';
import {HttpClient, HttpHeaders} from '@angular/common/http';
import {Observable, of} from 'rxjs';
import {environment} from '../../environments/environment';
import {Bot} from '../model/bot';
import {catchError} from 'rxjs/operators';
import {NotificationService} from './notification.service';
import {BotConfig} from '../model/bot-config';
import {BotDomain} from '../model/bot-domain';

@Injectable({
  providedIn: 'root'
})
export class BotService {

  private botsUrl = `${environment.apiUrl}/rasa`;
  httpOptions = {
    headers: new HttpHeaders({
      'Content-Type': 'application/json'
    })
  };

  constructor(private http: HttpClient, private notificationService: NotificationService) {
  }

  getBots(): Observable<Bot[]> {
    const url = `${this.botsUrl}/bots`;
    return this.http.get<Bot[]>(url, this.httpOptions).pipe(
      catchError(this.handleError<Bot[]>('fetching bots', []))
    );
  }

  getStories(botPath: string): Observable<string[]> {
    const url = `${this.botsUrl}/bots/${botPath}/stories`;
    return this.http.get<string[]>(url, this.httpOptions).pipe(
      catchError(this.handleError<string[]>('fetching stories', []))
    );
  }

  getBotDomain(botPath: string): Observable<BotDomain> {
    const url = `${this.botsUrl}/bots/${botPath}/domain`;
    return this.http.get<BotDomain>(url, this.httpOptions).pipe(
      catchError(this.handleError<BotDomain>('fetching domain', {
        actions: [],
        entities: [],
        intents: [],
        slots: [],
        templates: []
      }))
    );
  }

  getBotConfig(botPath: string): Observable<BotConfig> {
    const url = `${this.botsUrl}/bots/${botPath}/config`;
    return this.http.get<BotConfig>(url, this.httpOptions).pipe(
      catchError(this.handleError<BotConfig>('fetching config', {
        language: 'en',
        pipeline: [{
          name: 'supervised_embeddings'
        }],
        policies: []
      }))
    );
  }

  private handleError<T>(operation = 'operation', result?: T) {
    return (response: any): Observable<T> => {
      this.notificationService.error(`Error ${operation}: ${response.error.message}`);
      return of(result as T);
    };
  }

}
