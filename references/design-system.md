# Design system

Source of truth: `web/src/app.css`. Read its header comment first.

## Palette

Slate neutrals for text/borders/backgrounds, **indigo** for actions, selection and links, **emerald / amber / rose** for status
(ok / warning / problem). Page background `bg-slate-50`, cards white. Brand colour can be changed in one place by swapping the
indigo steps. No other hues unless the product needs a data-visualisation palette.

## One look for controls

Every `<button>`, `<input>`, `<select>`, `<textarea>`, checkbox and radio is styled in `@layer base`, so an unstyled control
still matches. Variants only recolour:

| Class | Meaning |
|---|---|
| (none) | secondary button |
| `.action` | the one main action of a form or bar (indigo fill) |
| `.danger` | destructive (rose outline) |
| `.button-link` | a full-width link that looks like a secondary button (e.g. "Continue with Google") |

## Components (in `@layer components`)

`.panel` (the one card), `.panel-heading`, `.badge` + `.tone-ok|warn|bad`, `.callout`, `.page-shell` (max-w-6xl container),
`.page-intro` + `.eyebrow` + `.intro-copy`, `.site-header/.header-inner/.brand/.primary-nav/.nav-link`, `.site-footer`,
`.toast`, `.skip-link`.

## Rules

1. One-off layout: Tailwind utilities in the template. Anything a script creates more than once: a named component in `app.css`
   built with `@apply`, so the JS only needs a class name.
2. Grid children get `min-w-0` (a single long line otherwise widens its column past the screen).
3. Tailwind scans `app/templates` and `app/static/js` (see `@source`). A class that only appears elsewhere is **not** compiled.
4. Headings via the base layer (`h1 text-3xl font-bold`); do not restyle per page.
5. Accessibility: skip link, `aria-current="page"` on the active nav link, `role="alert"` on error text, `aria-hidden` on icons,
   visible focus ring (base layer), labels tied to inputs.
6. Flags: use SVG flag icons (`flag-icons`), not emoji (emoji flags do not render on Windows).
7. Full-width pages; forms limited to a readable width (`max-w-3xl`) next to a section nav when long.
8. Motion: respect `prefers-reduced-motion` for any animation you add.

## Adding a component

1. Add it to `@layer components` in `web/src/app.css` with `@apply`.
2. `make css`. 3. Use the class in the template or script. 4. Commit the compiled CSS.
