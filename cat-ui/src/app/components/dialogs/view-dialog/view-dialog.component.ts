import {Component, Inject, OnInit} from '@angular/core';
import {MAT_DIALOG_DATA, MatDialogRef} from '@angular/material';
import {DialogData} from '../warning-dialog/warning-dialog.component';

export interface ViewData {
  title: string;
  data: string;
}

@Component({
  selector: 'app-view-dialog',
  templateUrl: './view-dialog.component.html',
  styleUrls: ['./view-dialog.component.css']
})
export class ViewDialogComponent implements OnInit {

  constructor(public dialogRef: MatDialogRef<ViewDialogComponent>,
              @Inject(MAT_DIALOG_DATA) public data: ViewData) { }

  ngOnInit() {
  }

  closeDialog() {
    this.dialogRef.close();
  }

}
