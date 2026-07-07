# Stage 4 — Pair 1 Canonical Results (verified)
### Style-DNA chat, pair 1 · 14 requirements · 157 ledger rows · verified by independent recomputation

## Verification verdict
- Ledger integrity: CLEAN — zero creation/labeled overlap within any requirement, zero duplicate (action, requirement) rows.
- Creators, counters, creation masses, mode classification: all CONFIRMED as reported.
- Arithmetic: 4 hand-sum errors found in the source chat's output (all in AI columns);
  three it had already self-corrected in its own Part 3; one (o1/r3: reported 42, actual 37.0)
  survived into its totals. Canonical numbers below supersede.

## Canonical panel values @ P1
| Panel element | Value |
|---|---|
| DIRECTION | **You 21.7% · AI 78.3%**  (Δ_you = 87.0, Δ_AI = 314.0, total 401.0) |
| DECISIONS | **4 you · 10 AI** · latest AI: "Final production scene generations must use the Style Anchor plus a texture crop plus a color swatch as triple-references" |
| TIMELINE P1 delta | blue 87.0 / orange 314.0 |
| Drawer | 14 requirement rows (13 grey chips, 1 orange — o5/r2), 5 open slots (all AI-origin) |
| HOW | **COPILOT** (w_you=4, w_AI=10, h_you=47.0, h_AI=239.0, substantive_user=true) |

## Corrected per-requirement masses (differences from source marked)
| req | creator | M_you | M_AI | note |
|---|---|---|---|---|
| o1/r1 | U | 14.0 | 6 | |
| o1/r2 | U | 15.0 | 23.0 | mixed-creator (5 creation ids), earliest U(1,5) → U — tie-break exercised on real data |
| o1/r3 | A | 12 | **37.0** | source said 42 — arithmetic error |
| o1/r4 | A | 3 | 16.0 | |
| o2/r1 | U | 10.0 | 33 | |
| o3/r1 | A | 5 | **55.0** | source Part 2 said 68 (self-corrected) |
| o3/r2 | A | 5 | **33.0** | source Part 2 said 38 (self-corrected) |
| o4/r1 | A | 2 | **10.0** | source Part 2 said 12 (self-corrected) |
| o4/r2 | A | 3 | 26.0 | |
| o5/r1 | A | 1 | 18.0 | |
| o5/r2 | A | 0 | 10.0 | only full-right bar |
| o6/r1 | U | 12.0 | 14 | |
| o6/r2 | A | 3 | 18.0 | |
| o6/r3 | A | 2 | 15.0 | |

## Reading the 78% honestly (context for interpretation)
1. **10 of 14 requirements are AI-created** — but several are the AI's own Bible process
   steps (o4, o5, o6/r2-r3), the exact over-extraction pattern flagged at pipeline-spec
   §10.5. The widened deferred-commitment re-run was never performed; this number sits on
   the un-re-verified requirement set.
2. **Multi-requirement mass compounding:** one action can legitimately influence many
   requirements (paper design), and it compounds — A(1,32) earned 17.0 across 6
   requirements; file-inspection EXECUTOR actions A(1,9)–A(1,17) each earned mass on ~4.
3. **15 AI creation rows × 5.0 = 75 mass** from creation alone (vs. your 40) — multi-creation
   requirements weigh more by construction.
4. Pattern echo: research/intake-heavy single exchanges previously produced the highest AI
   shares in the cross-session runs (Timeline UI Inspirations: 78%). Pair 1 here is pure
   intake/framework-setting — the number is consistent with that established pattern, and
   should fall as creative pairs arrive (Malabar full-chat: 41% AI).

## Status
- HOW threshold calibration vs. Budget/Portfolio ground truths: still pending.
- §10.5 hedge-clause re-verification: still pending; would likely demote o5/r1-r2 (and
  possibly o4) to slots, reducing both the AI decision count and AI mass.
