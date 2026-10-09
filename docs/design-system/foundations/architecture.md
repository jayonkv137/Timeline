# Foundation: Token architecture

How the COTRACE design system is built, so it can serve every surface in the Brain Vision (web workspace, browser side panel, in-chat widget, 3D brain, print, mobile) from one source. Ratified in DDR-000c; built in DDR-002 (v0.1.0).

## 1. One source, many outputs

```
web/src/design-system/tokens/tokens.json      ← the only file a human edits (W3C DTCG format)
        │  node web/src/design-system/tokens/build.mjs      (or: cd web && npm run tokens)
        ├── tokens.css            CSS custom properties: dark default, [data-theme="light"], .theme-dark scope, reduced motion, text-role classes
        ├── tokens.ts             resolved values (dark + light trees), cssVar(), activeTokens() for canvas/React
        ├── tokens.numeric.json   numbers and 0–1 RGB for WebGL / Three.js (the 3D brain)
        └── docs/DESIGN.md        agent-readable summary (frontmatter generated; body from DESIGN.body.md)
```

`npm run tokens:check` fails when an output is stale. Run it in CI and before commits.

## 2. Three tiers

| Tier | Path | CSS name | Who may use it |
|---|---|---|---|
| Primitive | `primitive.color.neutral-dark.6`, `primitive.space.3` | `--p-color-neutral-dark-6`, `--p-space-3` | Semantic tokens; spacing, radius and type steps in components |
| Semantic | `semantic.color.text.muted`, `semantic.color.party.ai.solid` | `--color-text-muted`, `--color-party-ai-solid` | All components and surfaces (default choice) |
| Component | `component.graph.bead.core`, `component.scrubber.rail` | `--graph-bead-core`, `--scrubber-rail` | That component only |

Rules:
- **Colour in components is always semantic or component tier.** A component never writes `--p-color-*`. If no semantic token fits, add one; don't reach down.
- **Scales (space, radius, font size, duration) may be used from the primitive tier.** They are the grid, not a meaning.
- **Re-theming changes semantic mappings only.** A new surface adds component tokens and never edits semantics.

## 3. Naming grammar

`{tier}.{category}.{role}.{variant}.{state}`, each segment lowercase kebab-case.

- Category: `color`, `type`, `space`, `radius`, `elevation`, `motion`, `duration`, `easing`, `opacity`, `z`, `breakpoint`, `zoom-tier`, or a component name (`graph`, `scrubber`, `brain`, `workspace`).
- Colour roles: `bg` (grounds), `surface` (things on grounds), `border`, `text`, `party`, `focus`, `status`.
- Scale steps are numbers (`1`–`13`, `0-5` for half-steps); sizes are t-shirt (`2xs`…`display`).

## 4. Modes and scopes

| Mechanism | Where | Use |
|---|---|---|
| Default (dark) | `:root` | The product's baseline theme |
| `data-theme="light"` on `<html>` | `[data-theme="light"]` block | Provisional light theme (D4 decides values) |
| `.theme-dark` class | Any element | Stages that stay dark in every theme: graph, brain, presentation |
| `prefers-reduced-motion` | Media block | Durations collapse to 0ms; breathe loops stop in component code |
| Planned: `data-theme="hc"` | — | High contrast (D4.S7) |
| Planned: `data-density="compact"` | — | Side panel (360–420px) and in-chat widget |

Each token's light value lives in its `$extensions["cotrace.modes"].light`. Component tokens that alias semantic tokens re-resolve automatically.

## 5. Status of every token

`$extensions["cotrace.status"]`: **baseline** (taken from the shipped prototype, default), **provisional** (chosen now, open for D4 and D5), **planned** (structure reserved for a future surface, not for use yet). Status is inherited down a group.

## 6. Surfaces and what they consume

| Surface | Consumes | Notes |
|---|---|---|
| Web workspace (React) | `tokens.css` variables; `tokens.ts` in canvas code | `main.tsx` imports tokens.css before any component CSS |
| Graph canvas | `tokens.component.graph.*`, party colours | `.theme-dark` on the graph section |
| 3D brain (Three.js) | `tokens.numeric.json` | `brain-frame.html` is still literal (debt) |
| Browser side panel (extension) | `tokens.css` + compact density (planned) | Party colours never follow the host page |
| In-chat widget (MCP Apps) | `tokens.css` inlined; host theme decides `bg`/`text`, never `party` | Planned |
| Print / design pack | Light mode + print overrides (planned) | — |
| Mobile (someday) | `tokens.numeric.json` → Swift/Kotlin generators | Add outputs to build.mjs |

## 7. Changing the system

| Change | Version bump | Needs |
|---|---|---|
| New token | minor (0.x.0) | A line in the decision record or STATE |
| Value change | patch (0.0.x) | DDR if it changes meaning (e.g. party colours) |
| Rename or remove | major (x.0.0) | DDR + migration of every use; `rg -- '--old-name'` must return nothing |

Version lives in `tokens.json` → `$extensions["cotrace.version"]` and is printed into every output.

## 8. Tools

| Script | Purpose |
|---|---|
| `web/src/design-system/tokens/build.mjs` | Build / `--check` |
| `scripts/design_system/inventory_prototype.py` | Count every literal visual value in the workspace |
| `scripts/design_system/migrate_to_tokens.py` | Rewrite literals to tokens by property role; prints a debt report |
| `scripts/design_system/check_contrast.py` | WCAG contrast checks |
| `node ui-craft/scripts/detect.mjs web/src/workspace` | Anti-patterns and undocumented colours (reads docs/DESIGN.md) |
