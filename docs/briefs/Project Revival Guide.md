# E2_BRIEF.md — Stage 4, the Numbers

**Phase:** E2
**Role:** ENGINE
**Tool:** Claude Code, Opus. Wrong-number-is-worse-than-slow.
**Depends on:** E1 closed (tag `e1-done`)
**Gate before E3:** Definition of Done, section 6

---

## 1. What this phase is

After E1 the engine knows everything: every action, decision and influence is in
`state.json` and `ledger.jsonl`. It cannot yet say anything a person would read.

Stage 4 turns that evidence into answers. Who steered, who decided, how they were working,
pair by pair.

It is **pure arithmetic.** No LLM, no network, no prompts, no randomness. That makes it the
fastest phase to build and the only one that can be proven exactly right, because the
fixture holds hand-verified answers for every number.

**The payoff at the end of this phase:** the first real numbers this engine has ever
produced from real conversations. The ten E1 corpus chats already have ledgers and
cassettes, so running Stage 4 on them costs nothing.

---

## 2. Scope

**Build**
- `engine/quant.py`: ledger + state → facts, per pair and cumulative
- `engine/projections/panel.py`: facts → `panel_bundle.json`
- Writers for `snapshots.json` and `panel_bundle.json`, schema-validated
- Stage 4 wired into the pipeline after Step 3
- Invariants 10 to 16 and 19 switched on
- Tests, tier1 only

**Do not build**
- `analysis.json`. Not designed yet. Designed with the owner after this phase.
- Anything in `web/` or `server/`
- Anything touching Steps 1a to 3
- Calibration of thresholds. That is Phase 5.

**Internal structure rule.** `quant.py` computes facts into plain Python data and knows
nothing about the panel. `projections/panel.py` shapes those facts into the bundle and does
no arithmetic of its own. One direction only: projections import quant, never the reverse.
This is what makes `analysis.json` a small addition later.

---

## 3. Source of truth, and the order it wins in

1. **`data/fixtures/Stage 4 Pair 1 Results.md`**: the hand-verified canonical numbers. It
   records that four hand-sum errors in the original source were corrected, and that its
   numbers supersede the source. When anything disagrees with it, the code is wrong.
2. **`docs/Cotrace Pipeline Spec.md` §10**: the formulas. Implement from the spec text, never
   from anyone's summary of it, including the briefs.
3. **`docs/PANEL_SPEC.md` §1 to §6**: what the bundle must contain, including the
   thread-collapse depth cases and the R-SUM template.
4. **`engine/schemas/snapshots.schema.json`, `panel_bundle.schema.json`**: the frozen shape.

### A known trap, read before S3

The mode rule has been summarised in project documents as: centaur if you lead on both `w`
and `h`, copilot if you lead on either, autopilot otherwise.

**That summary gives the wrong answer on the fixture.** The user leads on neither
(`w` 4 vs 10, `h` 47.0 vs 239.0), so it produces AUTOPILOT. The verified answer is
**COPILOT**, with `substantive_user = true`.

The real rule in §10.5 includes the `substantive_user` signal, and probably a QUIET case.
Mode has **never been computed by code before**: the Phase 0 test checks direction and
decisions but not mode. This is the first time.

Implement §10.5 literally. If the literal text cannot reproduce COPILOT on the fixture,
**stop, do not adjust anything to make it pass**, log it in `SPEC_QUESTIONS.md`, and report.

---

## 4. Pre-work, three small items

**P1. Fix the tier counter in `scripts/phase_report.py`.** It reports 82 tier0 and 82
tier1 out of 82 tests, while `pytest -m tier1` shows 81 plus 1 deselected. The report is
the project's trust instrument, so it must count correctly before it certifies another
phase.

**P2. Make quote matching honest in the report.** During E1, `inv_21` was widened from exact
matching to word-order matching with gaps of up to 15 words. Do not change it now. Instead,
have the checker record **how** each quote matched: exact, whitespace-normalised, segmented,
or fuzzy. Add those four counts to `run/report.json` and the phase report, and log the
widening as a `SPEC_QUESTIONS` entry with status REVISIT. The owner decides the policy
later with the numbers in front of him.

**P3. Reopen Q7.** It was closed on ten chats of at most seven pairs, none genuinely
multi-topic. Set it back to OPEN with a one-line reason. It is tested properly in E3.

---

## 5. Steps

Each step ends green with the owner's checklist. Pure maths throughout, so every
verification is exact.

### S1 — Direction

`quant.py` reads the ledger and computes, per pair `t`: `delta_you`, `delta_ai`, cumulative
`c_you`, `c_ai`, and the direction percentages.

**Verify on the fixture:** ΣU = **87.0**, ΣA = **314.0**, You **21.7%** / AI **78.3%**.
Exact. Also rounding: decide and document where rounding happens (once, at the end, never
on intermediate values) and write it down in the module docstring.

### S2 — Decisions

Per requirement, keyed on **`(outcome_id, req_id)`**, never `req_id` alone:
- creator, from the earliest creation action, ordered by pair, then U before A, then sequence
- `mass_you`, `mass_ai`
- chip: blue when AI mass is zero, orange when user mass is zero, grey otherwise
- counter: decisions by creator

**Verify:** **4 you · 10 AI** over **14** distinct requirements. And every per-requirement
mass matches the corrected table in `Stage 4 Pair 1 Results.md`, including the one it
flags as corrected (o1/r3: 37.0, not 42).

### S3 — Mode

Implement §10.5 literally: `w_you`, `w_ai`, `h_you`, `h_ai` (sum of SHAPER scores only),
`substantive_user`, the QUIET case, and the classification. Plus the running distribution
of modes across pairs.

**Verify:** **COPILOT**, `w` 4/10, `h` 47.0/239.0, `substantive_user` true.

Read section 3's trap first. If §10.5 cannot reproduce COPILOT literally, stop.

### S4 — Timeline

Per pair: the drawer rows (requirement ops at that pair with their deltas and chip), the
slot rows, and the summary line from the R-SUM template in PANEL_SPEC §4.5. Deterministic
template only, never generated text.

**Verify:** fixture pair 1 drawer has 14 requirement rows and 5 slot rows. Summary line
matches the template output for the highest-delta op.

### S5 — Goal view

The goal tree as `full_tree` and the thread-collapse `default_view` per PANEL_SPEC §1,
handling depth cases d=0, d=1, d=2 and d≥3 separately. The "N more" chip appears only at
depth 3 or more. Never "0 more".

**Verify:** a tier1 test for each depth case with a small synthetic tree, plus the fixture's
tree, which is depth 1.

### S6 — Writers and fixture equivalence

`projections/panel.py` builds the bundle, and both files are written through the existing
validate-then-write path in `artifacts.py`.

**Verify:** the generated `panel_bundle.json` and `snapshots.json` for the fixture are
**value-equal** to the frozen ones. Compare parsed JSON with floats rounded to the stated
precision and keys order-independent, not raw bytes, because the frozen files were built by
hand. Report every field that differs. Zero differences is the target. Any difference is
either a code bug or an error in the frozen file, and the second possibility gets logged,
never silently fixed.

The frozen fixture is read-only. Output goes to a scratch location.

### S7 — Into the pipeline

Stage 4 runs after Step 3 for every pair. Invariants 10 to 16 and 19 now receive the data
they were waiting for and must pass. `engine/checks.py` includes them in the runtime checks.

**Verify:** `pytest` green. Re-running Stage 4 twice on the same ledger gives identical
output (invariant 19).

### S8 — First real numbers

Run Stage 4 over the ten E1 corpus ledgers. **Replay mode only: the ledgers exist, so this
needs no LLM calls at all.**

**Deliver a table:**

| chat | pairs | you % | AI % | decisions you/AI | mode per pair | quote match exact/fuzzy |
|---|---|---|---|---|---|---|

Report it plainly, without interpretation. This is the first time the engine has produced
numbers from a real conversation, and the owner reads them himself.

Also report any chat where a number looks structurally odd: zero requirements, 100/0
splits, every pair QUIET. Odd is worth flagging, not fixing.

### S9 — Close

Generated phase report, BUILDLOG entry, commit, tag `e2-done`, AGENTS.md phase line, and the
self-review against this brief. Only an empty self-review list closes the phase.

---

## 6. Definition of Done

- [ ] Fixture: ΣU 87.0, ΣA 314.0, 21.7 / 78.3, exact
- [ ] Fixture: 4 you · 10 AI over 14 requirements, per-requirement masses match the corrected table
- [ ] Fixture: COPILOT from §10.5 literally, `w` 4/10, `h` 47.0/239.0
- [ ] Generated fixture bundle and snapshots value-equal to the frozen ones, or every difference logged
- [ ] All four goal-view depth cases tested
- [ ] Invariants 10 to 16 and 19 pass on the fixture and on all ten corpus chats
- [ ] Stage 4 runs in the pipeline after Step 3, checks included
- [ ] S8 table delivered for ten chats, zero LLM calls
- [ ] Phase report tier counts correct
- [ ] Quote-match breakdown reported
- [ ] Q7 reopened, inv_21 widening logged
- [ ] `data/chats/fixture_pair1/` untouched
- [ ] `pytest` green, all new tests tier1

---

## 7. Size

Small. Roughly 400 to 700 lines of Python across two modules plus tests. No external calls.
The difficulty is not volume, it is getting every rule exactly as the spec states it.
