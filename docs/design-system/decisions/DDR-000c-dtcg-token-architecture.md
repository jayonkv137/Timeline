# DDR-000c: Three-Tier DTCG Token Architecture (Settlement A3)

- **Status:** Ratified
- **Date:** 2026-10-08
- **Decider:** Owner (via D Track Brief §5 Settlement A3)
- **Phase / Step:** D0.S3
- **Affects:** Tokens, Build Pipeline, `DESIGN.md`

---

## 1. Context
Standard skill instructions assume a flat 6-section `DESIGN.md` file holding direct token definitions. However, our system must power 2D Web, 3D WebGL (numeric values), browser extensions, and multiple themes (light, dark, high-contrast, print) across the zoom ladder.

## 2. Decision
We adopt the **W3C Design Tokens Community Group (DTCG)** standard:
1. `web/src/design-system/tokens/tokens.json` is the **single source of truth**.
2. A lightweight generator script (`build.mjs`) builds all targets from `tokens.json`:
   - `tokens.css` (CSS custom properties for web and side-panel)
   - `tokens.ts` (strongly-typed tokens for React and canvas)
   - `tokens.numeric.json` (raw floats for Three.js, WebGL, and the 3D head)
   - `DESIGN.md` frontmatter (agent-readable token summary)
3. `DESIGN.md` serves as the concise documentation read by AI agents; detailed foundation theory lives in `docs/design-system/foundations/`.
