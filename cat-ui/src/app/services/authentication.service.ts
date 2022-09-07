import {EventEmitter, Injectable, Output} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Observable, BehaviorSubject} from 'rxjs';
import {environment} from '../../environments/environment';
import {AuthenticationStatus} from '../model/authentication-status';

@Injectable({
  providedIn: 'root'
})
export class AuthenticationService {

  private authUrl = `${environment.apiUrl}/auth`;

  @Output() authenticatedChange = new BehaviorSubject(false);

  constructor(private http: HttpClient) {
  }

  authenticate(pass: string): Observable<AuthenticationStatus> {
    const url = `${this.authUrl}/login`;
    return new Observable<AuthenticationStatus>(sub => {
      this.http.post<AuthenticationStatus>(url, {passphrase: pass})
        .subscribe(status => {
          this.authenticatedChange.next(status.authenticated);
          sub.next(status);
          sub.complete();
        }, err => {
          this.authenticatedChange.next(false);
          sub.error(err);
        });
    });
  }

  refreshAuthentication(): Observable<AuthenticationStatus> {
    const url = `${this.authUrl}/refresh`;
    return new Observable<AuthenticationStatus>(sub => {
      this.http.post<AuthenticationStatus>(url, {})
        .subscribe(status => {
          this.authenticatedChange.next(status.authenticated);
          sub.next(status);
          sub.complete();
        }, err => {
          this.authenticatedChange.next(false);
          sub.error(err);
          this.authenticate(environment.jwtPassphrase);
        });
    });
  }
}
