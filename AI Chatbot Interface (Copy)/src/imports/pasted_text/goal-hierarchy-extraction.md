# SKILL: Goal-Hierarchy Extraction for the Live Agency Panel
### Section 2 — the goal panel (Main Goal · Current Sub-Goal · Nested Hierarchy)
### Built on the **verbatim** COTRACE prompts (Kim et al., *Measuring AI Contributions to Goal Shaping*, Appendix B)

> **What this is.** A strict, repeatable procedure for producing the **goal-hierarchy section**
> of the live panel — and *only* that section. Its extraction engine is the paper's **exact
> prompts, reproduced verbatim** from Appendix B.2 (Steps 1a, 1b, 1c). On top of that engine sit
> our **display rules** (which leaf is lit, append-only tree, collapse). Determinism is the
> contract: same chat in → same panel out, every run.
>
> **Verbatim discipline.** The text inside the `PROMPT — …` blocks in §3 is **copied exactly
> from the paper**. Do not edit, "improve", reorder, or re-word it. If you change a prompt, you
> are no longer running COTRACE. Our additions are confined to §4–§9 and are labelled **[OURS]**.

---

## 0. SCOPE

### 0.1 Produces
1. **Main Goal** — the root of the outcome tree (rendered as the editable chat title).
2. **Current Sub-Goal** — the one outcome the latest pair is actively working on.
3. **Goal Hierarchy** — the nested outcome tree, collapsed to constant size.

### 0.2 Does NOT touch (separate skills)
DIRECTION bar · per-pair TIMELINE · HOW axis / driving analogy · "AI's idea count".
These need **requirements + influence** (paper Stages 2–4). **The goal panel needs only the
outcome tree from Stage 1.** Do not run Stages 2–4 here.

### 0.3 Paper prompts and where they belong
| Paper prompt (Appendix B.2) | Used by this skill? |
|---|---|
| **Step 1a — Action Extraction** | ✅ verbatim (§3.1) |
| **Step 1b — Outcome Extraction** | ✅ verbatim (§3.2) |
| **Step 1c — Intention Extraction** | ✅ verbatim (§3.3) — needed for side-track test |
| Step 2 — Requirement Extraction | ❌ other sections |
| Step 3 — Influence Labeling | ❌ other sections |
| Deliverable Extraction | ❌ other sections |
| Requirement-Deliverable Evaluation | ❌ other sections |

### 0.4 Two modes
- **Mode A — Real-time:** chat arrives pair-by-pair; maintain one growing STATE; re-render each pair. (§6)
- **Mode B — Full chat:** whole chat given; **replay Mode A pair-by-pair**; emit the full trace. (§7)

---

## 1. OPERATIONAL DEFINITIONS — verbatim from paper §B.1.1

> **Human–AI Collaboration.** *"We adopt the operational definition of human–AI collaboration
> from Shao et al. (2025a), who model a human–agent collaboration log as a Partially Observable
> Markov Decision Process (POMDP). An interaction is represented as an alternating sequence of
> actions a = (a₁^(l₁), a₂^(l₂), …, a_T^(l_T)), where T denotes the total number of steps and
> lₜ ∈ {U, A} indicates whether the user (U) or the agent (A) takes the action at step t."*

> **Goal and Requirement.** *"We define a goal as an explicit observable and actionable target
> specified in user and agent utterances. **Observable** means we only consider goals that are
> explicitly stated in the utterances (i.e., we do not infer latent intentions). **Actionable**
> means goal specifies a desired outcome (an intended artifact/state) and the goal attainment is
> evaluable from the dialogue and model outputs. For each collaboration log, we identify a set of
> goals G = {g₁, …, gₘ}, where each goal is represented as a tuple gⱼ = (oⱼ, Rⱼ). Here, oⱼ is the
> minimal intended artifact/state and Rⱼ = {rⱼ₁, …, rⱼₖ} is a set of independently verifiable
> requirements that determine whether oⱼ is achieved."*

> **For the goal panel we use only `oⱼ` (the outcome) and its parent/child links.** The
> requirement set `Rⱼ` and the influence math M(p, ρ, r) belong to other panel sections and are
> not computed here.

**The panel-to-paper identity** **[OURS, reading the paper's tree]:**
- **Main Goal = the root (parent) outcome** `oⱼ` of the hierarchy.
- **Current Sub-Goal = the active leaf outcome** the latest pair is working on.
- **Hierarchy connectors = the parent/child outcome links** — nothing written, the shape *is* the relation.

---

## 2. PIPELINE OVERVIEW — verbatim from paper §B.1.2 (Stage 1 only)

> *"The dialogue is divided into consecutive blocks of B turns (default **B=4**). Each block is
> processed sequentially by an LLM, which receives (i) the current block's utterances and (ii)
> previously identified outcomes and actions."*
>
> *"**Action extraction.** Each message is segmented into atomic actions, defined as the minimal
> actionable units of the interaction."*
>
> *"**Outcome identification.** For each extracted action, the model determines whether it
> introduces a newly specified desired outcome or updates an existing one, while maintaining its
> version history. Each action is then linked to an outcome and assigned one dialogue role:
> SHAPER (proposes goals, ideas, or requirements), EXECUTOR (carries out actions or produces
> output), or OTHER (provides information without directly shaping or executing the outcome)."*

> **This block mechanism IS the real-time engine.** Processing is sequential and carries prior
> outcomes forward — so the extraction at pair *n* sees pairs 1…n and **nothing after**
> (look-backward-only). Mode A (§6) and Mode B (§7) both rely on exactly this property.

---

## 3. THE EXACT PROMPTS (reproduced verbatim — run these unchanged)

> Run **1a → 1b → 1c in order**. Feed each prompt the placeholders it names. The output of 1b
> (`outcomes` + `action to outcome`) is the goal tree; 1c's `outcome to intention` is used by the
> side-track rule (§4.7). **Do not alter the text below.**

### 3.1 PROMPT — Step 1a: Action Extraction
```
You are analyzing **one block of a longer dialogue** to extract actions.

**ACTION** = An atomic communicative act a speaker **directly performed** in a turn.
- Atomic action = minimal unit of action the speaker directly performed.
- e.g. "User asks to find a paper about HCI in NLP conferences" → split into
  "User asks to find a paper about HCI", "User asks to find a paper in NLP conferences".
- Include evidence quote from the utterance.

**Possible action types** (generate new types if needed):
Accept, Acknowledge, Address, Allow, Analyze, Apologize, Ask, Challenge, Clarify,
Classify, Compare, Complain, Confirm, Connect, Constrain, Critique, Decide, Define,
Delegate, Describe, Draft, Emphasize, Evaluate, Explain, Feedback, Formalize, Frame,
Greet, Hypothesize, Implement, Include, Infer, Instruct, Invite, Justify, List,
Modify, Observe, Plan, Provide, Qualify, Recommend, Refuse, Report, Request, State,
Suggest, Summarize, Warn

**Role:** **SHAPER | EXECUTOR | OTHER**
* **SHAPER:** Creates/shapes/revises the goal/requirement by proposing new ideas,
  new tasks, constraints, alternatives, or directions.
* **EXECUTOR:** Executes/achieves the desired outcome/goal/requirement (e.g.,
  drafting text, providing requested information, coding, searching, implementing).
* **OTHER:** Neither SHAPER nor EXECUTOR.

=== DIALOGUE BLOCK START ===
{dialogue block}
=== DIALOGUE BLOCK END ===

Now, extract ALL actions from EVERY turn. Return JSON only:
{ "actions": [ { "turn id": <turn number>, "action type": "<action type>",
"action text": "<brief description in third person>", "role":
"<SHAPER|EXECUTOR|OTHER>", "evidence quote": "<quote from utterance>" } ] }
Respond with ONLY the JSON object. No additional text.
```

### 3.2 PROMPT — Step 1b: Outcome Extraction
```
You are given ALL actions extracted from a complete dialogue. Your task:
(1) Identify **outcomes** (purpose-linked desired deliverables)
(2) Assign every action to exactly one outcome

Every collaboration has a **purpose**. **Outcomes are purpose-linked desired
deliverables** --- concrete outputs that participants are actually working toward.
- **Outcomes = purpose-linked desired deliverables:** Deliverables are not limited
  to text or documents --- they can be a **decision**, **advice**, **plan**,
  **clarification**, or any other concrete result. Do **not** include things only
  mentioned without being adopted as a goal.
- **Requested or agreed outputs:** Any concrete output a participant **explicitly
  requests** or participants **agree to produce** is a deliverable.
- **Primary output:** The main thing the dialogue aims to produce must appear as an
  outcome. Sub-deliverables are children.
- **Phrasing:** e.g. "decision for X", "advice for X", "draft for X", "plan for X".
- **Hierarchy:** **parent** = abstract/general, **child** = specific/concrete. Use
  parent outcome id / child outcome ids.
- **Granularity:** Prefer consolidated, task-level outcomes. Example: "Workshop plan
  (date, venue, agenda)" NOT separate "Decide date", "Decide time", etc.
- **No duplicates.** Each distinct deliverable exactly once.

=== DIALOGUE CONTEXT === {dialogue summary}
=== ALL ACTIONS === {actions block}

Return JSON only:
{ "dialogue summary": "<collaboration purpose, 1-2 sentences>", "outcomes": [
{ "outcome id": "outcome 1", "outcome": "<purpose-linked desired deliverable
description>", "turn id": <turn where this outcome first appears>,
"parent outcome id": null, "child outcome ids": [], "related outcome ids": [],
"confidence": <float 0.0--1.0> } ], "action to outcome": { "<action id>":
"<outcome id>" } }
IMPORTANT: action to outcome must map EVERY action id to an outcome id. No action
left unassigned.
Respond with ONLY the JSON object. No additional text.
```

### 3.3 PROMPT — Step 1c: Intention Extraction
```
You are given a list of outcomes from a dialogue. (1) Identify distinct
**intentions** (high-level goals or purposes) that these outcomes serve. (2) Assign
each outcome to exactly one intention.
Output JSON only:
{ "intentions": [ {"intention id": "I1", "intention": "short label"},
{"intention id": "I2", "intention": "another label"} ], "outcome to intention":
[{"outcome id": "outcome 1", "intention id": "I1"}, ...] }
- Every outcome id appears exactly once in outcome to intention. Use intention id
from the intentions list
```

### 3.4 The one adaptation for live use (and why it changes nothing in the prompts)
Step 1b's prompt opens *"You are given ALL actions extracted from a complete dialogue."* In the
paper's **batch** run that is literally all actions. In **real-time** (Mode A), "ALL actions" =
**all actions extracted up to and including the current pair** — which is exactly what the block
mechanism (§2) already feeds forward. So:
- We **do not edit the prompt.** We only change what fills `{actions block}` and `{dialogue
  summary}`: the running set so far, never future turns.
- This preserves look-backward-only and keeps the prompt verbatim. **[OURS — adaptation, not edit.]**

---

## 4. DISPLAY LAYER — **[OURS]**, operating on the JSON from §3

The §3 prompts return a complete `outcomes` tree + `action to outcome` + `outcome to intention`.
The panel needs a live, constant-size, single-lit-node view. These rules build it **from that
JSON** — they add no new extraction.

### 4.1 R0 — Root = chat title
Set `root.label = chat_title` (the editable sidebar title). It equals the paper's root parent
outcome (the §3.2 outcome whose `parent outcome id = null` and that is most abstract). If no title
yet, seed it from that root outcome and let the user overwrite. Root never changes branch.

### 4.2 R-GROUP — when an intermediate node exists
Use an outcome as a **grouping (non-leaf) node only if §3.2 already made it a parent** of ≥2
child outcomes (`child outcome ids` length ≥ 2). Do **not** invent groupings the extractor didn't
return. (This keeps depth faithful to the paper's own hierarchy and is what makes §4.5 collapse
ever fire.)

### 4.3 R-LEAF — current sub-goal (**the key runtime rule**)
The **Current Sub-Goal** = the outcome that **this pair's user SHAPER actions operated on,
confirmed by the outcome the AI's EXECUTOR actions produced** this pair. Procedure per pair:
1. Among this pair's **user** actions with `role = SHAPER`, find the outcome (via `action to
   outcome`) they create/revise. That outcome is the candidate.
2. Confirm with the AI: the outcome this pair's **EXECUTOR** actions map to. If it matches, lock it.
3. **Vague pair** (no user SHAPER, no new outcome): keep the previously lit node — set Current
   Sub-Goal = the outcome the AI's EXECUTOR actions centered on (usually the same node, refined).
> **Not "most actions attached."** That metric is cumulative and biased toward old big nodes, so
> on a redirect it keeps the wrong node lit. Recency + SHAPER intent decide the lit node.

### 4.4 R-TREE — append-only display + back-references
The displayed tree is **append-only**: once a node is drawn it never moves. When §3.2 returns a
`related outcome ids` link or a pair re-opens an existing outcome, **keep the node in place** and
render a `↩ relates to X` marker; record it in `links`. Never re-parent or delete a drawn node.

### 4.5 R-DISPLAY — depth collapse (constant size). Let `d` = depth of current node below root.
- `d == 1`: `ROOT` + `● current`.
- `d == 2`: `ROOT` + `ancestor` + `● current`.
- `d >= 3`: `ROOT` + `⋯ (d−2 hidden)` + `immediate ancestor` + `● current`.
**One** ancestor, not two (settled). The full tree always lives in STATE; the panel shows the
local neighborhood only → **O(1), constant height for any chat length.**

### 4.6 R-SIBLING — sibling collapse
If the current node's parent has >3 children, show the current node + the 1–2 most-recently-active
siblings + `⋯ M more`. (Real chats are wide; this is the overflow that actually happens.)

### 4.7 R-SIDE — side-tracks (dashed branches)
Mark an outcome as a side-track iff, in §3.3's `outcome to intention`, its **intention differs
from the root outcome's intention** AND it is not a child sub-task of any work outcome. Render it
dashed, attached to root, with a `⤳` glyph — never as an ancestor of work nodes. (Paper has no
non-purpose-linked node; this is **[OURS]**.)

---

## 5. STATE OBJECT — **[OURS]** (persists across pairs)
```json
{
  "chat_title": "<= root label, user-editable>",
  "root_outcome_id": "outcome 1",
  "outcomes": { "outcome 1": { "label":"...", "parent":null,
                "kind":"root|group|leaf|side", "intention_id":"I1", "first_pair":1 } },
  "display_order": ["outcome 1", "..."],     // append-only
  "links": [ { "from_pair":44, "to_outcome":"outcome 7", "type":"back-ref" } ],
  "current_sub_goal_id": "outcome N",         // recomputed every pair (R-LEAF)
  "last_pair_processed": 0
}
```
**Invariants after every pair:** `display_order` only grows (never re-parent/remove); exactly one
`current_sub_goal_id`; every action maps to exactly one outcome (Step 1b); the lit node is one this
pair actually moved.

---

## 6. MODE A — REAL-TIME (per-pair procedure)
On each new pair (one user message + one AI message):
1. **Load STATE**; look backward only.
2. **Run PROMPT 1a (§3.1)** on the new turns (the current block, B=4 turns of context), tagging speaker → actions JSON.
3. **Run PROMPT 1b (§3.2)** with `{actions block}` = all actions so far (§3.4 adaptation) and `{dialogue summary}` carried forward → updated `outcomes` + `action to outcome`. This yields, for this pair, one of: **NEW leaf · GROUP open · REFINE (no new outcome) · SIDE-TRACK · BACK-REF**.
4. **Run PROMPT 1c (§3.3)** on the outcome set → `outcome to intention` (drives §4.7).
5. **Pick Current Sub-Goal (§4.3 R-LEAF).**
6. **Persist STATE**; enforce §5 invariants.
7. **Render (§4.5 + §4.6):** ROOT + collapsed ancestors + immediate ancestor + `● current` + sibling collapse + `↩`/`⤳` markers.

> The goal panel is the **slow** section: most pairs are step-3 REFINE, so the tree and lit node
> hold still while the timeline (another skill) updates each turn. **Holding still is correct.**

---

## 7. MODE B — FULL CHAT (same logic, run to completion)
Do **not** batch-consolidate. Replay Mode A across every pair:
1. Init empty STATE; set `chat_title`.
2. **For pair = 1…N:** run the full §6 procedure; after each pair, snapshot the rendered panel + lit node.
3. **Emit:** (a) the final whole tree (reference); (b) a **per-pair table** — `pair | user shaping move | current sub-goal | tree op | depth | collapse?`, **one row per pair, none skipped**; (c) **per-pair panel snapshots** grouped by stable stretch (consecutive pairs with an unchanged lit node) so every pair is accounted for without repeating identical frames.

> Mode B must reproduce the live sequence exactly (look-backward-only). A batch pass could "see"
> later pairs and draw a tidier tree than the user experienced — that would break the panel's honesty.

---

## 8. DETERMINISM & TIE-BREAKING — **[OURS]** (so two runs agree)
1. **Outcome vs requirement?** → requirement (fold in, no node). Bias to fewer nodes. *(Paper's top goal error, 66.7%, is mistaking a requirement for an outcome.)*
2. **New node vs refine?** → a node needs a **user SHAPER action introducing a distinct deliverable**; a new constraint on the same deliverable is a refine.
3. **Lit node, multiple candidates?** → §4.3 order: user-SHAPER target → outcome the AI produced this pair → most recently created.
4. **Group or not?** → §4.2: only if §3.2 made it a parent of ≥2 children.
5. **Side-track or work?** → §4.7: only if a different intention AND not a sub-task of any work outcome; else **work**.
6. **Back-ref or new node?** → if the outcome already exists in STATE, back-ref (add `↩`), never duplicate (Step 1b "No duplicates").

---

## 9. OUTPUT CONTRACT — **[OURS]** (what the renderer consumes)
```json
{ "pair": 36,
  "main_goal": "Birthday video for Malabar Amachi",
  "current_sub_goal": "Mother full-body",
  "render": [
    { "level":0, "label":"Birthday video for Malabar Amachi", "kind":"root" },
    { "level":1, "label":"1 level hidden", "kind":"ellipsis" },
    { "level":2, "label":"Great-grandparents", "kind":"ancestor" },
    { "level":3, "label":"Mother full-body", "kind":"current", "markers":[] } ],
  "siblings_collapsed":"3 more", "tree_op":"refine", "depth":3, "collapsed":true }
```
The renderer draws only this; all judgment lives in §3 (paper) + §4 (ours).

---

## 10. HONESTY LEDGER
- **Paper, run verbatim:** the three §3 prompts (Action/Outcome/Intention extraction), the goal
  definition (§1), the block-sequential look-backward processing (§2). Cite COTRACE for these.
- **[OURS], do NOT cite the paper:** the panel identity (§1 mapping), R0 root=title, R-LEAF lit
  node, R-TREE append-only + back-refs, R-DISPLAY/R-SIBLING collapse, R-SIDE side-tracks, the
  STATE object, both mode procedures, the §8 tie-breaks, the §9 contract, and the §3.4 live adaptation.
- **Known limit:** the paper validates **batch** extraction at 96.6% goal accuracy. Our **live,
  look-backward-only** use is unvalidated and will occasionally draw a node where a later pair
  shows it should differ; R-TREE accepts this for stability and surfaces the fix as a marker.