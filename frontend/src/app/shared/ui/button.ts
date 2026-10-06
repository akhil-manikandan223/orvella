import { Directive, computed, input } from '@angular/core';
import { cva, type VariantProps } from 'class-variance-authority';
import type { ClassValue } from 'clsx';

import { hlm } from './hlm';

/**
 * Spartan-style helm button. Variants map to the Foundations board:
 * default = Primary, outline = Secondary, ghost = Ghost,
 * destructive = Destructive. Works on <button> and <a>.
 */
export const buttonVariants = cva(
  [
    'inline-flex shrink-0 cursor-pointer items-center justify-center gap-2 whitespace-nowrap',
    'rounded-md border border-transparent font-sans text-sm font-medium no-underline',
    'transition-colors outline-none select-none',
    'focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
    'disabled:pointer-events-none disabled:opacity-50 aria-disabled:pointer-events-none aria-disabled:opacity-50',
    '[&_i]:text-[1rem] [&_i]:leading-none',
  ],
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-brand-700',
        outline: 'border-input bg-card text-secondary-foreground hover:bg-muted',
        ghost: 'bg-transparent text-secondary-foreground hover:bg-muted hover:text-foreground',
        destructive: 'bg-destructive text-destructive-foreground hover:brightness-95',
        link: 'h-auto bg-transparent px-0 text-accent-foreground underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-9 px-3.5',
        sm: 'h-[30px] px-2.5 text-[13px]',
        lg: 'h-[42px] px-[18px] text-[15px]',
        icon: 'size-9 p-0',
        'icon-sm': 'size-8 p-0',
      },
    },
    defaultVariants: { variant: 'default', size: 'default' },
  },
);

export type ButtonVariants = VariantProps<typeof buttonVariants>;

@Directive({
  selector: 'button[hlmBtn], a[hlmBtn]',
  host: { '[class]': 'computedClass()' },
})
export class HlmButton {
  readonly variant = input<ButtonVariants['variant']>('default');
  readonly size = input<ButtonVariants['size']>('default');
  readonly userClass = input<ClassValue>('', { alias: 'class' });

  protected readonly computedClass = computed(() =>
    hlm(buttonVariants({ variant: this.variant(), size: this.size() }), this.userClass()),
  );
}
