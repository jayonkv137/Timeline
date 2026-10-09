# Component inventory (v0.1 baseline)

Every component the workspace prototype ships, where it lives, which tokens it uses, and its state coverage. The status column says whether the component is extracted into `web/src/design-system/components/` (none are yet; they all live in `web/src/workspace/`). Extraction happens in D6, one batch at a time, each through `ui-craft lock` → `build`.

States key: D default · H hover · F focus · A active/selected · X disabled · L loading · E empty · R error.

## Shell (B4)

| Component | Class / file | Key tokens | States | Notes |
|---|---|---|---|---|
| Workspace grid | `.cotrace-workspace`, `.content-grid` | `workspace.*` widths, `bg.app` | — | 46 / 226 / 1fr / 342px; responsive at 1200, 1000, 760 |
| Activity rail | `.activity-rail` | `bg.app`, `border.subtle` | D H A | Brand mark, history, Brain, search |
| History sidebar | `.history-panel`, `.chat-list`, `.history-section` | `surface.panel`, `text.muted` | D H A E | Search, new conversation, conversation rows with unread dot |
| Tab strip | `.tab-strip`, `.workspace-tab`, `.close-tab`, `.new-tab` | `surface.panel`, `border.default`, `type.label` | D H A F | Permanent Brain tab first |
| Context bar | `.context-bar`, `.breadcrumbs`, `.context-actions` | `type.ui`, `text.muted` | D H F | Locate in Brain, panel toggle |
| Status bar | `.status-bar`, `.status-dot`, `.status-divider` | `type.caption`, `bg.app` | D | Was 9px; now 10px floor |
| Toast (workspace) | `.toast` | `surface.overlay`, `elevation.4` | D | |
| Expanded overlay | `.expanded-overlay`, `.expanded-bar` | `bg.graph` | D F | Dialog; Escape closes |
| Mobile menu | `.mobile-menu` | — | D | ≤ 760px |

## Conversation (B2)

| Component | Class / file | Key tokens | States | Notes |
|---|---|---|---|---|
| Exchange marker | `.exchange-marker` | `type.overline`, `border.subtle` | D A | "PAIR 07" divider; `.viewed` when graph pair |
| User message | `.message.human` | `surface.raised`, `radius.lg`, `type.body` | D H | Copy button on hover |
| Assistant message | `.message.ai`, `.message-text`, `.ai-emblem` | `type.body`, `text.primary` | D | Prose on canvas; headings, code |
| Author marker | `.human`, `.ai` | `party.*` | D | Previously clay and blue; now party tokens |
| Composer | `.composer-dock`, `.composer`, `.send-button`, `.composer-hint` | `surface.panel`, `radius.2xl`, `elevation.1` | D F X L | "Chat backend not connected" state |
| Back to latest | `.back-latest` | `surface.overlay` | D H | Shown in history mode |
| Empty conversation | `.new-conversation-empty`, `.empty-logo` | `type.display` | E | |
| Attachments note | `.attachments-note` | `text.muted` | D | Names only |

## Conversation map (B3), in `LocalGraph.tsx` and `obsidian-graph.css`

| Component | Drawn by | Key tokens | States | Notes |
|---|---|---|---|---|
| Graph stage | canvas | `bg.graph`, `.theme-dark` | D E | Physics, pan, zoom, drag |
| Outcome sphere + share ring | canvas | `graph.node.*`, `graph.share-ring.*` | D H A dormant focus | DDR-006 |
| Root anchor | canvas | `graph.node.root-radius` | D | Pinned |
| Beads | canvas | `graph.bead.*`, party | D H dormant | 24px hit |
| Links | canvas | `graph.link.*` | active dormant | Clip at the bead orbit |
| Labels | canvas (screen space) | `graph.node.label*` | D dormant | Wrap 165 / 112 |
| Scrubber capsule | `.og-capsule`, `.og-notch`, `.og-nav` | `scrubber.*`, `elevation.4` | D H F X A | Notches are buttons |
| Pair badge | `.og-badge` | `type.caption` | D | Genesis / Born / Reactivated / Surge |
| Legend | `.og-legend` | `type.caption`, party | D | Six entries; two lines in compact |
| Tooltip | `.og-tooltip` | `surface.overlay`, `type.overline` | D | Hover only (canvas gap) |
| Chat-jump toast | `.og-toast` | `surface.overlay`, party | D | 5s auto-dismiss |
| Corner tools | `.og-tool` | `radius.md` | D H F | Recenter, expand |

## Brain (B3 / G4), in `Brain.tsx`, `brain-engine.js`, `brain-frame.html`

| Component | Key tokens | States | Notes |
|---|---|---|---|
| 3D brain stage | `bg.brain`, `brain.*` numeric | D L | Literal colours inside the bundled renderer (debt) |
| Brain inspector | `surface.panel` | D E A | Selected conversation preview + its graph |
| Conversation list (accessible alternative) | `type.ui` | D H A | |

## Primitives (B1): implicit today

Icon button (`.icon-button`), text button (`.text-button`), search box (`.search-box`), eyebrow label (`.eyebrow`), dots (`.open-dot`, `.local-dot`, `.model-dot`). They are styled in `workspace.css` but not yet components with their own API. They are the first extraction batch.
