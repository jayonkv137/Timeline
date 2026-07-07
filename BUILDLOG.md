# BUILDLOG — append-only session journal
Every AI session on this repo ends by appending one entry below. Newest at the bottom.
This file is the context bridge to the command center (the planning chat): after each
session, the latest entry (+ test output, + screenshot if visual) is what gets reported
back. Never paste chat transcripts anywhere.

---
ENTRY TEMPLATE (copy, fill, append):

## [YYYY-MM-DD HH:MM] · <tool: Claude Code | Antigravity> · <model>
- **Phase/Step:** P0.S2 (example)
- **Did:** files created/changed, one line each
- **Decisions made:** anything not literally dictated by the specs (and why)
- **Spec contradictions/gaps flagged:** none | description (→ goes to command center)
- **Verification:** tests run + results, or "not applicable"
- **Next:** the exact next step
---

## 2026-07-08 01:00 · Antigravity · Claude Opus 4.6
- **Phase/Step:** P0.S1 — Scaffold
- **Did:**
  - Created directories: `engine/`, `engine/schemas/`, `server/`, `web/`, `data/chats/`, `data/fixtures/`, `tests/` (with `.gitkeep` files)
  - Created `.gitignore` (Python, Node, `.env`, `data/chats/*/run/`)
  - Created `.env.example` (`ANTHROPIC_API_KEY=`)
  - Created `README.md` (3 lines, pointing at `docs/`)
  - Created `requirements-dev.txt` (`pytest`, `jsonschema`)
  - Initialized git, committed as `P0.S1`
- **Decisions made:** Added `data/fixtures/` directory (referenced by brief but not yet populated). Added `.venv/`, `venv/`, `web/dist/` to `.gitignore` as standard practice.
- **Spec contradictions/gaps flagged:** none
- **Verification:** `git status` clean after commit; `find` tree matches brief's spec
- **Next:** P0.S2 — The five schemas

---

## 2026-07-08 01:03 · Antigravity · Claude Opus 4.6
- **Phase/Step:** P0.S2 — The five schemas
- **Did:**
  - `engine/schemas/dialogue.schema.json` — turns array: pair, speaker, text, attachments, ts
  - `engine/schemas/state.schema.json` — actions, outcomes tree, intentions, requirements (full lifecycle), slots (full lifecycle), operations_log
  - `engine/schemas/ledger_row.schema.json` — single JSONL row per Pipeline Spec §10.3
  - `engine/schemas/snapshots.schema.json` — per-pair t, delta_you, delta_ai, c_you, c_ai
  - `engine/schemas/panel_bundle.schema.json` — per pair: direction, decisions, timeline (drawer with per-req masses + chips + slots), goal (default_view + full_tree), how (mode + signals + split)
  - Committed as `P0.S2`
- **Decisions made:**
  - `dialogue.json` and `snapshots.json` schema as arrays; `state.json` and `panel_bundle.json` as objects; `ledger_row` validates one JSONL line (not array) — matches artifact semantics
  - `operations_log` items include `target_type` (requirement|slot) to disambiguate ops — not in spec but needed for unambiguous querying
  - Goal `default_view` and `full_tree` nodes include `depth` field — needed for thread-collapse display rules
  - All fields marked required; `additionalProperties: false` everywhere — strict contracts
- **Spec contradictions/gaps flagged:**
  - `operations_log` structure not specified anywhere in the four docs — Architecture §3 mentions it as a state.json field but no schema is given. Designed it as chronological op records with pair/outcome_id/op/target_id/target_type. → goes to command center for validation
- **Verification:** All 5 schemas pass `Draft202012Validator.check_schema()` — valid JSON Schema draft 2020-12
- **Next:** P0.S3 — Build the fixture (assigned to Claude Code)
---
