# Agency Panel — Interaction Specification (v1)
### How the whole system behaves: every interaction, state, and transition

**Status:** v1 — the third build document, completing the set: COTRACE_PIPELINE_SPEC v5
(backend), PANEL_SPEC v2.0 (what renders), and this document (how it behaves). Sources:
the Figma Make prototype ("AI Chatbot Interface"), its full build conversation, the
prototype screenshots, and the interaction decisions confirmed during design review. Where
this document and older prototype behavior disagree, this document wins (differences are
flagged inline as SUPERSEDED).

---

## 0. The one interaction model everything follows

**The pair (P1, P2, …) is the universal coordinate.** Every interactive element in the
product either (a) *sets* the viewed pair, or (b) *renders as of* the viewed pair. There
are no other interaction primitives. Two global states:

| State | Meaning | Indicator (ONE place only) |
|---|---|---|
| **LIVE** | viewed pair = latest pair; panel updates as new turns complete | Green `LIVE` pill in the rail's top status strip |
| **HISTORY** | viewed pair < latest; panel frozen at that moment | Amber `● VIEWING Pn · HISTORY` in the top status strip, plus position counter `n/N` |

Rule: live/history state renders **once**, in the top strip — never repeated per-row,
per-section, or per-message (v1.1 panel decision).

---

## 1. Layout regions & responsive behavior (from the prototype)

Three regions: **left sidebar** (conversation list) · **center chat** · **right rail**
(the agency panel).

- **Desktop (≥ 768px):** sidebar static and always visible; rail always visible.
- **Mobile (< 768px):** sidebar hidden off-screen; slides in as an overlay via hamburger;
  tap-outside or ✕ closes. A top bar carries current chat title + menu + new-chat. Spacing,
  padding, and bubble max-widths tighten. Keyboard hint hidden.
- **Rail on mobile:** not yet designed — open item (§8). The rail is desktop-only for the
  first build (lineage: it began as the VS-Code-minimap experiment, desktop-only by
  design; the 100px minimap sizing rule is SUPERSEDED by the full rail, ~360px).

**Chat empty state:** input box vertically + horizontally centered with icon and prompt
above. **Active conversation:** messages scroll above; input anchors at the bottom.

---

## 2. Chat area interactions (from the prototype, kept as built)

| Interaction | Behavior |
|---|---|
| Send | Enter sends; Shift+Enter = newline; send button activates only when text present |
| Input | Auto-growing textarea |
| AI response pending | Typing indicator with animated dots in the thread |
| Attachments | Render inside the sending user's bubble |
| Pair badges | Each user message carries its `Pn` chip — the visible half of the coordinate system |
| Viewed-pair highlight | Both bubbles of the viewed pair get the emphasis border; all other messages render normally |
| `● Back to latest ↓` pill | Appears floating above the input whenever state = HISTORY (or chat is scrolled away from the end); clicking returns to LIVE and scrolls to the newest exchange |

---

## 3. Setting the viewed pair — every scrub source

All of these do the same one thing (set viewed pair → whole system re-renders as of it):

1. **Timeline row click** — scrub to that pair; chat scrolls to that exchange; both
   bubbles highlight.
2. **Timeline chevron / drawer expand** — expanding IS scrubbing (a stronger form of the
   same intent). Accordion: one drawer open at a time; collapsing does not change the
   viewed pair.
3. **Goal-node click** — scrub to the pair where that goal **first appeared**
   (first-appearance rule, settled in design review). Hover shows `Pn · where this
   started`. Nodes must carry click signifiers (hover state + cursor) — the
   looks-like-static-text failure was an identified defect, not a choice.
4. **Decisions "latest example" tap** — scrub to that requirement's creation pair.
5. **`Back to latest`** — scrub to the newest pair; state returns to LIVE.

**Scroll↔scrub is one-directional:** scrubbing scrolls the chat; merely scrolling the chat
does NOT change the viewed pair (reading back is not a statement of intent). The Back pill
covers the return path.

---

## 4. The live-turn lifecycle (the processing choreography, from the prototype build)

When the user sends a message in LIVE state:

```
1. User bubble appears immediately (with its new Pn badge and any attachments).
2. Chat title generates/updates in the left sidebar (first turns only) — and the same
   shortened title appears at the rail's top. The title is EDITABLE (it is R0, the goal
   tree's root; editing it renames the root node).
3. AI typing indicator appears in the thread.
4. The rail enters its per-turn LOADING state: a loading treatment below the rail header
   signals "the panel is processing this turn too" — the pipeline (1a→1b→1c→2→3→Stage 4)
   runs after the AI reply lands, so the rail's update INTENTIONALLY lags the chat.
   Sections keep showing the previous pair's values while loading; they never blank.
5. Pipeline completes → sections update atomically: new timeline row appears (top-strip
   counter increments), Direction/Decisions/HOW re-render, goal section updates only if
   the lit node changed.
```

**If the user is in HISTORY when a new pair completes:** nothing yanks them. The new row
appears in the timeline, the counter's denominator increments (`2/7`), the Back pill stays
available. Auto-jumping a reader is forbidden.

---

## 5. Rail interactions, section by section

### 5.1 Goal (thread-collapse)
- Default: the fixed 3-node view (+ chip when nodes are hidden) per PANEL_SPEC §1.
- **Chip tap** → progressive reveal (next hidden segment; count decreases) — never an
  all-at-once dump. Revealed off-path nodes carry their own `⌄ N` chips.
- **"Show less"** → collapse to default in one tap.
- Section scrolls internally only while expanded; the default view never scrolls.
- Node click → scrub (first-appearance rule, §3.3).
- SUPERSEDED from prototype: "MAIN GOAL"/"CURRENT SUB-GOAL" labels (removed); the
  breadcrumb experiment (vertical tree restored); dead non-clickable `⋯` (every chip is
  interactive by definition now).

### 5.2 Direction / Decisions / HOW
Passive displays; re-render at the viewed pair. The single exception: the Decisions
latest-example is tappable (§3.4).

### 5.3 Timeline
- Collapsed row: click = scrub; chevron = expand (accordion).
- Hover on a collapsed row: tooltip card `Pn · <summary line>` (the R-SUM text — the
  prototype's "Shaped by: You" tooltip wording is SUPERSEDED by the R-SUM line).
- Drawer: renders that exchange's requirement rows + open-question rings (per-turn
  scoped). Requirement-row tap → **level-2 expansion** (interaction slot reserved; its
  internal design is the deferred item — but the tap target and its data contract exist
  now).
- Empty exchange drawer: single line "execution only — no requirements touched."

---

## 6. Sidebar interactions (from the prototype, kept)

Conversation list with timestamps · `+ New` chat button · delete-on-hover per chat ·
switching chats swaps the entire coordinate space (each chat has its own pairs, ledger,
tree, and rail state; viewed pair is remembered per chat within a session).

---

## 7. State inventory (per component)

| Component | States |
|---|---|
| Top status strip | LIVE · VIEWING Pn · HISTORY (+ n/N counter) |
| Rail (whole) | ready · per-turn loading (previous values shown, loading treatment on) · empty (new chat: sections render their zero states, no fake data) |
| Goal section | default (3-node) · partially expanded · fully expanded |
| Timeline row | collapsed · hovered (tooltip) · expanded (drawer) · viewed (left-edge bar + tint) |
| Drawer | populated · execution-only |
| Chat message | normal · viewed-pair highlight |
| Input | empty (send disabled) · typed (send active) · centered (empty chat) · anchored (active chat) |
| Sidebar (mobile) | hidden · overlay-open |

## 8. Open items
1. **Rail on mobile** — undesigned; desktop-only for the first build.
2. **Level-2 expansion internals** — tap target and data contract fixed; content design
   deferred (matches PANEL_SPEC §7).
3. **Legend/onboarding** — the design-review verdict stands (a first-timer meets unlabeled
   color/glyph encodings); a one-time legend or intro tooltip pass is required before any
   user test, not before the first build.
4. **Chat-switch while loading** — behavior when the user switches chats mid-pipeline-run
   (cancel vs. background-complete) is undecided; propose background-complete.
