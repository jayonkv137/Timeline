# Sample Data for Design Reference

Three complete chat exports — Steps 1 through 4, everything in one file per chat.

## Files

| File | Chat Type | Pairs | Size |
|------|-----------|-------|------|
| `c16_research_short.json` | Research (1 pair) | 1 | 20 KB |
| `c04_writing_short.json` | Writing (4 pairs) | 4 | 108 KB |
| `c05_research_medium.json` | Research (7 pairs) | 7 | 216 KB |

## What's Inside Each File

Every file is a single JSON object with this structure:

```
{
  "chat_id":              "c05_research_medium",
  "dialogue_summary":     "One-line plain-English summary of entire chat",
  "total_pairs":          7,
  "total_ledger_rows":    402,

  ── STEP 1: GOALS & INTENTIONS ──────────────────────────────
  "step_1_outcomes":      [ { id, text, parent, children, turn_id } ... ],
  "step_1_intentions":    [ { intention_id, intention, outcome_ids } ... ],

  ── STEP 2: REQUIREMENTS & SLOTS ─────────────────────────────
  "step_2_requirements":  [ { outcome_id, req_id, text, type, status,
                              creation_action_ids, implementation_action_ids,
                              rationale, created_at_pair } ... ],
  "step_2_slots":         [ { slot_id, outcome_id, text, origin, status,
                              creation_action_ids, resolved_into } ... ],

  ── STEP 3: ACTIONS & OPERATIONS LOG ─────────────────────────
  "step_3_all_actions":   [ { id, type, text, role, evidence_quote } ... ],
  "step_3_operations_log":[ { pair, outcome_id, op, target_id, target_type } ... ],

  ── STEP 4: PER-PAIR ANALYSIS ────────────────────────────────
  "step_4_mode_split":    { "COPILOT": 100.0 },
  "step_4_pairs": [
    {
      "pair":                    1,
      "user_actions":            [ ... actions starting with U(1,*) ],
      "ai_actions":              [ ... actions starting with A(1,*) ],
      "requirements_created":    [ ... reqs where created_at_pair == 1 ],
      "slots_created":           [ ... slots created by actions in this pair ],
      "operations":              [ ... ops log entries for this pair ],
      "ledger_rows":             [ ... all ledger rows for pair_added == 1 ],
      "influence": {
        "user_score":  27.0,
        "ai_score":    35.0,
        "total":       62.0,
        "user_pct":    43.5,
        "ai_pct":      56.5
      },
      "mode": {
        "classification": "COPILOT",
        "signals": {
          "w_you": 3,             ← reqs created by user
          "w_ai": 0,              ← reqs created by AI
          "h_you": 12.0,          ← user non-creation influence mass
          "h_ai": 35.0,           ← AI non-creation influence mass
          "substantive_user": true
        }
      },
      "cumulative_direction": {
        "user_pct": 43.5,        ← running total up to this pair
        "ai_pct":   56.5
      }
    },
    ... more pairs ...
  ]
}
```

## Quick Reference: What Each Section Answers

| Design Question | Look At |
|-----------------|---------|
| What is the overall goal of this chat? | `step_1_outcomes[0].text` (root, parent == null) |
| What sub-goals exist? | `step_1_outcomes` where parent != null |
| What did the user ask for in pair N? | `step_4_pairs[N-1].user_actions[].text` |
| What did the AI deliver in pair N? | `step_4_pairs[N-1].ai_actions[].text` |
| What decisions were locked in pair N? | `step_4_pairs[N-1].requirements_created[].text` |
| What open questions were raised? | `step_4_pairs[N-1].slots_created[].text` |
| Who was steering in pair N? | `step_4_pairs[N-1].influence.user_pct / ai_pct` |
| What mode was pair N? | `step_4_pairs[N-1].mode.classification` |
| Running direction over time? | `step_4_pairs[*].cumulative_direction` |
| Overall mode distribution? | `step_4_mode_split` |
