# Agent guide: building UI with the COTRACE design system

For any AI agent (Claude Code, Codex, Antigravity, a plain chat) about to touch anything that renders. Read this, `docs/DESIGN.md` and `docs/PRODUCT.md` first. The deep rules are in `docs/design-system/foundations/`.

## The ten rules

1. **Tokens only.** No hex, rgb, px font size, radius, shadow or duration literal in component code. Stylesheets use CSS variables from `tokens.css`; canvas and WebGL code import from `web/src/design-system/tokens/tokens.ts` (or `tokens.numeric.json`).
2. **Semantic first.** Colour comes from `--color-*` (semantic) or a component token. Never `--p-color-*` in a component. Spacing, radius, font size and duration may use the primitive scale (`--p-space-3`, `--p-radius-md`).
3. **Missing token? Add it,** in `web/src/design-system/tokens/tokens.json`, in the right tier, with a `$description`. Run `cd web && npm run tokens`. Don't inline a value "for now".
4. **Two party colours, one meaning.** `--color-party-human-*` and `--color-party-ai-*` are only ever the human and the AI. Not links, not focus, not selection, not status, not decoration.
5. **No good-or-bad colouring of people.** Status colours (`--color-status-*`) are for system state only.
6. **Stages stay dark.** Put `.theme-dark` on any graph, brain or presentation stage.
7. **Text floor and contrast.** Nothing below 10px. Readable copy uses `--color-text-muted` or stronger. `--color-text-faint` is for hints only.
8. **Targets and focus.** Interactive marks get at least 24px hit areas and a visible `--color-focus-ring` focus state. Use `<button>` for anything clickable.
9. **Motion means change.** `var(--motion-feedback)`, `var(--motion-state)`, `var(--motion-arrive)`; transform and opacity only; always a reduced-motion path; no new loops.
10. **Every mark traces to its source.** A visual element that represents data must lead (click or tooltip) to the pair that produced it.

## Recipes

**A new panel**
```css
.my-panel { background: var(--color-surface-panel); border: 1px solid var(--color-border-subtle);
  border-radius: var(--p-radius-lg); padding: var(--p-space-3) var(--p-space-4); color: var(--color-text-primary); }
.my-panel h2 { font-size: var(--type-title-size); font-weight: var(--type-title-weight); line-height: var(--type-title-line-height); }
.my-panel p { color: var(--color-text-muted); }
```

**A human/AI tag**
```css
.who-human { color: var(--color-party-human-text); background: var(--color-party-human-soft); }
.who-ai    { color: var(--color-party-ai-text);    background: var(--color-party-ai-soft); }
```

**Canvas drawing**
```ts
import { tokens } from '../design-system/tokens/tokens';
const G = tokens.component.graph;
ctx.strokeStyle = tokens.semantic.color.party.human.solid;
const r = G.node['radius-min'];
```

**An icon button**
```css
.icon-button { width: 28px; height: 28px; border-radius: var(--p-radius-sm); color: var(--color-text-muted);
  transition: background var(--motion-feedback), color var(--motion-feedback); }
.icon-button:hover { background: var(--color-surface-hover); color: var(--color-text-primary); }
.icon-button:focus-visible { outline: 2px solid var(--color-focus-ring); outline-offset: 3px; }
```

## Before you finish

```bash
cd web && npm run tokens:check          # outputs up to date
node ../ui-craft/scripts/detect.mjs src/workspace   # no new undocumented colours or anti-patterns
npx tsc -p tsconfig.app.json --noEmit
```
Then look at the result in a real browser, in both `data-theme` modes if you touched chrome.

## Changing the system itself

- A value that changes meaning (party colours, the encoding grammar) needs a DDR in `docs/design-system/decisions/` with the owner's words quoted. The owner decides; agents propose.
- Renames and removals are major versions. Migrate every use in the same change.
- Locked surfaces (`mockups/*.lock.md`) change only through `ui-craft resettle`.
