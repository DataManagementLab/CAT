import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {Table} from '../../model/table';

@Component({
  selector: 'app-table',
  templateUrl: './table.component.html',
  styleUrls: ['./table.component.css']
})
export class TableComponent implements OnInit {

  @Input() table: Table;
  @Input() id: number;
  @Input() step: number;
  @Output() stepChange = new EventEmitter();

  columnTab = 0;

  @Input() first = false;
  @Input() last = false;

  constructor() {
  }

  ngOnInit() {
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
