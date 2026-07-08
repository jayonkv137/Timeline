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
