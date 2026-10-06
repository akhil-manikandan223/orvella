import { PathKind, SchemaPath, SchemaPathRules, pattern } from '@angular/forms/signals';

// The raw pattern, for any non-Signal-Forms use (e.g. Validators.pattern(SLUG_PATTERN));
// Signal Forms code should use slugPattern() below.
export const SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

export function slugPattern<TPathKind extends PathKind = PathKind.Root>(
  path: SchemaPath<string, SchemaPathRules.Supported, TPathKind>,
): void {
  pattern(path, SLUG_PATTERN, {
    message: 'Must be lowercase letters, numbers, and hyphens only (e.g. "my-slug")',
  });
}
