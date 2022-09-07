import {Component, EventEmitter, Input, isDevMode, OnInit, Output} from '@angular/core';
import {FormBuilder, FormControl, FormGroup, Validators} from '@angular/forms';

import {environment} from '../../../../environments/environment';
import {DatabaseService} from '../../../services/database.service';
import {NotificationService} from '../../../services/notification.service';
import {Database} from '../../../model/database';
import {AuthenticationService} from '../../../services/authentication.service';

@Component({
  selector: 'app-database-step',
  templateUrl: './database-step.component.html',
  styleUrls: ['./database-step.component.css']
})
export class DatabaseStepComponent implements OnInit {

  ipPattern = '(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)';
  hostnamePattern = '(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])';

  formGroupDatabase: FormGroup;
  connecting = false;
  error = false;
  completed = false;

  @Output() connected = new EventEmitter();

  @Input() database: Database;
  @Output() databaseChange = new EventEmitter();

  constructor(private formBuilder: FormBuilder,
              private authService: AuthenticationService,
              private databaseService: DatabaseService,
              private notificationService: NotificationService) {
  }

  ngOnInit() {
    this.formGroupDatabase = this.formBuilder.group({
      hostname: ['', [Validators.required, Validators.pattern(this.ipPattern + '|' + this.hostnamePattern)]],
      port: ['', [Validators.required, Validators.min(0), Validators.max(65535)]],
      username: ['', Validators.required],
      password: ['', Validators.required],
      databaseName: ['', Validators.required],
      schemaName: ['', Validators.required],
    });
    this.formGroupDatabase.valueChanges.subscribe(_ => {
      this.completed = false;
      this.error = false;
      this.connecting = false;
    });

    this.formGroupDatabase.controls.hostname.setValue(this.database.hostname);
    this.formGroupDatabase.controls.port.setValue(this.database.port);
    this.formGroupDatabase.controls.username.setValue(this.database.username);
    this.formGroupDatabase.controls.password.setValue(this.database.password);
    this.formGroupDatabase.controls.databaseName.setValue(this.database.databaseName);
    this.formGroupDatabase.controls.schemaName.setValue(this.database.schemaName);

    if (isDevMode()) {
      this.testConnection();
    }
  }

  testConnection() {
    this.error = false;
    this.completed = false;
    this.connecting = true;

    if (environment.jwtOn) {
      this.authService.authenticatedChange.subscribe(isAuthenticated => {
        if (isAuthenticated) {
          this.handleConnect(this.getDatabase());
        } else {
          this.notificationService.error(`Connection failed, invalid access token.`);
          this.error = true;
          this.completed = false;
          this.connecting = false;
          this.connected.emit(this.completed);
        }
      });
    } else {
      this.handleConnect(this.getDatabase());
    }
  }

  validateFormFields(formGroup): boolean {
    return Object.keys(formGroup.controls).every(field => {
        const control = formGroup.get(field);
        if (control instanceof FormControl) {
          control.markAsTouched({onlySelf: true});
          return control.valid;
        } else if (control instanceof FormGroup) {
          return this.validateFormFields(formGroup);
        }
      }
    );
  }

  getDatabase(): Database {
    if (this.validateFormFields(this.formGroupDatabase)) {
      return {
        hostname: this.formGroupDatabase.controls.hostname.value,
        port: this.formGroupDatabase.controls.port.value,
        username: this.formGroupDatabase.controls.username.value,
        password: this.formGroupDatabase.controls.password.value,
        databaseName: this.formGroupDatabase.controls.databaseName.value,
        schemaName: this.formGroupDatabase.controls.schemaName.value
      } as Database;
    } else {
      this.connecting = false;
      this.error = true;
      this.completed = false;
      this.connected.emit(this.completed);
      return null;
    }
  }

  handleConnect(database: Database) {
    if (!database) {
      this.connecting = false;
      this.error = true;
      this.completed = false;
      this.database = null;
      this.databaseChange.emit(this.database);
      this.connected.emit(this.completed);
    }
    this.databaseService.connect(database)
      .subscribe(connected => {
        if (connected) {
          this.connecting = false;
          this.error = false;
          this.completed = true;
          this.database = database;
          this.databaseChange.emit(this.database);
          this.notificationService.success('Connection successful');
          this.connected.emit(this.completed);
        } else {
          this.connecting = false;
          this.error = true;
          this.completed = false;
          this.database = null;
          this.databaseChange.emit(this.database);
          this.connected.emit(this.completed);
          this.notificationService.error(`Connection failed`);
        }
      }, response => {
        this.connecting = false;
        this.error = true;
        this.completed = false;
        this.database = null;
        this.databaseChange.emit(this.database);
        this.connected.emit(this.completed);
        this.notificationService.error(`Connection failed: ${response.error.message}`);
      });
  }
}

