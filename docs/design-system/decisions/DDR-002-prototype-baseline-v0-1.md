# DDR-002: The workspace prototype becomes Design System v0.1 (baseline)

- **Status:** Accepted
- **Date:** 2026-10-09
- **Decider:** Owner
- **Phase / Step:** D2 (replaces D2.S3 for now), D3 build
- **Affects:** `web/src/design-system/tokens/`, `docs/DESIGN.md`, `docs/design-system/foundations/`, `web/src/workspace/*.css`, `LocalGraph.tsx`

## Owner's words

> "we don't have design system from this prototype … we need from this to create the foundational design system … that is possible for all our bigger wider vision plan"
> "right now i am okay with the prototype design in this stage … later once we've done the integration and the product then i can focus on the design and ui/ux and ui craft skill to improve the stuff but currently i want this to be properly built"

## Context

D2.S3 planned to explore three visual directions before building tokens. Meanwhile the Codex workspace prototype, with the ported graph (DDR-006), became the product's real face. It had no system behind it: 7 CSS variables, 176 distinct hex colours (137 one-off greys), 19 font sizes, 15 radii, 54 spacing values, and two contradictory party palettes (clay and blue in the chat chrome, cyan and amber in the graph).

## Decision

1. **Adopt the prototype's look as v0.1.** The three-direction exploration (D2.S3) is deferred to the UI/UX phase after backend integration. When it happens, it changes token values; the architecture stays.
2. **Build the real system now** on the ratified architecture (DDR-000c):
   - `tokens.json` (DTCG): 289 tokens over three tiers (168 primitive, 53 semantic, 68 component), generated to CSS, TypeScript, numeric JSON and `docs/DESIGN.md`
   - The prototype rewired to the tokens: 545 stylesheet values migrated, and the graph canvas reads `tokens.ts`
   - Foundations, agent guide, component inventory and a debt register written
3. **One party palette everywhere, provisionally cyan `#38bdf8` = human and amber `#fb923c` = AI.** This is what the graph, scrubber and brain already use (35 of 37 occurrences). Codex's v1 clay and blue are retired from the chat chrome. DDR-005 still decides the final pair; candidates are kept as `primitive.color.candidate-pairs`.
4. **Normalisation, not redesign.** Greys snap to a 12-step scale and font sizes to a scale with a 10px floor; radii and transition timings snap to their scales. Spacing converts only on exact matches, so layout is pixel-identical. Everything left literal is in `DEBT.md`.
5. **Dark is the default theme.** Light exists as a provisional mode, to prove that any surface can switch. Stage surfaces (graph, brain) stay dark through the `.theme-dark` scope class.

## Measured result

| | Before | After |
|---|---|---|
| Colour literals in our stylesheets and graph code | 176 distinct | 12 one-off tints left literal in stylesheets; the detector flags 3 as undocumented (plus 36 inside the bundled brain renderer) |
| Theme switch | impossible | one attribute: `data-theme="light"` |
| Detector design-system colour findings, our code | 27 | 3 |
| Computed colour drift on main surfaces | — | ≤ 1 step (context panel 29,32,34 → 28,30,32) |

## Consequences

- Any new screen or surface (extension side panel, in-chat widget, Brain tab, print) starts from tokens instead of copying hex values.
- Later visual work (D2 directions, D4 foundations, D5 grammar) edits `tokens.json` values and DDRs; components follow automatically.
- `ui-craft` now checks code against `docs/DESIGN.md`, so drift is caught by `detect.mjs`.
