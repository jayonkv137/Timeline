# DDR-000: Deliberate AI Co-Creation & Pre-v1 Baseline Ground Truth

- **Status:** Ratified
- **Date:** 2026-10-08
- **Decider:** Owner (via D Track Brief §5/§13 and D0 Charter)
- **Proposer / Agent:** DESIGN SYSTEM (Antigravity · Gemini)
- **Phase / Step:** D0.S3
- **Affects:** Entire Design System workstream, governance model, mock precedence

---

## 1. Context & Problem Statement
In earlier project tracks, the `DESIGN` role had a strictly passive charter (`docs/Design Support Charter.md`): prepare raw data packs without proposing layouts or representations, because the owner designed by hand in Figma.

Furthermore, standard UI tools (such as `ui-craft`) assume by default that the "shipped application" in `web/` is chrome ground truth for all future screens, and that an AI should not propose artistic or spatial designs.

This caused a structural block:
1. `web/` is currently an unpolished prototype with hardcoded styles, not a finished production design.
2. The owner specifically initiated the **D Track Programme** (`docs/briefs/D Track Brief.md`) as a parallel workstream to actively co-create a world-class design system alongside an AI.

---

## 2. Decision & Owner Rationale
1. **Deliberate Co-Creation Charter:** The owner explicitly establishes the **DESIGN SYSTEM** role (`docs/briefs/D Track Brief.md` §13) to propose, render, explore, critique, and document design solutions through the 8-move co-creation loop. The owner retains absolute decision authority on every gate; the AI is expected to provide honest critique and high-craft proposals.
2. **Pre-v1 Baseline Precedence:** The current frontend (`web/` and `design_pack/`) is classified as **pre-v1 exploration**. It is **not** ground truth. The design system programme starts from first principles to unify the visual language. Once `ds-1.0` releases and is integrated into `web/`, the shipped app becomes ground truth as standard workflows expect.

---

## 3. Consequences & Downstream Impact
- The DESIGN SYSTEM role operates under the governance rules of `docs/briefs/D Track Brief.md`.
- No existing stylesheet or prototype in `web/` is sacred or immune to replacement.
- Every system decision is captured in a Design Decision Record (DDR); every rendered surface is governed by a Lock Manifest (`mockups/<surface>.lock.md`).
