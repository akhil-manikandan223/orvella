import { Component, computed, input } from '@angular/core';

type BadgeTone = 'success' | 'neutral' | 'warning' | 'info';

const TONE_BY_STATUS: Record<string, BadgeTone> = {
  active: 'success',
  enabled: 'success',
  true: 'success',
  inactive: 'neutral',
  disabled: 'neutral',
  false: 'neutral',
  deprecated: 'warning',
};

const TONE_CLASSES: Record<BadgeTone, string> = {
  success: 'bg-success-surface text-success',
  neutral: 'bg-muted text-muted-foreground',
  warning: 'bg-warning-surface text-warning',
  info: 'bg-info-surface text-info',
};

/**
 * Status pill from the Foundations board: a dot plus the label, so the state
 * never rests on color alone.
 */
@Component({
  selector: 'app-status-badge',
  host: { class: 'inline-flex' },
  template: `
    <span
      class="inline-flex h-[22px] items-center gap-1.5 rounded-full px-2 text-xs leading-none font-medium whitespace-nowrap"
      [class]="toneClass()"
    >
      <span class="size-1.5 rounded-full bg-current" aria-hidden="true"></span>
      {{ displayLabel() }}
    </span>
  `,
})
export class StatusBadge {
  readonly status = input.required<string>();
  readonly label = input<string | undefined>();

  protected readonly toneClass = computed(
    () => TONE_CLASSES[TONE_BY_STATUS[this.status().toLowerCase()] ?? 'info'],
  );
  protected readonly displayLabel = computed(() => this.label() ?? this.status());
}
