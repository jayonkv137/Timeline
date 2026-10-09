# Foundation: Typography

Status: v0.1 baseline (DDR-002). Face and ratio open for D4.S2.

## Strategy

Product register: one sans family, fixed pixel sizes, hierarchy by size and weight. No display face in UI. Numbers that line up use tabular figures.

| Family token | Stack | Status |
|---|---|---|
| `font.family.sans` | Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif | Baseline. The ui-craft detector flags Inter as overused; D4.S2 decides whether to keep it |
| `font.family.mono` | JetBrains Mono, ui-monospace, SFMono-Regular, Menlo, monospace | Provisional, for pair indices, masses and counts |

No webfont is loaded yet. Inter renders only where it's installed, otherwise the system face. Bundling a font is a D4.S2 decision (MCP widgets can't fetch remote fonts).

## Size scale

| Token | px | Typical use |
|---|---|---|
| `2xs` | 10 | Captions, status bar, notch tags. **The floor** |
| `xs` | 11 | Labels, tabs, legend, graph labels (11.5 on canvas) |
| `sm` | 12 | UI controls, lists |
| `base` | 13 | Body, transcript |
| `md` | 15 | Titles |
| `lg` | 16 | Large titles |
| `xl` | 20 | Headings |
| `2xl` | 24 | Section headings in Brain and empty states |
| `3xl` | 27 | Display |
| `display` | 45 | Brand moments only |

The prototype used 19 sizes, including 8–9.5px. Everything snapped to this scale, and nothing renders below 10px. The scale is descriptive of the prototype. D4.S2 rationalises it to a ratio (product register: 1.125–1.2).

## Text roles (`semantic.type.*`, CSS classes `.type-*`)

| Role | Size / weight / line-height / tracking | Use |
|---|---|---|
| `display` | 27 / 500 / 1.2 / −0.02em | Empty states, Brain headings |
| `heading` | 20 / 600 / 1.2 / −0.02em | Panel and dialog titles |
| `title` | 15 / 450 / 1.38 / −0.02em | Conversation titles, inspector heads |
| `body` | 13 / 400 / 1.65 / 0 | Transcript prose, max 65–75ch |
| `ui` | 12 / 400 / 1.5 / 0 | Controls, lists, menus |
| `label` | 11 / 500 / 1.38 / 0 | Tabs, metadata, graph labels |
| `caption` | 10 / 500 / 1.38 / 0 | Status bar, timestamps |
| `overline` | 10 / 700 / 1.2 / 0.08em, uppercase | Tooltip headers; sparing |
| `metric` | 11 mono / 500 | Pair numbers, masses (provisional) |

Each role is available as variables (`--type-body-size`, `--type-body-weight`…) and as a class (`.type-body`).

## Rules

- **The 10px floor.** Nothing smaller, including canvas labels.
- **Tabular figures** (`font-variant-numeric: tabular-nums`) for any column of numbers, pair counters and the scrubber badge.
- **Sentence case** everywhere; uppercase only for `overline`.
- **Canvas labels keep screen size** at every zoom (DDR-006), wrap at 165px (112px in compact panels), and never overlap a bead row.
- **Long German words** and umlauts must wrap without clipping. Test with real corpus titles.
