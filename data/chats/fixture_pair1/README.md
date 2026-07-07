# Fixture: pair 1 of the Style-DNA chat

## What is verified (from the real pipeline extraction + independent recomputation)

- **ledger.jsonl** — all 157 rows: action_ids, speakers, roles, outcome_ids,
  req_ids, scores, kinds. Every field is from the verified extraction.
- **snapshots.json** — Δ_you=87.0, Δ_AI=314.0, cumulatives (= deltas for t=1).
  Independently recomputed and confirmed.
- **panel_bundle.json** — all panel values:
  - Direction: 21.7% / 78.3% (from 87.0 / 401.0)
  - Decisions: 4 you · 10 AI (creator = earliest creation action, U-before-A
    within same pair)
  - Timeline drawer: 14 requirement rows with per-req Δ(you,r) / Δ(AI,r),
    chip colors (13 grey, 1 orange — o5/r2), 5 open slots (all AI-origin)
  - HOW: COPILOT (w_you=4, w_ai=10, h_you=47.0, h_ai=239.0,
    substantive_user=true)
  - Goal: root "Style DNA & Production Bible" (from the chat)

## What is STUB / reconstructed (marked with "(not captured in fixture)")

- **dialogue.json** — placeholder turns. The actual chat text is not in the
  fixture data.
- **state.json**:
  - Action texts, types, and evidence quotes — not in the ledger data.
  - Outcome texts (except root "Style DNA & Production Bible") — not available.
  - Requirement texts — not in the ledger; only ids and creation_action_ids
    are real.
  - Slot texts and creation_action_ids — not available from ledger data.
  - Intention grouping — placeholder single-intention stub.
  - Requirement `type` field — set to "other" as placeholder; real types not
    in ledger.
  - Requirement `explicit_or_implicit` — set to "explicit" as placeholder.
- **panel_bundle.json**:
  - Goal section: outcome 2–6 texts are "(not captured in fixture)".
  - Timeline summary line: reconstructed ("adding Style DNA framework").
  - R-labels (R1–R14): assigned in outcome/req sort order — stable but not
    from the extraction.

## Corrections applied (from Stage 4 Pair 1 Results.md)

The source chat's inline math contained 4 arithmetic errors (all in AI columns):
- o1/r3: reported M(AI)=42, actual=37.0 (the raw ledger rows were correct;
  only the hand-sum was wrong)
- o3/r1: reported M(AI)=68, actual=55.0 (self-corrected in source Part 3)
- o3/r2: reported M(AI)=38, actual=33.0 (self-corrected in source Part 3)
- o4/r1: reported M(AI)=12, actual=10.0 (self-corrected in source Part 3)

All canonical numbers come from the independently verified Stage 4 Results,
not from the source chat's inline calculations.

## How to re-verify

```
python engine/scripts/build_fixture.py    # regenerate
pytest tests/test_phase0.py               # validate schemas + canonical numbers
```
