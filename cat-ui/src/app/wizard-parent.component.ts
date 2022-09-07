import {Component, EventEmitter, OnInit, Output} from '@angular/core';
import {AuthenticationService} from './services/authentication.service';
import {NotificationService} from './services/notification.service';
import {SimulationService} from './services/simulation.service';
import {environment} from '../environments/environment';

@Component({
  selector: 'app-root',
  templateUrl: './wizard-parent.component.html',
  styleUrls: ['./wizard-parent.component.css']
})
export class WizardParentComponent implements OnInit {
  title = 'CAT: Conversational Agents for Database Transactions';
  startTitle = 'Get started';
  configurationTitle = 'Configuration';
  trainingTitle = 'Training';

  constructor(private authService: AuthenticationService,
              private notificationService: NotificationService
  ) {
  }

  ngOnInit(): void {
    if (environment.jwtOn) {
    this.authService.authenticate(environment.jwtPassphrase)
      .subscribe(_ => {
        this.notificationService.success('Authentication successful.');
      }, err => {
        this.notificationService.error('Could not get authenticate with the server: ' + err);
      });
    } else {
      console.log('JWT authentication is disabled. Skipping authentication request.');
    }
  }
}
