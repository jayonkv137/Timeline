# G1_BRIEF.md — The Node Graph on Real Engine Data

**Phase:** G1, first phase of the graph track
**Roles:** ENGINE (S1–S4), APP (S5–S8), DESIGN SYSTEM (parallel, interface only), OWNER (two gates)
**Tools:** Claude Code, Opus for S1–S4 (masses and sums: wrong-number-is-worse-than-slow).
Codex or Antigravity for S5–S8 (your eyes are the test).
**Depends on:** E2 closed (`e2-done`). Nothing from E3.
**Cost:** zero LLM calls. Every run in this phase replays recorded cassettes.
**Gate before G2:** Definition of Done, section 7

---

## 1. Why this phase exists

The engine works. For ten real conversations it has produced `state.json`,
`ledger.jsonl` and `panel_bundle.json`, and every number passes the invariants.

The graph works too, as a prototype. `design_pack/playground_obsidian.html` and
`playground_3d.html` draw goals, decisions and open questions the way the owner designed
them in `design_pack/GRAPH_SYSTEM_SPEC.md`.

**The two have never met.** The prototype reads `all_chats_data.js`, a file compiled by hand
from copies of three chats in `design_pack/sample_data/`. Nothing about it is tested, and
several of its rules differ from the spec (section 3).

G1 joins them properly:

```
engine (per pair) → graph_bundle.json → server (REST + SSE) → web graph view
```

At the end of G1 you can open any processed chat in the real app, scrub it pair by pair,
and watch it build itself live as the pipeline replays. Every node size, bead and ring
traces to a ledger row or a state record, and a test proves it.

G1 does **not** connect to ChatGPT or Claude, run live LLM calls, or build the 3D head.
Those are G2 to G4 (section 10).

---

## 2. Read before starting

Every role reads:

1. `AGENTS.md` in full. The workflow gates apply.
2. `docs/Working Rules.md` and your entry in `docs/Roles Documentation.md`.
3. This brief in full.
4. `design_pack/GRAPH_SYSTEM_SPEC.md` in full. It is the owner's design and the source of
   truth for what the graph means.
5. The last two `BUILDLOG.md` entries.

Then, by role:

| Role | Also read |
|---|---|
| ENGINE | `docs/Cotrace Pipeline Spec.md` §10 (Stage 4) and §12.3 (1b has no prior-outcome memory); `engine/quant.py`, `engine/projections/panel.py`, `engine/pipeline.py` `run_chat()` and `step_1b()`; `tests/invariants.py` |
| APP | `docs/Architecture.md` §3–§5; `docs/Interaction Spec.md` in full; `design_pack/playground_obsidian.html` (the renderer to port); git history of `server/main.py` at commit `27e7d68` (the Phase 3 server) |
| DESIGN SYSTEM | `docs/briefs/D Track Brief.md`; from this brief, only section 6 (the graph's token contract) |

---

## 3. What the prototype does that G1 must not repeat

Found by reading `design_pack/compile_all_chats.js` against the spec. Each one is a rule
for G1.

| # | Prototype behaviour | Spec says | G1 rule |
|---|---|---|---|
| D1 | Dashed "related" links join neighbouring children in list order | Dashed links come from `outcome.related[]` | Edges only from `related[]` |
| D2 | Every child tethers to the root | Tether to `outcome.parent` | Real hierarchy, any depth |
| D3 | Open questions show only in the pair they were created | Persist until resolved or abandoned | Open from open pair until the resolve or abandon pair |
| D4 | Resolved-question "options" is the question text repeated | Options come from backend output | No such field exists. Show the question and the resolving action's quote. Choices are a future Step 2 extension, logged as a question |
| D5 | Positions from a fixed table of 6 slots | Deterministic, locked across pairs | Renderer layout, seeded, stable for any number of nodes |
| D6 | Fallbacks invent data (`A(1,1)`, first child as focus, mass floor of 10) | Every visual traces to data | No invented values. Missing means absent, and the UI says so |
| D7 | Reads hand-copied `sample_data/` | Engine output | Reads `data/chats/<id>/` through the server |
| D8 | Masses computed in JavaScript | Architecture D13: frontend does zero measurement math | Masses computed in Python, tested |

One more, from the data, not the prototype:

**D9. Outcomes are not stable across pairs.** Step 1b re-emits the whole tree every pair
(pipeline spec §12.3). In the c15 checkpoints in `design_pack/runs/`, titles change at
pairs 4–6, ids change format, and outcomes drop out and come back. `state.json` only holds
the final version. A graph that scrubs through history must know what the tree looked like
*at each pair*. S1 measures this before anything is built on it.

---

## 4. Scope

**In scope**
- ENGINE: per-pair state snapshots; `engine/projections/graph.py`; outcome mass facts in
  `engine/quant.py`; `engine/schemas/graph_bundle.schema.json`; graph invariants; wiring into
  `run_chat()`; replay of the ten chats
- APP: `server/` read API and SSE; a dev-only replay trigger; the graph view in `web/`;
  scrubber, tooltips, click-to-jump into the transcript; LIVE and HISTORY per the
  interaction spec
- DESIGN SYSTEM: nothing inside G1. Its own programme (D track) delivers the section 6
  tokens at milestone M1

**Out of scope, do not touch**
- Steps 1a–3 and their prompts. G1 never changes what the engine extracts.
- `quant.py`'s existing functions and the panel numbers. G1 adds functions; it changes none.
- `data/chats/fixture_pair1/`, the five existing schemas, `data/corpus/`
- Live chat (`POST /messages`), any live LLM call, the cost seam, model choice, Jev
- The 3D view, cross-chat views, the browser extension
- Any new dependency. Allowed: react, vite, zustand, fastapi, uvicorn, sse-starlette,
  jsonschema, pytest. A force-layout or graph library goes through `SPEC_QUESTIONS.md` first.

---

## 5. The contract: `graph_bundle.json`

This is the seam every role builds against. ENGINE writes it, APP reads it, and DESIGN
SYSTEM never sees it. **The draft below is approved or changed by the owner at gate S2,
then frozen.**

Two parts. `entities` holds every text once. `frames` holds one entry per pair with only
ids and changing values. A 60-pair chat stays small, and text is never duplicated.

```json
{
  "schema_version": "1.0",
  "chat_id": "c05_research_medium",
  "total_pairs": 7,
  "entities": {
    "outcomes": {
      "outcome 3": { "text_by_pair": { "1": "Expanded paper bank and recommendations" },
                      "first_action_id": "U(1,2)" }
    },
    "atoms": {
      "outcome 3/req 2": {
        "kind": "requirement",
        "outcome_id": "outcome 3",
        "text": "The selected research papers must bridge both angles ...",
        "creation_action_id": "U(2,1)",
        "creation_pair": 2,
        "provenance": "user",
        "resolved_from": "outcome 3/slot 1",
        "evidence_quote": "Both — I want the presentation to bridge them"
      },
      "outcome 3/slot 1": {
        "kind": "open_question",
        "outcome_id": "outcome 3",
        "text": "Selection of two specific research directions ...",
        "creation_action_id": "A(1,8)",
        "creation_pair": 1,
        "provenance": "ai",
        "evidence_quote": "..."
      }
    }
  },
  "frames": [
    {
      "pair": 2,
      "event": { "kind": "born", "outcome_ids": ["outcome 4"] },
      "focus_outcome_id": "outcome 4",
      "totals": { "mass": 237.0, "mass_user": 63.0, "mass_ai": 174.0 },
      "nodes": [
        { "id": "outcome 1", "role": "root", "parent": null },
        { "id": "outcome 3", "role": "outcome", "parent": "outcome 1",
          "born_pair": 1, "state": "active",
          "mass": 143.0, "mass_user": 34.0, "mass_ai": 109.0,
          "mass_rel": 1.0, "delta": 125.0 }
      ],
      "edges": [
        { "kind": "parent", "source": "outcome 1", "target": "outcome 3", "state": "active" },
        { "kind": "related", "source": "outcome 3", "target": "outcome 4" }
      ],
      "atoms": [
        { "id": "outcome 3/req 2", "status": "resolved", "resolved_by": "user" },
        { "id": "outcome 4/slot 1", "status": "open" }
      ]
    }
  ]
}
```

The masses in this example are c05 at pair 2, from today's ledger (outcome 2: 19 + 25,
outcome 3: 34 + 109, outcome 4: 10 + 40). Texts are shortened.

**Rules the schema encodes**

- Ids are `(outcome_id, local_id)`, joined as `"outcome 3/req 2"`, because `req_id` is
  unique only within an outcome (E0 lesson).
- `mass`, `mass_user`, `mass_ai`, `delta` are cumulative ledger sums per spec Function 2
  and 3. `mass_user + mass_ai == mass`, always.
- `mass_rel` = mass ÷ the largest child mass in that frame. It is the only size input the
  renderer gets. Pixels are design tokens, not data.
- `state`: `active` if `delta > 0` this pair, else `dormant` (spec Function 3).
- `event.kind`: `genesis` (pair 1), `born`, `reactivated`, `surge` (largest delta), `quiet`
  (no ledger rows this pair). Never invented.
- `focus_outcome_id`: the outcome of the latest open question created this pair; else the
  outcome with the largest delta (ties to the lowest id); else `null` for a quiet pair.
  Never "first child".
- Atom `provenance` comes from the creation action's prefix (`U` user, `A` AI). A resolved
  requirement has `resolved_from`, and `resolved_by` follows the same rule (spec Function 6).
- Atom `status` per frame: `active`, `open`, `resolved`. Abandoned questions are left out
  of the frame from the abandon pair on (spec Step 5.4 edge case 4).
- Multiple roots are allowed by the schema (`role: "root"` on more than one node), so
  question Q7 can be answered later without a schema change.
- **Brain compatibility** (`docs/Brain Vision.md`): every id is unique within its chat and
  becomes globally unique as `<chat_id>/<id>`, so a later cross-chat layer can link any
  node or atom. Every element keeps its action ids, so any mark can trace to its source
  pair. Nothing in the schema assumes one chat on screen.
- `text_by_pair` records an outcome's title at each pair it changed. One entry if it never
  changed. Its shape is decided at gate S2 from the S1 churn report.

---

## 6. The design system interface (for the parallel DESIGN SYSTEM agent)

The design system is its own co-created programme: `docs/briefs/D Track Brief.md`. It
takes as long as it takes, and G1 never waits for it. G1 needs exactly one thing from it:
**values for the names below**, delivered at D-track milestone M1 (end of D5). The graph
code uses these names and nothing else: no hex values, pixel sizes or durations written in
the graph's own code. Until M1, APP uses a clearly marked fallback file
(`web/src/graph/tokens.fallback.css`) with the prototype's current values. Swapping it for
the real tokens is then a one-line import change.

| Group | Token names |
|---|---|
| Surface | `--graph-bg`, `--graph-grid`, `--graph-vignette` |
| Parties | `--party-user`, `--party-ai`, `--party-user-soft`, `--party-ai-soft` |
| Nodes | `--node-root-fill`, `--node-fill`, `--node-stroke`, `--node-radius-min`, `--node-radius-max`, `--node-root-radius`, `--node-glow-strength` |
| Tethers | `--tether-active`, `--tether-active-opacity`, `--tether-dormant`, `--tether-dormant-opacity`, `--tether-width`, `--related-dash`, `--related-opacity` |
| Atoms | `--atom-bead-radius`, `--atom-ring-radius`, `--atom-ring-stroke`, `--atom-bullseye-outer-radius`, `--atom-orbit-gap` |
| Focus | `--focus-halo`, `--focus-halo-radius`, `--focus-breathe-duration` |
| Labels | `--label-font`, `--label-root-size`, `--label-size`, `--label-color`, `--label-muted`, `--label-min-zoom-opacity` |
| Tooltip | `--tooltip-bg`, `--tooltip-border`, `--tooltip-header-size`, `--tooltip-body-size` |
| Scrubber | `--scrub-rail`, `--scrub-fill-start`, `--scrub-fill-end`, `--scrub-notch`, `--scrub-notch-current` |
| Motion | `--motion-birth`, `--motion-dormancy`, `--motion-reactivate`, `--motion-scrub`, `--motion-reduced` (respects `prefers-reduced-motion`) |

The D track may rename or regroup these names (its D3 decides the naming grammar). If it
does, it publishes a mapping, and APP updates the graph's imports in one step.

**One decision the design system must make:** the party colours conflict.
`Build Playbook.md` §5 says colours are law: blue `#0057FF` = you, orange `#E85A0A` = AI.
`GRAPH_SYSTEM_SPEC.md` uses cyan `#38bdf8` and amber `#fb923c`. One pair has to win, or the
design system defines both as theme variants. G1 only reads `--party-user` and
`--party-ai`, so either answer works.

Delivery: a `tokens.css` (custom properties, light and dark) and a `tokens.json` with the
same names, in the design system's own folder. APP imports them, never copies them.

---

## 7. Steps

### Pre-work (OWNER, before S1)

- **P1** Commit `design_pack/` as the reference prototype, and the `AGENTS.md` symlink, in
  one owner commit. Leave the untracked corpus entries to DATA OPS.
- **P2** Append the APP role from section 9 and the DESIGN SYSTEM role from D Track
  Brief section 11 to `docs/Roles Documentation.md`.
- **P3** Log Q11 (outcome identity across pairs, D9) and Q12 (slot choices do not exist, D4)
  in `SPEC_QUESTIONS.md`.

---

### S1 — Per-pair state snapshots and the churn report · ENGINE

`run_chat()` overwrites `state.json` every pair, so history is lost. Fix that without
touching extraction.

- After each pair, also write `run/snapshots/state_p<NN>.json` (same schema as `state.json`,
  validated).
- Re-run all ten processed chats with `LLM_CACHE_MODE=replay`. Zero network calls.
- **Determinism check first:** the replayed `state.json` and `ledger.jsonl` must be
  byte-identical to the committed ones. If not, stop and report. That's an E-track bug, not
  a G1 problem.
- `scripts/graph_churn_report.py` prints per chat: outcomes per pair, renames, id changes,
  outcomes dropped and re-added, re-parenting, and requirements whose outcome changed.

**Verify:** churn table for ten chats, pasted. Network disabled during the run.

**Commit:** `G1.S1: per-pair state snapshots and churn report — history for the graph`

---

### S2 — OWNER GATE: identity rule and schema freeze

The owner reads the churn report and decides Q11:

- **(a)** Final titles at every pair, as the panel does today. Simple, but it rewrites history.
- **(b)** Per-pair titles from snapshots, same node when the id is the same, rename shown
  in the UI. True history, needs `text_by_pair`.
- **(c)** Spec change so Step 1b receives prior outcomes (§12.3). Fixes the cause, and goes
  to the command center as an E-track item.

**(b) is the default** unless the report shows id reuse, meaning one id pointing at two
different deliverables. In that case (c) is needed before G2 goes live.

Then the owner approves or edits section 5 and the schema is frozen.

**Output:** the decision logged in `SPEC_QUESTIONS.md`, and `graph_bundle.schema.json` committed.

---

### S3 — Graph facts and projection · ENGINE

Same split as Stage 4: facts in `quant.py`, shape in `projections/graph.py`. Projections
import quant, never the reverse.

- `quant.py`: `compute_outcome_masses(ledger_rows, max_pair)` → per outcome, cumulative
  `mass`, `mass_user`, `mass_ai`, and this pair's `delta`. Pure, no I/O.
- `projections/graph.py`: `export_graph_projection(target_dir, ledger_rows, snapshots,
  state_dict, max_pair)` → `graph_bundle.json`, schema-validated at write time.
- Every rule in section 5, nothing else. No layout, no pixels, no colours.

**Verify, tier1, against real data:**

| Chat | Pair | Total child mass |
|---|---|---|
| c05_research_medium | 1 → 7 | 62, 237, 412, 625, 919, 1049, 1137 |

These match the GRAPH_SYSTEM_SPEC audit table and today's ledger (checked 8 Oct 2026). Also
check pair 1, outcome 2 = user 19.0 + AI 25.0. Then the spec's slot story: `slot 1` on
outcome 3 opens at pair 1 and becomes a user-resolved bullseye `req 2` at pair 2.

**Commit:** `G1.S3: graph facts and projection — graph_bundle.json from ledger and snapshots`

---

### S4 — Graph invariants, pipeline wiring, ten-chat replay · ENGINE

Add to `tests/invariants.py` as `inv_g01` to `inv_g10`, and run them in `run_pair_checks`:

1. Every node id exists in that pair's state snapshot.
2. `mass` equals the ledger sum for that outcome up to that pair; user + AI = mass.
3. Every atom's creation action exists, and its quote passes the `inv_21` match.
4. An open question appears from its open pair until its resolve or abandon pair, and
   never after.
5. Every resolved requirement points at a slot that existed.
6. `born_pair` = first pair with a ledger row or atom for that outcome.
7. `focus_outcome_id` is a node in that frame, or `null` only on a quiet pair.
8. Every edge references nodes present in that frame; related edges are deduplicated.
9. No field outside the schema; no value the source data does not contain.
10. Purity: projecting twice gives byte-identical output, with no network.

Wire `export_graph_projection` into `run_chat()` right after the panel projection. Replay
all ten chats (and `fixture_pair1`, read-only, writing to a temporary folder).

**Verify:** all ten chats plus the fixture pass every invariant. `pytest -m tier1` green.
`data/chats/fixture_pair1/` untouched.

**Commit:** `G1.S4: graph invariants g01–g10, pipeline wiring, ten-chat replay`

**HANDOFF** to APP: the schema and ten real `graph_bundle.json` files are ready.

---

### S5 — Server: read API, events, replay trigger · APP

Restore only what the graph needs from the Phase 3 server (`git show 27e7d68:server/main.py`).

```
GET  /chats                     list: id, title, pairs, has_graph
GET  /chats/{id}/dialogue       turns, for the transcript pane
GET  /chats/{id}/graph          graph_bundle.json
GET  /chats/{id}/events         SSE: pipeline_status {phase}, pair_ready {pair}
POST /chats/{id}/replay         dev only: re-run the pipeline in replay mode, one pair at a
                                time, emitting events. Refuses unless LLM_CACHE_MODE=replay
```

- Files on disk stay the source of truth (Architecture D6). The server reads, never computes.
- `/replay` writes to a scratch copy of the chat folder, never over the committed one.

**Verify:** `curl` each endpoint against c05. The replay stream shows seven `pair_ready`
events in order, and the scratch `graph_bundle.json` is byte-identical to the committed one.

**Commit:** `G1.S5: server read API, SSE events, replay trigger — graph over HTTP`

---

### S6 — The graph view · APP · `ui-craft build graph-view`

**Input contract:** `mockups/graph-view.lock.md` and `mockups/graph-view.behavior.md`,
produced by the D track at D0.S5 from the owner's prototype with the section 3 fixes
applied. Building without both frozen is a blocking finding (skill rule). The finish line
is the skill's: **evidence for every manifest term** in a fidelity ledger, not green tests.

Port the 2D canvas renderer from `playground_obsidian.html` into `web/src/graph/`
(TypeScript, React, Zustand). Port the drawing, not the data logic: the bundle already
holds every value. Any term that seems wrong while building goes back to the D track as a
`resettle` request. It's never changed quietly in code.

- **Store:** one `viewedPair` and one LIVE or HISTORY state, shared with the panel. The
  graph is a new scrub source (interaction spec §3): node click scrubs to the node's
  `born_pair`, and atom click scrubs to `creation_pair` and scrolls the transcript to that
  action.
- **Layout:** seeded, computed once for the last frame's node set, then fixed, so nodes
  never jump while scrubbing (spec Phase 7 layout invariant). Atoms sit in the upper arc,
  labels below the node (spec Step 4.2). Lines are clipped at the circle edge (Function 5).
- **Drawing:** every colour, size and duration from the section 6 tokens. A test fails if
  a hex value or a pixel literal appears in `web/src/graph/`.
- **Tooltips:** spec Step 5.3, with D4 applied. No invented options.
- **Scrubber:** spec section 4, notches from `total_pairs`, arrow keys.
- **Empty and edge states:** a 1-pair chat, a quiet pair, a chat with no requirements, and
  a frame where the bundle is missing all render without errors and say what's happening.

**Verify:** all ten chats open and scrub end to end in the real browser, with no console
errors. Screenshot c05 at pairs 1, 2, 4 and 7 against the spec's state matrix.

**Commit:** `G1.S6: graph view — canvas renderer on graph_bundle, shared scrub state`

---

### S7 — Live, through replay · APP

Subscribe to `/events`. On `pair_ready`, fetch the bundle and animate the change:

- **born:** the node grows in at its fixed position, and its tether draws from the parent.
- **dormant:** the tether fades to the dormant tokens.
- **reactivated:** the tether brightens again.
- **resolved:** the ring fills into a bullseye.
- **focus:** the halo moves to the new focus outcome.

In HISTORY nothing yanks the view. The counter grows and the "Back to latest" pill appears
(interaction spec §4).

**Verify:** press replay on c05 and watch it build pairs 1→7. Screen recording or a
screenshot per pair. Same check while scrubbed back to pair 3: no jump.

**Commit:** `G1.S7: live updates via SSE — replay builds the graph pair by pair`

---

### S8 — OWNER GATE: visual check

First, in Claude Code, `ui-craft critique` on the running graph view (dual sub-agent,
with the D1 personas once they exist), then `ui-craft polish`. Then the owner opens every
chat and compares it with `GRAPH_SYSTEM_SPEC.md` and the lock by eye. APP fixes what the
owner marks, with at most one fix round before the phase close.

---

### S9 — Phase close · ENGINE

The standard ritual (Build Playbook §3): `scripts/phase_report.py` extended with a G1
section, BUILDLOG entry with its output pasted, tag `g1-done`, `AGENTS.md` current-phase
line updated, self-review against this brief.

---

## 8. Definition of Done

- [ ] Replayed state and ledger byte-identical to committed ones for all ten chats
- [ ] Churn report delivered; Q11 decided and logged
- [ ] `graph_bundle.schema.json` frozen; every bundle validates at write time
- [ ] c05 child mass 62, 237, 412, 625, 919, 1049, 1137, exact, in a tier1 test
- [ ] c05 slot 1 → req 2 bullseye at pair 2, user-resolved, in a tier1 test
- [ ] `inv_g01`–`inv_g10` pass on ten chats and the fixture
- [ ] `run_chat()` writes `graph_bundle.json` every pair
- [ ] Server endpoints pass `curl` checks; replay emits ordered events; scratch output
      byte-identical
- [ ] All ten chats render and scrub in the browser with no console errors
- [ ] No hex value or pixel literal in `web/src/graph/`; all from token names (the
      fallback file until D-track M1)
- [ ] Live replay of c05 animates births, dormancy, reactivation, resolution and focus
- [ ] Fidelity ledger: evidence for every term in `mockups/graph-view.lock.md`
- [ ] `ui-craft critique` and `polish` run; owner visual gate passed
- [ ] Zero LLM calls made in the phase (cassette replay only)
- [ ] `data/chats/fixture_pair1/` untouched; existing panel numbers unchanged
- [ ] `pytest` green, every new test carrying a tier marker

---

## 9. Roles to append to `docs/Roles Documentation.md`

```yaml
- name: APP
  job: serve engine artifacts and render them in the web app
  owns: server/, web/ (except web/src/design-system/)
  reads: everything
  never: engine/, tests/invariants.py, data/, the schemas, web/src/design-system/
  brief: docs/briefs/G1 Brief.md
  rules:
    - the frontend never computes a measured value; it renders the bundle
    - no colour, size or duration literal in graph code; tokens only
    - nothing yanks the user out of HISTORY

```

The DESIGN SYSTEM role entry is in `docs/briefs/D Track Brief.md` section 11. Append it
from there.

---

## 10. Who works when

| Week | ENGINE (Claude Code) | APP (Codex or Antigravity) | DESIGN SYSTEM (D track, own pace) | OWNER |
|---|---|---|---|---|
| 1 | S1 snapshots, churn | — | D0, ending with D0.S5 graph-view lock → HANDOFF | P1–P3, then gate S2; approve the graph-view lock |
| 1–2 | S3 projection | S5 server against a hand-made c05 bundle | D1 principles | — |
| 2 | S4 invariants, replay → HANDOFF | S6 `build graph-view` on fallback tokens | D2 directions | — |
| 3 | — | S7 live | D3 foundation architecture | Gate S8 |
| 3 | S9 close | — | — | Tag `g1-done` |
| later | — | Swap to real tokens at D-track M1 | D4–D5 → M1 HANDOFF | Visual re-check |

One writer per path holds throughout: ENGINE never touches `server/` or `web/`, and APP
never touches `engine/`. Each role starts from repo state, never another chat. If ENGINE
starts E3 in the same weeks, G1's ENGINE steps (about two days of work) go first.

---

## 11. Edge cases that must be handled, not discovered

| Case | Where | Expected |
|---|---|---|
| 1-pair chat | c10, c16, c17 | One frame, scrubber with one notch and disabled arrows |
| Quiet pair | any pair with no ledger rows | `event.kind = quiet`, focus `null`, every tether dormant |
| Outcome renamed | c15 pairs 4–6 (checkpoints) | Per S2 decision |
| Outcome dropped, then re-added | c15 | Same id → same node and position; gap frames omit it |
| Abandoned question | c05 slot 1 on outcome 1 (pair 4) | Visible until the abandon pair, gone after |
| Reactivation after dormancy | c05 outcome 4, pair 7 | `event.kind = reactivated`, tether brightens |
| Many outcomes | any chat with more than 6 | Layout still stable and readable; no fixed slots |
| Long requirement text | common | Tooltip wraps; nothing clipped |
| Engine run halted by an invariant | `status.json` unhealthy | Graph shows the last healthy pair and says so |

---

## 12. What G1 does not answer, and what comes next

- **G2 — Live in the app.** `POST /messages`, a real chat in the app, the pipeline running
  live per turn. Needs the cost seam and the model bake-off (cost playbook) first, and
  Q11 option (c) if S1 shows id reuse.
- **G3 — Outside sources.** Claude Code and Codex transcripts first, then the browser
  extension.
- **G4 — The head.** The 3D and cross-chat views, built on the same bundle.

G1 gives you the graph, correct and tested, on real data, in the real app, moving as the
engine produces pairs. Everything after it reuses this seam.

---

## 13. Kickoff prompts

**ENGINE, fresh Claude Code session:**

```
Read AGENTS.md fully first. Its workflow gates apply (one step per response, a preamble
before each step, wait for my "start task" and "Finish Step"). Then read docs/Working
Rules.md, your ENGINE entry in docs/Roles Documentation.md, docs/briefs/G1 Brief.md in
full, design_pack/GRAPH_SYSTEM_SPEC.md in full, and the files G1 section 2 lists for
ENGINE. Read the last two BUILDLOG entries.

You are doing G1.S1, then S3, S4 and S9, with the owner gate S2 after S1. Nothing else.

Hard rules: zero LLM calls; every run uses LLM_CACHE_MODE=replay with the network
disabled. Do not touch Steps 1a–3, their prompts, existing quant.py functions, the five
existing schemas, server/, web/, or data/chats/fixture_pair1/. Key every requirement and
slot on (outcome_id, local id). Anything touching a mass or a sum: never improvise; stop
and log it.

Begin with your preamble for S1.
```

**APP, fresh Codex or Antigravity session, after the S4 HANDOFF (S5 may start earlier
against a hand-made c05 bundle):**

```
Read AGENTS.md fully first. Its workflow gates apply. Then read docs/Working Rules.md,
your APP entry in docs/Roles Documentation.md, docs/briefs/G1 Brief.md in full,
design_pack/GRAPH_SYSTEM_SPEC.md in full, docs/Interaction Spec.md in full, and
docs/Architecture.md §3–§5. Read design_pack/playground_obsidian.html: it is the
renderer you are porting. Read the last two BUILDLOG entries.

You are doing G1.S5 through S7. Nothing else. For S6, read ui-craft/SKILL.md and
ui-craft/reference/build.md, then build against mockups/graph-view.lock.md and
mockups/graph-view.behavior.md.

Hard rules: the frontend never computes a measured value; it renders graph_bundle.json.
No colour, size or duration literals in web/src/graph/; use the token names in G1 section
6, with a clearly marked fallback file until the design system ships. No new dependency
without a SPEC_QUESTIONS entry. Do not touch engine/, tests/invariants.py, data/ or the
schemas. Verify in a real browser, not only with tests.

Begin with your preamble for S5.
```

**DESIGN SYSTEM:** use the kickoff prompt in `docs/briefs/D Track Brief.md` section 12.
It already points at section 6 of this file.
