import {Component, Input, OnInit, ViewChild} from '@angular/core';
import {COMMA, ENTER} from '@angular/cdk/keycodes';
import {Table} from '../../model/table';
import {Column} from '../../model/column';
import {DatabaseService} from '../../services/database.service';
import {MatChip, MatChipList, MatChipSelectionChange} from '@angular/material';
import {LookupEntry} from '../../model/lookup-entry';

@Component({
  selector: 'app-column-lookup-list',
  templateUrl: './column-lookup-list.component.html',
  styleUrls: ['./column-lookup-list.component.css']
})
export class ColumnLookupListComponent implements OnInit {

  @Input() table: Table;
  @Input() column: Column;
  @Input() addOnBlur = true;
  @Input() selectable = true;
  @Input() removable = true;

  targetValue: LookupEntry = undefined;
  @ViewChild('lookupTableList', {static: false}) chipList: MatChipList;

  constructor(private databaseService: DatabaseService) {
  }

  readonly valueSeparatorCodes: number[] = [ENTER, COMMA];

  ngOnInit() {
  }

  chipSelectionChange(event: MatChipSelectionChange) {
    if (event.selected) {
      const word = event.source.value.trim().replace(' cancel', '');
      const valueNames = this.column.lookupTable.map(v => v.value);
      const index = valueNames.indexOf(word);
      this.targetValue = this.column.lookupTable[index];
    }
  }

  chipClicked(value) {
    this.targetValue = undefined;
    const chip: MatChip = this.chipList.chips.find(c => c.value.trim() === (c.removable ? `${value} cancel` : value));
    chip.toggleSelected();
  }

  addValueToLookupTable(event) {
    const input = event.input;
    const value = event.value;
    this.addValueInternal(value);
    if (input) {
      input.value = '';
    }
  }

  getColumnValues() {
    this.databaseService.getColumnValues(this.table.name, this.column.name)
      .subscribe(values => {
        values.forEach(value => {
          this.addValueInternal(value);
        });
      });
  }

  private addValueInternal(lookupValue) {
    lookupValue = (lookupValue + '').toLowerCase().trim();
    const valueNames = this.column.lookupTable.map(v => v.value);
    if (lookupValue && valueNames.indexOf(lookupValue) === -1) {
      this.column.lookupTable.push({value: lookupValue, synonyms: [lookupValue]} as LookupEntry);
    }
  }

  removeValueFromLookupTable(value) {
    const valueNames = this.column.lookupTable.map(v => v.value);
    const index = valueNames.indexOf(value);
    if (index > -1) {
      this.column.lookupTable.splice(index, 1);
    }
    console.log(value);
    console.log(this.targetValue);
    if (this.targetValue.value === value) {
      this.targetValue = undefined;
    }
  }

}
