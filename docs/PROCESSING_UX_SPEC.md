# PROCESSING_UX_SPEC: from "Process" to a living map (core, KISS)

Status: **v1.1 (10 Oct 2026)**, rewritten minimal at the owner's request. Applies to S4.3, S4.4 and S4.8 (`docs/plans/STANDALONE_V1_PLAN.md`) and later live chat (S5).

## Owner's words
> "when I upload a chat … while it is processing and loading, show it in the UI … the graph nodes need to start dynamically forming … showing progress"
> "remember the KISS rule, keep it stupid simple and minimal … anything added should be very meticulously mapped and planned … only add it where it is necessary"
> "why would you block replying … blocking the user is bad design"
> "allowing to select more than 2 also makes sense … they can all run in parallel, but let the user know it is all running"

---

## 0. Where we are (verified 10 Oct 2026)
- S4.1 scan ✅ · S4.2 review dialog ✅.
- The **Process** button fires `cotrace:import-process`; **nothing listens yet** (S4.3 queue, S4.4 pipeline and S4.8 aren't built).

## 1. The constraint: mapping is slow
- Measured in the first paid run (`run/llm_monitor.txt`): engine steps 1a–1c alone take a median of 7.5–13 s per exchange.
- Steps 2–3 are about 70% of the calls on top of that, so **a full exchange is about 30–60 s**.
- A 1-exchange chat therefore maps in under a minute; a 3-exchange chat (archive median) in 2–3 min; a 20-exchange chat in 10–20 min; the largest (242) in a couple of hours.
- So mapping is a **background activity**: never a modal wait, never a spinner.
- (The S3 report's "0.01 s per pair" timed cached replays; S4.3 records real per-exchange time.)

## 2. Rules
1. **The conversation is readable instantly.** Import already has the full text; only the map is pending.
2. **The map grows exchange by exchange** with the motion we already have (`foundations/motion.md`: node born, reactivated, answered). **No new animation system.**
3. **Never fake progress.** Every count comes from an engine event. No ETA, no animated bar that isn't driven by a real event.
4. **Nothing blocks.** You can read, open other chats, use the Brain and **reply** while mapping runs.
5. **Add nothing that isn't needed.** Every element below earns its place; everything else is in §8 *Later*.

## 3. What the user sees (the whole core)

### 3.1 Sidebar row (the only always-visible status)
| State | Small text under the title | Visual |
|---|---|---|
| Waiting | `Waiting · 8 exchanges` | Dimmed title |
| Mapping | `Mapping · 3 of 8` | A thin line under the row fills one exchange at a time |
| Mapped | the normal row | — |
| Needs review | `1 exchange needs review` | Small amber "!" + the text |
| Stopped part-way (cancel or budget) | `Mapped 4 of 9 · Continue` | The line shows 4/9 |
| Couldn't map | `Couldn't map · Retry` | Red text; the reason on hover/focus |

### 3.2 One small pill, only while something runs (bottom-left, above the status bar)
`Mapping 4 chats · 9 waiting`, which tells you it is all running in parallel.
- **Click it:** a short list of the running and waiting chats, each with *Map next* and *Stop*, plus **Pause all / Stop all**.
- **Stop asks once:** "Stop mapping? Mapped exchanges are kept; nothing is deleted."
- **When everything is done the pill disappears.** No summary card. Results show on the rows.
- **It becomes a one-line message only when you must act:**
  - "Paused · monthly budget reached · Raise cap"
  - "Can't reach the model · check your key · Settings"

### 3.3 Inside a chat while it maps
- **Transcript:** fully readable. An exchange that isn't mapped yet shows `not mapped yet` next to its marker; the one being mapped shows `Mapping…`. Nothing else.
- **Graph:** after each exchange, it plays what the timeline already plays for that exchange (node born, beads settle, share ring updates). The timeline notches fill as exchanges are mapped; unmapped notches are hollow.
- **Scrolled back or inspecting evidence:** nothing jumps. The existing "Back to latest" control just shows the new total.
- **Before the first exchange is done:** "Mapping the first exchange…" in the empty graph. No spinner.
- **Replying (never blocked):** the AI answers at once. The new exchange queues behind the earlier ones (`not mapped yet`), and replying moves this chat to the front of the mapping queue. The first reply to an imported chat notes once: "This continues the conversation in COTRACE; the original stays as it was."
- **Evidence clicks** work for mapped exchanges; unmapped ones say "Not mapped yet".

### 3.4 Brain
- A chat appears in the Brain when its first exchange is mapped and grows as mapping continues.
- No forming animation in v1 (§8); the neuron work in BRAIN_NEURON_SPEC decides the final look.

## 4. Choices
| Choice | v1 |
|---|---|
| How many chats map at once | **Your choice in Settings: 1–8** (already there; default 2). More is fine: the work is model calls, not your computer. Two automatic safeguards: if the provider rate-limits, the queue backs off and retries by itself; and the monthly budget cap still stops spending |
| Order | Shortest chats first (you see results within a minute; a third of the archive is 1-exchange chats), plus **Map next** on any chat. *(Owner to confirm.)* |
| Replying while mapping | Never blocked (§3.3) |
| Notifications | None in v1; the row and pill are enough |

## 5. Every state (what happens, in one line each)
| Situation | Behaviour |
|---|---|
| Provider busy or timeout | Retry up to 2× with backoff; the row stays "Mapping" |
| Rate-limited (many chats in parallel) | Back off and retry automatically; nothing for the user to do |
| Bad or missing key | Stop before any spend; pill: "check your key · Settings" |
| Budget cap reached | Finish the current exchange, then pause; pill: "budget reached · Raise cap" |
| Invariant fails on an exchange | Flag it, keep going if the state is valid; row "needs review" |
| Engine crash on one chat | That row "Couldn't map · Retry"; the others continue |
| App closed or laptop sleeps | Resume on restart from the last mapped exchange; never pay twice |
| One-exchange chat | Waiting → Mapped |
| No goals found | Chat shows "No goals found in this conversation"; the transcript is still readable |
| Already in library | Skipped at review ("already in library") |
| Same chat with new messages | Only the new exchanges map |
| Chat deleted while waiting or mapping | Leaves the queue; recoverable from trash |

## 6. Event contract (server → UI, `GET /api/events`)
| Event | Payload | Drives |
|---|---|---|
| `queue_changed` | running and waiting chat ids | pill, rows |
| `job_progress` | `{chatId, pair, of}` | row line, `Mapping…` marker |
| `pair_ready` | `{chatId, pair}` → the client fetches the partial bundle | graph growth, notches, Brain |
| `pair_flagged` | `{chatId, pair, reason}` | "needs review" |
| `chat_ready` | `{chatId}` | row → Mapped |
| `job_error` | `{chatId, kind: transient\|rate_limit\|auth\|crash}` | retry, pill message or row |
| `budget_stop` | `{spent, cap}` | pill message |

- `GET /api/chats/{id}` returns the partial bundle while mapping (`status: "processing"`, `processedPairs`).
- The client re-syncs from `GET /api/jobs` on load and on SSE reconnect.

## 7. Build steps
| Step | Builder | What | Done when |
|---|---|---|---|
| S4.3 | CC / AG+ | Queue (`jobs.json`), parallel up to the setting, order, Map next, pause/stop, resume, rate-limit backoff, per-exchange timing log | Kill and restart resumes without re-paying; parallelism and backoff tests |
| S4.4 | CC / AG+ | Pipeline per chat + §6 events + partial bundles + §5 behaviours | Event-sequence and injected-error tests (replay) |
| S4.R | AG | **Rehearsal mode** (dev only): replay recorded runs through the real queue at real pace, **zero spend**, so the experience can be judged and tested before paying | A full batch replays end to end |
| S4.UX | AG | §3.1 rows, §3.2 pill, §3.3 chat view, §3.4 Brain | e2e on rehearsal for each state in §5 |
| **S4.T** | You | Owner test: rehearsal batch, then a real batch of 5 chats you know | log entry |

## 8. Later (deliberately not in v1)
Add only if real use shows a need, one at a time, each designed properly first:
- step-by-step wording inside the mapping exchange
- time estimates
- live cost ticker
- end-of-batch summary
- desktop notifications
- a Brain "forming" animation
- a dedicated motion pass for mapping (the existing motion tokens cover v1)
