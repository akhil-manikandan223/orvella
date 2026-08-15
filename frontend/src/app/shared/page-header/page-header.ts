import { Component, inject, input, output } from '@angular/core';
import { Location } from '@angular/common';
import { IconField } from 'primeng/iconfield';
import { InputIcon } from 'primeng/inputicon';
import { InputText } from 'primeng/inputtext';
import { ButtonDirective } from 'primeng/button';

@Component({
  selector: 'app-page-header',
  imports: [IconField, InputIcon, InputText, ButtonDirective],
  templateUrl: './page-header.html',
  styleUrl: './page-header.scss',
})
export class PageHeader {
  private readonly location = inject(Location);

  readonly title = input.required<string>();
  readonly subtitle = input<string | undefined>();
  readonly icon = input<string | undefined>();

  readonly showBack = input(false);

  readonly showSearch = input(false);
  readonly searchPlaceholder = input('Search');
  readonly search = output<string>();

  readonly showRefresh = input(false);
  readonly refresh = output<void>();

  protected onSearchInput(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.search.emit(value);
  }

  protected goBack(): void {
    this.location.back();
  }
}
