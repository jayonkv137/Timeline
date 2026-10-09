# Foundation: Accessibility

Floor: **WCAG 2.2 AA** (DDR-000e). Measured values are in `color.md` §3.

| Requirement | Standard | v0.1 status |
|---|---|---|
| Body text contrast ≥ 4.5:1 | 1.4.3 | Pass: muted text ≥ 4.9:1 on every ground |
| Non-text marks ≥ 3:1 | 1.4.11 | Pass for party marks (≥ 6:1). Dormant tethers (slate 32%) are intentionally below; dormancy is also carried by opacity and position |
| Target size ≥ 24 × 24px | 2.5.8 | Pass for beads (24px hit) and controls (28–32px). 44px for touch surfaces is planned with compact density |
| Focus visible | 2.4.7 / 2.4.11 | Pass: 2px ice ring, 3px offset; notches are real buttons |
| Text ≥ 10px | House rule | Pass after migration (prototype had 8–9.5px) |
| Reduced motion | 2.3.3 | Pass: durations collapse; canvas pulses freeze |
| Colour not the only signal | 1.4.1 | Partly. Bead kinds differ by shape; share-ring arcs rely on hue plus order (human first, clockwise). Tooltips name the party in words |
| Colour-vision safety | House rule | Pass: party pair distance ≥ 24 under protan, deutan and tritan simulation |

## Known gaps (DEBT.md)

1. **Canvas graph is not keyboard-navigable.** Beads and spheres are canvas pixels. The scrubber, notches and corner tools are keyboard-accessible, and the section carries `data-pair`, `data-node-count` and an `aria-label`. Planned: an offscreen list of outcomes and atoms mirrored to focusable elements, with the tooltip on focus.
2. **No live-region announcements** when a pair finishes analysing (needed for G2).
3. **Light theme** contrast is untested in real use.
4. **Brain (WebGL)** has the conversation list as its accessible alternative. Picking in 3D is mouse-only.

## Checks

- `python3 scripts/design_system/check_contrast.py`: contrast.
- `node ui-craft/scripts/detect.mjs web/src/workspace`: anti-patterns and undocumented colours.
- `ui-craft audit`: the full technical audit before any release.
