# Frozen Behavior Ledger: `graph-view` (v0)

- **Surface:** `graph-view`
- **Companion Lock:** `mockups/graph-view.lock.md`
- **Status:** Frozen
- **Date:** 2026-10-08
- **Author:** DESIGN SYSTEM (Antigravity · Gemini)
- **Target Consumer:** APP role (`web/src/graph/`) for Phase G1.S6

---

## Story 1: Canvas Pan & Zoom Navigation

1. **Mouse Drag / Pan:**
   - Mousedown on canvas background initiates panning (`isPanning = true`).
   - Mouse cursor transforms from `grab` to `grabbing`.
   - Viewport translates relative to drag delta with 1:1 pixel fidelity.
   - Releasing mouse ends panning and restores `grab` cursor.
2. **Mouse Wheel / Trackpad Pinch Zoom:**
   - Scrolling wheel scales the canvas transform smoothly between `zoom = 0.4x` (macro overview) and `zoom = 2.5x` (micro atom detail).
   - Zoom pivots around the mouse cursor position.
3. **Orientation Anchor:**
   - The Root Goal node remains anchored at coordinate origin `(0, 0)`.
   - The Root Goal label maintains 100% opacity and clamped font floor regardless of zoom level so the user never gets lost in deep space.

---

## Story 2: Pair Scrubbing Interaction

1. **Notch Clicking:**
   - Clicking notch `P[N]` on the timeline scrubber immediately scrubs the graph to pair `N`.
   - Scrubber progress track animates fill width to notch index.
   - URL updates with deep link state `?pair=N`.
2. **Keyboard Arrow Navigation:**
   - Pressing `ArrowLeft` scrubs to `max(1, currentPair - 1)`.
   - Pressing `ArrowRight` scrubs to `min(totalPairs, currentPair + 1)`.
   - Response is instantaneous (<16ms, zero reflow).
3. **Scrubber Controls:**
   - `Prev` button disabled when `currentPair === 1`.
   - `Next` button disabled when `currentPair === totalPairs`.
   - Badge updates with active pair label (e.g. `Pair 2 · Born: Outcome 4`).

---

## Story 3: Hover Affordances & Tooltip Inspection

1. **Satellite Micro-Atoms (Requirements & Open Questions):**
   - Moving cursor within `radius + 8px` (24px hit circle) of any satellite atom highlights the element.
   - Cursor switches to `pointer`.
   - Floating Obsidian Tooltip appears at `(clientX + 14px, clientY + 14px)`.
   - Tooltip header displays uppercase category tag (`USER REQUIREMENT` in cyan `#38bdf8` or `AI OPEN QUESTION` in amber `#fb923c`).
   - Tooltip body displays verbatim text from `state.json`. Zero ID tags, zero numeric formulas.
   - Moving cursor away hides tooltip with a `120ms` fade-out.
2. **Deliverable Nodes:**
   - Hovering over a deliverable sphere elevates its frosted rim brightness from `0.55` to `0.85`.
   - Hovering displays outcome title in high contrast.

---

## Story 4: Click Interactions & Cross-Pane Scrub Sources

Per `docs/Interaction Spec.md` §3 (Graph as a Scrub Source):
1. **Node Click:**
   - Clicking a child deliverable node scrubs the entire application (graph + panel) to that node's `born_pair`.
2. **Satellite Atom Click:**
   - Clicking a requirement bead or open question ring scrubs to its `creation_pair`.
   - Emits scroll event to transcript pane, scrolling the conversation to the exact creation turn (`U(p,t)` or `A(p,t)`) with quote highlighting.

---

## Story 5: Live Pipeline Replay Choreography (Phase G1.S7)

When replaying a live session turn-by-turn via SSE events (`pair_ready`):
1. **Node Birth (`event.kind === "born"`):**
   - The new deliverable sphere animates from scale `0.0` to `1.0` at its deterministic coordinate over `400ms` (`--motion-birth`).
   - Its parent-child tether animates drawing outwards from the parent node circumference.
2. **State Transition to Dormant:**
   - If a node receives zero ledger mass this pair ($\Delta = 0$), its tether line gently fades from crisp white (`0.70`) to neutral slate (`0.32`) over `300ms` (`--motion-dormancy`).
3. **Reactivation:**
   - If a dormant node receives new ledger delta in a subsequent pair, its tether line brightens back to crisp white over `300ms` (`--motion-reactivate`).
4. **Question Resolution (Slot $\rightarrow$ Req):**
   - When an open question slot is resolved by the user, the hollow pulsing amber ring collapses and fills into a solid requirement bead with an outer ancestry ring (`bullseye`) over `300ms`.
5. **Session Focus Cursor:**
   - The terminal focus breathing halo moves smoothly to the newly lit outcome for this turn.
6. **History Non-Interference:**
   - If the user is currently scrubbed back in `HISTORY` mode, live updates append silently to the scrubber rail without yanking the camera view. A "Back to latest" pill appears in the UI.

---

## Story 6: Reduced Motion & Performance

1. **Reduced Motion (`prefers-reduced-motion: reduce`):**
   - Radial breathing pulses and entry scale transitions are disabled (`duration = 0ms`).
   - State changes apply instantaneously without animations.
2. **Dirty-Flagged Canvas Loop:**
   - When the canvas is stationary (no mouse movement, no active scrub, no breathing pulse), the animation frame loop pauses to conserve CPU/GPU battery.
