import {Component, Input, OnChanges, OnInit, SimpleChanges} from '@angular/core';
import {ThemePalette} from '@angular/material';

@Component({
  selector: 'app-template-display',
  templateUrl: './template-display.component.html',
  styleUrls: ['./template-display.component.css']
})
export class TemplateDisplayComponent implements OnInit, OnChanges {

  @Input() template: string;
  @Input() regex = '{(.+?)}';
  @Input() flags = 'gi';
  @Input() chipColor: ThemePalette = 'primary';

  re: RegExp;
  templateParts: string[];

  constructor() {
  }

  ngOnInit() {
    this.re = RegExp(this.regex, this.flags);
    this.templateParts = this.template.split(this.re);
  }

  ngOnChanges(changes: SimpleChanges): void {
    const templateChanges = changes.template;
    if (templateChanges) {
      this.templateParts = this.template.split(this.re);
    }
  }
}
