# Surfaces: one system, every place COTRACE appears

How each surface in `docs/Brain Vision.md` §9 and `docs/ROADMAP.md` uses this foundation. Everything a surface needs is either in v0.1 or reserved as a planned token, so building it never starts with new colours.

| Surface | Zoom tiers | Theme | Density | Tokens it relies on | Ready in v0.1? | Still to add |
|---|---|---|---|---|---|---|
| **Web workspace** (`web/workspace.html`) | brain, chat, pair, source | dark (light provisional) | comfortable | all semantic + graph, scrubber, workspace | **Yes**, running on tokens | Component extraction (D6) |
| **Graph view** (right panel and expanded) | chat | `.theme-dark` stage | comfortable / compact by width | `component.graph.*`, `component.scrubber.*`, party | **Yes** | Keyboard mirror list; provisional live-tier style |
| **Brain tab** (3D) | brain, project | `.theme-dark` stage | — | `tokens.numeric.json`: `bg.brain`, `brain.*`, party | Partly: tokens exist, renderer still literal | Feed numeric tokens into `brain-engine.js` |
| **Browser extension side panel** (claude.ai, chatgpt.com) | chat, pair | own dark stage; never follows the host page's colours | compact (360–420px) | `breakpoint.side-panel-*`, graph compact rules (scale ≥ 0.72, label wrap 112, stacked legend) | Mostly: graph compact mode exists | `data-density="compact"` tokens, 44px touch targets, onboarding and consent patterns (D7) |
| **In-chat widget** (MCP Apps in Claude or ChatGPT) | chat | host decides `bg` and `text`; party colours fixed | compact | `tokens.css` inlined (no remote fonts), party, graph | Planned | Host-adaptation token mapping; size budget |
| **Claude Code / Codex session view** | chat, pair | dark | comfortable | same as workspace | Yes (same app) | Tool-call atom kinds (new bead kind, D5) |
| **Print / design pack (A3)** | chat (storyline), pair | light + print overrides | comfortable | light mode, `type.*` | Planned | `data-theme="print"`: ink-safe party colours |
| **Marketing site, slides** | — | either | spacious | brand subset of `DESIGN.md` | Planned | Display type decisions (D2.S5 identity) |
| **Mobile** | brain, chat | dark | comfortable | `tokens.numeric.json` → native generators | Planned | Add Swift/Kotlin outputs to `build.mjs` |

## Rules that hold on every surface

1. Party colours never follow a host theme.
2. Stages (graph, brain) keep their own dark ground.
3. A surface may drop zoom tiers but never change what a channel means (grammar in `foundations/dataviz.md`).
4. Every mark keeps a route to its source exchange, even if on that surface the route opens the web app.
