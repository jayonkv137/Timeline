# PHASE 2 BRIEF — The Engine (offline CLI)
**Tool: Claude Code · Opus, exclusively. The correctness core of the whole product.**

## Goal
`python -m engine run --input data/exports/<chat>.json --out data/chats/<name>/`
implements COTRACE_PIPELINE_SPEC v5 end to end: Steps 1a→1b→1c per pair, Step 2 per
touched outcome (with open slots), Step 3 Triggers A+B, Stage 4 → all five artifacts,
schema-valid, with caching, monitoring, and verification harnesses.

## Read first
COTRACE_PIPELINE_SPEC.md — ALL of it; it is the implementation spec. Prompts (§3–§7)
are copied VERBATIM into code. §9 = the iteration loop to implement literally. §10 =
Stage 4 math. §11.4 = the mechanical checks (become pytest). ARCHITECTURE §2–§3.

## Pre-requisites (owner does before session)
`.env` with `ANTHROPIC_API_KEY`. One exported chat placed at `data/exports/` (any JSON
with an ordered list of user/assistant turns — S1 writes the loader against whatever
format it actually has and documents it in the loader docstring).

## Steps
**S1 — Skeleton + LLM layer.** `engine/config.py` (env-driven: `MODEL_FAST` default
`claude-haiku-4-5` for Step 1a; `MODEL_MAIN` default `claude-sonnet-4-6` for
1b/1c/2/3; `STEP3_BATCH_SIZE` default 3). `engine/llm.py`: Anthropic client wrapper —
retries w/ backoff, every call appended to `<out>/run/llm_monitor.txt` (full prompt +
response), response → strip fences → `json.loads` → `json_repair` fallback; parse
failure after repair = hard error. `engine/prompts.py`: the spec's prompts verbatim,
file header states "FROZEN — copied from COTRACE_PIPELINE_SPEC v5 §<n>; do not edit
without spec change."
**S2 — STATE + artifact writers.** In-memory STATE (actions, outcome tree, intentions,
requirements, slots, ops log) ↔ `state.json`; `ledger.jsonl` append-only writer;
`snapshots.json`; every write validated against `engine/schemas/*` — validation failure
raises.
**S3 — Steps 1a/1b/1c** per pair exactly per §9.1 (B=1 pair; dialogue_summary
SELF-REFERENCE loop; `{all actions block}` ACCUMULATE; turn-id format U(x,y)/A(x,y)
enforced by regex check on every returned id).
**S4 — Step 2** per touched outcome (§9.2): per-outcome prior-requirements and
prior-open-slots blocks; ops applied to STATE (create/revise/delete/open_slot/resolve/
abandon incl. the 3-pair abandonment sweep); creation rows → ledger (5.0, kind=creation,
pair_added=t); resolve → slot-origin rows.
**S5 — Step 3** Triggers A+B per §9.3: origin turn = earliest creation id; Section A =
whole-dialogue FILTER minus exclusions; Section B incremental (track labeled action ids
per requirement so Trigger B sends only new ones); batching per STEP3_BATCH_SIZE;
labels → ledger rows (NO CONNECTION → no row); REVISES → revise_action_ids.
**S6 — Stage 4 (§10), pure code:** Δ(t,p), C(t,p), decisions counters (earliest-creation
tie-break), per-turn drawer data + chip colors, HOW signals + classification (§10.5
thresholds as config constants), R-SUM summary line (PANEL_SPEC §4.5 deterministic
template), panel_bundle.json writer.
**S7 — CLI + caching.** Per-step response cache keyed on (step, input-hash) under
`<out>/run/`; `--pairs N` limit; `--resume`; `--contributions-only` (recompute Stage 4
from existing ledger without LLM calls).
**S8 — Verification harnesses (the phase's teeth):**
(a) `tests/test_engine_checks.py` — §11.4 mechanical checks against any output folder.
(b) **Fixture regression (EXACT, deterministic):** run the Stage-4 module alone on
`data/fixtures/ledger_pair1.json` → must reproduce Δ_you=87.0, Δ_AI=314.0, direction
21.7/78.3, counts 4/10, mode COPILOT, chip colors (13 grey/1 orange). No tolerance —
this path has no LLM in it.
(c) **Full-pipeline smoke:** run on the export, pair 1 only → all artifacts
schema-valid, checks (a) pass, and write `COMPARISON.md` (requirement count, direction,
mode vs. the fixture) for human review. Numbers WILL differ from the fixture —
LLM nondeterminism is documented and expected; structure and checks are the gate,
the comparison is for the owner's eyes.

## Definition of Done
pytest green on (a)+(b) · (c) artifacts valid + COMPARISON.md generated · cost & latency
summary extracted from llm_monitor into the BUILDLOG entry.

## Out of scope
Server, SSE, frontend, embeddings prefilter (P5), E1/E2 evaluation layer.

## Kickoff prompt addendum
```
AGENTS.md rule 5 is absolute for S8(b): exact reproduction of the canonical numbers
from the fixture ledger, zero tolerance — if it disagrees, the Stage-4 code is wrong.
Prompts are copied verbatim from the spec; if a prompt seems to need changing, that is
a SPEC_QUESTIONS.md entry and a conservative workaround, never an edit.
```
