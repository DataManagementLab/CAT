import {Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges} from '@angular/core';
import {Argument} from '../../model/argument';
import {Table} from '../../model/table';
import {Column} from '../../model/column';

@Component({
  selector: 'app-entity-sample',
  templateUrl: './entity-sample.component.html',
  styleUrls: ['./entity-sample.component.css']
})
export class EntitySampleComponent implements OnInit, OnChanges {

  @Input() tables: Table[];
  @Input() parameters: Argument[];
  @Input() selectedParameter: Argument;
  @Input() selectedTable: Table;
  @Input() selectedColumn: Column;

  @Input() predicates: string[];
  @Output() predicatesChange = new EventEmitter();
  @Input() tableName: string;
  @Output() tableNameChange = new EventEmitter();
  @Input() columnName: string;
  @Output() columnNameChange = new EventEmitter();
  @Input() parameterName: string;
  @Output() parameterNameChange = new EventEmitter();

  constructor() {
  }

  ngOnInit() {
  }

  ngOnChanges(changes: SimpleChanges): void {
    const predicatesChange = changes.predicates;
    if (predicatesChange && predicatesChange.currentValue) {
      this.predicatesChange.emit(this.predicates);
    }
  }

  onParameterChange(event) {
    if (this.selectedParameter) {
      this.parameterName = this.selectedParameter.name;
      this.parameterNameChange.emit(this.parameterName);
      this.tableName = this.selectedParameter.tableReference;
      this.tableNameChange.emit(this.tableName);
      this.selectedTable = this.tables.find(t => t.name === this.tableName);
    } else {
      this.parameterName = null;
      this.parameterNameChange.emit(this.parameterName);
      this.tableName = null;
      this.tableNameChange.emit(this.tableName);
      this.columnName = null;
      this.columnNameChange.emit(this.columnName);
    }
  }

  onColumnChange(event) {
    if (this.selectedColumn) {
      this.columnName = this.selectedColumn.name;
      this.columnNameChange.emit(this.columnName);
    } else {
      this.columnName = null;
      this.columnNameChange.emit(this.columnName);
    }
  }

}
