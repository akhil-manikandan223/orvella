import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Joins class values and resolves Tailwind conflicts (last one wins), the
 * same `hlm()` helper Spartan's generated helm components use. Lets a caller
 * pass `class="w-full"` to a helm component without fighting its defaults.
 */
export function hlm(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
