import { themeQuartz } from 'ag-grid-community';

/**
 * Orvella's AG Grid theme. Every color points at a design token from
 * src/styles/tokens.css rather than a hex value, so the grid follows
 * .app-dark with no second theme object. Row tints follow the design rule:
 * hover on primary/50, selection on primary/100, never a solid brand fill.
 */
export const orvellaGridTheme = themeQuartz.withParams({
  fontFamily: 'var(--orv-font-sans)',
  fontSize: 13.5,
  headerFontWeight: 600,
  headerHeight: 42,
  rowHeight: 46,
  accentColor: 'var(--primary)',
  backgroundColor: 'var(--card)',
  foregroundColor: 'var(--foreground)',
  headerTextColor: 'var(--secondary-foreground)',
  headerBackgroundColor: 'var(--muted)',
  chromeBackgroundColor: 'var(--muted)',
  borderColor: 'var(--border)',
  rowHoverColor: 'var(--grid-row-hover)',
  selectedRowBackgroundColor: 'var(--grid-row-selected)',
  checkboxCheckedBackgroundColor: 'var(--primary)',
  // Inherit, never force light: tokens.css sets color-scheme per theme, and a
  // forced value here would render native controls and light-dark() colors
  // inside the grid (checkboxes, expansion templates) light on a dark page.
  browserColorScheme: 'inherit',
  // The surrounding .data-table__wrapper card draws the border and radius.
  wrapperBorder: false,
  wrapperBorderRadius: 0,
});
