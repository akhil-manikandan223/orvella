import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { Toaster } from './core/feedback/toaster';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, Toaster],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {}
