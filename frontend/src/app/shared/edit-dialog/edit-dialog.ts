import { Component, input, output } from '@angular/core';
import { Dialog } from 'primeng/dialog';

@Component({
  selector: 'app-edit-dialog',
  imports: [Dialog],
  templateUrl: './edit-dialog.html',
  styleUrl: './edit-dialog.scss',
})
export class EditDialog {
  readonly visible = input.required<boolean>();
  readonly visibleChange = output<boolean>();
  readonly header = input.required<string>();
  readonly width = input('28rem');
}
