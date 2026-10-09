# STANDALONE_V1_PLAN: from prototype to a working app on your own chats

Track **S** (Standalone). Written 9 October 2026 from a full read of the repo: the engine (`engine/`), the old Phase 3 server (in git history, `27e7d68`), `Architecture.md`, `IMPORT_SPEC.md`, the G1 brief, the workspace prototype (`web/src/workspace/`), the design system and the Brain.

This plan is the brief source for every S phase. An agent working a phase reads: `AGENTS.md` → this file's section for the phase → the docs that section names.

---

## 0. What you will have at the end (plain words)

You run one command. A browser tab opens on `localhost`. That is COTRACE, running on your machine, with your data in a folder you own.

1. **Your history is in it.** You drop in your Claude export (and later ChatGPT and Gemini). It lists every conversation it found, with its size and an estimated processing cost. You tick the ones you want and press Process. The chats appear one by one in the sidebar and as territories on the Brain as they finish.
2. **Every chat is fully mapped.** Opening a chat gives the same workspace you have today: the transcript, the node graph growing pair by pair with the scrubber, the share rings and beads, and every number traced to a quote. The difference is that it is computed by the engine from the real pipeline, not a hand-made file.
3. **You can talk to it.** Start a new conversation in the app, or continue an old one. Each time the AI replies, the engine processes that exchange in the background (seconds). The graph grows a node, the share updates, and the chat's territory on the Brain grows.
4. **It is honest and safe.** Every run shows its cost before it starts and stays under a budget you set. If the engine is unsure (an invariant fails), that exchange is marked "needs review" with a Rerun button; it is never silently wrong. Deleting something moves it to trash. You can back up the whole library as one zip.
5. **It is yours.** Single user, local files, no account. Chats leave your machine only to reach the AI model you configured, with your own key.

**Not in v1** (later tracks, already on the roadmap):
- capturing chats from inside claude.ai or chatgpt.com (the browser extension, G3)
- links between chats on the Brain (B1)
- the final visual polish (D-track UI/UX phase)
- multi-user or cloud sync
- a desktop installer

---

## 1. Where we are today (verified 9 Oct 2026)

| Piece | State | Evidence |
|---|---|---|
| Engine Steps 1a–3, Stage 4, invariants | **Works**, per pair and per chat (`process_pair`, `run_chat`) | `e2-done`, 102 tests pass (`.venv/bin/python -m pytest`) |
| Importers (zero LLM) | **Claude export works** (→ canonical archive → corpus, with a sensitive-content flag). ChatGPT and Gemini parsers are **not written yet** | `scripts/archive_scan.py` (only `parse_claude_export`; 313 Claude chats in `data/archive/registry.json`), `scripts/promote_from_archive.py`, `scripts/ingest_export.py` |
| Processed chats | 10 chats with `full_export.json`, `panel_bundle.json`, ledger | `data/chats/c*` |
| Workspace UI | **Works as a prototype**: sidebar, tabs, transcript, graph and scrubber, Brain, composer | `web/src/workspace/` |
| Workspace data | **Static.** One hand-run script turns 10 exports into `data.generated.json`, with hard-coded ids, titles and node positions | `web/scripts/compile-workspace.py`, `store.ts` line 2 |
| Composer, "New conversation" | UI exists; it says "Chat backend not connected" | `Workspace.tsx` line 49 |
| Server | **None in the tree.** A FastAPI server with SSE, per-chat locks and reruns existed in Phase 3 and was removed in the engine-first re-plan | `git show 27e7d68:server/main.py` (1,007 lines) |
| Cost metering, budget, settings | None | — |
| Design system v0.1, Brain (DDR-008 proposed) | Done, **uncommitted** | `git status`: 74 changed paths |
| Web end-to-end tests | Written, cannot run (Playwright not installed) | `scripts/workspace-tests/*.cjs` |

The gap is three seams:
1. engine output → the UI's data shape
2. a server between them
3. an input path (upload or live chat) into the engine

Almost everything on both sides of those seams already exists.

---

## 2. Target architecture

```
                 ┌───────────── browser: localhost:8765 ──────────────┐
                 │  Workspace (React)  ·  Brain (Three.js iframe)       │
                 │  reads /api, listens to /api/events (SSE)            │
                 └───────────────┬──────────────────────────────────────┘
                                 │ REST + SSE
                 ┌───────────────▼──────────────────────────────────────┐
                 │ SERVER (FastAPI, server/)                              │
                 │  chats · imports · messages · settings · jobs · events │
                 │  JOB QUEUE: sequential per chat, N chats in parallel   │
                 └──────┬─────────────────┬───────────────────┬─────────┘
          upload        │        live turn│                   │ read
     ┌──────────────────▼───┐   ┌─────────▼──────────┐        │
     │ IMPORT (zero LLM)     │   │ CHAT MODEL (stream) │        │
     │ archive_scan → promote│   │ reply → pair done   │        │
     └──────────┬───────────┘   └─────────┬──────────┘        │
                └──── pair events ─────────┘                    │
                           ▼                                    │
                 ┌────────────────────────┐                      │
                 │ ENGINE process_pair     │ usage meter, cache   │
                 │ 1a→1b→1c→2→3→Stage 4    │ invariants           │
                 └──────────┬─────────────┘                      │
                            ▼ writes                              │
                 ┌──────────────────────────────────────────────┐ │
                 │ LIBRARY (files, outside git)                  │◄┘
                 │ chats/<id>/ dialogue · state · ledger ·       │
                 │   panel_bundle · workspace_bundle · run/      │
                 │ imports/ · trash/ · jobs.json · settings      │
                 └──────────────────────────────────────────────┘
```

This keeps Architecture.md's governing idea: **one engine, input sources don't matter**. Upload becomes the replay adapter promoted to a product feature, and live chat is the second source.

### Decisions (S-D1 to S-D12)

| # | Decision | Choice | Why |
|---|---|---|---|
| S-D1 | The UI contract | **`workspace_bundle.json` = today's `Chat` type** (`types.ts`), produced by the engine | The UI already renders it, so swapping the data source changes no screens. G1's compact `graph_bundle` (entities + frames) stays a later size optimisation |
| S-D2 | Where data lives | **A library folder outside the repo**, `COTRACE_HOME` (default `~/Cotrace`) | Private chats never end up in git. The repo's `data/` stays the test corpus |
| S-D3 | Server | **FastAPI**, revived from Phase 3 patterns (locks, SSE broadcast, rerun), rewritten to this contract | Same language as the engine; the patterns were already proven |
| S-D4 | Push | **SSE**, one global stream `/api/events` | One-way updates; reconnects automatically (Architecture D5) |
| S-D5 | Jobs | **A persistent queue** (`jobs.json`): strictly sequential per chat, default 2 chats in parallel, cancellable, resumes after a restart | State is iterative per pair (D11); a 300-chat import must survive a laptop sleep |
| S-D6 | Models | **One OpenAI-compatible client, per-step models from settings** (Gemini default, as `.env.example`) | The model is a swappable layer: build the seam, measure, then choose |
| S-D7 | Live chat model | **A config value**, default the cheapest good Gemini model; Claude optional | Same seam as S-D6 |
| S-D8 | Cost | **Meter every call; estimate before every run; budget cap enforced** | Never spend without a gate |
| S-D9 | Invariant failure in product mode | **Flag, don't crash.** The pair is marked `needs_review`, the chat shows up to the last good pair, Rerun is offered | The UI must stay usable, and the error must stay visible |
| S-D10 | Packaging | **One command** (`./cotrace start`) that serves the built web app from FastAPI. Desktop installer later | Smallest thing that is truly standalone |
| S-D11 | Deletes | **Move to `trash/`**, restorable; permanent delete only from trash, with a confirmation | Destructive actions archive and preview |
| S-D12 | Offline fallback | `?offline=1` keeps the bundled sample data | Design work and tests keep running without a server |

---

## 3. Contracts (frozen at gate S1.G; changed only by a DDR)

### 3.1 `workspace_bundle.json` (one per chat)
The exact shape of `Chat` in `web/src/workspace/types.ts`. The table is each field's source of truth. Projection code may compute, never invent.

| Field | Source |
|---|---|
| `id` | library folder name (stable; derived from the source conversation id) |
| `title` | `source_meta.json` title, else the first user message (42 chars); the owner can edit it |
| `rootTitle` | `state.outcomes[root].text` at the latest pair |
| `category` | `meta.json` category (owner-set or confirmed suggestion), else `"Uncategorised"` |
| `totalPairs` | `dialogue.json` pair count |
| `dialogue[]` | `dialogue.json` |
| `nodes[]` | `state.outcomes` + first ledger row or op per outcome (`born`); `x, y` from a deterministic layout (S1.2), not a fixed table |
| `atoms[]` | `state.requirements` + `state.slots` + `operations_log` (as `compile-workspace.py` does today) |
| `snapshots[]` | `ledger.jsonl` summed per pair per outcome (cumulative human/ai, delta, terminal) |
| `summary` | the engine's dialogue summary |
| **new** `status` | `ready` · `processing` (with `processedPairs`) · `needs_review` (with `flaggedPairs`) · `error` |
| **new** `source` | `{platform, importedAt, conversationId}` or `{platform:"live"}` |

### 3.2 API (all under `/api`)
```
GET    /health                         → {version, library, model config ok?}
GET    /chats                          → [{id,title,category,totalPairs,status,updatedAt,mass,share}]
GET    /chats/{id}                     → workspace_bundle
PATCH  /chats/{id}                     → {title?, category?}
DELETE /chats/{id}                     → moves to trash
POST   /chats/{id}/restore             → from trash
POST   /chats                          → new live chat
POST   /chats/{id}/messages            → streams the reply (SSE: token…, done); enqueues the pair
POST   /chats/{id}/pairs/{n}/rerun     → re-process from pair n (cost-gated)
POST   /imports                        → multipart upload → {importId}
GET    /imports/{id}                   → report: conversations[], pairs, fidelity, duplicates, estimate
POST   /imports/{id}/process           → {conversationIds[], confirmCost} → jobs
GET    /jobs  ·  POST /jobs/{id}/cancel
GET    /settings  ·  PUT /settings     → key is write-only (never returned)
GET    /usage                          → spend this month, per chat, per step
GET    /events                         → SSE stream
```

### 3.3 Events (`/api/events`)
`chat_created` · `job_progress {chatId, pair, of}` · `pipeline_status {chatId, pair, phase}` · `pair_ready {chatId, pair}` · `chat_ready {chatId}` · `pair_flagged {chatId, pair, invariant}` · `budget_stop {spent, cap}` · `import_scanned {importId}`

### 3.4 Library layout
```
$COTRACE_HOME/
  chats/<id>/   dialogue.json · source_meta.json · meta.json · state.json · ledger.jsonl ·
                snapshots.json · panel_bundle.json · workspace_bundle.json · run/{cache,usage.jsonl,status.json,report.json}
  imports/<importId>/  raw/ · report.json
  trash/<id>/
  jobs.json · settings.json · secrets.json (0600, key only)
```

---

## 4. The phases

Every step has an id, a builder, the files it touches and a **done-when** you can check yourself. Gates (**G**) are yours. A phase closes only with its Definition of Done met, a BUILDLOG entry and a tag.

Builder legend:
- **AG** = Antigravity (Gemini)
- **CC** = Claude Code (Opus), recommended where "a wrong number is worse than a slow answer" (AGENTS.md tool routing)
- **AG+** = Antigravity with the extra checks listed for that step, if you want Antigravity to do everything

### S0 · Freeze the baseline (½ day)
Goal: the repo is the shared brain, so the prototype must be in git before another tool touches it.

| Step | Builder | What | Done when |
|---|---|---|---|
| S0.1 ✅ | CC | Commit today's work in logical commits on a branch `s/standalone-v1` (design system · workspace port · Brain cortex · docs · corpus promotions). Tag `prototype-v0.1` | `git status` clean except ignored data; tag exists |
| S0.2 ✅ | CC | `.gitignore`: library paths, `secrets.json`, `dist-*`; `.env.example` gains `COTRACE_HOME`, `CHAT_MODEL`, `BUDGET_MONTHLY_USD` | no private data can be staged |
| S0.3 ✅ | AG | Install Playwright (`npm i -D playwright` in the repo root, plus the browser) and add `npm run e2e` to run `scripts/workspace-tests/*.cjs` | `npm run e2e` passes on `cotrace-workspace.html` |
| S0.4 ✅ | CC | AGENTS.md "Current phase" → "Track S, phase S1 (docs/plans/STANDALONE_V1_PLAN.md)". ROADMAP: link this plan | the next agent reads the right phase |
| **S0.G** | You | Review the commit list and tag | — |

### S1 · The engine writes what the UI reads (about 1 week)
Goal: replace the hand-run `compile-workspace.py` with an engine projection that runs after every pair. No server yet, no LLM calls.

| Step | Builder | What | Done when |
|---|---|---|---|
| S1.1 ✅ | CC / AG+ | `engine/schemas/workspace_bundle.schema.json` from `types.ts` + §3.1, including `status` and `source` | the schema validates today's `data.generated.json` chats (with the new fields defaulted) |
| S1.2 ✅ | CC / AG+ | `engine/projections/workspace.py`: a pure function from (dialogue, state, ledger, source_meta, meta) to a bundle. Port the logic of `compile-workspace.py`, with no hard-coded ids, titles or positions. Layout: root at (0,0); children on rings by depth, angle by birth order, seeded by outcome id (deterministic) | same inputs give byte-identical output |
| S1.3 ✅ | CC / AG+ | **Equivalence test (tier1):** for the 10 chats, the projection equals `data.generated.json` on every field except `x, y`, `status` and `source` | the test passes; any difference is explained in BUILDLOG or fixed |
| S1.4 ✅ | CC / AG+ | Workspace invariants W1–W6 in `tests/invariants.py`: W1 per-pair snapshot mass sums equal ledger sums · W2 an outcome is never born after its first ledger row · W3 every atom's action ids exist · W4 `len(snapshots) == totalPairs` · W5 every non-root parent exists · W6 shares are in [0,1] | 10 chats + fixture green |
| S1.5 | CC / AG+ | Call the projection at the end of each pair in `run_chat`, and from a `python -m engine project <chat_dir>` CLI | rerunning replay on one chat writes `workspace_bundle.json` |
| S1.6 | AG | `web/scripts/compile-workspace.py` becomes a 10-line wrapper over the projection (offline sample data stays reproducible) | `data.generated.json` regenerates through the engine |
| S1.7 | AG | `python -m engine report <chat>` writes a readable one-page Markdown for a chat: outcomes with their shares, decisions, top quotes, flagged pairs. This is for **you** to judge maps against your memory | report renders for all 10 chats |
| **S1.T** | You | **Owner test (§6A):** open the reports for 3 chats you remember well and mark each map right, partly right or wrong in the test log | log entry written |
| **S1.G** | You | **Contract freeze**: read §3.1 and one generated bundle; accept the schema v1.0 | — |

**Extra checks for AG+ steps:**
- The frozen fixture stays untouched.
- `pytest` stays at 102 or more passing.
- The fixture numbers are sacred: 21.7% / 78.3%, 4 · 10, COPILOT.
- Any change to engine math is out of scope; stop and report instead.

### S2 · A local server and the library (read path, about 1 week)
Goal: the workspace you have today, served by the server from the library. It looks identical, but the data is live.

| Step | Builder | What | Done when |
|---|---|---|---|
| S2.1 | AG | `server/library.py`: library layout §3.4, `COTRACE_HOME`, atomic writes (write a temp file, then rename), trash and restore | unit tests: create, list, trash, restore |
| S2.2 | AG | `server/app.py` (FastAPI): `/health`, `GET/PATCH/DELETE /chats`, `/chats/{id}`, `/events` (SSE broadcaster; reuse the Phase 3 queue pattern from `27e7d68:server/main.py`) | tier1 API tests with `TestClient` |
| S2.3 | AG | `scripts/seed_library.py`: copy the 10 processed chats into the library and project their bundles. No LLM | library has 10 chats; `GET /chats` returns them |
| S2.4 | AG | Frontend data layer `web/src/workspace/api.ts`: the store loads the list from `/api/chats` and each bundle when its tab opens, and keeps the event stream open. `?offline=1` uses the bundled sample. Add loading, empty and error states | the workspace looks the same as the prototype, with data from the server |
| S2.5 | AG | Serve `web/dist-workspace` from FastAPI at `/`; `./cotrace start` (builds if stale, starts on 8765, opens the browser); `./cotrace dev` (Vite + server with a proxy) | one command → working app |
| S2.6 | AG | Point `npm run e2e` at the server URL; all existing assertions pass | e2e green against the server |
| S2.7 | AG | `scripts/perf_report.py`: the §6A performance metrics for the app (first load, chat open, Brain fps, API latency) → `docs/plans/reports/S2_perf.md` | report generated and committed |
| **S2.T** | You | **Owner test:** run `./cotrace start` yourself, open 5 chats, scrub, use the Brain, delete and restore one chat | log entry written |
| **S2.G** | You | Screenshot check against `docs/workspace/*.png`: same screens, real data path | — |

### S3 · Keys, models, cost and budget (about 4–5 days). Must close before any LLM spend.
| Step | Builder | What | Done when |
|---|---|---|---|
| S3.1 | CC / AG+ | Usage meter in `engine/llm.py`: tokens in and out per call → `run/usage.jsonl` (step, model, pair, tokens, cost); price table in `engine/models.yaml` | replaying a cassette chat writes usage rows (zero cost in replay, recorded token counts) |
| S3.2 | CC | `estimate(dialogue) → {low, high}` calibrated on the recorded runs of the 10 chats (tokens per pair by step versus chat length) | the estimate is within ±35% on the 10 chats, measured in a test |
| S3.3 | AG | Settings API and screen: provider URL, API key (write-only, stored in `secrets.json` with mode 0600), model per step, chat model, monthly budget, parallel jobs. Health check "Test connection" makes one tiny call | the key never appears in any API response, log or bundle (test greps for it) |
| S3.4 | AG+ | Budget guard: jobs refuse to start above the remaining budget; a running job stops at the cap and emits `budget_stop`; `/usage` page | test with a fake price table |
| S3.5 | CC | **Model bake-off:** 3 golden chats × 3 cheap configurations, graded with `scripts/grade_golden.py`; cost per pair and latency recorded | a table in `docs/plans/S3_BAKEOFF.md` |
| S3.6 | CC / AG+ | **First real spend, with you present:** process 3 never-processed corpus chats (from c37–c56, one short, one medium, one long) through the CLI with metering → the first cost and performance report `docs/plans/reports/S3_cost_perf.md` (cost per pair by step and model, seconds per pair, token growth, estimate vs actual) | report committed; total spend under $1 |
| **S3.T** | You | **Owner test:** read the 3 maps (S1.7 reports) and the cost report; decide whether quality is worth the cost | log entry written |
| **S3.G** | You | Pick the default models and the budget. Enter your key in Settings yourself | — |

### S4 · Upload and batch processing (about 1.5–2 weeks)
| Step | Builder | What | Done when |
|---|---|---|---|
| S4.1 | AG+ | Turn the `archive_scan.py` and `promote_from_archive.py` logic into library functions (no CLI-only code paths). `POST /imports` stores raw files; scanning runs in a background thread → `report.json` (conversations, pairs, fidelity grade, duplicates, estimate) | uploading your real Claude export lists 313 conversations with zero LLM calls |
| S4.2 | AG | Import dialog: drop zone (zip, json, md) → review table: title, date, pairs, fidelity, sensitive flag (from `check_sensitive`), estimate, checkbox. Filters: "≥ 3 exchanges", search, sort. Footer: "Process 12 chats · ≈ $0.40–0.70". This button is the cost gate | e2e: a fixture export → the table shows the expected rows |
| S4.3 | CC / AG+ | Job queue (`server/jobs.py`): persistent `jobs.json`, one worker per chat (sequential pairs), `parallel_jobs` in parallel, cancel, **resume** from the last completed pair after a restart (state.json + LLM cache make this cheap) | kill the server mid-job, restart: it resumes without re-paying for finished pairs |
| S4.4 | CC / AG+ | Pipeline per chat: promote → `run_chat` (caching client, usage meter) → project → `chat_ready`. `job_progress` after every pair | the sidebar shows "Processing 4/12"; the chat appears when ready |
| S4.5 | CC | Product-mode invariants (S-D9): `run_chat(stop_on_violation=False)` records the violation, marks the pair `needs_review`, keeps going if the state is still valid, otherwise stops at the last good pair; the bundle carries `flaggedPairs` | a test with an injected violation produces a flagged, still-renderable chat |
| S4.6 | AG+ | Re-upload: same conversation id + same content → skipped; new messages appended → only the new pairs are processed, starting from the existing state | a test with a chat extended by 2 pairs costs 2 pairs |
| S4.7 | AG | Category: the owner sets it in the review table. Optional "Suggest categories" makes one `MODEL_FAST` call per chat over its title and first exchange, mapped to the 6 lobes; shown as a suggestion until confirmed | categories drive Brain lobes; nothing is auto-accepted |
| S4.8 | AG | The Brain and sidebar update on `chat_ready` (territory birth animation); flagged chats show a small "needs review" mark | live Brain growth visible during a batch |
| S4.9 | AG+ | ChatGPT (`conversations.json` message tree → main branch) and Gemini (Takeout) parsers to IMPORT_SPEC rules (C-track work), with fixture exports and pairing tests | a sample of each format imports with a fidelity grade |
| S4.10 | AG | Cost and performance report for the batch: actual vs estimate per chat, queue throughput, scan time for 313 chats → `reports/S4_cost_perf.md` | report committed |
| **S4.T** | You | **Owner test:** the full upload flow by hand (§6A script S4) | log entry written |
| **S4.G** | You | Upload your real export, process 5–10 chats you know well, and check the maps, the cost against the estimate, and a forced restart | — |

### S5 · Live chat in the app (about 1.5 weeks; roadmap G2)
| Step | Builder | What | Done when |
|---|---|---|---|
| S5.1 | AG | `POST /chats` (new) and `POST /chats/{id}/messages`: append the user turn, stream the chat model's reply as SSE tokens, append the AI turn | the composer streams a reply |
| S5.2 | CC / AG+ | On reply completion, enqueue `process_pair` for that pair on the chat's queue. Events: `pipeline_status` → `pair_ready` | the graph gains the pair 5–20 s after the reply |
| S5.3 | AG | Frontend live choreography (INTERACTION_SPEC §4, the Phase 3 versions in history): typing indicator, streaming bubble, the rail keeps the previous pair until `pair_ready`, LIVE versus HISTORY (no yanking when scrubbed back), Back-to-latest pill, "the panel is thinking" state | an e2e test with a stubbed model |
| S5.4 | CC / AG+ | Continue an imported chat: the model's context is the dialogue (capped; older pairs summarised); new pairs are processed from the existing state | continuing c05 adds pair 8 to the same graph |
| S5.5 | CC | **Incremental equals batch (E4):** a chat replayed pair by pair through the live path produces byte-identical artifacts to the batch run (cassettes) | a tier0 test passes on 3 chats |
| S5.6 | AG | Edge cases: send while the pipeline is running (queued, shown); reply fails (Retry); pipeline fails (flag + Rerun); reload mid-stream (reconnect, resume from `status.json`) | e2e covers each |
| S5.7 | AG | Live cost and performance report: time from reply to graph update (p50/p90), cost per live turn → `reports/S5_cost_perf.md` | report committed |
| **S5.T** | You | **Owner test:** §6A script S5 | log entry written |
| **S5.G** | You | Have a real 10-turn conversation in the app and judge whether the map matches what happened | — |

### S6 · Long chats and scale (about 1–2 weeks; roadmap E3 slice)
| Step | Builder | What | Done when |
|---|---|---|---|
| S6.1 | CC | Run the longest promoted chat (up to 242 pairs) with metering: time per pair, token growth, Step 3 batch size tuning | the report states the per-pair cost curve |
| S6.2 | CC | Context caps where tokens grow linearly (spec §12.2), behind flags, with invariants green | per-pair cost flat-ish after pair 50 |
| S6.3 | AG | Frontend at 300 chats: virtualised sidebar, lazy bundles, Brain at 300 territories (the unit-doubling rule in BRAIN_SYSTEM_SPEC §2) | smooth scrolling; Brain holds 60 fps on the desktop |
| S6.4 | AG | Logs: per-chat run log viewer (`llm_monitor`, invariant report) in a Details drawer | a failure can be diagnosed in-app |

### S7 · Standalone v1 release (about 1 week)
| Step | Builder | What | Done when |
|---|---|---|---|
| S7.1 | AG | First-run wizard: library folder → key and models → budget → "Import your history" or "Start a conversation" | a fresh machine reaches a working app in under 5 minutes |
| S7.2 | AG | Backup: export the library as a zip; import from a backup; trash view with restore and permanent delete (confirmed) | round-trip test |
| S7.3 | AG | `README` "Run COTRACE locally", privacy note (what leaves the machine: only model calls), troubleshooting | you can follow it on a clean account |
| S7.4 | CC | Release audit: full pytest, e2e, invariants on 10 chats + 10 newly imported, secret-leak grep, `npm run tokens:check` | all green |
| **S7.T** | You | **Owner test:** the full §6A script on a fresh user account, start to finish | log entry written |
| **S7.G** | You | Use it for a week of real work. Tag `standalone-v1` | — |

---

## 5. Sequencing and parallel lanes

```
week   1      2      3      4      5      6      7      8      9     10
S0     █
S1      ████████
S2             ███████
S3                    █████
S4                         ██████████
S5                                   ██████████
S6                                             ███████
S7                                                    █████
D-track UI/UX, Brain polish   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ (parallel, web/src/design-system and brain-* only)
```

About **9–10 weeks part-time**, re-dated at every gate.

**What can overlap safely** (one writer per path):
- S2.1–S2.3 (server, AG) can start while S1.4–S1.5 (engine tests, CC) finish, because the server reads `workspace_bundle.json` and doesn't write engine code.
- S3.3–S3.4 (settings UI and budget, AG) run alongside S3.2/S3.5 (estimator and bake-off, CC).
- S4.2 (import dialog UI, AG) runs alongside S4.3–S4.5 (queue and pipeline, CC).
- Design-system and Brain work continues the whole time, touching only `web/src/design-system/`, `brain-*` and `docs/design-system/`.

**Never in parallel:** two agents in `engine/`, or two agents in `server/`.

---

## 6. How to run this with Antigravity (the working ritual)

This is the workflow we have used so far, made explicit.

**Roles**
- **You, the owner:** gates, decisions, real-data judgement.
- **Command center (a planning chat: Claude Code or Gemini):** writes and amends this plan and the briefs, answers "is this right?", reviews diffs at gates. It never builds.
- **Antigravity:** builds one step at a time.
- **Claude Code:** the CC steps, or a second opinion on AG+ steps.

**Per step:**
1. Paste the kickoff prompt (below) with the step id.
2. Antigravity gives a preamble (why, decisions, plan of files). You check that it names the right files, then reply **"start task"**.
3. It builds, runs the step's done-when check, appends BUILDLOG and commits `S<phase>.<step>: <what> — <why>`.
4. Antigravity ends every step with an **Owner check** block: what to open or run, what to click, and what you should see. You do it yourself. Tests green? Done-when met? Diff size sensible? Any engine number changed (it must not)? Then reply **"Finish Step"**, or report what's wrong (it becomes a fix step).
5. Gate steps: you decide, then the command center records the decision (a DDR for contract or visual changes).

**Full prompts** (first session, resume, owner test, gate): [`GEMINI_KICKOFF.md`](GEMINI_KICKOFF.md).

**Short kickoff prompt:**
```
You are the build agent for COTRACE (repo: Timeline). Read, in order:
AGENTS.md (all), docs/plans/STANDALONE_V1_PLAN.md §0–§3 and the section for phase <S#>,
the latest BUILDLOG.md entry, and `git log --oneline -15`.
Do ONLY step <S#.#>. First give a short preamble: why this step, decisions needed,
files you will create or change, how you will prove "done when". Then wait for "start task".
Rules: one step per response; never edit engine math or the frozen fixture unless the step
says so; never commit secrets or library data; every new test carries exactly one tier marker;
run `.venv/bin/python -m pytest` (and `npm run e2e` once it exists) before finishing; append a
BUILDLOG entry; commit as "S#.#: <what> — <why>"; end with an "Owner check" block (exact steps for the owner
to try and the expected result); then stop and wait for "Finish Step".
If the plan contradicts the code or a spec, STOP and report it. Do not improvise.
```

**When an AG+ step goes wrong:**
- a red invariant
- a changed fixture number
- an equivalence diff it can't explain

Stop. Hand the step to Claude Code with the BUILDLOG entry and the failing test, not with the chat.

**Review checklist at each gate:** done-when met · tests (count went up, not down) · BUILDLOG accurate · no files outside the phase's paths · screenshots checked · open questions logged in `SPEC_QUESTIONS.md`.

---

## 6A. You test everything: the owner test protocol

Automated tests prove the plumbing. **You** prove the product. These rules are part of the build process, not extras.

**T1. Nothing is approved until you've tried it.**
- Every step ends with an Owner check (§6, point 4).
- Every phase has an **owner test step (S#.T)** before its gate. You run the phase's test script by hand and record the result in [`OWNER_TEST_LOG.md`](OWNER_TEST_LOG.md) as **Approved** or **Changes needed**.
- A phase cannot close with an open "Changes needed".

**T2. Real data from the start, not at the end.**

| Phase | Real data |
|---|---|
| S1 | Your 10 processed chats, read as plain reports (S1.7) |
| S2 | The same 10 in the running app |
| S3 | 3 brand-new chats processed with real money, with you present (S3.6) |
| S4 | Your own export |
| S5 | Your own conversations |

There is never a phase where only synthetic data has been seen.

**T3. Cost and performance are measured every phase, from S2 on.**
- Each phase commits a report in `docs/plans/reports/` with the same metrics, so phases can be compared.
- At the gate you compare it against the budgets below. A budget miss is either fixed or explicitly accepted by you in the log.

| Metric | Budget (starting point; reset at S3.G from measured data) |
|---|---|
| Cost per processed pair | ≤ $0.005 (archive of 2,759 pairs ≤ ~$15) |
| Pipeline time per pair, chats < 30 pairs | p50 ≤ 20 s · p90 ≤ 45 s |
| Reply → graph updated (live) | p50 ≤ 25 s |
| Estimate vs actual cost | within ±35% |
| Import scan of 313 chats (no LLM) | ≤ 30 s |
| App first load with 300 chats | ≤ 2 s |
| Open a chat | ≤ 500 ms |
| Brain frame rate (desktop) | ≥ 45 fps |

**T4. Every problem you find becomes a tracked fix.**
- Log it as `T-<n>` with what you did, what you expected and what happened.
- The agent fixes it as step `S#.fix-T<n>` (tests first), and you re-test.
- The log keeps the whole history.

**Owner test scripts** (the agent turns each into a numbered checklist in the log before the session):

| Phase | You do | You look for |
|---|---|---|
| S1 | Read 3 chat reports | Do the outcomes and the human/AI split match what you remember? |
| S2 | `./cotrace start`; open, scrub, Brain, delete and restore | Same as the prototype; nothing lost; restore works |
| S3 | Enter your key; test the connection; read the S3 cost report | Key never shown again; costs make sense; quality worth it? |
| S4 | Upload your export → review table → process 5–10 chats → kill the app mid-run → restart | Estimate before spending; chats appear as they finish; resume without re-paying; maps believable |
| S5 | New chat, 10 turns; continue an old chat; scrub back while it's thinking | Graph grows per turn; no jumping when you're scrubbed back; failures show Retry or Rerun |
| S6 | Open the longest chat; scroll 300 chats; spin the full Brain | Smooth; long chat readable; costs flat |
| S7 | Fresh account: install → wizard → import → chat → backup → restore | Under 5 minutes to a working app; nothing private in git |

---

## 7. Testing (added to TEST_STRATEGY's tiers)

| Tier | New in track S |
|---|---|
| tier0 replay | import → process with cassettes; incremental equals batch (S5.5); resume after kill (S4.3) |
| tier1 exact | workspace projection equivalence (S1.3); W1–W6; API contract tests; estimator accuracy; key never leaks |
| tier2 live | one real import of 3 short chats and one live 3-turn chat; runs at gates only, under budget |
| e2e (Playwright) | prototype smoke + refinement; upload flow; live flow (stubbed model); offline mode |

---

## 8. Cost and privacy

- **Cost today (ROADMAP):** mapping all 2,759 archived pairs is about $5–15 with the cheap setups in the cost playbook, against about $780 at old settings. S3 replaces these estimates with measured numbers.
- **A live turn** is about 3 + touched outcomes + ⌈requirements ÷ batch⌉ model calls (Architecture §5), metered from S3 on.
- **Every spend passes a gate:** the import button shows the estimate, the budget cap is enforced, and reruns are confirmed.
- **What leaves the machine:** only model API calls (the dialogue text the pipeline needs), to the provider you configured. Nothing else, no telemetry. The key is stored locally in `secrets.json` (0600) and never returned by the API.

---

## 9. Risks and answers

| Risk | Answer in this plan |
|---|---|
| Projection differs from the prototype data | S1.3 equivalence test; differences are explained before the freeze |
| Costs surprise you | S3 before S4; estimate gate; budget cap |
| An invariant fails on a new, messy chat | S-D9: flag and continue; Rerun; the logs drawer |
| A long chat makes per-pair cost grow | S6.1–S6.2 measured caps |
| The agent drifts or one-shots a phase | one step per response; done-when per step; gates |
| Two tools edit the same files | lanes in §5; one writer per path |
| Laptop sleeps during a 300-chat import | persistent queue with resume (S4.3) |
| The Brain gets crowded at 300 chats | the global unit-doubling rule (BRAIN_SYSTEM_SPEC §2) |

---

## 10. Decisions needed from you (recommendation first)

| # | Question | Recommendation |
|---|---|---|
| 1 | UI contract: `workspace_bundle` (today's shape) now, G1's compact `graph_bundle` later? | **Yes** (S-D1) |
| 2 | Library location | **`~/Cotrace`**, outside the repo |
| 3 | Who builds the CC steps | **Claude Code** for S1.2–S1.5, S3.1–S3.2, S3.5, S4.3–S4.5, S5.2, S5.5 and S6.1–S6.2. Antigravity everything else. If you prefer Antigravity for all, use the AG+ checks |
| 4 | Live chat model | Decided at S3.G from the bake-off. Default: the cheapest Gemini model that passes |
| 5 | First real import | **Your 20 favourite chats**, not all 313, until S4.G passes |
| 6 | Category suggestions by a cheap model | **Yes, as suggestions you confirm** |
| 7 | The S0 commit: commit today's uncommitted work as the baseline | **Yes, before any other tool starts** |

---

## 11. After v1 (the bigger vision, in order)

1. **D-track UI/UX phase.** The visual direction work deferred by DDR-002, on a now-real app.
2. **B1 Brain data layer.** Cross-chat links with evidence (similar < continued < reused) drawn as tracts (BRAIN_SYSTEM_SPEC §9.1), placement by evidence instead of topic lobes, and a global time scrubber.
3. **G3 outside sources.** Claude Code and Codex sessions mapped live, then the browser extension side panel on claude.ai and chatgpt.com, using the same server API.
4. **Public beta (M8).** Desktop packaging, privacy policy, calibration (E5), open source.
