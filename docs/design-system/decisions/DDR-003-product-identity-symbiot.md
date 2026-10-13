# DDR-003: Product Identity: the Name "Symbiot" and the Two-Ring Brain Mark

- **Status:** Accepted (name) · Proposed (mark, awaiting the owner's review of the rendered options)
- **Date:** 2026-10-13
- **Decider:** Owner (verbatim quote: _"change the logo and name of the app from cotrace to symbiot please and also like make the logo like a mix of the rings and a brain in between like a really good logo please"_)
- **Proposer / Agent:** DESIGN SYSTEM (Claude Code · Claude Opus 5.5)
- **Phase / Step:** D2 (planned DDR-003, "Product Identity & Head Motif Mark")
- **Affects:** Workspace rail mark, sidebar wordmark, page title and favicon, course documentation

---

## 1. Context & Problem Statement
The app showed "COTRACE", the name of the research method it is built on, as its product name. The owner presents it as **Symbiot**. The old mark was two overlapping CSS rings (human sky, AI ember) with nothing between them.

## 2. Constraints & Principles Checked
- **DDR-001:** "hybrid human+ai or symbiotic", "mix of both organism and machine", "the graph node structure and the brain stuff is the core design philosophy".
- **Party colours:** only the two party colours carry meaning (human `--color-party-human-solid`, AI `--color-party-ai-solid`).
- **Scale:** the mark must read at 16 px (favicon) and 26 px (rail), on both dark and light grounds.
- **Scope of the rename:** visible product text only. `./cotrace`, `~/Cotrace`, `$COTRACE_HOME`, `cotrace:*` events and the CoTrace method citation stay as they are.

## 3. Options Explored & Rendered
All options were rendered at 16, 24, 32, 56 and 128 px on dark and light. The sheets are in `docs/symbiot/logo/options-round1..4.png`.

### Option A: the overlap is the brain
- **Description:** two rings; their lens-shaped overlap is filled as a top-view brain.
- **Pros:** the most conceptual. The shared region *is* the shared mind.
- **Cons / Risks:** the lens is narrow, so the brain reads as a spine or a seed. It is busy at small sizes.

### Option E: a brain in front, rings interlocked behind it (chosen, final E12)
- **Description:** a lobed top-view brain sits between two interlocking rings. The rings pass behind it with a thin knockout halo, cross clearly above and below it, and interlock like chain links: AI over at the top, human over at the bottom.
- **Pros:** the brain is unmistakable at every size. The rings stay rings. The interlock says "bound together", not just "side by side".
- **Cons / Risks:** less abstract than A. Earlier passes (E4) crossed the rings at the edge of the halo and left slivers at large sizes. E12 fixes this with larger rings.

## 4. Decision & Owner Rationale
> _"change the logo and name of the app from cotrace to symbiot please and also like make the logo like a mix of the rings and a brain in between like a really good logo please"_

**Rationale:** the owner asked for the rings with a brain *between* them. Option E is the literal and most legible answer. The name change is the owner's decision. The specific mark (E12) is the agent's proposal, shipped so the course screenshots show it, and stays open for the owner to swap for any rendered option.

## 5. Consequences & Implementation
- **Component:** `web/src/workspace/SymbiotMark.tsx`. The rings use `var(--human)` and `var(--ai)`, and the brain uses `currentColor`.
- **Surfaces:**
  - the rail mark (`.brand-symbol`, 34 × 26 px)
  - the sidebar wordmark "SYMBIOT"
  - the "SYMBIOT LIBRARY" eyebrow
  - the offline notice
  - the `<title>` "Symbiot · Workspace" and the favicon in `web/workspace.html`
- **Assets:** `docs/symbiot/logo/`:
  - `symbiot-mark-on-dark.svg` and `symbiot-mark-on-light.svg` (light uses the light-theme party colours)
  - `symbiot-favicon.svg`
  - `symbiot-lockup.png`
- **Tests:** `tests/test_cotrace_cli.py` now expects the new title.
- **Not changed:**
  - CLI, library path, env vars, event names, internal identifiers
  - dev-only pages (`brain-lab.html`, `design-system.html`)
