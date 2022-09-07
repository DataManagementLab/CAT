import {Component, DoCheck, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChange, SimpleChanges} from '@angular/core';
import {Procedure} from '../../model/procedure';
import {Table} from '../../model/table';
import {Argument} from '../../model/argument';
import {Column} from '../../model/column';
import {ViewDialogComponent} from '../dialogs/view-dialog/view-dialog.component';
import {MatDialog} from '@angular/material';
import {Parameter} from '../../model/parameter';

@Component({
  selector: 'app-procedure',
  templateUrl: './procedure.component.html',
  styleUrls: ['./procedure.component.css']
})
export class ProcedureComponent implements OnInit {

  @Input() procedure: Procedure;
  @Input() tables: Table[];
  @Input() id: number;
  @Input() step: number;
  @Output() stepChange = new EventEmitter();

  paramTab = 0;
  returnValueTab = 0;

  @Input() first = false;
  @Input() last = false;

  examplePhrasing = 'Provide some predicates and arguments to get example phrasings';
  readonly phrasingPrefixes = ['Alright, so you want to', 'Sure, let us', 'No problem, lets begin to'];

  constructor(private dialog: MatDialog) {
  }

  ngOnInit() {
  }

  phraseExample() {
    if (this.procedure.nlPairs.length > 0) {
      const prefixIndex = Math.floor(Math.random() * this.phrasingPrefixes.length);
      const pairIndex = Math.floor(Math.random() * this.procedure.nlPairs.length);
      const pair = this.procedure.nlPairs[pairIndex];
      this.examplePhrasing = `${this.phrasingPrefixes[prefixIndex]} ${pair.predicate} ${pair.argument}`;
    } else {
      this.examplePhrasing = 'Provide some predicates and arguments to get example phrasings';
    }
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

  getOtherParameters(param: Parameter) {
    return this.procedure.parameters.filter(p => p.name !== param.name);
  }

  getSampleEntityParameter() {
    if (!this.procedure.nlSample.parameterName) {
      return null;
    }
    return this.procedure.parameters.find(p => p.name === this.procedure.nlSample.parameterName);
  }

  getSampleEntityTable() {
    if (!this.procedure.nlSample.tableName) {
      return null;
    }
    const table = this.tables.find(t => t.name === this.procedure.nlSample.tableName);
  }

  getSampleEntityColumn() {
    if (!this.procedure.nlSample.columnName) {
      return null;
    }
    const table = this.tables.find(t => t.name === this.procedure.nlSample.tableName);
    return table.columns.find(c => c.name === this.procedure.nlSample.columnName);
  }

  getTableReference(value: Argument): Table {
    if (!value.tableReference) {
      return null;
    }
    return this.tables.find(t => t.name === value.tableReference);
  }

  getColumnReference(value: Argument): Column {
    const table = this.getTableReference(value);
    if (!table) {
      return null;
    }
    return table.columns.find(c => c.name === value.columnReference);
  }

  openBody(event) {
    event.stopPropagation();

    this.dialog.open(ViewDialogComponent, {
      width: '1000px',
      data: {
        title: `Procedure ${this.procedure.name}`,
        data: this.procedure.body
      }
    });
  }

}
