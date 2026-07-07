# PHASE 0 BRIEF — Contracts & Scaffold
(Paste this as the opening message of the Claude Code session. Repo root already
contains: CLAUDE.md, docs/ with the four spec documents, data/fixtures/ with
ledger_pair1.json and stage4_pair1_results.md.)

---

Read CLAUDE.md first, then ARCHITECTURE.md §3 (artifact contracts), §6 Phase 0, and §7
(protocol). Also skim COTRACE_PIPELINE_SPEC.md §10.3–§10.5 (ledger + derivations) and
PANEL_SPEC.md §6 (element→backend contract). Follow the workflow gates in CLAUDE.md rule 2
strictly: one step per response, preamble first, wait for my "start task" and "Finish
Step".

## Phase goal
Freeze the data contracts and produce the first complete, schema-valid fixture chat
folder — before any application code exists. Nothing in this phase calls an LLM.

## Steps (in order, one at a time)

**STEP 1 — Scaffold.**
Create the monorepo skeleton: `engine/` `engine/schemas/` `server/` `web/` `data/chats/`
`tests/`, plus `.gitignore` (python, node, .env, data/chats/*/run/), `.env.example`
(ANTHROPIC_API_KEY=), a stub `README.md` (three lines, pointing at docs/), and
`requirements-dev.txt` (pytest, jsonschema). Initialize git. No app code.

**STEP 2 — The five schemas** (JSON Schema, draft 2020-12, one file each in
`engine/schemas/`), fields exactly per ARCHITECTURE.md §3:
1. `dialogue.schema.json` — turns: pair (int), speaker (user|ai), text, attachments[],
   ts.
2. `state.schema.json` — actions[] (id `U(x,y)`/`A(x,y)`, type, text, role
   SHAPER|EXECUTOR|OTHER, evidence_quote), outcomes[] (id, text, turn_id, parent, children,
   related), intentions[], requirements[] (outcome_id, req_id, text, type, status,
   creation_action_ids, contributing_action_ids, implementation_action_ids,
   revise_action_ids, related_to, explicit_or_implicit, rationale, created_at_pair),
   slots[] (slot_id, outcome_id, text, type, origin user|AI, status open|resolved|abandoned,
   creation_action_ids, contributing_action_ids, resolved_into), operations_log[].
3. `ledger_row.schema.json` — one JSONL line: pair_added, action_id, speaker (U|A), role,
   outcome_id, req_id, score (number), kind (creation|labeled|slot-origin). This is
   PIPELINE_SPEC §10.3 verbatim.
4. `snapshots.schema.json` — per pair: t, delta_you, delta_ai, c_you, c_ai.
5. `panel_bundle.schema.json` — per pair, everything PANEL_SPEC §6 names: direction
   {you_pct, ai_pct}; decisions {you_count, ai_count, latest_ai_example}; timeline row
   {pair, delta_you, delta_ai, summary, drawer: {requirements: [{outcome_id, req_id,
   label, op, delta_you, delta_ai, chip: blue|grey|orange}], slots: [{slot_id, origin,
   status, resolved_into}]}}; goal {default_view nodes[], full_tree}; how {mode
   CENTAUR|COPILOT|AUTOPILOT|QUIET, signals {w_you, w_ai, h_you, h_ai, substantive_user},
   split {centaur_pct, copilot_pct, autopilot_pct}}.

**STEP 3 — Build the fixture** `data/chats/fixture_pair1/` by a script
(`engine/scripts/build_fixture.py`) that reads `data/fixtures/ledger_pair1.json`
(fields: pair,aid,spk,role,o,r,s,k) and `stage4_pair1_results.md`, and writes:
- `ledger.jsonl` — the 157 rows, field names mapped to the schema.
- `snapshots.json` — one entry: t=1, delta/c from the canonical numbers.
- `panel_bundle.json` — pair 1, using ONLY the verified values in
  stage4_pair1_results.md (direction 21.7/78.3; decisions 4·10 with the triple-references
  example text; the 14 drawer rows with per-req masses and chip colors — 13 grey, o5/r2
  orange; 5 open slots, all AI-origin; HOW COPILOT with signals 4/10, 47.0/239.0, true).
  Goal section: root "Style DNA & Production Bible", current per the fixture README note.
- `state.json` and `dialogue.json` — STUB level: schema-valid, requirements/slots real
  (ids, creators, known texts), but action texts / dialogue turns marked
  "(not captured in fixture)". Add `data/chats/fixture_pair1/README.md` stating exactly
  which fields are verified vs. reconstructed — no silent fake data (CLAUDE.md rule 5
  spirit).

**STEP 4 — The DoD tests** (`tests/test_phase0.py`):
(a) every fixture file validates against its schema;
(b) canonical-numbers check recomputed from ledger.jsonl: sum U scores == 87.0, sum A ==
314.0, 14 distinct (outcome_id, req_id), creator split 4/10 by earliest-creation-action
rule, zero creation/labeled overlap per requirement, zero duplicate (action_id, req) rows
— i.e., PIPELINE_SPEC §11.4 as executable checks;
(c) panel_bundle direction values equal ledger-derived values within 0.1.
Run pytest; all green = Phase 0 done. Then update CLAUDE.md's Current phase line to
Phase 1 and stop.

## Out of scope (do not touch)
LLM calls, prompts, server code, React code, styling, Phase 1 concerns.
