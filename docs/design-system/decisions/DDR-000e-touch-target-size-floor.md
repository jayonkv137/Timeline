# DDR-000e: Touch Target Size Floor (Settlement A5)

- **Status:** Ratified
- **Date:** 2026-10-08
- **Decider:** Owner (via D Track Brief §5 Settlement A5)
- **Phase / Step:** D0.S3
- **Affects:** Accessibility, Scrubber, Graph Beads

---

## 1. Context
`ui-craft audit` flags any interactive element smaller than 44 × 44 px. However, WCAG 2.2 §2.5.8 sets a legal floor of 24 × 24 px for pointer inputs, and dense data visualizations (like timeline scrubber notches and satellite graph beads) cannot visually occupy 44px without destroying visual information hierarchy.

## 2. Decision
1. **Desktop & Pointer Targets:** A strict floor of **24 × 24 px** applies to all interactive elements. Small visual marks (e.g., 3.5px beads, 10px scrubber markers) must implement invisible padding/pseudo-element hit areas of at least 24 × 24 px.
2. **Touch Surfaces:** Touch devices and mobile viewports enforce the full **44 × 44 px** target size.
