# DDR-000b: Pre-v1 Baseline Precedence (Settlement A2)

- **Status:** Ratified
- **Date:** 2026-10-08
- **Decider:** Owner (via D Track Brief §5 Settlement A2)
- **Phase / Step:** D0.S3
- **Affects:** Mock Precedence, UI Architecture

---

## 1. Context
`ui-craft` enforces a rule that the shipped application wins over mock scaffolds during fidelity checks. However, today's `web/` panel is an unreleased experimental prototype created during Phase 0–1, and `design_pack/` is an exploratory canvas playground.

## 2. Decision
The system is formally declared **pre-v1**. Existing UI code is reference input, not ground truth. The design system programme establishes the unified design standard from first principles. When `ds-1.0` releases and is integrated into `web/`, the application becomes the official ground truth for subsequent surfaces.
