import {Component, ElementRef, EventEmitter, Input, OnInit, Output, ViewChild} from '@angular/core';
import {ThemePalette} from '@angular/material';

@Component({
  selector: 'app-upload-button',
  templateUrl: './upload-button.component.html',
  styleUrls: ['./upload-button.component.css']
})
export class UploadButtonComponent implements OnInit {

  @Input() icon: string;
  @Input() iconColor: ThemePalette;
  @Input() accept: string;
  @Input() buttonText: string;
  @Input() buttonRaised = false;
  @Input() multiple = false;

  files: FileList;
  @Output() filesChange = new EventEmitter();

  @ViewChild('fileInput', {static: false}) fileInputRef: ElementRef;

  constructor() { }

  ngOnInit() {
  }

  onChange() {
    this.files = this.fileInputRef.nativeElement.files;
    this.filesChange.emit(this.files);
    this.fileInputRef.nativeElement.value = '';
  }

}
