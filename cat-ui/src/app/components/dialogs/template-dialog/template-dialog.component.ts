import {Component, ElementRef, EventEmitter, Inject, OnInit, Output, ViewChild} from '@angular/core';
import {MAT_DIALOG_DATA, MatDialogRef, MatInput} from '@angular/material';
import {Templateable} from '../../../model/templateable';

export interface TemplateData {
  title: string;
  templateable: Templateable;
}

@Component({
  selector: 'app-template-dialog',
  templateUrl: './template-dialog.component.html',
  styleUrls: ['./template-dialog.component.css']
})
export class TemplateDialogComponent implements OnInit {

  template: string;
  @Output() templateChange = new EventEmitter();

  @ViewChild(MatInput, {static: false, read: ElementRef}) input: ElementRef;

  constructor(public dialogRef: MatDialogRef<TemplateDialogComponent>,
              @Inject(MAT_DIALOG_DATA) public data: TemplateData) {
  }

  ngOnInit() {
    this.template = '';
  }

  onInputChange(e) {
    this.templateChange.emit(this.template);
  }

  addPlaceholder(placeholderText: string) {
    const cursorPosition = this.input.nativeElement.selectionStart;
    this.template = ''.concat(...this.template.slice(0, cursorPosition), `{${placeholderText}}`, this.template.slice(cursorPosition));
    this.input.nativeElement.focus();
  }

  addTemplate() {
    if (this.template.trim().length > 0) {
      this.data.templateable.templates.push(this.template.trim());
    }
    this.closeDialog();
  }

  closeDialog() {
    this.dialogRef.close();
  }

}
