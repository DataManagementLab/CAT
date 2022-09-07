import {Component, Input, OnInit} from '@angular/core';
import {ThemePalette} from '@angular/material';
import * as JSZip from 'jszip';
import {DataFile} from '../../model/data-file';

@Component({
  selector: 'app-download-button',
  templateUrl: './download-button.component.html',
  styleUrls: ['./download-button.component.css']
})
export class DownloadButtonComponent implements OnInit {

  ZIP_TYPE = 'application/zip';

  @Input() icon;
  @Input() iconColor: ThemePalette;
  @Input() buttonText: string;
  @Input() buttonRaised = false;
  @Input() fileName: string;
  @Input() fileExt: string;
  @Input() timestamp = true;
  @Input() data: any;
  @Input() type: string;
  @Input() disabled: boolean;

  constructor() {
  }

  ngOnInit() {
  }

  downloadData() {
    if (this.type === this.ZIP_TYPE) {
      const zip = new JSZip();
      (this.data as DataFile[]).forEach(file => {
        zip.file(`${file.filename}.${file.extension}`, file.data);
      });
      zip.generateAsync({type: 'blob'})
        .then(blob => {
          this.downloadBlob(this.fileName, this.fileExt, blob, this.type, this.timestamp);
        });
    } else {
      this.downloadBlob(this.fileName, this.fileExt, this.data, this.type, this.timestamp);
    }
  }

  downloadBlob(file, extension, data, type, timestamp) {
    const blob: any = new Blob([data], {type: this.type});
    const url = window.URL.createObjectURL(blob);
    // window.location.href = url;
    const anchor = document.createElement('a');
    let filename = file;
    if (timestamp) {
      filename += Date.now();
    }
    anchor.download = `${filename}.${extension}`;
    anchor.href = url;
    anchor.click();
  }

}
