import {Component, ElementRef, EventEmitter, Input, OnInit, Output, ViewChild} from '@angular/core';
import {MatAutocomplete, MatAutocompleteTrigger, MatChipInputEvent, MatChipList} from '@angular/material';
import {COMMA, ENTER} from '@angular/cdk/keycodes';
import {Table} from '../../model/table';
import {Column} from '../../model/column';

@Component({
  selector: 'app-column-chip-list',
  templateUrl: './column-chip-list.component.html',
  styleUrls: ['./column-chip-list.component.css']
})
export class ColumnChipListComponent implements OnInit {
  @Input() columns: Column[];
  @Input() target: string[];
  @Output() targetChange = new EventEmitter();
  @Input() removable = true;
  @Input() addOnBlur = true;
  @Input() placeholder = 'Add columns used for representing an entity of this table';

  @ViewChild('chipInput', {static: false}) columnInput: ElementRef<HTMLInputElement>;
  @ViewChild('columnList', {static: false}) chipList: MatChipList;
  @ViewChild('auto', {static: false}) matAutocomplete: MatAutocomplete;
  @ViewChild(MatAutocompleteTrigger, {static: false}) matAutocompleteTrigger: MatAutocompleteTrigger;

  readonly separatorKeysCodes: number[] = [ENTER, COMMA];

  constructor() { }

  ngOnInit() {
  }

  removeColumn(columnName: string): void {
    const index = this.target.indexOf(columnName);
    if (index >= 0) {
      this.target.splice(index, 1);
      this.targetChange.emit(this.target);
    }
  }

  add(event: MatChipInputEvent): void {
    const input = event.input;
    const value = event.value.toLowerCase().trim();

    if (value && this.target.indexOf(value) === -1) {
      this.target.push(value);
      this.targetChange.emit(this.target);
    }
    if (input) {
      input.value = '';
    }
    this.chipList.chips.forEach(c => c.deselect());
  }

  onColumnSelected(event): void {
    const value = event.option.viewValue;
    const inputEvent: MatChipInputEvent = {
      input: this.columnInput.nativeElement,
      value: value.trim()
    };
    this.add(inputEvent);
  }

}
