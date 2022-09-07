import {Injectable} from '@angular/core';
import {environment} from '../../environments/environment';
import {HttpClient, HttpHeaders} from '@angular/common/http';
import {NotificationService} from './notification.service';
import {catchError} from 'rxjs/operators';
import {Observable, of} from 'rxjs';
import {Synonym} from '../model/synonym';

@Injectable({providedIn: 'root'})
export class NaturalLanguageService {

  private nlUrl = `${environment.apiUrl}/nl`;

  httpOptions = {
    headers: new HttpHeaders({
      'Content-Type': 'application/json'
    })
  };

  constructor(private http: HttpClient, private notificationService: NotificationService) {
  }

  getSynonyms(word: string): Observable<Synonym[]> {
    const url = `${this.nlUrl}/synonyms/${word}`;
    return this.http.get<Synonym[]>(url, this.httpOptions).pipe(
      catchError(this.handleError<Synonym[]>('fetching synonyms', []))
    );
  }

  private handleError<T>(operation = 'operation', result?: T) {
    return (response: any): Observable<T> => {
      this.notificationService.error(`Error ${operation}: ${response.error.message}`);
      return of(result as T);
    };
  }
}
