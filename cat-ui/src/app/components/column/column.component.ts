import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {Column} from '../../model/column';
import {DatabaseService} from '../../services/database.service';
import {Table} from '../../model/table';
import {COMMA, ENTER} from '@angular/cdk/keycodes';

@Component({
  selector: 'app-column',
  templateUrl: './column.component.html',
  styleUrls: ['./column.component.css']
})
export class ColumnComponent implements OnInit {

  @Input() table: Table;
  @Input() column: Column;
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

}
