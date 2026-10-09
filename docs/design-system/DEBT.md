# Design debt register (v0.1)

Everything the baseline migration deliberately left literal or out of rule, so the UI/UX phase starts from a known list instead of rediscovering it. Regenerate the counts with:

```bash
python3 scripts/design_system/migrate_to_tokens.py web/src/workspace/workspace.css --dry-run
python3 scripts/design_system/migrate_to_tokens.py web/src/workspace/obsidian-graph.css --dry-run
node ui-craft/scripts/detect.mjs web/src/workspace
```

Measured 9 Oct 2026, after DDR-002.

## Where we started

| | Prototype | After v0.1 |
|---|---|---|
| Distinct colour literals (stylesheets + graph code) | 176 | 12 left in the stylesheets (11 one-off tints + 1 tint colour); 36 inside the bundled brain renderer |
| Font sizes | 19, some 8–9.5px | 10-step scale, 10px floor |
| Radii | 15 | 9-step scale |
| Values converted to tokens | 0 | 545 in the two stylesheets (401 + 144), plus every colour and geometry constant on the main graph drawing path |

## Open items (updated after the full application pass, 9 Oct 2026)

Detector on `web/src/workspace`: **48 findings → 8** (3 one-off tints in our code, 5 inside the brain frame). No side-stripes, no layout animations, no off-grid spacing left.

| # | Debt | Status |
|---|---|---|
| 1 | Off-grid spacing | **Done.** 127 values snapped to the 4px grid (`scripts/design_system/snap_spacing.py`); positions untouched; no overflow |
| 2 | One-off translucent tints | 14 left across stylesheets and brain frame (party 20/30/80/90%, glass 70–96%). Decide per use in the UI/UX phase |
| 3 | `#bae6fd` text tint | Open |
| 4 | Four looping animations (brain `breathe` 3.2s and 3.4s, `questionPulse` 2.5s, `photonFlow` 4s) | **Open, owner decision**: keep, retime to `duration.breathe`, or remove (principle 5) |
| 5 | Width transitions | **Done.** Scrubber fill uses `transform: scaleX`; the dead workspace rule was removed |
| 6 | Side-stripe accent borders | **Done.** Dead rules removed; tooltip stripes became tinted panels |
| 7 | Brain renderer colours | **Done.** Reads `window.COTRACE_TOKENS`, defaults to the party palette (was grey "neutral study"), frame CSS on tokens. 5 one-off tints remain |
| 8 | Canvas graph not keyboard-navigable | Open (D6 B3) |
| 9 | Inter flagged as overused; no bundled font | Open (D4.S2) |
| 10 | Light theme untested in real use | Open (D4.S1); visible in the gallery |
| 11 | Primitives not yet components | Open (D6 B1) |
| 12 | `?mix=legacy` comparison mode literals | Keep until D5, then remove |
