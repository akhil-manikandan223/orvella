import { Component, OnInit, inject, input, signal, viewChild } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { ButtonDirective } from 'primeng/button';

import { TenantService } from '../../../core/data-access/tenant.service';
import { TenantDetailRead } from '../../../core/models/tenant.model';
import { PageHeader } from '../../../shared/page-header/page-header';
import { TenantEditForm } from '../tenant-edit-form/tenant-edit-form';

@Component({
  selector: 'app-tenant-edit-page',
  imports: [ButtonDirective, PageHeader, RouterLink, TenantEditForm],
  templateUrl: './tenant-edit-page.html',
  styleUrl: './tenant-edit-page.scss',
})
export class TenantEditPage implements OnInit {
  private readonly tenantService = inject(TenantService);
  private readonly router = inject(Router);

  readonly id = input.required<string>();

  protected readonly tenant = signal<TenantDetailRead | null>(null);
  protected readonly formRef = viewChild(TenantEditForm);

  ngOnInit(): void {
    this.tenantService.get(this.id()).subscribe((tenant) => this.tenant.set(tenant));
  }

  protected save(): void {
    this.formRef()?.submit();
  }

  protected onSaved(): void {
    this.router.navigate(['/tenants', this.id()]);
  }
}
