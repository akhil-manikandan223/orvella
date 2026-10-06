import { PathKind, SchemaPath, SchemaPathRules, pattern } from '@angular/forms/signals';

export const BRAND_COLOR_PATTERN = /^#[0-9a-fA-F]{6}$/;

/** Optional field: an empty value is left alone, since `pattern` only runs on
 * non-empty input and a tenant with no brand colour inherits Orvella's. */
export function brandColorPattern<TPathKind extends PathKind = PathKind.Root>(
  path: SchemaPath<string, SchemaPathRules.Supported, TPathKind>,
): void {
  pattern(path, BRAND_COLOR_PATTERN, {
    message: 'Must be a 6-digit hex colour (e.g. "#6d5ce0")',
  });
}
