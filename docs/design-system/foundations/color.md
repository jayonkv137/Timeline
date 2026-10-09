# Foundation: Colour

Status: v0.1 baseline (DDR-002). Party pair provisional (DDR-005). Light mode provisional (D4.S1).

## 1. Strategy

**Restrained, two-voice.** A cool charcoal neutral system carries all chrome. Two hues are reserved for the two parties of the collaboration and mean nothing else. Status colours exist only for system state. Colour is never decoration.

Three Named Rules (also in `docs/DESIGN.md`):
- **One Voice:** human sky and AI ember mean the two parties, everywhere and only.
- **Mirror:** no red or green on anything a person or the AI did.
- **Stage:** the graph and the brain are dark stages in every theme (`.theme-dark`).

## 2. Neutral scale (dark), 12 functional steps plus one

| Step | Hex | Role | Semantic tokens |
|---|---|---|---|
| 1 | `#141619` | Canvas, deepest ground | `bg.canvas` |
| 2 | `#17191b` | App root | (primitive) |
| 3 | `#1c1e20` | Chrome: rail, tab frame | `bg.app` |
| 4 | `#222426` | Panels: sidebar, inspector, composer | `surface.panel` |
| 5 | `#2b2e30` | Raised: bubbles, inputs; subtle line | `surface.raised`, `border.subtle` |
| 6 | `#333638` | Hover fill; default line | `surface.hover`, `surface.active`, `border.default` |
| 7 | `#414548` | Strong line | `border.strong` |
| 8 | `#5d6367` | Disabled | `text.disabled` |
| 9 | `#7f888d` | Faint: hints and placeholders only | `text.faint` |
| 10 | `#969c9f` | Muted text: lowest for readable copy | `text.muted` |
| 11 | `#c5c9ca` | Secondary text | `text.secondary` |
| 12 | `#dedfdc` | Primary text | `text.primary` |
| 13 | `#f1f5f9` | Strongest ink: graph labels, emphasis | `text.strong` |

Special grounds: graph stage `#141417` (`bg.graph`), brain space `#080b10` (`bg.brain`), overlay `rgba(9,10,15,0.92)` (`surface.overlay`).

Alpha scales (`primitive.color.white-alpha.N`, `black-alpha.N`, N = opacity %) for rails, glints, scrims and shadows on dark grounds.

## 3. Contrast (WCAG 2.2), measured on the v0.1 values

| text \ ground | canvas | app | panel | raised | graph |
|---|---|---|---|---|---|
| primary `#dedfdc` | 13.5 | 12.5 | 11.6 | 10.2 | 13.7 |
| secondary `#c5c9ca` | 10.9 | 10.0 | 9.3 | 8.2 | 11.0 |
| muted `#969c9f` | 6.5 | 6.0 | 5.6 | 4.9 | 6.6 |
| faint `#7f888d` | 5.0 | 4.6 | 4.3 | **3.8** | 5.1 |
| strong `#f1f5f9` | 16.5 | 15.3 | 14.2 | 12.5 | 16.8 |
| disabled `#5d6367` | 3.0 | 2.7 | 2.6 | 2.2 | 3.0 |
| human text `#7dd3fc` | 10.9 | 10.0 | 9.3 | 8.2 | 11.0 |
| AI text `#fdba74` | 10.7 | 9.9 | 9.2 | 8.1 | 10.9 |
| human solid `#38bdf8` | 8.5 | 7.8 | 7.3 | 6.4 | 8.6 |
| AI solid `#fb923c` | 8.0 | 7.4 | 6.9 | 6.0 | 8.1 |

Rules that follow:
- Readable copy uses **muted or stronger** (≥ 4.9:1 everywhere).
- **Faint** is for hints only and never sits on raised surfaces (3.8:1).
- Party solids pass 3:1 for marks and 4.5:1 for text on every dark ground.

## 4. Party colours

| Token | Dark | Light (provisional) | Use |
|---|---|---|---|
| `party.human.solid` | `#38bdf8` | `#0284c7` | Ring arcs, beads, markers, scrubber past |
| `party.human.text` | `#7dd3fc` | `#0369a1` | Human-coloured words |
| `party.human.soft` | sky at 15% | sky-600 at 10% | Tinted fills |
| `party.human.line` | sky at 45% | sky-600 at 45% | Thin connectors |
| `party.ai.*` | `#fb923c` / `#fdba74` / 15% / 45% | `#ea580c` / `#c2410c` / … | The same roles for the AI |

### Candidate pairs for DDR-005 (colour-vision test)

OKLab distance ×100 between the two party colours, normal vision and Machado-simulated deficiencies. Under 10 means the two parties can be confused.

| Pair | Normal | Protan | Deutan | Tritan | Verdict |
|---|---|---|---|---|---|
| **spec (current)** `#38bdf8` / `#fb923c` | 30 | 24 | 26 | 29 | Safe |
| playbook `#0057ff` / `#e85a0a` | 44 | 34 | 40 | 34 | Safe; strongest separation; heavier on dark |
| clay `#d79a82` / `#7ca9d8` | 16 | 12 | 15 | 19 | Marginal |
| rose `#d98fa4` / `#55b9b0` | 19 | 7 | **3** | 24 | Fails deutan |
| ochre `#c8ac65` / `#729fdc` | 21 | 19 | 21 | 17 | Safe, low energy |
| cyan `#d5779c` / `#63bdd1` | 21 | 15 | **8** | 27 | Fails deutan |

The current pair is a sound default. Rose and cyan are out.

## 5. Status colours (provisional)

`status.danger` red-400, `status.warning` amber-400, `status.success` green-400, with -700 variants in light mode. Only for system state (send failed, backend offline, analysis complete). Never on human or AI data.

## 6. Focus

`focus.ring` `#b7cbd7`: a neutral ice tone, 2px, 3px offset. Focus is never a party colour.

## 7. Open for D4.S1

- Final party pair (DDR-005), tested again on the light ground.
- Light theme values (now mirrored, untested in use).
- High-contrast mode.
- Whether the neutral hue should warm slightly toward the "notebook" side of the personality scale (DDR-001: observatory 4 / notebook 6).
