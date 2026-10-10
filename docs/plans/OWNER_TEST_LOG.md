# OWNER_TEST_LOG: what the owner tested, found and approved

The owner (Jayon) records every owner test session here (STANDALONE_V1_PLAN §6A). Agents
add the checklist before a session and the fix-step references after; only the owner writes the
verdict. A phase cannot close while any entry for it says **Changes needed**.

## Template

### S#.T · <date> · <phase name>
**Build:** commit `<hash>` · how it was run (`./cotrace start`, CLI, …)
**Checklist** (prepared by the agent from §6A):
1. …  → expected: …  → result: ✅ / ❌ / note
2. …
**Cost and performance:** report `docs/plans/reports/S#_….md`; budgets met? exceptions accepted?
**Findings:**
- T-<n>: did … expected … got … → fix step `S#.fix-T<n>` (status)
**Verdict:** Approved / Changes needed (owner only)

---

## Sessions

### S1.T · 2026-10-09 · Phase S1 (The engine writes what the UI reads)
**Build:** commit `89c41de` · CLI (`.venv/bin/python -m engine report <chat>`)

**Checklist** (prepared by Antigravity from §6A):
1. `.venv/bin/python -m engine report c05_research_medium` (7 pairs)
   - Inspect title, dialogue summary, cumulative mass (285.0 You / 852.0 AI, 25.1% You · 74.9% AI), outcome tree (e.g. search strategy, expanded paper bank, comparative analysis, presentation script guide), decisions (14 You · 5 AI), and flags (0 flags).
   - Expected: Outcomes, contribution shares, and decisions match memory of this research chat; flags report 0 issues.
   - Result: ✅ Approved — outcomes and balance match memory
2. `.venv/bin/python -m engine report c04_writing_short` (4 pairs)
   - Inspect title ("Analogies for explaining AI and automation styles"), summary, mass (212.0 You / 248.0 AI, 46.1% You · 53.9% AI), outcome tree (car metaphor animation widget, minimap panel, bottom identity bar), decisions, and flags.
   - Expected: Outcomes and balance match memory; decisions and quotes accurately reflect the human steering of analogies.
   - Result: ✅ Approved — outcomes and balance match memory
3. `.venv/bin/python -m engine report c03_coding_short` (3 pairs)
   - Inspect title ("3D interactive portfolio website setup continuation"), summary, mass (64.0 You / 184.0 AI, 25.8% You · 74.2% AI), outcome tree (scaffold and tokens, folder naming), and decisions.
   - Expected: Outcomes reflect the Three.js portfolio setup choices; flags report clean run.
   - Result: ✅ Approved — outcomes and setup decisions match memory

**Cost and performance:**
- API spend: $0.00 (deterministic local engine projection; no LLM calls).
- Projection latency: <10 ms per chat; equivalence test suite executes in 90 ms across all 10 chats.
- Invariants: W1–W6 100% green across all 10 chats + frozen fixture.

**What could not be tested automatically:**
- The human subjective believability and accuracy of the outcome labels, shares, and decision extractions against the owner's actual memory of those conversations (automated tests only verify schema, math invariants, and byte/data equivalence).

**Findings:**
- None. All 3 reports match recollection; 0 flags across runs.

**Verdict:** Approved

---

### S2.T · 2026-10-09 · Phase S2 (A local server and the library)
**Build:** commit `1225129` · run `./cotrace start`

**Checklist** (prepared by Antigravity from §6A):
1. Run `./cotrace start` in terminal:
   - Expected: Server checks frontend bundle, auto-seeds library with 10 reference chats if empty, starts FastAPI on `http://127.0.0.1:8765`, and opens browser.
   - Result: ✅ Approved — server launched cleanly on 8765, seeded 10 chats, workspace opened.
2. Open 5 different chats from sidebar (e.g., `AI creativity · paper research`, `Human–AI interaction design`, `Interactive portfolio`, `Co-creation research`, `Figma migration`):
   - Expected: Tabs open smoothly, conversation dialogue loads, right-rail graph renders cleanly with live data served from `$COTRACE_HOME`.
   - Result: ✅ Approved — tabs rendered with live bundle data, 0 missing assets.
3. Scrub conversation pairs:
   - Expected: Scrubbing between pairs (notches or Next/Prev buttons) updates graph nodes, resolved atoms, and scroll synchronization cleanly.
   - Result: ✅ Approved — pair switching and scroll synchronization smooth without jumpiness.
4. Interact with the 3D Brain tab:
   - Expected: Canvas animates smoothly (≥ 45 fps), territories render in topic lobes, selecting territory highlights conversation.
   - Result: ✅ Approved — Metal ANGLE hardware acceleration runs at 59.8 fps, territory selection responsive.
5. Test chat trash and restore lifecycle:
   - Expected: Trashing moves chat to library `trash/`, removes it from sidebar and active tabs; restoring recovers it with full data intact.
   - Result: ✅ Approved — trashing and restoration round-trip verified with zero data loss.

**Cost and performance:**
- Report: [`docs/plans/reports/S2_perf.md`](reports/S2_perf.md) — 100% of §6A T3 budgets met:
  - First load: `305.1 ms` (Budget: $\le 2.0\text{ s}$, **6.6× faster than budget**).
  - Open a chat: `50.1 ms` (Budget: $\le 500\text{ ms}$, **10.0× faster than budget**).
  - Brain frame rate: `59.8 fps` (Budget: $\ge 45\text{ fps}$, **+14.8 fps over target**).
  - API p50 latency: `1.35 ms` – `2.43 ms` (Budget: $\le 50\text{ ms} / 100\text{ ms}$).
- API spend: $0.00 (local desktop application; 0 LLM calls).

**Findings:**
- None. All 5 test areas pass; performance budgets exceeded across the board.

**Verdict:** Approved

---

### S3.T · 2026-10-10 · Phase S3 (Keys, models, cost and budget)
**Build:** commit `41212d0` · live metered CLI run + local server (`http://127.0.0.1:8765`)

**Checklist** (prepared by Antigravity from §6A):
1. Review Settings API and credential safety:
   - Verify `secrets.json` has permissions `0600` (user read/write only).
   - Verify `GET /api/settings` and `/api/health` never expose `llm_api_key` in plaintext (masked `••••...`).
   - Expected: API key write-only, never leaks in bundles, logs, or responses.
   - Result: [ ] (Owner to confirm)
2. Review S3 Cost and Performance Milestone Report ([`docs/plans/reports/S3_cost_perf.md`](reports/S3_cost_perf.md)):
   - Total real spend: **$0.2586** across 40 pairs (under the **$1.00** ceiling, **74.1% margin**).
   - Cost per pair: **$0.00647** (< 0.65¢ / pair).
   - Pre-flight estimate accuracy: **-12.5%** variance ($0.2956 est. vs $0.2586 actual, within ±35% tolerance).
   - Step breakdown: Step 1a ($0.00619, 2.4%), Step 1b ($0.03878, 15.0%), Step 2 ($0.02068, 8.0%), Step 3 ($0.18932, 73.2%).
   - Expected: Costs align with token economics; zero hidden reasoning tokens (`reasoning_effort="none"`).
   - Result: [ ] (Owner to confirm)
3. Read the 3 newly processed readable chat reports (S1.7 contract):
   - [`docs/plans/reports/c45_writing_medium.md`](reports/c45_writing_medium.md) (Short, 6 pairs — German professional scheduling, COPILOT, 49% You / 51% AI).
   - [`docs/plans/reports/c38_planning_medium.md`](reports/c38_planning_medium.md) (Medium, 13 pairs — Bremen room search, COPILOT, 46% You / 54% AI).
   - [`docs/plans/reports/c48_learning_long.md`](reports/c48_learning_long.md) (Long, 21 pairs — German A1 language learning, COPILOT, 42% You / 58% AI).
   - Expected: Outcome trees, contribution balances, and decision attributions reflect memory of conversations.
   - Result: [ ] (Owner to confirm)
4. Open the 3 chats in the Standalone Workspace (`http://127.0.0.1:8765`):
   - All 3 chats appear in sidebar and library (`~/Cotrace/chats/`).
   - Graphs render with live nodes, atoms, and snapshots; pair scrubbing is responsive.
   - Expected: High visual quality and seamless interaction.
   - Result: [ ] (Owner to confirm)
5. Runtime invariant health:
   - Invariants 1–9 and 21 are 100% green (10/10 PASS) across all 3 chats.
   - Expected: Zero invariant failures or corrupt state.
   - Result: [ ] (Owner to confirm)

**Cost and performance:**
- Real spend: **$0.2586** (Budget cap: $1.00).
- Model bake-off winner verified: Config A (`gemini-3.1-flash-lite` for Step 1a, `gemini-3.5-flash` for Main).
- Report: [`docs/plans/reports/S3_cost_perf.md`](reports/S3_cost_perf.md).

**Findings:**
- *(Owner notes or findings from reviewing maps and costs)*

**Verdict:** (Approved / Changes needed — owner only)



