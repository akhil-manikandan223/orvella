import { PathKind, SchemaPath, SchemaPathRules, pattern } from '@angular/forms/signals';

// Exported for forms that fall back to Reactive Forms (e.g. Validators.pattern(SLUG_PATTERN))
// because they contain a PrimeNG component incompatible with Signal Forms' [formField] — see
// slugPattern() below for the Signal Forms equivalent.
export const SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

export function slugPattern<TPathKind extends PathKind = PathKind.Root>(
  path: SchemaPath<string, SchemaPathRules.Supported, TPathKind>,
): void {
  pattern(path, SLUG_PATTERN, {
    message: 'Must be lowercase letters, numbers, and hyphens only (e.g. "my-slug")',
  });
}
