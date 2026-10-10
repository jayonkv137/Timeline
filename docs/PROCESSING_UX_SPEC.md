# PROCESSING_UX_SPEC: from "Process" to a living map

Status: **v1.0 proposed (10 Oct 2026)**, for S4.3, S4.4 and S4.8 (`docs/plans/STANDALONE_V1_PLAN.md`) and later live chat (S5). Owner decisions in §12.

## Owner's words
> "when I upload a chat and add it, it needs to have a proper way, while it is processing and loading, to show in the UI … as the engine runs, the graph nodes need to start dynamically forming in a good way and show proper UI notation to show it is coming up and showing progress … decide in detail all the possibilities … very meticulously, like the world's best designer"

---

## 0. Where we are today (verified in the repo, 10 Oct 2026)
| Piece | State |
|---|---|
| S4.1 scan (`POST /api/imports`, zero LLM) | ✅ built |
| S4.2 review dialog (drop zone, table, filters, cost button) | ✅ built (`ImportModal.tsx`) |
| "Process N chats" button | Fires `cotrace:import-process` and closes the dialog. **Nothing listens yet, so nothing happens.** |
| S4.3 job queue (`server/jobs.py`) | not built |
| S4.4 pipeline wiring + progress UI | not built |
| S4.8 Brain and sidebar updates | not built |
| Live events (`GET /api/events`, SSE) | stream exists; only trash and restore events so far |

## 1. The constraint that shapes everything: mapping is slow

Measured in the engine call log of the first paid run (S3.6, `run/llm_monitor.txt`):

| Steps 1a–1c alone, per exchange (median) | c45 (6 exchanges) | c38 (13) | c48 (21) |
|---|---|---|---|
| Seconds | 7.5 | 10.3 | 12.9 |

- Steps 2 and 3 are about 70% of the calls (282 of 402) and aren't in that log. **A full exchange realistically takes 30–60 s.**
- That puts a 1-exchange chat at under a minute, the archive median (3 exchanges) at 2–3 min, a 20-exchange chat at 10–20 min, and the largest chat (242) at a couple of hours.
- The S3 report's "0.01 s per pair" column measured cached replays. S4.3 must record real wall time per exchange (§10).

**Consequences:**
1. Processing is a **background activity measured in minutes or hours**, never a modal wait.
2. The user must see value within the **first minute** (§3).
3. Progress has to stay alive and honest over a long time: real, per-exchange progress, never a fake spinner.
4. It must survive closing the laptop (resume, §8).

## 2. Principles (the rules every screen follows)
1. **The conversation is there instantly.** Import already has the full transcript (zero LLM), so a chat is readable the moment it's queued. Only the *map* is pending.
2. **The map grows in front of you, exchange by exchange,** using the same birth animations as the timeline scrubber. A live build is a replay that happens to be real.
3. **Never fake progress.**
   - Every bar, count and ETA is driven by an engine event.
   - The ETA appears only after real measurements; before that it says "estimating…".
   - Cost shows actual spend, with the estimate beside it as a range.
4. **Calm by default, detail on demand.** The sidebar and a small dock carry the ambient status; step-level detail appears only inside the chat you're watching.
5. **Nothing blocks.** While mapping runs you can read, open other chats, use the Brain, chat later. Mapping never steals focus or scroll.
6. **Every failure is visible and recoverable,** with an action. No silent drops, and no "something went wrong" without a next step.
7. **Same grammar as the rest of COTRACE:** blue = you, orange = AI, white = selection/focus, grey = missing. Text labels always accompany colour.

## 3. Time to first map (the first minute)
| Default | Why |
|---|---|
| **Shortest chats first** (by exchanges; ties by newest) | One-exchange chats (99 of 298 in the archive) finish in under a minute, so the Brain and sidebar start filling almost immediately |
| **2 chats in parallel** (`parallel_jobs`, Settings), exchanges strictly sequential within a chat | Engine state is per exchange (Architecture D11) |
| **"Map this next"** on any queued chat | Lets you pull the chat you care about to the front |
| Optional order: "As listed" / "Newest first" | In the review footer |

## 4. The journey, moment by moment
| # | Moment | What the user sees |
|---|---|---|
| 1 | **Review footer** (before spending) | "Process 12 chats · **≈ $0.40–0.70** · **about 25 min** · runs in the background". Long chats are flagged in their row: "≈ 2 h". The button is the cost gate (spec S3) |
| 2 | **Click Process** | The dialog closes into the **mapping dock** (§5.2). Queued chats appear at the top of the sidebar under a "Mapping now" group, each with its state (§5.1). A toast: "12 chats queued · you can keep working" |
| 3 | **First exchange running** | The first chat's row shows "Mapping · exchange 1 of 3", with a thin line under it filling per exchange. The dock reads "Mapping 1 of 12 chats · estimating time…" |
| 4 | **First exchange done** | Its row line advances. If the chat is open, its graph grows (§5.3). In the Brain, its neuron starts forming (§5.4). The dock's ETA appears once 3 exchanges have finished anywhere |
| 5 | **A chat finishes** | Row → **Mapped ✓** (it moves into the normal list, keeping its place by date). Toast if you're elsewhere: "Jellyfish motion study is mapped · Open". The Brain neuron completes its birth |
| 6 | **Batch finishes** | The dock becomes a **summary** (§5.5) until dismissed |
| 7 | **Later** | Re-uploading the same export maps only new exchanges (S4.6); live chat (S5) uses the same per-exchange choreography |

## 5. Surfaces

### 5.1 Sidebar row (always visible)
| State | Glyph + text (small, under the title) | Visual |
|---|---|---|
| Queued | `Queued · 8 exchanges` | Dimmed title, no line |
| Mapping | `Mapping · 3 of 8` | A thin progress line under the row = exchanges done ÷ total; the current exchange's segment breathes softly (static with reduced motion) |
| Mapped | `Research · 8 exchanges` (the normal row) | — |
| Needs review | `Mapped · 1 exchange needs review` | Small amber "!" (+ text). Not red: the map is usable |
| Partial (cancelled or budget stop) | `Mapped 4 of 9 · Continue` | The line shows the 4/9 split |
| Paused | `Paused · 3 of 8` | The line freezes |
| Failed | `Couldn't map · Retry` | Red text with the reason on hover/focus (§7) |
| Already in library | not shown as a new row; the review table and summary say "skipped" | — |

A "Mapping now" group sits at the top of the sidebar while anything is queued or mapping, so the user sees the work without hunting. It collapses when empty.

### 5.2 Mapping dock (global, bottom-left above the status bar)
- **Collapsed pill:** `◐ Mapping 3 of 12 chats · 18 / 64 exchanges · $0.11 · ~14 min left` (the ETA only after 3 measured exchanges).
- **Expanded panel** (click the pill or press `M`):
  - one row per chat: state, exchanges done/total, actual cost, "Map this next", cancel
  - drag to reorder the queue
  - **Pause all / Resume** and **Cancel remaining**
  - a **budget line**: "This month: $1.40 of $5.00", marked when the batch would cross it
- **Cancel shows a preview first:**
  > "Stop mapping 9 chats? 3 finished chats stay. 'Figma migration' keeps its 4 mapped exchanges and can continue later. Nothing is deleted."
- Never covers the composer or graph controls; minimisable to a dot; hidden when no work exists.

### 5.3 Inside a chat that is being mapped (the signature moment)
**Transcript (left):** fully readable from the start. Each exchange marker gets a state:

| Exchange | Marker |
|---|---|
| Mapped | `PAIR 03 ✓` (quiet) |
| Being mapped | `PAIR 04 · Mapping…`, plus the step line (below) |
| Waiting | `PAIR 05 · not mapped yet` (muted) |
| Needs review | `PAIR 06 · needs review` (amber, "What's this?" explains) |

**Step line** (only for the exchange being mapped, only in the open chat), the engine's steps in plain words:

`Reading the exchange → Finding goals → Extracting requirements & questions → Weighing who shaped it → Updating the map`

Steps tick through as `pipeline_status` events arrive. No percentages inside a step, because the engine doesn't report them.

**Graph (right):**
- **LIVE (default, following the latest mapped exchange):** when an exchange is ready, the graph plays exactly what the scrubber would play for it. New outcomes **bloom**, a reactivated outcome pulses, new requirement and question beads settle onto their orbit, and the share ring re-balances. Same animations, same timing tokens, so a live build feels identical to replay.
- **The scrubber** shows mapped exchanges as filled notches, pending ones as hollow notches, and the one being mapped as a slowly breathing notch. You can't scrub into unmapped exchanges (they say "not mapped yet").
- **HISTORY** (you scrubbed back, or you're inspecting evidence): nothing yanks you. A pill appears: `Exchange 5 mapped · Go to latest`. The denominator grows quietly.
- **Throttle:** if several exchanges land within a second (one-exchange chats, cached replays), their animations queue at the motion token's pace, at most one birth wave per 600 ms.
- **Empty state before the first exchange:** "Mapping the first exchange… your map will start here", with the graph stage's neutral orbit, not a spinner.
- **Evidence clicks** (EVIDENCE_SPEC) work for mapped exchanges; unmapped ones say "Not mapped yet".

**Composer: never blocked.** You can reply at any time, even while earlier exchanges are still mapping (owner, 10 Oct 2026: blocking the user is bad design).
- The AI replies immediately; the reply doesn't depend on the map.
- The engine maps exchanges strictly in order (each builds on the previous state), so the new exchange **joins the end of this chat's mapping queue**. Its marker reads `PAIR 09 · not mapped yet · after 4 earlier exchanges`, and it maps as soon as they finish.
- **Replying moves this chat to the front of the mapping queue.** You're engaged with it, so it gets mapped first.
- The graph keeps growing in order; nothing is skipped or lost.
- Replying to an imported chat continues it **here in COTRACE**, not on the original platform. The first reply says so once: "This continues the conversation in COTRACE; the original on Claude stays as it was".

### 5.4 Brain
- A chat's neuron (or today's territory) **appears at its first mapped exchange** as a faint "forming" outline at its place. It grows as mapped mass grows, and completes with a single **birth pulse** at "chat ready".
- While forming: translucent, no title label unless hovered or selected; the share light is based on mapped exchanges so far, marked "so far" in the inspector.
- The Brain never re-lays out existing neurons when new ones arrive (BRAIN_SYSTEM_SPEC: first-seen claim order).

### 5.5 Batch summary (replaces the dock when everything is done)
> **12 chats mapped** · 64 exchanges · 31 min · **$0.52** (estimate $0.40–0.70)
> 1 chat needs review · 2 skipped (already in library) · [Open Brain] [Review the flagged exchange] [Dismiss]

When the window was hidden, a system notification says the same (opt-in, Settings).

## 6. Engine steps → words (one vocabulary everywhere)
| Engine | Shown as |
|---|---|
| 1a actions | Reading the exchange |
| 1b / 1c outcomes, intentions | Finding goals |
| 2 requirements and questions | Extracting requirements & questions |
| 3a / 3b influence | Weighing who shaped it |
| Stage 4 + projection | Updating the map |

## 7. Every state and edge case
| Situation | What happens | What the user sees |
|---|---|---|
| Transient model error (timeout, 5xx, rate limit) | Retry up to 2× with backoff, same exchange | Step line: "Retrying (provider busy)…"; no failure unless all retries fail |
| Bad or missing API key | Stop the whole queue at the first call (no partial spend) | Dock: "Can't reach the model: check your key in Settings" + [Open Settings]; rows → Paused |
| Provider quota exhausted | Pause the queue | Dock: "Provider quota reached · Resume" |
| Budget cap reached | Finish the current exchange, then pause (spec S3) | Dock: "Paused at your $5.00 monthly cap ($4.98 spent) · Raise cap / Resume next month" |
| Invariant violation on an exchange | Flag the exchange, keep the last good state, continue if valid (S-D9) | Row "needs review"; marker on that exchange; a Rerun action (cost-gated) |
| Engine crash on a chat | Mark failed, continue the queue | Row "Couldn't map · Retry"; the summary lists it |
| User cancels one chat | Stop after the current exchange | Partial: "Mapped 4 of 9 · Continue" |
| User pauses all | Stop after the current exchanges | Rows Paused; dock "Paused · Resume" |
| App closed or laptop sleeps | `jobs.json` persists | On restart: toast "Resuming 3 chats…"; finished exchanges are never re-paid (cache) |
| SSE disconnect | Auto-reconnect; re-sync from `GET /api/jobs` | Nothing visible unless the gap is > 10 s: dock "Reconnecting…" |
| One-exchange chat | Maps in < 1 min | Goes straight from Queued to Mapped; one birth |
| Very long chat (≥ 50 exchanges) | Flagged at review with its own time estimate | Row "≈ 2 h"; ETA in the dock; continues across restarts |
| No goals found | Engine returns no outcomes | Chat opens with "No goals found in this conversation", the transcript still readable, nothing invented |
| Duplicate upload | Skipped (S4.6) | "Already in library" in the review table and the summary |
| Same chat with new messages | Only the new exchanges are mapped | Row "Mapping 2 new exchanges" |
| Sensitive-flagged chat | Unticked by default in the review table | Needs an explicit tick; label "flagged sensitive" |
| Chat deleted while queued or mapping | Removed from the queue (moved to trash, recoverable) | The dock updates; nothing lost |
| User opens a chat mid-exchange | Shows every mapped exchange; the current one in progress | — |
| User replies while earlier exchanges are still mapping | The reply is sent at once; the new exchange queues behind them; the chat jumps to the front of the queue | New marker "not mapped yet · after N earlier exchanges"; the row shows the larger total |

## 8. Persistence and recovery
- The queue lives in `jobs.json`: order, state, last finished exchange per chat, spend.
- On startup the server resumes Mapping/Queued jobs (Paused stays paused) and broadcasts `queue_changed`.
- The client never trusts local state alone: on load and on every SSE reconnect it fetches `GET /api/jobs` and the open chat's bundle.

## 9. Event contract (server → UI, `GET /api/events`)
| Event | Payload | Drives |
|---|---|---|
| `queue_changed` | full queue summary | dock, sidebar group |
| `job_progress` | `{chatId, pair, of, step, spentUsd, etaSec?}` | row line, step line, dock |
| `pair_ready` | `{chatId, pair}` → client fetches the bundle (or a delta) | graph growth, notches, Brain forming |
| `pair_flagged` | `{chatId, pair, reason}` | needs-review marker |
| `chat_ready` | `{chatId, flaggedPairs}` | row → Mapped, Brain birth pulse, toast |
| `job_error` | `{chatId, pair, kind: transient\|auth\|quota\|crash, retryAt?}` | retry line / failed row / dock banner |
| `budget_stop` | `{spent, cap}` | dock banner |

`GET /api/chats/{id}` returns the partial bundle while mapping (`status: "processing"`, `processedPairs`). The graph renders exactly the mapped exchanges.

## 10. Measuring it (so ETAs are true)
- S4.3 writes `{chatId, pair, startedAt, endedAt, calls, tokens, cost}` per exchange to `run/pairs.jsonl`.
- The ETA = rolling median seconds per exchange × the exchanges left ÷ parallel jobs. It is shown only after 3 measured exchanges, in whole minutes, with "about".
- A cost and performance report (S4.10) checks: median and p90 per exchange, time to first map, estimate vs actual.

## 11. Rehearsal mode (design and test without spending)
`./cotrace dev --rehearse` replays recorded runs (cassettes) through the real queue at a real-time pace (default: each exchange takes its recorded wall time). This lets us design the motion, test every state (with injected errors) and run e2e tests for the whole journey **with zero LLM spend**. It doubles as a demo mode.

## 12. Decisions for the owner
1. **Default order:** shortest first (recommended) vs as listed vs newest first.
2. **Parallel chats:** 2 (recommended; safe for rate limits) vs 3–4.
3. ~~While an imported chat maps: block replying~~. **Decided (owner): never block.** Replies go through at once; the new exchange queues behind the earlier ones, and replying moves the chat to the front of the mapping queue (§5.3).
4. **System notifications** when a batch finishes while the window is hidden: off by default, opt-in in Settings (recommended).
5. **Rehearsal mode** built first so the experience can be judged before real spend (recommended).

## 13. Build steps (refines S4.3, S4.4, S4.8; S4.UX steps are new)
| Step | Builder | What | Done when |
|---|---|---|---|
| S4.3 | CC / AG+ | Queue, persistence, resume, order, parallelism, pause/cancel/"map next", per-exchange timing (§8, §10) | Kill and restart resumes without re-paying; ordering tests |
| S4.4 | CC / AG+ | Pipeline per chat + the §9 events + partial bundles + retry policy (§7) | Event-sequence tests with replay; injected-error tests |
| S4.R | AG | Rehearsal mode (§11) | A full batch replays at real pace with zero spend |
| S4.UX1 | AG | Sidebar states and "Mapping now" group (§5.1) | e2e on rehearsal |
| S4.UX2 | AG | Mapping dock + cancel preview + summary (§5.2, §5.5) | e2e: pause, resume, cancel preview, summary numbers equal the events |
| S4.UX3 | AG | Live chat view: exchange markers, step line, live graph growth, notches, LIVE/HISTORY, throttle (§5.3) | e2e: graph grows per `pair_ready`; no yank in HISTORY |
| S4.8 | AG | Brain forming → birth pulse (§5.4) | e2e on rehearsal |
| S4.UX4 | AG | Every §7 state wired to injected errors | one e2e per row |
| **S4.T** | You | Owner test: rehearsal batch of 12, then a real batch of 5 chats you know | log entry |
