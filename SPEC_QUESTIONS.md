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

## Q2 — PHASE2_BRIEF S1 export loader deferred (data/exports/ empty)
- **What:** The brief's pre-requisite "one exported chat placed at `data/exports/`" is
  not met; the folder was created empty in S1. S1 says the loader is written "against
  whatever format it actually has", which is impossible without the file.
- **Taken:** Conservative deferral — loader will be written when the export lands
  (owner said before S8(c), the only step that needs it). No format invented.
- **Status:** OPEN until the export file appears. Not a spec problem, a sequencing note.

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

## Q6 — Tool narration left inside AI text (OPEN)
- **What:** Claude web exports flatten tool use into the assistant's prose as
  "Used tool … Done". 17 of 186 messages in one sample. Step 1a will extract actions
  from this text, so an AI searching its own project history may appear as a
  goal-shaping action.
- **Options considered:** (a) strip at import; (b) leave it and let Step 1a decide;
  (c) tag the turn and give Step 1a an instruction about it, which needs a prompt
  change and therefore a pipeline spec amendment.
- **Taken:** (b) for now, with (c) prepared: the importer tags the turn
  `tool_narration` and counts it, so the decision can be made on evidence after E1
  shows what is actually extracted from those turns.
- **Status:** OPEN until E1 close.

