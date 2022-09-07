import {Injectable} from '@angular/core';
import {HttpHeaders, HttpClient} from '@angular/common/http';
import {Observable, of} from 'rxjs';
import {Database} from '../model/database';
import {environment} from '../../environments/environment';
import {Table} from '../model/table';
import {NotificationService} from './notification.service';
import {catchError} from 'rxjs/operators';
import {Procedure} from '../model/procedure';

@Injectable({providedIn: 'root'})
export class DatabaseService {

  private databaseUrl = `${environment.apiUrl}/database`;

  httpOptions = {
    headers: new HttpHeaders({
      'Content-Type': 'application/json'
    })
  };

  constructor(private http: HttpClient, private notificationService: NotificationService) {
  }

  connect(database: Database): Observable<boolean> {
    const url = `${this.databaseUrl}/connect`;
    return this.http.post<boolean>(url, database, this.httpOptions);
  }

  getTables(): Observable<Table[]> {
    const url = `${this.databaseUrl}/tables`;
    return this.http.get<Table[]>(url, this.httpOptions).pipe(
      catchError(this.handleError<Table[]>('fetching tables', []))
    );
  }

  getColumnValues(tableName: string, columnName: string): Observable<string[]> {
    const url = `${this.databaseUrl}/tables/${tableName}/columns/${columnName}/values`;
    return this.http.get<string[]>(url, this.httpOptions).pipe(
      catchError(this.handleError<string[]>('fetching column values', []))
    );
  }

  getProcedures(): Observable<Procedure[]> {
    const url = `${this.databaseUrl}/procedures`;
    return this.http.get<Procedure[]>(url, this.httpOptions).pipe(
      catchError(this.handleError<Procedure[]>('fetching procedures', []))
    );
  }

  private handleError<T>(operation = 'operation', result?: T) {
    return (response: any): Observable<T> => {
      this.notificationService.error(`Error ${operation}: ${response.error.message}`);
      return of(result as T);
    };
  }
}
