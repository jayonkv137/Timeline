# PHASE 5 BRIEF — The Pending Science & Hardening
**Tool: Claude Code · Opus. This phase produces DECISIONS-AS-REPORTS; where the command
center would normally rule, the rules are encoded below.**

## Goal
Close the honesty-ledger items the build was allowed to defer: HOW threshold
calibration, the §12.5 widened-hedge re-run, the Step-2a prefilter, and a cost report.

## Read first
COTRACE_PIPELINE_SPEC §10.5 (thresholds + the calibration plan), §12.5, §9.5 ·
STAGE4 worked-proof numbers · the two ground-truth trajectories below.

## Steps
**S1 — Produce the calibration ledgers.** Owner places the Budget-chat and
Portfolio-chat exports in `data/exports/`. Run the engine on both, full length.
**S2 — Calibration harness.** `engine/scripts/calibrate_how.py`: computes per-pair mode
from each ledger and compares against ground truth (encode verbatim):
- Budget chat: E1–E6 Centaur · E7 Cyborg · E8 Centaur.
- Portfolio chat: early exchanges Centaur · E21 Cyborg · E25 Centaur.
**Adjustment rules (this replaces command-center judgment):** thresholds may change
ONLY via the named config constants (quiet-pair Δ floor; the w/h comparison operators
or ratio margins); make the MINIMAL change that reproduces BOTH trajectories; every
change logged before/after in `CALIBRATION.md` with the failing pairs shown. If no
single setting reproduces both, DO NOT force it: keep the spec's proposed thresholds,
document the irreducible mismatches in CALIBRATION.md as known limitations, and mark
the HOW section's mode line as "beta" in the UI copy.
**S3 — §12.5 widened-hedge re-run.** Re-run the engine (Step 2 stage) on the Style-DNA
export with the v5 prompt; write `HEDGE_RERUN.md`: which requirements became slots
(expected candidates: o5's deferred-commitment pair, possibly o4), what pair-1's
direction/decisions become on the new set. **The frozen fixture is NOT touched** —
output goes to `data/chats/style_dna_v5/`; the fixture remains the historical ground
truth for regression.
**S4 — Step-2a prefilter (spec §9.5).** Implement behind `PREFILTER=on|off` (default
off): turn-level embeddings (text-embedding-3-small via env-keyed OpenAI client, or
skip with a SPEC_QUESTIONS entry if no key), τ=0.5, intention-group filter,
adjacent-turn floor, contributing-turn force-include. A/B one chat: token cost + label
coverage with vs. without → `PREFILTER_REPORT.md`. Turn default on only if coverage
loss is zero on DIRECT/creation-adjacent labels.
**S5 — Cost report + close-out.** From llm_monitor across all runs: tokens and cost per
step per pair → `COST_REPORT.md`. Update AGENTS.md phase line to "BUILD COMPLETE —
maintenance mode." Final BUILDLOG entry summarizing the whole build (phases, dates,
open REVISIT items from SPEC_QUESTIONS.md).

## Definition of Done
CALIBRATION.md (both trajectories reproduced, or documented limitation + beta label) ·
HEDGE_RERUN.md · PREFILTER_REPORT.md · COST_REPORT.md · all test suites green ·
close-out entry written.

## Kickoff prompt addendum
```
S2's adjustment rules are the law of this phase: minimal named-constant changes only,
everything logged, and an honest failure is a valid outcome — a forced fit is not.
The fixture folder is frozen; nothing in this phase writes into it.
```
