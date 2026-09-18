# TEST_STRATEGY.md — v1.0

How this engine is proven correct, and what "correct" means when half of it calls an LLM.

Authority: below COTRACE_PIPELINE_SPEC, beside PANEL_SPEC / INTERACTION_SPEC.
Read-only from the build side.

---

## 0. The governing problem

The pipeline makes five LLM calls per pair. You cannot write a test that says "this
chat produces 14 requirements", because tomorrow it produces twelve. Chasing exact
values on LLM output wastes months and proves nothing.

**The rule: test properties, not values.**

Exactness is demanded only where there is no model in the path. Everywhere else, the
question is whether the output obeys the rules that must always hold.

---

## 1. The four tiers

Every test belongs to exactly one tier. The marker is mandatory.

| Tier | Marker | Covers | Standard | Runs |
|---|---|---|---|---|
| **1 Exact** | `tier1` | No LLM in the path: Stage 4a maths, projections, state transitions, schema validation, mode classifier, R-SUM, importer | Byte-exact. Canonical numbers every time. | Every commit |
| **0 Replay** | `tier0` | The LLM half, against recorded responses | Deterministic. Same as tier 2 but free and fast. | Every commit |
| **2 Live** | `tier2`, `live` | The LLM half, against the real API, on real chats | Invariants hold. Values vary within measured bands. | Phase gates, weekly |
| **3 Robustness** | `tier3` | Scale, volume, malformed input, failure injection | Does not crash, hang, leak, or corrupt. Correctness not asserted. | On demand, before a phase closes |

`pytest.ini` markers:

```ini
[pytest]
pythonpath = .
testpaths = tests
markers =
    tier0: replay tests against recorded LLM responses
    tier1: exact, deterministic, no network
    tier2: live API, slow, costs money
    tier3: robustness and scale
addopts = -m "not tier2 and not tier3"
```

Default `pytest` runs tier0 and tier1 only. Everything else is opt in:

```bash
pytest                      # tier0 + tier1, the everyday run
pytest -m tier1             # the exact suite alone
pytest -m tier2             # live, costs API budget
pytest -m tier3             # robustness
pytest -m "tier0 or tier1 or tier2 or tier3"   # everything
```

---

## 2. The invariant catalogue

These must hold on every chat, every run, forever. They live in `tests/invariants.py`
as one function per invariant, imported by the test suites and by `engine/checks.py`.

### Referential integrity

1. Every artifact validates against its schema.
2. Every action id matches `^([UA])\((\d+),(\d+)\)$` and is unique within the chat.
3. Every ledger row's `action_id`, `req_id` and `outcome_id` exist in state.
4. Every action maps to exactly one outcome.
5. No duplicate ledger rows on `(action_id, outcome_id, req_id, pair_added, kind)` (requirement identity is `(outcome_id, req_id)`, never `req_id` alone; see Q8).


### Structure

6. The outcome tree has exactly one root, no cycles, every parent exists, and
   `children[]` agrees with `parent` pointers in both directions.
7. Every requirement has at least one creation action.
8. Every requirement's `created_at_pair` is less than or equal to the current pair.
9. Slot status is one of `open`, `resolved`, `abandoned`. A `resolved` slot links to a
   requirement. An `abandoned` slot was inactive for at least three pairs.

### Arithmetic

10. All scores are finite and strictly positive.
11. The sum of per-pair deltas equals the cumulative total at the final pair.
12. Creator counts sum to the number of distinct requirements.
13. Cumulative mass is monotonically non-decreasing across pairs.
14. `h_you <= delta_you` and `h_ai <= delta_ai`. SHAPER scores are a subset of all
    scores. If this fails, a definition has drifted.
15. Percentages are within `[0, 100]` and sum to 100 within rounding tolerance.
16. The mode is a pure function of `w` and `h` and is one of the four defined values.

### Process

17. **Append-only.** Ledger rows for pair `t` are unchanged after pair `t+1` is
    processed, unless an explicit rerun wipes them.
18. **Idempotency.** Rerunning pair `t` twice leaves the same ledger state as running
    it once.
19. **Purity.** The same ledger produces byte-identical `analysis.json`.
20. **Batch equals live.** The same chat through both entry points, with cached LLM
    responses, produces identical ledgers.
21. **Provenance.** Every ledger row traces to a turn present in `dialogue.json`, and
    every attributed action's `evidence_quote` appears verbatim in that turn's text.

Invariant 20 is what makes the two entry modes one engine rather than two.
Invariant 21 is what makes every number on any future screen defensible.

---

## 3. The corpus

Built per IMPORT_SPEC. Ten chats, chosen to cover the matrix rather than to be
plentiful.

| Dimension | Values to cover | Why |
|---|---|---|
| Length | short 3-5 pairs, medium 6-20, long 21+ | Long chats stress the accumulate window, cost, and Trigger B |
| Task type | coding, writing, planning, research, creative, debugging | COTRACE found technical closed-ended tasks produce more AI goal-shaping than open-ended ones |
| Prompt style | specified, vague | COTRACE found underspecified prompts move AI share from 30.65% to 69.64% |
| Expected mode | one you-driving, one copilot, one autopilot | Gives the classifier something real to be judged against |
| Awkward content | code blocks, non-English, very long single message, lists | Extraction breakers |

### The golden chat

One short chat, three pairs, where the owner writes out every action, requirement and
attribution **by hand** before the engine ever runs on it. Stored as
`data/corpus/golden_01/expected.md`.

This is fixture two. It does not replace fixture one.

| Fixture | Contains | Tests |
|---|---|---|
| `fixture_pair1` | A ledger, dialogue text stubbed | Stage 4a maths. Exact, forever frozen. |
| `golden_01` | Real dialogue text, hand labels | Extraction quality. Judged, not asserted. |

The existing fixture cannot test extraction because its dialogue text is
`"(not captured in fixture)"`. This is why the second fixture exists.

### Grading the golden chat

For each hand-labelled requirement, mark the engine's output:

- **match**: the engine found it, meaning the same thing
- **miss**: the engine did not find it
- **spurious**: the engine invented one that is not a real requirement
- **split**: the engine fragmented one requirement into several
- **merged**: the engine collapsed several into one

Target at E1 close: **match rate at or above 80%, spurious rate at or below 20%.**
Record the actual numbers in the BUILDLOG entry. These are judged by the owner and no
test asserts them.

---

## 4. Stability, the honest answer to non-determinism

Rather than treating variance as unknown, measure it and publish it.

**Protocol.** Three corpus chats, five runs each against the live API. Record:

| Metric | Record |
|---|---|
| Requirement count | min, max, mean, coefficient of variation |
| Direction split | spread in percentage points |
| Decision split | spread |
| Mode | how many runs of 15 agreed |
| Ledger rows | spread |
| Wall time per pair | mean, max |
| Tokens per pair | mean, max |

Write the result to `docs/STABILITY.md` and amend COTRACE_PIPELINE_SPEC §12.9 with the
real figures.

**What it buys.** A sentence like: *direction varies by plus or minus 4 points across
runs and the mode was stable in 14 of 15 runs.* That turns an unknown into a documented
property of the instrument.

It also settles a design question that cannot currently be answered: how many
significant figures the interface is allowed to display. A panel showing 21.7% when the
true figure is 21.7 plus or minus 4 is making a precision claim it cannot support.

**The test that follows.** Once bands are recorded, a tier2 run outside its band is a
regression signal. Variance stops being an excuse and becomes a gate.

---

## 5. Robustness scenarios

Tier 3. Correctness is not asserted. Survival is.

| Scenario | Method | Must not happen |
|---|---|---|
| Very long chat | 40+ pair corpus chat through batch | Context overflow, superlinear slowdown, unbounded memory, cost blowup |
| Huge single message | One pair with a 20,000 word turn | Silent truncation. A clean hard error is acceptable, silence is not |
| Rapid succession, live | Five messages sent without waiting | Interleaving, lost pairs, out-of-order processing |
| Mid-run crash | Kill the process between steps | Half-written artifacts, unresumable state |
| API failure | Inject 500s and timeouts | Anything other than four retries with backoff, then a clean failed status |
| Malformed model output | Broken JSON through the replay cache | A bad row reaching the ledger. Repair chain then hard error is correct |
| Empty or trivial pair | "ok" answered with "ok" | A crash, or invented requirements. A quiet pair is correct |
| Slot churn | Chat where questions open and never resolve | Slots accumulating past the three-pair abandonment sweep |
| Two chats at once | Batch two chats in parallel | Cross-contamination. D11 says this is free. Prove it |
| Duplicate import | Import the same source twice | A second divergent corpus entry |

**Two curves to record during the long-chat run**, because they decide what is feasible
later: wall time per pair against pair index, and tokens per pair against pair index.
If either bends upward, the accumulate windows are growing without bound and long chats
will eventually become unusable.

---

## 6. Checks run in production, not just in tests

`engine/checks.py` holds the invariants and runs **after every pipeline run, on every
chat, live or batch.**

```
process_pair() -> write artifacts -> run checks
    pass: continue
    fail: write the violation to run/status.json, mark the pair unhealthy, stop the run
```

COTRACE_PIPELINE_SPEC §11.4 already defines mechanical checks. This promotes them from
a test-time nicety to a runtime guarantee, so a corrupt ledger can never accumulate
silently.

### The run report

Every run writes `data/chats/<id>/run/report.json`:

```json
{
  "chat_id": "c01_coding_short",
  "pairs_processed": 4,
  "wall_time_per_pair": [12.1, 9.4, 15.8, 11.2],
  "tokens_per_pair": [4210, 5133, 6902, 7455],
  "llm_calls": 20,
  "retries": 1,
  "cache_hits": 0,
  "requirements_created": 9,
  "slots": { "opened": 3, "resolved": 1, "abandoned": 0 },
  "checks": { "passed": ["inv_01", "inv_02"], "failed": [] },
  "final": { "direction": [31.2, 68.8], "decisions": [3, 6], "mode": "COPILOT" }
}
```

This is the instrument panel for the instrument, and the raw material for the thesis
chapter on system performance.

---

## 7. What to test after each engine feature, and what to expect

### After Steps 2 and 3 (E1)

**Test.** Golden chat against hand labels. Invariants 1-9 on all ten corpus chats,
tier0 replay.

**Expect.** Roughly 1 to 6 requirements per pair on substantive pairs. Zero on
pure-execution pairs. Every action mapped to exactly one outcome.

**Investigate if.** A single pair yields more than 15 requirements, which means
extraction is fragmenting. Or a whole chat yields zero, which means the prompt is
failing on that content type.

### After Stage 4a (E2)

**Test.** Recompute canonical numbers from the frozen 157-row ledger.

**Expect.** Exactly `ΣU=87.0`, `ΣA=314.0`, `21.7 / 78.3`, decisions `4 / 10`,
mode `COPILOT`, `w 4/10`, `h 47.0/239.0`. No tolerance. Tier 1.

**Investigate if.** Anything differs at all. Per AGENTS.md rule 5, the code is wrong,
not the numbers.

### After the batch adapter (E3)

**Test.** All ten chats end to end. Stability protocol on three. Long-chat and
huge-message robustness.

**Expect.** Every chat completes. `direction_hint` in `meta.yaml` matches direction of
travel. The vague-prompt chat shows a higher AI share than the specified-prompt chat.

That last one is worth calling out: it reproduces COTRACE's own finding on your data.
If it holds, the method is validated independently. If it inverts, either the
classification of those chats is wrong or something in scoring is.

### After the live adapter (E4)

**Test.** Invariant 20, batch against live on the same chat with cached responses.
Rapid succession, crash resume, API failure.

**Expect.** Identical ledgers. Queued pairs. Clean recovery.

### After projections (E5)

**Test.** Rebuild `panel_bundle.json` as a projection of `analysis.json`.

**Expect.** Byte-identical to the frozen fixture bundle. That is the proof the 4a/4b
split lost nothing.

---

## 8. Standing rules

1. No phase closes with any invariant red.
2. Every test carries exactly one tier marker. An unmarked test fails CI.
3. Recorded LLM responses are committed. Re-record only when a prompt changes, and say
   so in the BUILDLOG entry.
4. Tier 2 never runs in CI.
5. The frozen fixture is never regenerated. Ever.
6. A corpus entry is never hand-edited. Fix the importer and re-import.
7. Owner-judged results, meaning golden-chat grading and stability bands, are recorded
   as numbers in the BUILDLOG, never asserted by a test.
