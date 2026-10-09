# Human × AI Co-Creation Design System

Welcome to the Design System programme for the Human × AI Co-Creation Brain.

This repository workstream defines the design tokens, visual data grammar, components, and surfaces bridging the entire Zoom Ladder—from the top-level macroscopic **Brain** down to the **verbatim exchange quote**.

---

## 1. Quick Start for Any AI Agent or Contributor

**Current version: v0.1.0 baseline** (DDR-002). The workspace prototype runs on these tokens.

Building UI? Read, in order:
1. [`AGENT_GUIDE.md`](AGENT_GUIDE.md): the ten rules and copy-paste recipes.
2. [`docs/DESIGN.md`](../DESIGN.md): the generated summary (tokens in frontmatter, six sections).
3. [`docs/PRODUCT.md`](../PRODUCT.md): who it's for, personality, principles.
4. The foundation you need: [architecture](foundations/architecture.md) · [colour](foundations/color.md) · [typography](foundations/typography.md) · [layout](foundations/layout.md) · [motion](foundations/motion.md) · [visual grammar](foundations/dataviz.md) · [accessibility](foundations/accessibility.md) · [voice](foundations/voice.md).
5. [`components/INVENTORY.md`](components/INVENTORY.md) and [`surfaces/README.md`](surfaces/README.md).
6. [`DEBT.md`](DEBT.md) before cleaning anything up.

Continuing the design programme? Also read [`STATE.md`](STATE.md), [`decisions/INDEX.md`](decisions/INDEX.md) with the newest DDRs, and `docs/briefs/D Track Brief.md`.

**See it:** `cd web && npm run workspace`, then open `/design-system.html` (the living gallery) and `/workspace.html` (the app).

Tokens live in `web/src/design-system/tokens/tokens.json`. Rebuild with `cd web && npm run tokens`; check with `npm run tokens:check`.

---

## 2. Standing Operational Rules

- **Co-Creation Loop:** We follow the 8-move loop in `docs/briefs/D Track Brief.md` §2. The AI researches, proposes, renders on real data, and critiques honestly (including the owner's favorite). The owner makes every final decision.
- **Workflow Gates:** One step per response. Provide a preamble before each step. Wait for `start task`, `Decide: <option>`, and `Finish Step`.
- **Render First:** Never describe a visual option without rendering it on real project data under the real-data protocol.
- **Zero Literals:** No raw hex codes, pixel sizes, or arbitrary animation durations outside `tokens.json`.
- **System Decisions vs. Surface Locks:**
  - A **Design Decision Record (DDR)** in `decisions/` records a system decision (token, principle, foundation rule).
  - A **Lock Manifest** (`mockups/<surface>.lock.md`) records a checkable screen/surface contract.
- **Third-Party Research:** Any reference screenshots or competitive captures go strictly into `docs/design-system/research/_local/` (gitignored).

---

## 3. Directory Layout

```
docs/design-system/
├── README.md               ← You are here (orientation)
├── STATE.md                ← Live phase, step, and open decisions tracker
├── AGENT_GUIDE.md          ← Rules for AI agents implementing UI with tokens
├── decisions/              ← DDR-NNN-<slug>.md and INDEX.md
├── DESIGN.body.md          ← Hand-written body of docs/DESIGN.md (frontmatter is generated)
├── DEBT.md                 ← What the baseline left literal, with where each item gets fixed
├── components/INVENTORY.md ← Every shipped component, its tokens and states
├── foundations/            ← architecture, color, typography, layout, motion, dataviz, accessibility, voice
├── surfaces/               ← Surface guides (web, side-panel, widget, 3D, print)
└── research/               ← Audit, scope, benchmarks; _local/ (gitignored)

mockups/                    ← Rendered HTML/CSS/JS mocks served locally
├── INDEX.md                ← Surface ledger (Surface / Concept / Status / File)
├── index.html              ← Mockup navigator
├── _theme.css              ← Generated theme stylesheet
├── _shell.js, SCAFFOLD.md  ← Shared test harness bar (theme, density, CVD filters)
├── captures/               ← Sanitized chat fixtures (c05, etc.)
└── foundations/            ← Visual test specimens (color.html, type.html, etc.)

web/src/design-system/      ← Production implementation
├── tokens/                 ← tokens.json (source) · build.mjs · generated tokens.css / tokens.ts / tokens.numeric.json
├── components/             ← (D6) extracted React components; today they live in web/src/workspace/
└── gallery/                ← (D8) living reference route
```
