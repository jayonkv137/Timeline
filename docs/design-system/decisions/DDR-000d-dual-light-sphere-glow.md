# DDR-000d: Dual-Light Sphere Glow Policy (Settlement A4)

- **Status:** Ratified
- **Date:** 2026-10-08
- **Decider:** Owner (via D Track Brief §5 Settlement A4)
- **Phase / Step:** D0.S3
- **Affects:** Graph View, Detector Rules, Visual Language

---

## 1. Context
`ui-craft` and `design-rules.md` explicitly flag colored glow (`box-shadow: 0 0 Xpx color`) on dark backgrounds as an anti-pattern and a tell of cheap AI-generated UI.
However, the owner's graph specification (`GRAPH_SYSTEM_SPEC.md` Step 2.3) relies on frosted spheres with internal dual point-lights (User Cyan and AI Amber mixing photons to create a white core and outer energy aura).

## 2. Decision
1. The detector (`detect.mjs`) will continue to report `[dark-glow]` findings as diagnostic awareness.
2. The glow is **not** auto-fixed or blindly removed.
3. In Phase D5 (Visual Grammar across Zoom Ladder), the owner explicitly decides whether the glow stays, evolves into physically plausible shader lighting/scattering, or is replaced by pure geometry. Until D5, the frosted internal lighting remains an intentional design feature.
