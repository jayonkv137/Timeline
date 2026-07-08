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
