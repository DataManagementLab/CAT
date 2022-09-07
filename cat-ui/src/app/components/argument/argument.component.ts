import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {Table} from '../../model/table';
import {Column} from '../../model/column';
import {Argument} from '../../model/argument';

@Component({
  selector: 'app-argument',
  templateUrl: './argument.component.html',
  styleUrls: ['./argument.component.css']
})
export class ArgumentComponent implements OnInit {

  @Input() argument: Argument;
  @Input() tables: Table[];
  @Input() selectedTable: Table;
  @Input() selectedColumn: Column;

  @Input() id: number;
  @Input() tab: number;
  @Output() tabChange = new EventEmitter();
  @Input() first = false;
  @Input() last = false;

  constructor() {
  }

  ngOnInit() {
  }

  previousTab() {
    this.tab--;
    this.tabChange.emit(this.tab);
  }

  nextTab() {
    this.tab++;
    this.tabChange.emit(this.tab);
  }

  updateReference(event) {
    if (!event.checked) {
      this.argument.tableReference = null;
      this.argument.columnReference = null;
    }
  }

  onTableChange(event) {
    if (this.selectedTable) {
      this.argument.tableReference = this.selectedTable.name;
    } else {
      this.argument.tableReference = null;
    }
    this.selectedColumn = null;
    this.argument.columnReference = null;
  }

  onColumnChange(event) {
    if (this.selectedColumn) {
      this.argument.columnReference = this.selectedColumn.name;
    } else {
      this.argument.columnReference = null;
    }
  }
}
