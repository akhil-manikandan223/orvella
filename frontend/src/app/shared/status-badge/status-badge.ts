import { Component, computed, input } from '@angular/core';
import { Tag } from 'primeng/tag';

type TagSeverity = 'info' | 'success' | 'warn' | 'danger' | 'secondary' | 'contrast';

const SEVERITY_BY_STATUS: Record<string, TagSeverity> = {
  active: 'success',
  enabled: 'success',
  true: 'success',
  inactive: 'secondary',
  disabled: 'secondary',
  false: 'secondary',
  deprecated: 'warn',
};

@Component({
  selector: 'app-status-badge',
  imports: [Tag],
  templateUrl: './status-badge.html',
  styleUrl: './status-badge.scss',
})
export class StatusBadge {
  readonly status = input.required<string>();
  readonly label = input<string | undefined>();

  protected readonly severity = computed<TagSeverity>(
    () => SEVERITY_BY_STATUS[this.status().toLowerCase()] ?? 'info',
  );
  protected readonly displayLabel = computed(() => this.label() ?? this.status());
}
