# SPEC_QUESTIONS.md
(Contradictions, gaps, and deviations — per Build Playbook §4. Newest at the bottom.)

## Q1 — Provider/SDK: OpenAI-compatible Gemini instead of Anthropic (RESOLVED, owner-approved)
- **What:** PHASE2_BRIEF S1 specifies the Anthropic SDK with `MODEL_FAST=claude-haiku-4-5`
  / `MODEL_MAIN=claude-sonnet-4-6`, and Build Playbook §5's dependency allowlist names
  `anthropic`. The owner switched the project to Gemini via the OpenAI-compatible
  endpoint (BUILDLOG entry 2026-07-08 07:37, commit 990b096: `.env` scheme `LLM_API_KEY`
  + `LLM_BASE_URL`, `MODEL_FAST=gemini-3.1-flash-lite`, `MODEL_MAIN=gemini-3.5-flash`),
  and confirmed verbally in the Phase 2 session ("I only changed to Gemini, no problem").
- **Options considered:** (a) follow the brief literally (Anthropic SDK), (b) follow the
  owner's amendment (OpenAI SDK, configurable `base_url`).
- **Taken:** (b). `engine/llm.py` builds on the `openai` package with `base_url` from
  config; `openai` replaces `anthropic` on the dependency allowlist. Model defaults come
  from env with Gemini fallbacks. Everything else in S1 (retries, monitor logging, fence
  strip → json.loads → json_repair → hard error) is unchanged from the brief.
- **Status:** RESOLVED — owner decision, recorded here because other agents cannot see
  the chat. Not a REVISIT.

## Q2 — PHASE2_BRIEF S1 export loader deferred (RESOLVED in E0)
- **What:** The brief's pre-requisite "one exported chat placed at `data/exports/`" was
  initially deferred when data/exports/ was empty.
- **Taken:** Resolved in Phase E0. `scripts/ingest_export.py` implements the official
  export loader per `IMPORT_SPEC.md` v1.0, normalizing real chat exports into `data/corpus/`
  with full schema validation and fidelity accounting.
- **Status:** RESOLVED in E0.S2-S4.

## Q3 — state.schema.json has no home for cross-pair working data
- **What:** The pipeline needs several pieces of cross-pair working data that
  `state.schema.json` (additionalProperties: false) cannot hold: Step 1b's
  `action_to_outcome` mapping (consumed by Step 2's per-outcome FILTER), the rolling
  `dialogue_summary` (Step 1b SELF-REFERENCE), Trigger B's per-requirement
  labeled-action-id tracking (§9.3: send only NEW subsequent actions), and slot age
  counters for the 3-pair abandonment sweep. ARCHITECTURE §3's state.json contract has
  no fields for these.
- **Options considered:** (a) extend state.schema.json — rejected: schemas are frozen
  Phase 0 contracts, and the frozen fixture's state.json would no longer be the same
  shape; (b) recompute from scratch each run — impossible for dialogue_summary and
  Trigger-B tracking, which are genuinely stateful; (c) persist them in an internal,
  non-contract file under `<out>/run/` (already gitignored, already designated for
  run-internal artifacts like caches and llm_monitor.txt).
- **Taken:** (c) — `<out>/run/pipeline_state.json`, written by `engine/state.py`
  alongside every state.json save, read on `--resume`. The five contract artifacts are
  untouched; this file is engine-internal and carries no panel-facing data.
- **Status:** REVISIT — if the command center wants this data in the contract, a spec
  amendment can move it into state.schema.json later; the engine change would be small.

## Q4 — Provenance sidecar lives outside the frozen contract (REVISIT)
- **What:** IMPORT_SPEC needs per-turn provenance (origin: typed | injected | model,
  flags, dropped media) and per-chat fidelity counts. `dialogue.schema.json` is a
  Phase 0 frozen contract with `additionalProperties: false`, so these cannot be added
  to it without changing the shape of the frozen fixture's dialogue.json.
- **Options considered:** (a) extend dialogue.schema.json — rejected, same reasoning as
  Q3; (b) discard provenance — rejected, it is needed to interpret results and to make
  the injected-text decision reversible; (c) a sidecar file in the corpus entry.
- **Taken:** (c) — `data/corpus/<id>/source_meta.json`, parallel to dialogue.json and
  joinable by index. Not a contract artifact, engine-internal, same precedent as Q3's
  `run/pipeline_state.json`.
- **Status:** REVISIT — if the command centre later wants origin inside the contract,
  the importer change is small.

## Q5 — Injected text counted as user input (RESOLVED, owner decision)
- **What:** Some turns arrive in the user slot but were produced by tooling: slash
  command expansions, loaded skill text, system notices, auto-continue strings, task
  notifications. Measured on a real Claude Code session, 2,006 lines contained 22
  non-tool user turns of which roughly 16–18 were actually typed. Counting injected
  text as user input inflates user SHAPER mass with words the person never wrote.
- **Options considered:** (a) strip injected turns at import; (b) count them as user
  input; (c) tag them and decide at pipeline time.
- **Taken:** (b) as the v1 behaviour, per owner decision: if it is text in the user
  slot, the engine treats it as user text. Implemented as (c) mechanically — the
  importer tags `origin` and never strips — so the behaviour matches the decision while
  remaining reversible via `IMPORT_INJECTED_AS_USER`, read at pipeline time.
- **Status:** RESOLVED. Revisit after the first stability measurement, which will show
  whether injected turns materially move the numbers on any corpus chat.

## Q6 — Tool narration left inside AI text (RESOLVED)
- **What:** Claude web exports flatten tool use into the assistant's prose as
  "Used tool … Done". 17 of 186 messages in one sample. Step 1a will extract actions
  from this text, so an AI searching its own project history may appear as a
  goal-shaping action.
- **Options considered:** (a) strip at import; (b) leave it and let Step 1a decide;
  (c) tag the turn and give Step 1a an instruction about it, which needs a prompt
  change and therefore a pipeline spec amendment.
- **Taken:** (b). Empirical inspection across multi-turn chats containing tool narration
  (e.g., `c05_research_medium` pair 1 reading 13 files) shows that Step 1a accurately
  extracts execution acts (e.g. `A(1,2)` "AI reads the user's handwritten notes") and
  assigns `role="EXECUTOR"`. Step 1c and Step 2/3 score them as standard execution
  activities without creating spurious requirements or corrupting SHAPER metrics.
- **Status:** RESOLVED.

## Q7 — Single-root outcome tree constraint vs multi-topic conversational drift (OPEN)
- **What:** `inv_06_outcome_tree` enforces that the outcome tree has exactly one root
  (`len(roots) == 1`). Real chats can span multiple totally unrelated topics in the same
  session (e.g. visa extension, bed frame, portfolio website). Forcing a single root may
  compel Step 1b to invent an artificial umbrella goal that the user never expressed.
- **Options considered:** (a) require a single umbrella root in state; (b) allow a forest
  of multiple disconnected root outcomes in `state.json` and attach a virtual root only
  at UI render time; (c) split multi-topic sessions into separate corpus chats at import.
- **Taken:** (a). In the 10-chat corpus extraction evaluation across 4 distinct domains
  (creative, research, coding, writing) up to 7 pairs deep, Step 1b consistently and
  accurately established a single, natural overarching root outcome representing the
  session's core objective (e.g., "Course assignment strategy and deliverables" in `c05`,
  "Design system audit and Figma migration plan" in `c20`, "Design system for AI
  interaction modes" in `c04`). Evolving topics and sub-tasks branched cleanly as child
  outcomes under this single root without any observed hallucination of unnatural umbrella
  constructs. All 10 chats satisfied `inv_06_outcome_tree` cleanly (`len(roots) == 1`).
- **Status:** OPEN — Reopened before E2; closed prematurely on ten chats of at most 7 pairs, none genuinely multi-topic. Tested properly in E3 with stratified long chats.

## Q8 — 5-tuple uniqueness key for honesty ledger rows (RESOLVED)
- **What:** `docs/TEST_STRATEGY.md` §2 item 5 specified a 4-tuple `(action_id, req_id, pair_added, kind)`
  for ledger row uniqueness. However, `req_id` is scoped per outcome (`o1.r1` vs `o3.r1`).
  Rows sharing the same action, req_id, pair, and kind across different outcomes appeared
  as duplicates under the 4-tuple.
- **Options considered:** (a) enforce 4-tuple globally — would falsely reject valid ledger
  rows; (b) scope ledger uniqueness by including `outcome_id` as a 5-tuple:
  `(action_id, outcome_id, req_id, pair_added, kind)`.
- **Taken:** (b). `inv_05_no_duplicate_ledger_rows` enforces the 5-tuple. `TEST_STRATEGY.md` §2
  item 5 amended to match. Design note added: **requirement identity is `(outcome_id, req_id)`,
  never `req_id` alone.** Any future view or analysis module that treats a requirement as
  a node and keys it on `req_id` alone will silently merge unrelated requirements.
- **Status:** RESOLVED.

## Q9 — Widening of inv_21 quote matching beyond exact verbatim (REVISIT)
- **What:** During Phase E1, `inv_21` (quote provenance) was widened from strict verbatim substring matching to tolerate real-world transcript artifacts across four classes:
  1. `exact`: Verbatim character-for-character substring (including standard surrounding quotes stripping).
  2. `whitespace_normalised`: Case-folding, collapsed whitespace sequences (`\s+` -> `' '`), smart punctuation/dashes normalization, and markdown styling marker (`*`, `_`, `` ` ``, `>`) stripping.
  3. `segmented`: Sequential ordered segment appearance for quotes joined across ellipses (`...`, `…`) or transition arrows (`->`, `→`).
  4. `fuzzy`: In-order word matching with gap tolerance up to 15 words and speech stutter head/tail stripping (e.g. model cleaning conversational filler).
- **Why:** In real LLM chats, the model frequently quotes across pauses, strips formatting syntax, or cleans up speech disfluencies. Enforcing byte-exact substring matching falsely flagged genuinely grounded quotes as ungrounded hallucinations.
- **Empirical counts across all 10 E1 corpus chats (305 total action quotes):**
  - `exact`: 252 (82.6%)
  - `whitespace_normalised`: 23 (7.5%)
  - `segmented`: 26 (8.5%)
  - `fuzzy`: 4 (1.3%)
  - `unmatched`: 0 (0.0%)
- **Status:** REVISIT — The matching logic is preserved for pipeline stability, and every run now explicitly records the four counts in `run/report.json` and the phase verification report. The owner decides whether to retain fuzzy tolerances or tighten quote extraction prompts with the empirical numbers in front of him.

## Q10 — QUIET pair mode classification and schema representation (RESOLVED)
- **What:** Pipeline Spec §10.5 states: `quiet pair (no ops, Δ total < 2) → inherit`, whereas `panel_bundle.schema.json` explicitly defines the `"mode"` enum as `["CENTAUR", "COPILOT", "AUTOPILOT", "QUIET"]` and defines `split` as `% of non-quiet pairs`.
- **Options considered:**
  (a) set `mode` directly to the inherited prior mode — rejected: this would make `"QUIET"` unreachable despite being in the frozen schema enum, and would prevent downstream consumers from identifying quiet exchanges.
  (b) classify `mode = "QUIET"`, track `inherited_mode` (the previous non-quiet mode for UI metaphor inheritance), and exclude quiet pairs from the running `split` denominator.
- **Taken:** (b). `ModeFact` assigns `mode = "QUIET"`, preserves `inherited_mode` for the UI narrative line, and computes `split` percentages strictly over non-quiet history up to pair $t$.
- **Status:** RESOLVED.



