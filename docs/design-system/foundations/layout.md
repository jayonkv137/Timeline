# Foundation: Space, layout, shape and depth

Status: v0.1 baseline (DDR-002).

## Space

A 4px grid with 2px half-steps for dense product UI.

| Token | px | | Token | px |
|---|---|---|---|---|
| `space.0` | 0 | | `space.4` | 16 |
| `space.px` | 1 | | `space.5` | 20 |
| `space.0-5` | 2 | | `space.6` | 24 |
| `space.1` | 4 | | `space.7` | 28 |
| `space.1-5` | 6 | | `space.8` | 32 |
| `space.2` | 8 | | `space.10` | 40 |
| `space.2-5` | 10 | | `space.12` | 48 |
| `space.3` | 12 | | `space.16` | 64 |
| `space.3-5` | 14 | | | |

The prototype still has off-grid values (13, 15, 17, 19, 21px…). The migration converted only exact matches so layout stays pixel-identical. The rest are listed in `DEBT.md` and move to the grid during the UI/UX phase, one screen at a time with a screenshot check.

## Workspace layout (baseline)

```
┌────┬──────────┬──────────────────────────────┬──────────────┐
│rail│ sidebar  │ tab strip (44px)             │              │
│46px│ 226px    ├──────────────────────────────┤ context panel│
│    │ history  │ conversation (65–75ch)       │ 342px        │
│    │          │ composer dock                │ graph / Brain│
├────┴──────────┴──────────────────────────────┴──────────────┤
│ status bar                                                   │
└──────────────────────────────────────────────────────────────┘
```

| Breakpoint token | Value | Behaviour in the prototype |
|---|---|---|
| `breakpoint.wide` | ≥ 1600px | Context panel 380px |
| `breakpoint.laptop` | ≤ 1200px | Rail 42 · sidebar 198 · context 300 |
| `breakpoint.tablet` | ≤ 1000px | Context panel moves to an overlay |
| `breakpoint.phone` | ≤ 760px | Sidebar becomes an overlay; one column |
| `breakpoint.side-panel-min` / `-max` | 360–420px | Browser extension side panel (planned compact density) |

## Shape

| Token | px | Use |
|---|---|---|
| `radius.xs` | 2 | Hairline chips, tags |
| `radius.sm` | 4 | Buttons, icon buttons, inputs |
| `radius.md` | 6 | Menus, small cards, tool buttons |
| `radius.lg` | 8 | Message bubbles, tooltips |
| `radius.xl` | 12 | Toasts, larger cards |
| `radius.2xl` | 16 | Composer |
| `radius.3xl` | 20 | Large sheets |
| `radius.pill` | 9999 | Scrubber capsule, badges |
| `radius.round` | 50% | Avatars, round buttons, beads |

## Depth

Tonal steps first (see colour §2), shadows only for floating layers:

| Token | Value | Use |
|---|---|---|
| `elevation.1` | 0 8px 24px black 13% | Composer, hovered cards |
| `elevation.2` | 0 4px 12px black 27% | Menus, popovers |
| `elevation.3` | 0 10px 30px black 33% | Dialogs, inspectors |
| `elevation.4` | 0 14px 38px black 75% | Controls floating over the graph |

## Layers (`z`)

`base 0 · raised 10 · sticky 20 · overlay 50 · popover 100 · toast 200 · tooltip 300`. Never 999. Floating graph controls sit inside the graph's own stacking context (`isolation: isolate`).
