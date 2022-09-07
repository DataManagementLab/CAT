import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {MatDialog} from '@angular/material';
import {TemplateDialogComponent} from '../dialogs/template-dialog/template-dialog.component';
import {Templateable} from '../../model/templateable';

@Component({
  selector: 'app-template',
  templateUrl: './template.component.html',
  styleUrls: ['./template.component.css']
})
export class TemplateComponent implements OnInit {

  @Input() templateable: Templateable;

  @Input() id: number;
  @Input() step: number;
  @Output() stepChange = new EventEmitter();

  @Input() first: boolean;
  @Input() last: boolean;

  constructor(private dialog: MatDialog) { }

  ngOnInit() {
  }

  deleteTemplate(template) {
    const index = this.templateable.templates.indexOf(template);
    if (index > -1) {
      this.templateable.templates.splice(index, 1);
    }
  }

  openTemplateDialog() {
    this.dialog.open(TemplateDialogComponent, {
      width: '800px',
      data: {
        title: `Add a template for ${this.templateable.name}`,
        templateable: this.templateable
      }
    });
  }

  previousStep() {
    this.step--;
    this.stepChange.emit(this.step);
  }

  nextStep() {
    this.step++;
    this.stepChange.emit(this.step);
  }

  openStep() {
    this.step = this.id;
    this.stepChange.emit(this.step);
  }
}
