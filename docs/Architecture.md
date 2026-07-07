# Agency Panel — System Architecture & Build Plan (v1)
### The command-center document: every architectural decision, the full data flow, and the phased plan executed step-by-step in Claude Code

**Status:** v1.1 — the fourth and final planning document. Companions: COTRACE_PIPELINE_SPEC
v5 (what the backend computes), PANEL_SPEC v2.0 (what renders), INTERACTION_SPEC v1 (how it
behaves). This document decides HOW it is built: stack, APIs, storage, orchestration,
real-time mechanism, and the incremental milestone plan.
v1.1: build site corrected to **Claude Code** (§7: CLAUDE.md routing, terminal briefs,
executable DoDs). v1.3: multi-tool build protocol — AGENTS.md as the canonical cross-tool
router (CLAUDE.md imports it), BUILDLOG.md as the append-only session journal and the
context bridge to the command center, and explicit tool/model routing (Antigravity =
scaffolding/UI/boilerplate; Claude Code Opus = engine/math/correctness-critical). Grounded
in current spec-driven-development practice: the repo is the only shared brain; hand off
filesystem state, never chats. v1.2: **goal corrected — the product IS the live chat application**
(type a message, AI replies in-app, panel computes in real time). Replay is demoted from
user-facing instrument to engine test harness only; live mode moves up to Phase 3.

---

## 1. The governing architectural idea: one engine, two input sources

The single design move that makes this buildable incrementally: **the pipeline engine
consumes "pair events" and does not know where they come from.**

```
 ┌────────────────────┐        ┌────────────────────┐
 │ REPLAY ADAPTER      │        │ LIVE CHAT           │
 │ (exported chat JSON,│        │ (user msg → Claude  │
 │  emitted pair by    │        │  reply → pair done) │
 │  pair, on command)  │        │                     │
 └─────────┬──────────┘        └─────────┬──────────┘
           └──────────── pair event ──────┘
                          ▼
              ┌──────────────────────────┐
              │  ENGINE (Python)          │   per pair: 1a → 1b → 1c →
              │  spec v5 §9 loop          │   2 (touched) → 3 (A+B) →
              │                           │   Stage 4 (pure math)
              └──────────┬───────────────┘
                          ▼ writes
              ┌──────────────────────────┐
              │  ARTIFACT STORE (files)   │  state.json · ledger.jsonl ·
              │  one folder per chat      │  snapshots.json · panel_bundle.json
              └──────────┬───────────────┘
                          ▼ read by
              ┌──────────────────────────┐
              │  SERVER (FastAPI)         │  REST for data · SSE for
              │                           │  "pair N ready" push
              └──────────┬───────────────┘
                          ▼
              ┌──────────────────────────┐
              │  WEB APP (React + Vite)   │  chat UI + the 5-section rail,
              │                           │  rendered per PANEL_SPEC v2.0
              └──────────────────────────┘
```

Consequences: **the live chat application is the product**; the replay adapter is the
engine's TEST HARNESS (a CLI input, never a user-facing mode). Same engine either way —
which is exactly what lets every build phase be verified against the manually-traced
chats we already trust, while building toward live only.

---

## 2. Decisions, with rationale (the architect's table)

| # | Decision | Choice | Why |
|---|---|---|---|
| D1 | Product & build order | **The live chat app is the product.** Replay = test harness only (engine CLI on exported chats), never a user-facing mode | The thesis is in-the-moment; a post-hoc viewer as destination would rebuild what the design rejects. Verified ground truth (pair-1 ledger; 7 traced chats) still anchors testing — at the terminal, not in a browser UI we'd later discard. |
| D2 | Engine language | **Python** | trace_engine.py exists; the official repo is Python; json-repair/numpy/embeddings ecosystem; the manual-verification scripts from this project are Python. |
| D3 | Frontend | **React + Vite (+ Zustand for state)** | Already the owner's proven working stack and Claude Code Desktop workflow from prior, unrelated projects — zero new learning cost. (No connection to those projects; purely a familiarity argument.) |
| D4 | Server | **FastAPI** | Same language as engine (no serialization seam), async-native for background pipeline jobs, SSE support trivial. |
| D5 | Real-time push | **SSE (Server-Sent Events), not WebSockets** | Panel updates are strictly one-directional (server→client). SSE is HTTP, simpler, auto-reconnects. WebSockets buy nothing here. |
| D6 | Storage | **Files, one folder per chat** (repo pattern) — no database in v1 | Debuggable, git-diffable, matches the repo's proven artifact layout and our manual workflow. A DB earns its place only if multi-user; this is a single-user instrument. |
| D7 | Chat LLM | **Anthropic API (Claude), streamed** | The product's own chat. Streaming = the typing indicator choreography in INTERACTION_SPEC §4. |
| D8 | Pipeline LLM | **Anthropic API, per-step model tiering**: cheap/fast model for Step 1a; stronger model for 1b/2/3 | Repo precedent (`--action_model` separate from `--model`). 1a is high-volume + simple; 2/3 are judgment-heavy. Config, not hardcode. |
| D9 | Step-2a embeddings | **Deferred to Phase 5** | v1 chats are short; sending the full preceding list is affordable and matches how all our verified data was produced. The τ=0.5 recipe (spec §9.5) is documented and slots in later without API changes. |
| D10 | Step-3 batching | **Adopt the repo's request batching** (N requirement blocks per call) from Phase 2 | Step 3 is the cost center (spec §12.7); batching is their proven mitigation. |
| D11 | Per-chat concurrency | **Strictly sequential per chat** (pair N+1's pipeline waits for N) | STATE is iterative by design (spec §9). Parallelism across *different* chats is free. |
| D12 | Engineering practices | Per-step caching · llm_monitor.txt (full call log) · json.loads-immediately + json-repair · frozen prompt files with version header | All four proven in the official repo; all four already required by spec v5 §11/§12. |
| D13 | Panel data shape | Server pre-computes a **panel_bundle** (all per-pair derived values); frontend does zero math | Keeps every number's provenance in one (tested, Python) place; the frontend is a pure renderer of PANEL_SPEC §6's contract table. |

---

## 3. The artifact contracts (the seam everything plugs into)

One folder per chat: `data/chats/<chat_id>/`

| File | Written by | Contains |
|---|---|---|
| `dialogue.json` | adapter (replay) or server (live) | turns: `{pair, speaker, text, attachments, ts}` |
| `state.json` | engine, after each pair | actions[], outcomes tree, intentions, requirements (with status/revise_action_ids), slots (with lifecycle), operations_log |
| `ledger.jsonl` | engine, append-only | one line per score row: `(pair_added, action_id, speaker, role, outcome_id, req_id, score, kind)` — exactly spec §10.3 |
| `snapshots.json` | engine | per-pair `(t, C_you, C_AI)` + per-pair Δ |
| `panel_bundle.json` | engine (Stage 4) | per pair: direction %, decisions counts + latest example, timeline rows (delta, R-SUM summary, drawer rows with per-turn Δ and chip colors, slot rings), goal render (3-node view + full tree), HOW mode + split — i.e., PANEL_SPEC §6, materialized |
| `run/` | engine | per-step raw outputs, cache, `llm_monitor.txt` |

**Schema-first rule:** these five schemas are written and frozen in Phase 0, before any
code. Fixture: the verified pair-1 ledger (`ledger_pair1.json`, 157 rows) converted into a
complete example folder by hand+script — the panel's first meal.

---

## 4. API surface (server)

```
POST /chats                          create chat (live) or import (replay: exported JSON)
POST /chats/{id}/messages            live mode: user message → streams Claude reply (SSE)
GET  /chats/{id}/bundle              full panel_bundle + dialogue (initial load)
GET  /chats/{id}/events              SSE: "pair_ready {t}" · "pipeline_status {phase}"
PATCH /chats/{id}/title              edit R0 (renames root node)
GET  /chats                          sidebar list
```

Five endpoints. The frontend never computes; it fetches the bundle, subscribes to events,
and re-renders at `viewedPair`. (Replay never reaches the server: it lives in the engine
CLI — `python -m engine run --input exported_chat.json` — as the test harness.)

## 5. One live turn, end to end (the sequence the whole system exists for)

```
user hits Enter
 → POST /messages; user bubble renders instantly (P-badge assigned)
 → server streams Claude's chat reply (SSE tokens) → typing dots → bubble fills
 → on reply completion: server enqueues pipeline job for pair t (asyncio task)
 → SSE "pipeline_status: running" → rail shows loading treatment
   (previous pair's values stay on screen — INTERACTION_SPEC §4 rule)
 → engine runs spec §9 loop → appends ledger rows → Stage 4 → rewrites panel_bundle
 → SSE "pair_ready t" → frontend fetches bundle delta → sections update atomically,
   timeline row t appears, counter increments
 → if user was in HISTORY: no yank; denominator increments; Back-pill available
```

Expected pipeline latency per turn at v1 (no batching of 1a–1c, Step-3 batched): roughly
5–20s depending on chat length — inside the loading choreography this is a feature
("the panel is thinking too"), not a bug. Cost scale: ~3 + touched-outcomes + ceil(reqs/batch)
LLM calls per pair; token growth is linear per spec §12.2 — accepted for v1, measured via
llm_monitor before optimizing.

---

## 6. The phased build plan (SDLC — what goes to Claude Code, in order)

Each phase has a **Definition of Done** and produces something runnable. One phase = one
or a few Claude Code sessions. Never start phase N+1 with phase N's DoD unmet. Wherever
possible a DoD is **executable** — a command Claude Code runs (a pytest suite, a diff
against fixture data), not a promise in prose.

**PHASE 0 — Contracts & scaffold** *(smallest possible; mostly schemas)*
Monorepo: `engine/` `server/` `web/` `data/` `docs/` (the four spec documents copied in)
plus `CLAUDE.md` at the root (§7 — how Claude Code inherits context). Write the five artifact schemas. Convert the pair-1
verified results into the first complete fixture folder.
**DoD:** `data/chats/fixture_pair1/` validates against the schemas.

**PHASE 1 — Panel shell on fixture** *(frontend, real data, zero backend)*
React app renders all five sections + chat transcript from the fixture folder loaded
statically. Visual language per PANEL_SPEC (trace colors, chips, spine bars); interactions
that exist with one pair: drawer accordion, goal chip, tooltip.
**DoD:** the first honest screenshot — the real pair-1 numbers (21.7/78.3 · 4 you/10 AI ·
COPILOT · 14 drawer rows, 13 grey 1 orange, 5 rings) on the real design.

**PHASE 2 — Engine as offline CLI** *(the heart)*
`python -m engine run --input exported_chat.json --out data/chats/x/` implementing spec v5:
prompt runner (Anthropic API, per-step caching, llm_monitor, json-repair), steps 1a→1c per
pair, Step 2 per touched outcome (with open-slot ops), Step 3 Trigger A+B (batched), Stage
4 → all artifacts.
**DoD:** engine re-runs the Style-DNA pair 1 and lands within nondeterminism range of the
manual ledger (structure identical; scores comparable); mechanical checks from spec §11.4
pass automatically.

**PHASE 3 — THE LIVE LOOP** *(the product moment)*
FastAPI server: `POST /messages` with streamed Claude replies (chat model per D7); on
reply completion, async pipeline job for the pair (D11 sequential); SSE `pipeline_status`
/ `pair_ready` events; frontend wires the full §5 sequence — typing dots, rail loading
treatment, atomic section update, growing timeline; editable title → R0. Multi-pair
interactions come alive here for free: scrubbing, drawers per exchange, thread-collapse,
HOW per pair.
**DoD:** a genuinely new conversation, typed live in the app, produces a correct growing
panel across ≥6 pairs — and the engine test harness reproduces a manually-traced chat's
structure in parallel as the regression check.

**PHASE 4 — Instrument quality**
The interactions that make it feel finished: viewed-pair highlight + Back-to-latest,
accordion + tooltips polish, goal full-expansion, per-chat memory of viewed pair, empty
states, error/retry on pipeline failures (a failed pair must be re-runnable without
corrupting the ledger — append-only makes this safe).
**DoD:** INTERACTION_SPEC v1 checklist passes end-to-end on a live chat.

**PHASE 5 — The pending science & hardening**
HOW threshold calibration against Budget+Portfolio ledgers (now cheap — the engine
produces them) · spec §12.5 widened-hedge re-run · Step-2a embedding prefilter (D9) ·
legend/onboarding pass (INTERACTION_SPEC §8.3) · optional: E1/E2 report layer.
**DoD:** calibration reproduces both ground-truth trajectories; thresholds locked in spec.

---

## 7. The multi-tool working protocol (command-center ↔ build-sites)

- **This chat = command center**: architecture decisions, spec changes, verification of
  results, cross-phase judgment. **Build sites = Antigravity IDE (Gemini/Sonnet/Opus by
  task complexity) and Claude Code Desktop (Opus)** on the same repo folder: one
  phase-scoped brief at a time, pasted as the session's opening message. Tool routing per
  AGENTS.md: Antigravity for scaffolding/UI/boilerplate; Claude Code for
  engine/math/correctness-critical work.
- **Context bridge = BUILDLOG.md** (append-only, in repo): every session ends by
  appending an entry (tool, phase/step, changes, decisions, flags, verification, next).
  The owner reports back to the command center with the latest entry + test output +
  screenshots — never chat transcripts. No tool can see another tool's chats and
  Claude Code sessions cannot join claude.ai Projects (open feature request, not
  shipped) — the repo is the only shared brain, by design.
- **Context routing via AGENTS.md** (canonical, read by all tools; CLAUDE.md is a
  one-line import of it for Claude Code) at the repo root — read automatically
  every session. It is a ROUTER, not a copy: (a) three-sentence project description,
  (b) pointers to the four spec documents in `docs/` ("read the sections the brief
  names"), (c) the standing rules below, (d) one line naming the CURRENT PHASE and its
  DoD — updated as phases close, so every new session lands oriented.
- **Standing rules (written into CLAUDE.md):** the spec documents are read-only from the
  build side — anything discovered that contradicts a spec comes BACK to the command
  center before the spec is edited (single source of truth, versioned, changes-tables);
  the owner's step-gate workflow applies — one step per response, preamble (why, decisions
  needed, high-level picture) before each step, wait for "start task", wait for "Finish
  Step" before advancing, screenshot rule on visual changes; never commit `.env`.
- **Briefs are terminal-sized**: phase scope, the spec sections in play (by number, never
  restated), the DoD, and the first step. One phase may span several sessions; CLAUDE.md's
  current-phase line is what keeps session N+1 continuous with session N.
- **DoDs run as code where possible**: spec §11.4 mechanical checks as a pytest suite;
  Phase 2's ledger comparison as a diff script against `data/fixtures/ledger_pair1.json`;
  Claude Code executes them and reports results back here for judgment.
- Secrets: `ANTHROPIC_API_KEY` in `.env`, never committed; `.env.example` in repo (repo
  pattern).

## 8. Risks the architecture already answers — and the honest remainder
Answered: live-vs-replay divergence (D1: same engine) · frontend/backend drift (D13:
bundle contract) · cost blowup (D8/D10 tiering+batching, measured via monitor) · state
races (D11 sequential) · losing provenance (append-only ledger + llm_monitor).
**Remaining, accepted:** LLM nondeterminism means replayed numbers vary run-to-run
(documented since the o2 flip); Step-1b outcome-id drift over long live chats (spec §12.3)
is the known open research risk of being live — Phase 3's multi-pair replays are exactly
where it gets measured for the first time.
