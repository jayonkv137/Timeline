# SCOPE.md — Surfaces, Zoom Ladder & Component Taxonomy

**Date:** 2026-10-08  
**Phase/Step:** D0.S2 (Phase D0: Charter, audit and setup · Step 2: Scope)  
**Author:** DESIGN SYSTEM (Antigravity · Gemini)  
**References:** `docs/briefs/D Track Brief.md` §11, `docs/Brain Vision.md` §2/§5/§9, `docs/PANEL_SPEC.md`, `design_pack/GRAPH_SYSTEM_SPEC.md`, `docs/Interaction Spec.md`

---

## 1. Executive Scope

The Design System does not merely style a single web page. It must govern **6 physical delivery surfaces**, bridge **5 levels of the semantic zoom ladder**, and supply a library of **~35 token-governed components** across 4 build batches.

Every token and component designed in this programme must function consistently from the top-level **Human × AI Co-Creation Brain** down to the **verbatim chat quote**.

---

## 2. Target Surfaces & Environmental Constraints

| Surface | Timeline Target | Viewport & Layout Constraints | Theme & Styling Constraints | Zoom Levels Displayed |
|---|---|---|---|---|
| **1. Web Application** | Now (G1 / Phase C) | Full desktop workspace (1280px+), multi-column layout (Left sidebar, central chat/graph canvas, 380px right-rail Agency Panel). | Supports Light, Dark, and High-Contrast modes. Comfortable and compact density. | All 5 levels (Brain, Project, Chat, Pair, Source). |
| **2. Browser Side Panel** | G3 (Chrome/Edge Extension) | Constrained width: **360px – 420px**. High density. Must fit alongside claude.ai / chatgpt.com. | Host-independent party colours. Host-adapted surface neutrals. Compact density default. | Chat (Outcome Map), Pair, and Source. "Open in Brain" jumps to Web. |
| **3. In-Chat Widget** | Later (MCP Apps / ChatGPT Canvas) | Sandboxed `<iframe>` inside third-party chat host. Width variable (400px–800px). | Must follow host ground/text themes; strictly **no external font downloads** (system-safe or SVG rendered text). | Chat (Map) and Pair summary. |
| **4. 3D Spatial Head** | G4 (Three.js / WebGL) | Full-screen interactive canvas or 3D viewport widget. 60fps rendering required. | Consumes `tokens.numeric.json` for camera, lighting, material translucency, and spatial depth. | Brain and Project clusters. |
| **5. Print & Static Pack** | Now / Ongoing (A3, PDF) | Fixed physical aspect ratios (A3 / A4 portrait & landscape). Static vector / PDF export. | **Ink-safe** color palette; no pure black floods; high-contrast lines; no glow/animations. | Chat storyline, Pair transitions, Session summary. |
| **6. Mobile Web / Touch** | Roadmap | Mobile viewports (375px–430px). Single-column stacked sheets. | Touch target floor: **44 × 44 px** minimum. Swipe gesture navigation for pair scrubbing. | Chat trajectory, Pair drawer, Source transcript. |

---

## 3. The 5-Level Zoom Ladder

The design system models collaboration as a single continuous spatial structure, not disconnected screens:

```
Level 1: BRAIN  (300+ chats, clusters, macro human/AI balance)
   │
   ▼
Level 2: PROJECT / GOAL  (Cluster of related chats, overarching objectives)
   │
   ▼
Level 3: CHAT TRAJECTORY & MAP  (Evolution through time, root goal + outcomes tree)
   │
   ▼
Level 4: PAIR TRANSITION & DRAWER  (Single exchange P, delta Δ, requirement bars)
   │
   ▼
Level 5: SOURCE TRANSCRIPT  (Original user message + AI reply, verbatim quote)
```

1. **Level 1 — Brain:**
   - *Questions answered:* "What have Human and AI created together? Where did I drive vs where did AI lead?"
   - *Visuals:* Macro regions/clusters, global Human × AI influence proportions, cross-chat connection threads, subtle head silhouette boundary.
2. **Level 2 — Project / Goal:**
   - *Questions answered:* "What deliverables make up this project?"
   - *Visuals:* Sub-goals, chat nodes grouped by common domain, handoff links.
3. **Level 3 — Chat Trajectory & Outcome Map:**
   - *Questions answered:* "How did this line of thinking evolve? What were the main outcomes?"
   - *Visuals:* The outcome tree (root node + child nodes), tether lines, satellite atom crowns, and the timeline scrubber.
4. **Level 4 — Pair Transition & Drawer:**
   - *Questions answered:* "What changed in this exact turn, and who shaped it?"
   - *Visuals:* State before $\rightarrow$ turn $\rightarrow$ state after. Direction bar odometer, decision delta counters, requirement progress bars, open question rings.
5. **Level 5 — Source Transcript:**
   - *Questions answered:* "What were the exact words spoken?"
   - *Visuals:* Chat bubbles with verbatim evidence quote highlighting, creation turn tags (`U(1,2)`), and provenance badges.

---

## 4. Master Component Taxonomy

The component library is organized into four delivery batches:

### Batch B1: Foundational Primitives
Everyday UI controls that all screens inherit:
- **Button:** Primary, secondary, ghost, destructive, icon-only.
- **Icon Button:** Standardized 24px/32px/40px touch targets with accessible tooltips.
- **Pill & Chip:** Category badges, pair indicators (`@ P3`), provenance tags (`User`, `AI`).
- **Tooltip:** High-contrast floating cards, zero flicker, directional arrows.
- **Popover & Disclosure:** Floating mathematical explanations (`InfoPopover`), section help.
- **Tabs & Segmented Controls:** Surface switchers (Brain / Chat / Graph / Pair).
- **Toggle & Switch:** Density (Comfortable / Compact), Theme (Light / Dark).
- **Text Input & Search:** Chat filter, search in sidebar, prompt input.
- **Keyboard Hint (`kbd`):** Shortcut visualizers (`← / →` for scrubbing, `Space` for play).
- **Divider & Separator:** Hairline structural borders respecting theme contrast.
- **Skeleton / Shimmer:** Content loading placeholders.

### Batch B2: Chat & Agency Panel Components
The right-rail analytical panel and conversation transcript:
- **Message Bubble:** User turn, AI turn, streaming state, typing indicator, quote highlight.
- **Panel Status Strip:** Top status bar ("VIEWING P2 · HISTORY" / "LIVE").
- **Back-to-Latest Pill:** Floating pill alerting user to newer turns while scrubbing history.
- **Goal View (Thread-Collapse Tree):** Main goal, hidden segment chip (`⌄ N more`), lit current goal.
- **Direction Bar:** Running odometer split bar with percentage readouts (`59% You · 41% AI`).
- **Decisions Counter:** Countable agency ledger (`9 you · 4 AI`).
- **Timeline Row & Drawer:** Accordion row per exchange, drawer with requirement delta bars.
- **Mode Indicator (HOW Section):** Centaur / Copilot / Autopilot descriptive status and distribution bar.

### Batch B3: Graph Data-Viz Atoms
The 2D/3D spatial visualization components:
- **Root Goal Sphere:** Origin anchor beacon, prominent size and permanent label visibility.
- **Child Outcome Spheres:** Frosted translucent spheres scaling with ledger mass.
- **Satellite Requirement Bead:** Solid circular atom (3.5px radius) in upper crown canopy.
- **Satellite Open Question Ring:** Hollow pulsing ring (4.5px radius) awaiting resolution.
- **Resolved Question Bullseye:** Transitioned state when user answers an open slot.
- **Tether Lines:** Solid parent-child lines (clipped to sphere edge), dashed relational cross-links.
- **Terminal Focus Halo:** Breathing radial beacon highlighting the latest active deliverable.
- **Scrubber Capsule:** Floating glass playback bar with notch markers, tag labels, and play/pause controls.
- **Graph Legend:** Minimal bottom indicator showing party dots and tether line samples.
- **Obsidian Graph Tooltip:** Deep-black card with uppercase tracked accent tags.

### Batch B4: Workspace Shells & Global States
The container application framing the experience:
- **Workspace Shell:** Multi-tab layout (Brain tab, individual Chat tabs, collapsible Left Sidebar, Right analytical rail).
- **Side Panel Shell:** Ultra-compact 380px extension frame for claude.ai / chatgpt.com.
- **Empty States:** 1-pair chats, zero-requirement chats, no results found.
- **Quiet Pair State:** Turn with execution only and zero ledger activity.
- **Halted / Engine Error State:** Warning banner when an invariant halts pipeline processing.
- **Print / PDF Sheet Frame:** High-resolution export frame with metadata block.

---

## 5. Priority Delivery Roadmap

```
Phase D0.S5 ──► Lock Graph View v0 (mockups/graph-view.lock.md) ──► HANDOFF to APP for G1
Phase D1    ──► Brand Personality & Principles (PRODUCT.md + Personas via `init`)
Phase D2    ──► 3 Divergent Visual Directions (Paper vs Obsidian vs 3rd World)
Phase D3    ──► DTCG Token Architecture (tokens.json, tokens.css, build.mjs)
Phase D4    ──► Foundations (Colour, Typography, Space, Depth, Motion, A11y)
Phase D5    ──► Data-Viz Grammar (Reconciling Size vs Thickness, Glow, Zoom Semantics)
Phase D6    ──► Component Library Builds (Batches B1, B2, B3, B4 into web/src/design-system/)
Phase D7    ──► Interaction Patterns (Live streaming, scrubbing, transitions)
Phase D8    ──► Documentation, Gallery & Release `ds-1.0`
```

### Critical Path Gate
- **D0.S5 Graph View v0 Lock:** Must freeze `graph-view.lock.md` and `graph-view.behavior.md` using the owner's existing prototype + G1 spec fixes. This allows the APP role to begin G1.S6 on fallback tokens without waiting for the full D-Track foundation.
