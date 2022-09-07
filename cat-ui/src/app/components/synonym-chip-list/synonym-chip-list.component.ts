import {Component, ElementRef, EventEmitter, Input, OnInit, Output, ViewChild} from '@angular/core';
import {
  MatAutocomplete,
  MatAutocompleteSelectedEvent, MatAutocompleteTrigger, MatChip,
  MatChipInputEvent, MatChipList,
  MatChipSelectionChange
} from '@angular/material';
import {COMMA, ENTER} from '@angular/cdk/keycodes';
import {NaturalLanguageService} from '../../services/natural-language.service';
import {Synonym} from '../../model/synonym';
import {Observable, of} from 'rxjs';

@Component({
  selector: 'app-synonym-chip-list',
  templateUrl: './synonym-chip-list.component.html',
  styleUrls: ['./synonym-chip-list.component.css']
})
export class SynonymChipListComponent implements OnInit {
  @Input() target: string[];
  @Output() targetChange = new EventEmitter();
  @Input() removable = true;
  @Input() selectable = true;
  @Input() addOnBlur = true;
  @Input() placeholder = 'Add natural language description...';
  readonly separatorKeysCodes: number[] = [ENTER, COMMA];

  availableSynonyms: Observable<Synonym[]>;

  @ViewChild('chipInput', {static: false}) synonymInput: ElementRef<HTMLInputElement>;
  @ViewChild('nlList', {static: false}) chipList: MatChipList;
  @ViewChild('auto', {static: false}) matAutocomplete: MatAutocomplete;
  @ViewChild(MatAutocompleteTrigger, {static: false}) matAutocompleteTrigger: MatAutocompleteTrigger;

  constructor(private nlService: NaturalLanguageService) {
  }

  ngOnInit() {
  }

  removeNL(expression: string): void {
    const index = this.target.indexOf(expression);
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

  chipSelectionChange(event: MatChipSelectionChange) {
    if (event.selected) {
      const word = event.source.value.trim().replace(' cancel', '');
      this.availableSynonyms = this.nlService.getSynonyms(word);
      if (!this.matAutocompleteTrigger.panelOpen) {
        this.matAutocompleteTrigger.openPanel();
      }
    } else {
      const previousSelectedChip = this.chipList.selected as MatChip;
      if (previousSelectedChip && previousSelectedChip.value === event.source.value) {
        this.availableSynonyms = of([]);
      }
    }
  }

  onSynonymSelected(event: MatAutocompleteSelectedEvent) {
    const value = event.option.viewValue;
    const inputEvent: MatChipInputEvent = {
      input: this.synonymInput.nativeElement,
      value: value.trim()
    };
    this.add(inputEvent);
  }

  chipClicked(value) {
    const chip: MatChip = this.chipList.chips.find(c => c.value.trim() === (c.removable ? `${value} cancel` : value));
    chip.toggleSelected();
  }

  onManualInput() {
    const selectedChip = this.chipList.selected as MatChip;
    if (selectedChip) {
      selectedChip.deselect();
    }
  }

  displaySynonymGroup(synonym: Synonym) {
    return `${synonym.meaning} (${synonym.type}) - ${synonym.definition}`;
  }

}
