import {Component, ElementRef, EventEmitter, Input, OnInit, Output, ViewChild} from '@angular/core';
import {NaturalLanguagePair} from '../../model/nl-pair';
import {Form, FormBuilder, FormGroup, FormGroupDirective, Validators} from '@angular/forms';
import {MatAutocompleteSelectedEvent, MatChip, MatChipInputEvent, MatChipList, MatChipSelectionChange} from '@angular/material';
import {Synonym} from '../../model/synonym';
import {Observable, of} from 'rxjs';
import {NaturalLanguageService} from '../../services/natural-language.service';

@Component({
  selector: 'app-pair-chip-list',
  templateUrl: './pair-chip-list.component.html',
  styleUrls: ['./pair-chip-list.component.css']
})
export class PairChipListComponent implements OnInit {

  @Input() target: NaturalLanguagePair[];
  @Output() targetChange = new EventEmitter();
  @Input() removable = true;
  @Input() selectable = true;
  @Input() addOnBlur = true;

  @ViewChild('predicateInput', {static: false}) predicateInput: ElementRef<HTMLInputElement>;
  @ViewChild('argumentInput', {static: false}) argumentInput: ElementRef<HTMLInputElement>;
  @ViewChild('chipList', {static: false}) chipList: MatChipList;


  @ViewChild('f', {static: false}) form: FormGroupDirective;
  formGroup: FormGroup;

  availablePredicateSynonyms: Observable<Synonym[]>;
  availableArgumentSynonyms: Observable<Synonym[]>;

  constructor(private formBuilder: FormBuilder, private nlService: NaturalLanguageService) {
  }

  ngOnInit() {
    this.formGroup = this.formBuilder.group({
      predicate: ['', Validators.required],
      argument: ['', Validators.required]
    }, {
      validators: (group: FormGroup) => {
        const predicate = group.controls.predicate;
        const argument = group.controls.argument;
        // either provide both values or none
        if (!predicate.value && argument.value) {
          predicate.setErrors({required: true});
        } else if (predicate.value && !argument.value) {
          argument.setErrors({required: true});
        } else if (predicate.value && argument.value) {
          const pVal = predicate.value.trim();
          const aVal = predicate.value.trim();
          if (pVal === '') {
            predicate.setErrors({required: true});
          }
          if (aVal === '') {
            argument.setErrors({required: true});
          }
        } else {
          predicate.setErrors(null);
          argument.setErrors(null);
        }
      }
    });
  }

  onSubmit() {
    const predicateCtrl = this.formGroup.controls.predicate;
    const argumentCtrl = this.formGroup.controls.argument;
    const value: NaturalLanguagePair = {
      predicate: predicateCtrl.value.trim(),
      argument: argumentCtrl.value.trim()
    };
    const duplicate = this.target.find(expr => (expr.predicate === value.predicate && expr.argument === value.argument));
    if (!duplicate) {
      this.target.push(value);
      this.targetChange.emit(this.target);
    }
    this.form.resetForm();
  }

  removePair(pair: NaturalLanguagePair) {
    const index = this.target.indexOf(pair);
    if (index >= 0) {
      this.target.splice(index, 1);
      this.targetChange.emit(this.target);
    }
  }

  onPredicateSynonymSelected(event: MatAutocompleteSelectedEvent) {
    const value = event.option.viewValue;
    this.formGroup.controls.predicate.setValue(value);
  }

  onArgumentSynonymSelected(event: MatAutocompleteSelectedEvent) {
    const value = event.option.viewValue;
    this.formGroup.controls.argument.setValue(value);
  }

  onManualInput() {
    const selectedChip = this.chipList.selected as MatChip;
    if (selectedChip) {
      selectedChip.deselect();
    }
  }

  chipSelectionChange(event: MatChipSelectionChange) {
    if (event.selected) {
      this.formGroup.controls.predicate.setValue(null);
      this.formGroup.controls.argument.setValue(null);
      const value = event.source.value.trim().replace(' cancel', '');
      const index = this.target.map(expr => `${expr.predicate} ${expr.argument}`).indexOf(value);
      if (index >= 0) {
        const pair = this.target[index];
        this.availablePredicateSynonyms = this.nlService.getSynonyms(pair.predicate);
        this.availableArgumentSynonyms = this.nlService.getSynonyms(pair.argument);
      }
    } else {
      const previousSelectedChip = this.chipList.selected as MatChip;
      if (previousSelectedChip && previousSelectedChip.value === event.source.value) {
        this.availablePredicateSynonyms = of([]);
        this.availableArgumentSynonyms = of([]);
      }
    }
  }

  chipClicked(expression) {
    const searchValue = `${expression.predicate} ${expression.argument}`;
    const chip: MatChip = this.chipList.chips.find(
      c => c.value.trim() === (c.removable ?
        `${searchValue} cancel` :
        searchValue)
    );
    chip.toggleSelected();
  }

  displaySynonymGroup(synonym: Synonym) {
    return `${synonym.meaning} (${synonym.type}) - ${synonym.definition}`;
  }
}
