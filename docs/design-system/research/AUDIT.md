# AUDIT.md — Visual Audit & Conflict Inventory

**Date:** 2026-10-08  
**Phase/Step:** D0.S1 (Phase D0: Charter, audit and setup · Step 1: Visual Audit & Conflict Inventory)  
**Auditor:** DESIGN SYSTEM (Antigravity · Gemini)  
**Tools used:** `ui-craft/scripts/detect.mjs`, AST inspection, spec inventory  

---

## 1. Executive Summary

The project's backend and measurement engine are mature and mathematically verified (Phase E2 closed, 10 corpus chats replaying deterministically with 100% invariants passing). However, the front-facing product currently fractures across **three disconnected visual worlds**, with conflicting color assignments, contradictory visual encoding rules between specs, and several classic AI tells and layout performance anti-patterns.

| Surface / Spec | Theme & Atmosphere | Party Colours | Typography | Token System |
|---|---|---|---|---|
| **`web/` right-rail panel** | Warm off-white paper (`#faf9f6`, `#f1efe9`) | Blue `#0057FF` (You) / Orange `#E85A0A` (AI) | Inter + DM Mono | Ad-hoc CSS variables in `index.css` |
| **`design_pack/` graph prototypes** | Deep dark obsidian (`#141417`, `#090a0f`) | Cyan `#38bdf8` (User) / Amber `#fb923c` (AI) | System sans-serif stack | Hand-coded hex/rgba values |
| **`AI Chatbot Interface (Copy)/`** | Stock shadcn light/dark zinc defaults | None assigned (generic neutral theme) | Unspecified system sans | Radix / shadcn default theme CSS |
| **`PANEL_SPEC.md` & `Build Playbook.md`** | Specified as strict "law" | Blue `#0057FF` (You) / Orange `#E85A0A` (AI) | Inter / DM Mono | Unspecified |
| **`GRAPH_SYSTEM_SPEC.md`** | 3D frosted glass spheres, dual light emission | Cyan `#38bdf8` (User) / Amber `#fb923c` (AI) | Not tokenized | Unspecified |
| **`Brain Vision.md`** | Spatial map across zoom ladder | Persistent 2-party colors; notes cite Cyan/Violet | Not tokenized | 6-channel grammar draft |

---

## 2. Inventory of Visual Decisions

### 2.1 Color Tokens & Palettes

#### `web/src/index.css`
- `--you`: `#0057FF` (Pure high-saturation electric blue)
- `--ai`: `#E85A0A` (Deep red-orange)
- `--bg`: `#faf9f6` (Warm off-white parchment)
- `--panel`: `#f1efe9` (Warm light stone)
- `--border`: `rgba(0, 0, 0, 0.08)`
- `--border-strong`: `rgba(0, 0, 0, 0.15)`
- `--text-primary`: `#1a1a1a`
- `--text-muted`: `#888880`
- `--card-bg`: `#ffffff`

#### `design_pack/playground_obsidian.html` & `playground_3d.html`
- Canvas background: `#141417` (Obsidian near-black)
- Tooltip background: `#090a0f` (Pitch black)
- User entity / photon source: `#38bdf8` (Tailwind Sky 400 - electric cyan)
- AI entity / photon source: `#fb923c` (Tailwind Orange 400 - warm amber)
- Active tether / line: `rgba(255, 255, 255, 0.65–0.75)` / `rgba(255, 255, 255, 0.4)`
- Dormant tether / line: `#334155` / `rgba(148, 163, 184, 0.2)`
- Scrubber rail: `#1e293b`
- Card borders: `rgba(255, 255, 255, 0.1–0.12)`
- Text primary: `#f1f5f9`, `#f8fafc`
- Text secondary: `#94a3b8`, `#cbd5e1`
- Text muted: `#64748b`

#### `AI Chatbot Interface (Copy)/default_shadcn_theme.css`
- Background: `#ffffff` (light), `oklch(0.145 0 0)` (dark)
- Foreground: `oklch(0.145 0 0)` (light), `oklch(0.985 0 0)` (dark)
- Primary: `#030213`
- Border: `rgba(0, 0, 0, 0.1)`
- Radius: `0.625rem`

### 2.2 Typography

- **`web/`**:
  - UI Font: `Inter` via Google Fonts (`300;400;500;600;700`)
  - Label / Numeric Font: `DM Mono` (`300;400;500`)
  - Hierarchy: 11px (chips, meta), 12px (subtitles, secondary), 13px (body small), 14px (primary body), 16px (titles), 20px/24px (headers).
- **`design_pack/`**:
  - Font Stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", monospace, sans-serif`
  - Hierarchy: Overly dense micro-steps (8.5px, 9.5px, 10px, 10.5px, 11px, 11.5px, 12px, 13px, 14px, 15px) with ratio ~1.5:1 across the whole spectrum. Tooltip headers tracked uppercase at 9.5px.

### 2.3 Spacing & Layout Geometry

- **`web/`**:
  - Right-rail Agency Panel: 380px fixed width, flex column, inner card paddings 12px–16px.
  - Chat central container: max-width 768px (`max-w-3xl`), message bubble padding 12px 16px.
  - Left navigation sidebar: collapsible drawer / icon rail.
- **`design_pack/`**:
  - Full-bleed canvas viewport (`100vw x 100vh`).
  - Floating HUD overlays with absolute positioning: top-left bar (`top: 16px; left: 20px`), top-right view switcher (`top: 16px; right: 20px`), bottom-center scrubber (`bottom: 24px; left: 50%; transform: translateX(-50%)`).

### 2.4 Component Inventories

1. **Agency Panel Components (`web/src/components/`)**:
   - `GoalSection`: Thread-collapse tree hierarchy, lit node emphasis, expander chips (`⌄ N more`).
   - `TimelineSection`: Scrubber notches, turn delta bar, decision counter (`N you · M AI`), expandable drawer with requirement bars.
   - `HowSection`: Centaur / Copilot / Autopilot descriptive mode indicators, mode distribution split bar.
   - `InfoPopover`: Popover disclosures explaining mathematical concepts without cluttered UI prose.
2. **Graph View Components (`design_pack/`)**:
   - `CanvasRenderer`: 2D canvas with panning, zooming, and node layout.
   - `RootSphere` & `ChildSpheres`: Frosted spheres with dual internal light sources.
   - `SatelliteAtoms`: Solid requirement beads (3.5px radius) and hollow open question rings (4.5px radius) placed in the upper crown canopy.
   - `TetherLines`: Solid and dashed connection lines clipped to sphere circumferences.
   - `TerminalFocusHalo`: Breathing radial halo on the currently active deliverable.
   - `ScrubberCapsule`: Floating glass capsule with pair notches and playback control.
   - `ObsidianTooltip`: Minimal black card with colored uppercase category tags.

---

## 3. Technical Audit (`ui-craft audit` Diagnostic Scan)

Diagnostic checks run across `web/` and `design_pack/` per `ui-craft/reference/audit.md`:

### 3.1 Audit Health Score

| # | Dimension | Score (0–4) | Key Finding |
|---|---|---|---|
| 1 | **Accessibility (A11y)** | **1 / 4** | Touch targets on scrubber notches and graph beads are 8–10px (violates WCAG 2.2 AA 24px floor); low contrast dormant tethers (0.20 opacity on dark fails 3:1); missing keyboard focus traps and ARIA roles on canvas. |
| 2 | **Performance** | **2 / 4** | Animated `transition: width` triggers layout thrashing in `web/` and `design_pack/`; Three.js / Canvas render loops lack dirty-checking when stationary. |
| 3 | **Responsive Design** | **2 / 4** | Panel assumes fixed desktop layout (380px); canvas HUD overlays clip on narrow mobile viewports (<640px); no compact/comfortable density toggle. |
| 4 | **Theming** | **1 / 4** | Zero unified tokens. `web/` is hardcoded light warm paper; `design_pack/` is hardcoded dark obsidian; party colors differ completely; no dark theme for panel; no light theme for graph. |
| 5 | **Anti-Patterns** | **1 / 4** | Colored glow on dark background in graph prototype; colored side-tab border on card in `web/src/App.tsx`; Inter overused font; flat typography scale. |
| **Total** | | **7 / 20** | **Poor (major overhaul needed — standard pre-v1 baseline)** |

---

## 4. Anti-Patterns Scan (`detect.mjs` Output)

Ran `node ui-craft/scripts/detect.mjs` directly against `web/` and `design_pack/`.

### 4.1 Findings in `web/` (5 issues)
- `web/src/App.tsx:710`: `[side-tab]` — Thick colored border on one side of a card (`borderLeft: '3px solid ...'`). Classic AI tell.
- `web/src/App.tsx:634`: `[layout-transition]` — `transition: width`. Causes layout thrash and jank.
- `web/src/components/TimelineSection.tsx:383`: `[layout-transition]` — `transition: width`. Causes layout thrash.
- `web/src/components/TimelineSection.tsx:433`: `[layout-transition]` — `transition: width`. Causes layout thrash.
- `web/src/index.css:2`: `[overused-font]` — Google Fonts: `Inter`. Default AI styling convergence.

### 4.2 Findings in `design_pack/` (7 issues)
- `design_pack/playground_obsidian.html:234`: `[dark-glow]` — Colored glow (`rgb(56,189,248)`) on dark page. Default "cool AI" look.
- `design_pack/playground_obsidian.html:194`: `[layout-transition]` — `transition: width`. Causes layout thrash.
- `design_pack/playground_obsidian.html:40`: `[flat-type-hierarchy]` — Sizes: 8.5px, 9.5px, 10px, 10.5px, 11px, 11.5px, 12px, 13px (ratio 1.5:1). Font sizes too close together.
- `design_pack/playground_3d.html:261`: `[dark-glow]` — Colored glow (`rgb(56,189,248)`) on dark page.
- `design_pack/playground_3d.html:221`: `[layout-transition]` — `transition: width`. Causes layout thrash.
- `design_pack/playground_3d.html:44`: `[flat-type-hierarchy]` — Sizes: 8.5px to 15px (ratio 1.8:1).
- `design_pack/node_playground_3d.html:42`: `[flat-type-hierarchy]` — Sizes: 10px to 15px (ratio 1.5:1).

---

## 5. The Conflicts List

Every unresolved contradiction in the repository is recorded below. Resolving these is the core work of the D Track programme.

### Conflict 1: Party Colours (Blue/Orange vs Cyan/Amber vs Cyan/Violet) — PRIORITY 1
- **`Build Playbook.md` §5 & `PANEL_SPEC.md` §0**: State as **strict law**:
  $$\text{User / You (Left)} = \text{Blue } (\texttt{\#0057FF}), \quad \text{AI (Right)} = \text{Orange } (\texttt{\#E85A0A})$$
- **`GRAPH_SYSTEM_SPEC.md` Step 2.3 & `design_pack/`**: Hardcoded across all prototypes as:
  $$\text{User} = \text{Cyan / Sky } (\texttt{\#38bdf8}), \quad \text{AI} = \text{Amber / Orange } (\texttt{\#fb923c})$$
- **`Brain Vision.md` research notes**: Mention a third potential candidate pair (Cyan `#00e5ff` and Violet `#b388ff`).
- **Nature of the Conflict**:
  - The graph prototype depends on photon light mixing inside a frosted shell. Blue `#0057FF` is dark and heavy when mixed or blurred; Cyan `#38bdf8` glows cleanly in dark mode.
  - However, in light mode on warm paper (`#faf9f6`), Cyan `#38bdf8` fails WCAG 2.2 AA contrast miserably against light backgrounds (contrast ratio ~2.0:1), whereas Blue `#0057FF` passes easily (contrast ratio >6.5:1).
  - Furthermore, Cyan and Violet fail accessibility under tritanopia (blue-yellow CVD confusion).
  - Neither pair has been evaluated for proportional mixing (50/50, 70/30, 90/10) to verify they do not produce an ugly or muddy midpoint.
- **Resolution Path:** D4.S1 (Colour Foundation) via DDR.

---

### Conflict 2: Theme & Environmental Atmosphere (Warm Paper vs Obsidian Dark vs Stock shadcn)
- **`web/` right-rail panel**: Built in a warm, editorial, physical paper aesthetic (`#faf9f6` background, `#f1efe9` panel, `#1a1a1a` ink text). Feels like a quiet notebook or scientific journal.
- **`design_pack/` graph**: Built in an intense, futuristic obsidian dark space (`#141417` / `#090a0f`, glowing neon spheres, dark glass HUD). Feels like an observatory or planetarium.
- **`AI Chatbot Interface (Copy)/`**: Stock shadcn zinc defaults with no character.
- **Nature of the Conflict**: They cannot sit side-by-side in one application without jarring cognitive dissonance. The design system must define whether the product is dark-first, light-first, or has true multi-theme modes that share semantic tokens.
- **Resolution Path:** D2 (Directions) & D3 (Foundation Architecture / Theme Modes).

---

### Conflict 3: Visual Channel Encoding (Size vs Thickness for Contribution)
- **`GRAPH_SYSTEM_SPEC.md` Step 2.2**: Node radius scales by cumulative ledger mass:
  $$R_{\text{child}} = R_{\text{base}} + \Delta \cdot \left(\frac{M_{\text{child}}}{M_{\text{max}}}\right)$$
  (Visual Channel: $\text{Size} = \text{Contribution}$).
- **`Brain Vision.md` §4**: The working visual grammar states:
  - $\text{Thickness} = \text{Contribution}$
  - $\text{Size} = \text{Significance}$
- **Nature of the Conflict**: Direct clash in the visual language. If node size represents significance (importance/weight of a goal) at the Brain level, using node size for turn-by-turn ledger mass in the graph confuses the semantic zoom ladder.
- **Resolution Path:** D5.S1 (Visual Grammar reconciliation).

---

### Conflict 4: Colored Glow on Dark Background (AI Tell vs Core Design Feature)
- **`ui-craft` detector & `design-rules.md` Absolute Bans**: Explicitly bans colored glow (`box-shadow: 0 0 Xpx color`) on dark pages as one of the most recognizable tells of cheap AI-generated interfaces.
- **`GRAPH_SYSTEM_SPEC.md`**: The dual-light glowing sphere and neon halos are the owner's deliberate artistic metaphor ("photons mixing inside a frosted diffuser").
- **Nature of the Conflict**: The detector flags this as an anti-pattern (A4 settlement). The glow cannot be auto-deleted because it is core to the owner's graph concept, but it must be refined into intentional, physically plausible illumination rather than CSS box-shadow slop.
- **Resolution Path:** Settled in DDR-000d / D5.

---

### Conflict 5: Typographic Hierarchy & Font Selection
- **`web/`**: Uses `Inter` (flagged by `detect.mjs` as an overused default face) and `DM Mono`.
- **`design_pack/`**: Uses generic system sans-serif with a compressed micro-scale (8.5px, 9.5px, 10px, 11px, 12px, 13px) where font sizes are separated by 0.5px–1px increments with no deliberate ratio.
- **Nature of the Conflict**: Neither surface has a distinctive, production-grade typographic system with display, body, numeric, and code roles.
- **Resolution Path:** D4.S2 (Typography Foundation).

---

### Conflict 6: Animation Performance & Layout Thrashing
- **`web/src/components/TimelineSection.tsx`**: Animates `transition: width` on bars.
- **`design_pack/playground_obsidian.html`**: Animates `transition: width` on the scrubber notch bar.
- **Nature of the Conflict**: Animating layout properties (`width`, `height`, `margin`) triggers browser reflow on every frame, causing dropped frames during scrubbing. Both surfaces must be refactored to use hardware-accelerated `transform` and `opacity`.
- **Resolution Path:** D4.S5 (Motion Foundation) & component builds.

---

### Conflict 7: Hit Targets on Small Visual Marks (Fitts's Law & WCAG 2.2 AA)
- **`GRAPH_SYSTEM_SPEC.md`**: Requirement beads are 3.5px radius (7px diameter); scrubber notch markers are 10px diameter.
- **WCAG 2.2 §2.5.8**: Minimum target size is 24 × 24 px; touch surfaces require 44 × 44 px.
- **Nature of the Conflict**: Tiny visual marks without invisible hit-area padding are impossible to click reliably, especially on mobile or during interactive scrubbing.
- **Resolution Path:** Settled in DDR-000e & D4.S7 (Accessibility).

---

## 6. Audit Conclusion & Next Actions

This audit confirms that the design system cannot merely tweak existing CSS. It requires a ground-up foundation programme (the D Track) that:
1. Reconciles the party colors and proves them under CVD and proportion mixing (D4.S1).
2. Establishes a single design direction across both light and dark themes (D2).
3. Defines a W3C DTCG token architecture (`tokens.json`) to eliminate all literal values (D3).
4. Creates checkable lock contracts for every surface before implementation (D0.S5, D6).
