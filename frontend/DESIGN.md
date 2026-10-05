# Orvella UI design

Source of truth for the visual language while the UI moves from PrimeNG to
Spartan UI + AG Grid. Token values live in `src/styles/tokens.css`; this file
explains the decisions behind them.

## Stack direction

| Concern    | Today                                | Target                                              |
| ---------- | ------------------------------------ | --------------------------------------------------- |
| Components | PrimeNG (Aura preset)                | Spartan UI (`@spartan-ng/brain` + helm, Tailwind)   |
| Data grids | `p-table` inside `shared/data-table` | AG Grid Community (`ag-grid-angular`), Quartz theme |
| Styling    | Component SCSS + PrimeNG tokens      | Tailwind v4 utilities over the tokens below         |

Verified compatibility (Oct 2026): `@spartan-ng/brain@1.5` peers on
`@angular/core >=21 <23`; `ag-grid-angular@36` on `>=20`. Every grid today
pages, sorts and filters client-side, so AG Grid Community is enough - no
Enterprise license.

## Migration order

1. **Tokens & theme** - navy PrimeNG preset, `tokens.css`, Tailwind (no
   preflight), IBM Plex. _(done)_
2. **AG Grid** - swap the `p-table` inside `shared/data-table`; every list
   page follows.
3. **Shell** - navy topbar, white sidebar, page headers, login.
4. **Spartan by feature folder** - tenants, geo, taxonomy, features, audit,
   profile, tenant workspace. Thin toast/confirm services replace PrimeNG's
   `MessageService` / `ConfirmationService`.
5. **Remove PrimeNG** - then enable Tailwind preflight in `src/tailwind.css`.

## Color

- Brand: `primary/600` **#0E4491**. Scale 50-900 in `--orv-primary-*`,
  mirrored in the PrimeNG preset in `app.config.ts` until step 5.
- Semantic names follow Spartan (`--background`, `--primary`, `--muted`,
  `--border`, `--ring` ...) so helm components need no remapping.
- Status pairs (text on tint): success `#177A45/#ECF8F1`, warning
  `#9A5B00/#FFF6E5`, danger `#C0352B/#FDEEEE`, info = primary 600 on 50.
  Badges always carry a dot + label - never color alone.
- Grid rows: hover `primary/50`, selected `primary/100`. Never fill a row
  with 600.

### Dark mode (`.app-dark`)

Dark is its own set of steps, not an inversion. Navy #0E4491 vanishes on a
near-black page, so in dark mode the primary button lifts to `#3366C2`, link
and accent text to `primary/300`, and the topbar deepens to `primary/800`.
Surfaces: page `#0D121B`, card `#151B26`, raised `#1B2230`, border `#2A3342`.

## Layout

- **Topbar:** primary background (`--topbar`), white icons, translucent
  search field. Chosen over a navy sidebar - keep a clear gap between the
  topbar and page-level primary buttons so they don't merge.
- **Sidebar:** white (`--sidebar`), grouped nav, active item on
  `primary/50` with primary text.
- **Pages:** title 24/32 semibold + one-line description, actions right.

## Type & shape

- IBM Plex Sans for UI, IBM Plex Mono for slugs, license numbers and IDs.
- Scale: display 30/38, h1 24/32, h2 18/26, body 14/20, label 13/18,
  caption 12/16.
- Radius: 6px controls (`--radius`), 10px cards. 4px spacing grid.
- Controls: 36px default height (30 small, 42 large).

## Open decisions

- **People status** - the design shows Active / On leave / Probation /
  Inactive, but `PersonRead` has no status field. Add it in the backend or
  drop the column.
