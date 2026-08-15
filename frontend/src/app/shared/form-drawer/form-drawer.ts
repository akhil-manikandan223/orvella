import { Component, input, output } from '@angular/core';
import { Drawer } from 'primeng/drawer';

@Component({
  selector: 'app-form-drawer',
  imports: [Drawer],
  templateUrl: './form-drawer.html',
  styleUrl: './form-drawer.scss',
})
export class FormDrawer {
  readonly visible = input.required<boolean>();
  readonly visibleChange = output<boolean>();
  readonly header = input.required<string>();
  readonly width = input('28rem');
}
