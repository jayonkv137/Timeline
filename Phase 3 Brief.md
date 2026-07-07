# PHASE 3 BRIEF — THE LIVE LOOP (the product moment)
**Two sessions: S1–S4 in Claude Code · Opus (server + orchestration). S5–S7 in
Antigravity · Sonnet (frontend wiring).**

## Goal
The real product: type a message in the app → Claude replies in-app (streamed) → the
pipeline runs on the completed pair → the panel updates live. ARCHITECTURE §5's sequence,
made real.

## Read first
ARCHITECTURE §4 (the 5 endpoints) + §5 (the live-turn sequence) · INTERACTION_SPEC §3
(scrub sources) + §4 (the choreography — implement it literally) · PHASE2's engine API.

## Steps — Session A (Claude Code · Opus)
**S1 — FastAPI app.** `server/`: app factory, chat folders under `data/chats/<id>/`,
CORS for the Vite dev origin. Endpoints: `GET /chats` (sidebar list), `POST /chats`
(create — new folder, empty artifacts), `GET /chats/{id}/bundle` (panel_bundle +
dialogue), `PATCH /chats/{id}/title` (renames R0 in state + bundle).
**S2 — `POST /chats/{id}/messages`.** Append user turn to dialogue.json (assign pair
number), stream Claude's reply token-by-token (SSE; chat model from `CHAT_MODEL` env,
default `claude-sonnet-4-6`), append assistant turn on completion.
**S3 — The pipeline job.** On reply completion: enqueue an asyncio task running the
engine's per-pair loop for pair t. **Strictly sequential per chat** (an asyncio.Lock per
chat id; a second message queues behind the running job). Emits SSE events on
`GET /chats/{id}/events`: `pipeline_status {phase: running|done|failed, pair}` and
`pair_ready {t}`. **Failure = recoverable:** a failed pair is marked in a small
`run/status.json`, `POST /chats/{id}/pairs/{t}/rerun` re-runs it; append-only ledger
makes re-runs safe (the engine must be idempotent per pair — wipe that pair's ledger
rows by pair_added before re-adding).
**S4 — Server tests.** httpx-based: create chat → post message (mock the LLM layer with
a canned reply + canned pipeline outputs) → assert dialogue grows, events fire in order,
bundle updates, rerun works. Engine LLM calls mocked; this tests orchestration, not
judgment.

## Steps — Session B (Antigravity · Sonnet)
**S5 — Swap data source.** Frontend reads from the API instead of static fixture
(fixture mode stays behind `?fixture=1` for offline dev). Sidebar lists real chats;
`+ New` works; title editable (PATCH).
**S6 — The choreography (INTERACTION_SPEC §4, literally).** Send on Enter → user bubble
+ P-badge instantly → streamed reply fills the assistant bubble (typing dots until first
token) → on `pipeline_status: running`, rail shows the loading treatment WHILE KEEPING
the previous pair's values (never blank) → on `pair_ready`, fetch bundle delta, sections
update atomically, new timeline row appears, top-strip counter increments. **No-yank
rule:** if viewing history when a pair lands, nothing moves; denominator increments;
Back-to-latest pill available.
**S7 — Scrub sources wired** (INTERACTION_SPEC §3): timeline row click = scrub (chat
scrolls, viewed-pair bubbles highlight); drawer expand = scrub; Back-to-latest; top
strip LIVE ↔ VIEWING Pn · HISTORY n/N. Scroll≠scrub (one-directional rule).

## Definition of Done
(a) Server tests green (mocked LLM). (b) Engine tests from P2 still green. (c) **The
real thing:** a genuinely new conversation, typed live, ≥6 pairs, walked against this
checklist and screenshotted per pair: reply streams · rail lags with loading treatment,
old values visible · every section updates on pair_ready · timeline grows · scrub any
old pair → whole panel renders as-of that pair → Back to latest returns · one forced
pipeline failure (kill network mid-pair) → rerun endpoint recovers it.

## Out of scope
Polish states (P4), mobile, calibration, coach marks.

## Kickoff prompt addendum (Session A)
```
Mock the LLM layer in all server tests. The engine is a black box you call — do not
modify engine internals except the per-pair idempotency requirement in S3 (wipe that
pair's ledger rows by pair_added before re-run), which is an engine change: implement
it as a small, tested engine function, not server-side file surgery.
```
## Kickoff prompt addendum (Session B)
```
INTERACTION_SPEC §4 is implemented literally — especially: previous values stay during
loading (never blank a section), and the no-yank rule. Live/history state renders ONCE
(top strip), never per-row.
```
