# Agency Panel — Design Specification (v2.0 — FINAL FOR BUILD)
### The right-rail panel: five sections, every element defined, every value's source named

**Status:** v2.0 — the frontend counterpart to COTRACE_PIPELINE_SPEC.md v5 (the backend).
Everything a builder needs to render the panel from the backend's outputs: section goals,
element inventories, generation rules, interaction rules, and the element→query contract.
Locked this version: per-turn drawer scoping (§4.4), the summary-line rule R-SUM (§4.5),
the cockpit metaphor (§5). Remaining open items are listed in §7 — none blocks a first
working build.

---

## 0. What the panel is

A live right-rail beside an AI chat that makes visible, turn by turn, how a piece of work
is being shaped between the person and the AI. **A mirror, not a judge**: every element
states a fact traceable through the backend to a verbatim quote, and no element praises or
shames any way of working.

**Coordinate system:** the pair (P1, P2, …) = one user message + one AI reply. Every
section renders "as of" a pair. Clicking any pair anywhere scrubs the whole panel to that
moment. Live-vs-history state is shown ONCE, in the panel's top status strip
("VIEWING P2 · HISTORY" / "LIVE") — never per-row.

**Colors:** blue = you, orange = the AI. Left = yours, right = the AI's, everywhere,
without exception. No third accent color may take a side.

**Vocabulary:** UI prose says *decisions* (not "requirements"), *open questions* (not
"open slots"), *you / AI* (not "user / assistant"). The R/S label system (R1, R2a…, S1…)
is the one systematic exception — the stable, reviewable naming shared with the backend
and the SVG traces. **No textual state labels anywhere** (no "MAIN GOAL", "CURRENT",
"NOW", "exploring"): position, indentation, and emphasis carry meaning; words never
restate what the visual already says.

---

## 1. GOAL section (top)

**Design goal:** answers *"where am I in my own work right now?"* Orientation, not
attribution. The slow section — changes only when the work's direction changes. Zero
influence data.

**Form — the thread-collapse blueprint** (YouTube comment-thread mechanism), generic for
any project shape. Default view, top to bottom:

```
[main goal]
   ⌄ N more                ← expander chip, ONLY if nodes are hidden between
      [previous goal]         the main goal and the two nodes below
         [current goal]    ← the single emphasized line
```

**All depth cases** (d = current goal's depth below the main goal):
| Case | Default view |
|---|---|
| d = 0 | one line: the main goal, emphasized |
| d = 1 | main goal · current — no chip |
| d = 2 | main goal · previous · current — no chip |
| d ≥ 3 | main goal · chip "⌄ d−2 more" · previous · current |

**Expansion:** tapping the chip reveals the next hidden segment (progressive, never an
all-at-once dump); revealed nodes with off-path children carry their own "⌄ N" chips;
at full expansion the entire goal structure of the project is explorable. "Show less"
restores the default in one tap. The section scrolls internally only while expanded.

**Element inventory (nothing else exists in this section):**
| Element | Definition | Source |
|---|---|---|
| Goal node | The goal's text; position + indentation = its place. No metadata. | Step 1b outcome tree + display rules (R0, R-LEAF, R-SIDE, R-TREE, R-GROUP) |
| Emphasis | Exactly one node (current) carries the section's single emphasis. | R-LEAF (this pair's lit node) |
| Expander chip | "⌄ N more" — hidden-node count; the only interactive element. | Tree depth arithmetic |

When no confident current goal exists, the current line holds the last stable goal — no
precision manufactured, no ambiguity announced.

---

## 2. DIRECTION section

**Design goal:** answers *"across this chat so far, how much of the steering has come from
each of us?"* One cumulative number pair — a running odometer. The scrub interaction IS the
trend display: viewing P3 shows the split as of P3.

| Element | Definition | Source (backend §10) |
|---|---|---|
| Split bar | Blue from left, orange from right, meeting at the split. | `C(t,you) / (C(t,you)+C(t,AI))` — snapshot row t |
| Readouts | `You — 59%` · `AI — 41%` | same |
| Pair badge | `@ P3` | viewed pair |

---

## 3. DECISIONS section

**Design goal:** the **countable face of agency** — Direction answers "how much," this
answers "how many." Counts are concrete and checkable; "which four?" is the reflective
moment the panel exists to create. Neutral ledger, never a verdict.

| Element | Definition | Source (backend §10.5) |
|---|---|---|
| Counter | `Decisions — 9 you · 4 AI` as of viewed pair. A decision = a requirement; side = creator. | creation rows grouped by earliest-creation-action speaker |
| Latest example | Most recent AI-created decision's text, truncated at a clause boundary, never re-worded. | highest-pair AI-created requirement's `fields.text` |

---

## 4. TIMELINE section

**Design goal:** the chat's **factual record** — *"what actually happened, and who made it
happen?"* The goal section shows intention; the timeline shows events. Three depths, one
principle — every level down answers "show me" about the level above:
**scan** (collapsed rows) → **record** (drawer) → **proof** (level-2).

### 4.1 Collapsed row
| Element | Definition | Source |
|---|---|---|
| Pair label `P2` | The coordinate. Click = scrub. | pair index |
| Turn-delta bar | Micro-spine: blue-left = mass you added this exchange, orange-right = the AI's. Chat-wide fixed scale k = half-width / maxₜ Δ(t,·). | `Δ(t,you)` vs `Δ(t,AI)` (§10.4) |
| Summary line | ≤ 5 words, what happened. | R-SUM (§4.5) |
| Expand chevron | Opens the drawer. | — |

### 4.2 Drawer — one exchange of the SVG trace, cropped to rail width
Exactly two content types, in the trace's visual language (spine, bars, chips), nothing
else:

| Element | Definition | Source |
|---|---|---|
| Requirement row | One per requirement created/revised **in this exchange**: R-chip on the spine + bar. Chip color: blue = user-only (`M(AI,r)=0`), orange = AI-created (`M(you,r)=0`), grey = straddling — evaluated as of the viewed pair. | ops at pair t; bars per §4.4 |
| Open-question ring | Dashed circle per slot opened/resolved this exchange, with its S-label. Dashed = open; solid faded = resolved. | `open_slot_ops` at pair t |

**R/S labeling:** chat-wide running numbers in creation order; revisions carry a suffix
(R2a). Stable across the panel, the backend, and the full SVG trace.

### 4.3 Level-2 expansion (per requirement) — exists; design deferred
Tapping a requirement row opens its full story: exact text, extraction rationale, the
direct/indirect influence detail with evidence quotes, and its **cumulative** shaping
history (`M(p,r)` over time). This is where the pipeline's complete output surfaces.
Internal design: deferred (§7).

### 4.4 Scoping rule — LOCKED: per-turn
Drawer bars show **only the mass added in this exchange** (`Δ(t,p,r)`), making each drawer
a self-contained record — stacking all drawers reconstructs the whole story with no
double-counting. Cumulative per-requirement bars live in level-2. (Locked per the owner's
stated per-turn preference; both scopings are one-line ledger queries, so revisiting later
costs nothing.)

### 4.5 R-SUM — the summary-line rule (LOCKED, v1: deterministic template)
Inputs: this pair's requirement/slot ops and their per-op mass deltas.
1. If ≥1 requirement op: take the op with the highest `Δ(t,·,r)`; verb by op —
   create → "adding", revise → "revising", resolve → "settling", delete → "dropping";
   summary = verb + the requirement's short label. ≤ 5 words total.
2. Else if slot ops only: "raising an open question" (or "parking N questions").
3. Else: "execution only".
An optional LLM micro-call may smooth the phrasing but may never add facts not in the
inputs. Regenerated only when the pair's own data changes — never retroactively.

**Interaction:** accordion — one drawer open at a time; expanding scrubs to that pair;
empty exchange shows "execution only — no requirements touched."

---

## 5. HOW section (bottom)

**Design goal:** a **descriptive mirror of usage mode** — per exchange and as a running
distribution — with zero preachiness. Definitional core (Randazzo et al.): two questions —
**Q1: who selects WHAT needs to be done? Q2: who identifies HOW it gets done?**

| Mode | Paper's name | Q1 / Q2 | LOCKED metaphor sentence |
|---|---|---|---|
| Centaur | Directed Knowledge Co-Creation | Human / Human | **"You're driving — the AI assists when asked."** |
| Cyborg | Fused Knowledge Co-Creation | Human / Shared-AI | **"Copilot — you're flying this together."** |
| Self-Automator | Abdicated Knowledge Co-Creation | AI / AI | **"Autopilot — the AI is flying; you're along for the ride."** |

Displayed with identical neutrality: none is wrong; the only risk the section guards
against is sliding into autopilot *without noticing* — and that realization must come from
the user, never from the panel's tone.

| Element | Definition | Source (backend §10.5) |
|---|---|---|
| Mode line | This exchange's mode, one locked sentence. | HOW classification @ viewed pair |
| Mode split | Running distribution bar: % of non-quiet exchanges per mode. | mode history up to viewed pair |

Classification thresholds: defined at backend §10.5, **proposed pending calibration**
against the Budget and Portfolio ground-truth trajectories.

---

## 6. Element → backend contract (the whole panel in one table)

| Panel element | Backend query (COTRACE_PIPELINE_SPEC v5) |
|---|---|
| Goal tree + current node | Step 1b tree + display rules — no math |
| Direction bar @ t | snapshot `C(t,·)` (§10.4) |
| Decisions counter + example | creation-row group-by (§10.5) |
| Turn-delta bar | `Δ(t,·)` (§10.4) |
| Drawer requirement bars | `Δ(t,p,r)` per-turn (§4.4 / §10.5) |
| Drawer chip colors | `M(p,r)` zero-tests as of t |
| Open-question rings | slot ops at t (§6 of backend) |
| Summary line | R-SUM over ops at t (§4.5) |
| Level-2 detail | full per-requirement label history + `M(p,r)` series |
| HOW mode + split | §10.5 signals + classification |

## 7. Open items (none block a first build)
1. **Level-2 expansion internal design** — deferred; its data contract is already fixed.
2. **HOW threshold calibration** — run against the two ground-truth trajectories before
   trusting mode output; until then the mode line renders with the proposed rules.
3. Upstream (backend §12.5): the widened-hedge re-run — will change real numbers on the
   pair-1 dataset when done.
