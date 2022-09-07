import {Component, ElementRef, EventEmitter, Input, OnInit, Output, ViewChild} from '@angular/core';
import {Table} from '../../model/table';
import {MatInput} from '@angular/material/input';

@Component({
  selector: 'app-table-representation',
  templateUrl: './table-representation.component.html',
  styleUrls: ['./table-representation.component.css']
})
export class TableRepresentationComponent implements OnInit {

  @Input() table: Table;

  @ViewChild(MatInput, {static: false, read: ElementRef}) input: ElementRef;

  constructor() {
  }

  ngOnInit() {
  }

  addPlaceholder(placeholderText: string) {
    const cursorPosition = this.input.nativeElement.selectionStart;
    this.table.representation = ''
      .concat(
        ...this.table.representation.slice(0, cursorPosition), `{${placeholderText}}`,
        this.table.representation.slice(cursorPosition)
      );
    this.input.nativeElement.focus();
  }

}
