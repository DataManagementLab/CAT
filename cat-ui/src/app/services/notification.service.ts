import {Injectable} from '@angular/core';
import {MatSnackBar} from '@angular/material';

@Injectable({providedIn: 'root'})
export class NotificationService {

  constructor(private snackbar: MatSnackBar) {
  }

  success(message: string, showDuration?: number) {
    this.snackbar.open(`Success: ${message}`, 'Dismiss', {
      duration: showDuration ? showDuration : 2000
    });
  }

  error(message: string, showDuration?: number) {
    this.snackbar.open(`Error: ${message}`, 'Dismiss', {
      duration: showDuration ? showDuration : 2000
    });
  }
}
