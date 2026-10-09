# E1_BRIEF.md — The Extraction Pipeline (Steps 2 and 3)

**Phase:** E1, second phase of the engine-first rebuild
**Tool:** Claude Code, Opus. **ONLY.** Routing rule: wrong-number-is-worse-than-slow.
**Depends on:** E0 closed honestly, `golden_01` existing, ten chats classified
**Gate before E2:** see Definition of Done

---

## 1. Why this phase exists

Steps 1a, 1b and 1c are on disk and working. They produce actions, an outcome tree and
intentions. Nothing yet produces **decisions** or **scores**.

E1 builds the two steps that do:

- **Step 2** turns actions into requirements and slots, the things a person would call
  decisions and open questions.
- **Step 3** decides who influenced each requirement and by how much, writing one ledger
  row per influence claim.

After E1 the engine can look at a real conversation and say what was decided and who
shaped it. It cannot yet say what that adds up to; that is E2.

This is the phase where the project stops being plumbing and starts producing the thing
it exists to produce. It is also the phase with the most ways to be quietly wrong, which
is why it is Opus-only and why the grading is done by hand.

---

## 2. Read before starting

In this order. Do not skip and do not read more.

1. `AGENTS.md` in full. Workflow gates apply to every step.
2. `docs/Cotrace Pipeline Spec.md` **§6** (Step 2 prompt), **§7** (Step 3 prompt),
   **§9** (the iteration mechanism, Triggers A and B, the abandonment sweep),
   **§10.3** (ledger row format), **§11.4** (mechanical checks).
3. `docs/TEST_STRATEGY.md` §1, §2, §6, §7.
4. `engine/pipeline.py` in full. Steps 2 and 3 must match its existing shape.
5. `data/corpus/golden_01/expected.md`, the hand labels you will be graded against.
6. The last two `BUILDLOG.md` entries.

**Do not read** PANEL_SPEC or INTERACTION_SPEC. No UI work happens in this phase.

---

## 3. Scope

**In scope**
- `engine/pipeline.py`: `step_2()`, `step_3()`, and a `run_level2()` orchestrator
- `engine/checks.py`: the invariants promoted to runtime
- Ledger writing through the existing `LedgerWriter`
- Slot lifecycle including the three-pair abandonment sweep
- Cassette recording for every corpus chat used
- Tests, tier0 and tier1

**Out of scope, do not touch**
- Stage 4, `quant.py`, `analysis.json`. That is E2 and its schema is not designed yet.
- Anything under `web/` or `server/`
- The five frozen schemas
- `data/chats/fixture_pair1/`, frozen forever
- The prompts themselves. They are copied verbatim from the spec. If a prompt looks
  wrong, that is a SPEC_QUESTIONS entry, not an edit.

**The rule that outranks momentum:** if implementing reveals a contradiction in the
pipeline spec, stop, log it, take the most conservative reading, mark it REVISIT. Do not
improvise anything that touches a score.

---

## 4. Pre-work, before S1

These carry over from the E0 verification. Small, and they block clean measurement.

- **P1** `inv_21` implements the `evidence_quote` verbatim check, or its docstring is
  narrowed. E1 produces the first real `evidence_quote` values, so this is the phase
  where it starts mattering.
- **P2** Q7 (single-root constraint) and Q8 (5-tuple key) logged in SPEC_QUESTIONS.
- **P3** `fidelity_grade` present in every `meta.yaml` and in `manifest.json`.
- **P4** `scripts/phase_report.py` exists, because this phase's DoD is reported with it.

---

## 5. Steps

### S1 — Golden chat harness

Build the grading machinery before the thing being graded.

`scripts/grade_golden.py` compares engine output for `golden_01` against
`expected.md` and prints:

```
requirements expected : N
requirements found    : M
match                 : n  (same meaning, allowing different wording)
miss                  : n
spurious              : n
split                 : n  (one expected requirement fragmented into several)
merged                : n  (several expected requirements collapsed into one)
match rate            : xx.x%
spurious rate         : xx.x%
```

Matching is **owner-judged, not automatic.** The script emits a side-by-side table and
the owner marks each row. Do not attempt semantic similarity scoring; it would be
measuring your embedding, not your extraction.

**Verify:** runs against empty engine output and reports 0 found, N missed, without
crashing.

**Commit:** `E1.S1: golden chat grading harness — side-by-side table, owner-judged`

---

### S2 — Step 2, requirement and slot extraction

Implement `step_2()` in `engine/pipeline.py`, matching the existing style of `step_1b()`.

- Prompt copied **verbatim** from pipeline spec §6, `FROZEN` header naming the section.
- **Fans out: one LLM call per touched outcome.** An outcome is touched when any action
  added this pair maps to it, via the `action_to_outcome` mapping from Step 1b.
- Input per call: that outcome's actions (FILTER), its prior requirements, its prior
  open slots.
- Output: requirement operations `create` / `revise` / `delete`, and slot operations
  `open_slot` / `resolve` / `abandon`.
- Each `create` writes a ledger row with `kind: "creation"` and `score: 5.0`.
- Each `resolve` writes a `kind: "slot-origin"` row.
- Validation, hard errors like Step 1b: unknown `outcome_id`, unknown `req_id` on revise
  or delete, duplicate `req_id` within an outcome, malformed operation.

**Remember from E0:** `req_id` is unique **within** an outcome, not globally. Key every
lookup on `(outcome_id, req_id)`.

**Verify:** run on `golden_01` pair 1 only, with `LLM_CACHE_MODE=record`. Paste the
extracted requirements. They should be recognisable as decisions a person made.

**Commit:** `E1.S2: Step 2 — requirement and slot extraction, per-outcome fan-out`

---

### S3 — Slot lifecycle and the abandonment sweep

Slot ages live in `run/pipeline_state.json`, per SPEC_QUESTIONS Q3. Do not put them in
`state.json`.

- A slot's age resets on any activity referencing it.
- After three pairs with no activity, it transitions to `abandoned` automatically.
- A `resolved` slot links to the requirement it became.
- `inv_09` must pass on every chat processed.

**Verify:** a synthetic four-pair fixture where a slot opens at pair 1 and is never
mentioned again. It must be `abandoned` by pair 4 and not before.

**Commit:** `E1.S3: slot lifecycle — age tracking and 3-pair abandonment sweep`

---

### S4 — Step 3, Trigger A

The whole-dialogue scan for newly created requirements.

- Prompt verbatim from spec §7.
- For each new requirement, scan all preceding actions in the dialogue, minus the
  exclusions the spec names.
- Each scored action becomes a ledger row with `kind: "labeled"`.
- `NO CONNECTION` produces **no row**. Never a zero-score row.
- Every row must carry `outcome_id`, `req_id`, `action_id`, `speaker`, `role`,
  `pair_added`, `score`, `kind`.

**Verify:** run on `golden_01`. Pick three requirements and trace each row back to the
action and the verbatim quote. Paste one full trace.

**Commit:** `E1.S4: Step 3 Trigger A — whole-dialogue influence scan for new requirements`

---

### S5 — Step 3, Trigger B, and batching

- Track, per requirement, which `action_id`s have already been labelled. Store in
  `run/pipeline_state.json`.
- On re-analysis send **only new subsequent actions.** Never re-score what was scored.
- Batch requirements `STEP3_BATCH_SIZE` at a time, default 3, from config.

**Verify:** process a chat twice in replay mode. The second run must add zero duplicate
rows. `inv_05` and `inv_17` green.

**Commit:** `E1.S5: Step 3 Trigger B — incremental scoring with batching`

---

### S6 — `engine/checks.py`, invariants in production

Promote the invariants from test-time to runtime.

- `engine/checks.py` imports the same functions from `tests/invariants.py`. One
  implementation, two callers. Do not copy them.
- After every pair completes, run every applicable invariant.
- On violation: write it to `run/status.json`, mark the pair unhealthy, **stop the run.**
  Do not continue and accumulate a corrupt ledger.
- Emit `run/report.json` per TEST_STRATEGY §6: timings, tokens, retries, cache hits,
  counts, check results.

**Verify:** inject a deliberate violation, confirm the run stops and `status.json` names
the invariant.

**Commit:** `E1.S6: runtime invariant checks + run report — §11.4 promoted to production`

---

### S7 — Golden chat run and grading

Run the full 1a→1b→1c→2→3 pipeline on `golden_01` in record mode. Then run
`grade_golden.py` and **stop for the owner to judge the table.**

Paste into the BUILDLOG: the grading table, the counts, the wall time and token totals.

**This is the phase's real gate.** If match rate is below 80% or spurious above 20%, do
not proceed. Log what kind of error dominates: missed requirements, invented ones,
fragmentation, or collapsing. Each points at a different fix and none of them is
"adjust the prompt", which is out of scope.

**Commit:** `E1.S7: golden chat extraction run — grading table recorded`

---

### S8 — Corpus run

Run the ten classified chats, record mode, cassettes committed.

Skip anything graded `unusable`. They are for E3 robustness, not extraction quality.

Then run invariants 1 to 9 on every result and paste the summary.

**Two things to watch and report**, both from TEST_STRATEGY §5:
- wall time per pair against pair index
- tokens per pair against pair index

If either curve bends upward, the accumulate windows grow without bound and long chats
will eventually be unaffordable. Report the shape either way. This is the first real data
anyone will have on it.

**Also required, closing Q7:** pick the most multi-topic chat in the ten, paste the root
outcome Step 1b invented for it, and say plainly whether it is an honest description of
what the person was doing or a fiction created to satisfy `inv_06`.

**Commit:** `E1.S8: corpus extraction run — 10 chats, invariants 1-9, timing curves`

---

### S9 — Phase close

Full ritual, Build Playbook §3:

1. DoD run for real via `scripts/phase_report.py`. Paste the output.
2. BUILDLOG entry, template, with pasted output not prose.
3. Commit, tag `e1-done`.
4. `AGENTS.md` current phase to E2 with its DoD.
5. Self-review: *"Re-read this brief top to bottom. List anything specified that was not
   delivered, or delivered differently. If the list is non-empty, we are not done."*
   Only an empty list closes the phase.

Point 5 failed silently in E0. Treat it as a real check this time.

---

## 6. Definition of Done

Verified by running, not by reading:

- [ ] `pytest` green, all tiers that apply
- [ ] Golden chat: **match rate ≥ 80%, spurious rate ≤ 20%**, owner-judged, numbers in BUILDLOG
- [ ] Ten corpus chats processed end to end, none `unusable`
- [ ] Invariants 1 to 9 green on every processed chat
- [ ] `inv_05` and `inv_17` green after a double run, proving no duplicate rows
- [ ] Every ledger row traces to an action and a verbatim quote, `inv_21` green
- [ ] `engine/checks.py` runs in the pipeline and halts on violation, demonstrated
- [ ] `run/report.json` produced for every run
- [ ] Cassettes committed, tier0 tests replay without network
- [ ] Timing and token curves recorded
- [ ] Q7 answered with evidence from a real multi-topic chat
- [ ] `data/chats/fixture_pair1/` untouched

---

## 7. Cost control

Step 3 is the cost centre of the whole pipeline. It fans out over requirements and scans
actions, so cost grows faster than conversation length.

- **Record once, replay forever.** Every corpus run in `record` mode. Every test in
  `replay`. A test that hits the live API is a bug.
- **Golden chat first**, 3 pairs. Do not run the ten-chat corpus until the golden chat
  grades acceptably. A prompt problem found at 3 pairs costs nothing; found at 909 it
  costs a day and a budget.
- **`MODEL_FAST` for Step 1a only.** Steps 2 and 3 use `MODEL_MAIN` or their overrides.
  Never downgrade a scoring call to save money.
- Report actual token totals per chat in S8. Nobody currently knows what this costs.

---

## 8. Edge cases that must be handled, not discovered

From the corpus, measured:

| Case | Where it occurs | Expected behaviour |
|---|---|---|
| Empty AI turn | 6 turns across c11, c12, c19, c32, c33 | Zero AI actions, zero requirements, quiet pair. No crash, no invented actions. |
| Pure-execution pair | Common | Zero requirement ops. `execution only` is a valid outcome, not a failure. |
| Tool narration in AI text | 69 turns | Whatever Step 1a does with it, report it. This closes Q6. |
| Very long single message | Several chats | Must not silently truncate. A clean hard error is acceptable. |
| Multi-topic drift | See S8 | Closes Q7. |
| Re-run of a processed pair | S5 | Idempotent. Wipe that pair's rows, re-add, identical result. |
| Requirement influenced many pairs later | Trigger B | Row added at the later pair, `pair_added` reflects when it was added. |

---

## 9. What E1 does not answer

So nobody is surprised at the gate:

- No percentages, no direction split, no decision counts, no mode. All Stage 4, all E2.
- No `analysis.json`. Its schema is not designed yet.
- No panel, no server, no live mode.
- No calibration of anything. E5.

E1 produces `state.json` and `ledger.jsonl` for real conversations, and the confidence
that both are right. That is all, and it is enough.

---

## 10. Kickoff prompt

Fresh Claude Code session, paste verbatim:

```
Read AGENTS.md fully first — its workflow gates apply to this session (one step per
response, a preamble before each step, wait for my "start task" and "Finish Step").
Then read docs/briefs/E1_BRIEF.md in full, the pipeline spec sections it names
(§6, §7, §9, §10.3, §11.4), engine/pipeline.py in full, and the last two BUILDLOG entries.

You are doing E1 pre-work P1–P4 and then E1.S1 through E1.S9. Nothing else.

Hard rules: prompts are copied verbatim from COTRACE_PIPELINE_SPEC, never paraphrased or
improved. Do not touch Stage 4, web/, server/, the five schemas, or
data/chats/fixture_pair1/. req_id is unique within an outcome, not globally — key every
lookup on (outcome_id, req_id). Every corpus run in LLM_CACHE_MODE=record; every test in
replay. If the spec contradicts itself, stop and log it in SPEC_QUESTIONS.md, take the
most conservative reading, mark it REVISIT — and never improvise anything that touches a
score.

The golden chat gate is owner-judged. At S7 you stop and I grade the table.

Begin with your preamble for P1.
```
