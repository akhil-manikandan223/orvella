import { Directive, computed, input } from '@angular/core';
import type { ClassValue } from 'clsx';

import { hlm } from './hlm';

/** Field chrome shared by HlmInput and AppSelect so text inputs and selects line up. */
export const fieldClasses = [
  'h-[38px] w-full min-w-0 rounded-md border border-input bg-card text-sm text-foreground',
  'transition-[color,box-shadow] outline-none',
  'focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30',
  'aria-invalid:border-danger aria-invalid:ring-3 aria-invalid:ring-danger/20',
  'disabled:cursor-not-allowed disabled:bg-muted disabled:text-muted-foreground',
];

/**
 * Spartan-style helm input for <input> and <textarea>. Invalid state comes
 * from aria-invalid, which signal forms' [formField] sets on native inputs.
 */
@Directive({
  selector: 'input[hlmInput], textarea[hlmInput]',
  host: { '[class]': 'computedClass()' },
})
export class HlmInput {
  readonly userClass = input<ClassValue>('', { alias: 'class' });

  protected readonly computedClass = computed(() =>
    hlm(
      fieldClasses,
      'px-3 font-sans placeholder:text-muted-foreground [&:is(textarea)]:h-auto [&:is(textarea)]:py-2',
      this.userClass(),
    ),
  );
}
