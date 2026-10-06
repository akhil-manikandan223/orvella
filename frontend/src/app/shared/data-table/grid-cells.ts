import {
  Component,
  DestroyRef,
  ElementRef,
  TemplateRef,
  afterNextRender,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ICellRendererAngularComp, INoRowsOverlayAngularComp } from 'ag-grid-angular';
import type { ICellRendererParams, INoRowsOverlayParams } from 'ag-grid-community';

import { EmptyState } from '../empty-state/empty-state';
import { HlmButton, severityToButton } from '../ui/button';
import { DataTableAction } from './data-table.model';

/** Marker key carried by the synthetic full-width rows that hold an expansion. */
export const DETAIL_ROW = '__detailOf';

export interface DetailRow<T> {
  [DETAIL_ROW]: T;
  __detailKey: string;
}

export function isDetailRow<T>(row: unknown): row is DetailRow<T> {
  return typeof row === 'object' && row !== null && DETAIL_ROW in row;
}

/** Renders a caller-supplied `TemplateRef` column (DataTableColumn.template) inside a grid cell. */
@Component({
  selector: 'app-grid-template-cell',
  imports: [NgTemplateOutlet],
  template: `
    @if (template(); as tpl) {
      <ng-container *ngTemplateOutlet="tpl; context: { $implicit: row() }" />
    }
  `,
})
export class GridTemplateCell<T> implements ICellRendererAngularComp {
  protected readonly template = signal<TemplateRef<{ $implicit: T }> | null>(null);
  protected readonly row = signal<T | undefined>(undefined);

  agInit(params: ICellRendererParams<T> & { template: TemplateRef<{ $implicit: T }> }): void {
    this.refresh(params);
  }

  refresh(params: ICellRendererParams<T> & { template: TemplateRef<{ $implicit: T }> }): boolean {
    this.template.set(params.template);
    this.row.set(params.data);
    return true;
  }
}

/** Per-row icon buttons / links (DataTable `actions` input). */
@Component({
  selector: 'app-grid-actions-cell',
  imports: [HlmButton, RouterLink],
  template: `
    <div class="grid-actions">
      @for (action of actions(); track action.label) {
        @if (row(); as r) {
          @if (!action.visible || action.visible(r)) {
            @if (action.routerLink) {
              <a
                hlmBtn
                size="icon-sm"
                [variant]="tone(action).variant"
                [class]="tone(action).class"
                [routerLink]="action.routerLink(r)"
                [attr.aria-label]="action.label"
              >
                <i [class]="action.icon" aria-hidden="true"></i>
              </a>
            } @else {
              <button
                hlmBtn
                type="button"
                size="icon-sm"
                [variant]="tone(action).variant"
                [class]="tone(action).class"
                [disabled]="action.disabled ? action.disabled(r) : false"
                [attr.aria-label]="action.label"
                (click)="action.onClick?.(r)"
              >
                <i [class]="action.icon" aria-hidden="true"></i>
              </button>
            }
          }
        }
      }
    </div>
  `,
  styles: `
    .grid-actions {
      display: flex;
      align-items: center;
      gap: 0.25rem;
      height: 100%;
    }
  `,
})
export class GridActionsCell<T> implements ICellRendererAngularComp {
  protected readonly actions = signal<DataTableAction<T>[]>([]);
  protected readonly row = signal<T | undefined>(undefined);

  protected tone(action: DataTableAction<T>) {
    return severityToButton(action.severity, 'icon');
  }

  agInit(params: ICellRendererParams<T> & { actions: DataTableAction<T>[] }): void {
    this.refresh(params);
  }

  refresh(params: ICellRendererParams<T> & { actions: DataTableAction<T>[] }): boolean {
    this.actions.set(params.actions);
    this.row.set(params.data);
    return true;
  }
}

/**
 * Full-width row holding a record's expansion (DataTable `expansionTemplate`).
 * AG Grid's master/detail is Enterprise-only, so expansion is a synthetic row
 * inserted after its parent. Its content height is unknown up front, so it is
 * measured after render and fed back to the grid.
 */
@Component({
  selector: 'app-grid-detail-row',
  imports: [NgTemplateOutlet],
  template: `
    @if (template(); as tpl) {
      <div #content class="grid-detail">
        <ng-container *ngTemplateOutlet="tpl; context: { $implicit: row() }" />
      </div>
    }
  `,
  styles: `
    :host {
      display: block;
    }

    .grid-detail {
      padding: 0.75rem 1rem;
    }
  `,
})
export class GridDetailRow<T> implements ICellRendererAngularComp {
  private readonly content = viewChild<ElementRef<HTMLElement>>('content');
  private params: ICellRendererParams<DetailRow<T>> | null = null;
  private frame = 0;

  protected readonly template = signal<TemplateRef<{ $implicit: T }> | null>(null);
  protected readonly row = signal<T | undefined>(undefined);

  constructor() {
    // Measures the content box, not the row the grid sizes, so resizing the
    // row never feeds back into the observer. The frame delay keeps the
    // grid's relayout out of the observer callback, which the browser would
    // otherwise report as a "ResizeObserver loop" error.
    const observer = new ResizeObserver(() => {
      cancelAnimationFrame(this.frame);
      this.frame = requestAnimationFrame(() => this.syncHeight());
    });
    afterNextRender(() => {
      const element = this.content()?.nativeElement;
      if (element) {
        observer.observe(element);
      }
    });
    inject(DestroyRef).onDestroy(() => {
      cancelAnimationFrame(this.frame);
      observer.disconnect();
    });
  }

  agInit(
    params: ICellRendererParams<DetailRow<T>> & { template: TemplateRef<{ $implicit: T }> | null },
  ): void {
    this.refresh(params);
  }

  refresh(
    params: ICellRendererParams<DetailRow<T>> & { template: TemplateRef<{ $implicit: T }> | null },
  ): boolean {
    this.params = params;
    this.template.set(params.template);
    this.row.set(params.data?.[DETAIL_ROW]);
    return true;
  }

  private syncHeight(): void {
    const node = this.params?.node;
    const element = this.content()?.nativeElement;
    const height = element ? Math.ceil(element.getBoundingClientRect().height) : 0;
    if (node && height > 0 && node.rowHeight !== height) {
      node.setRowHeight(height);
      this.params?.api.onRowHeightChanged();
    }
  }
}

@Component({
  selector: 'app-grid-empty-overlay',
  imports: [EmptyState],
  template: `<app-empty-state [message]="message()" [icon]="icon()" />`,
})
export class GridEmptyOverlay implements INoRowsOverlayAngularComp {
  protected readonly message = signal('No records found.');
  protected readonly icon = signal('pi pi-inbox');

  agInit(params: INoRowsOverlayParams & { message: string; icon: string }): void {
    this.message.set(params.message);
    this.icon.set(params.icon);
  }

  refresh(params: INoRowsOverlayParams & { message: string; icon: string }): void {
    this.agInit(params);
  }
}
