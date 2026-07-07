#!/usr/bin/env python3
"""
build_fixture.py — Phase 0, Step 3

Reads:
  data/fixtures/ledger_pair1.json    (markdown table with 157 ledger rows)
  data/fixtures/Stage 4 Pair 1 Results.md  (verified canonical values)

Writes to data/chats/fixture_pair1/:
  ledger.jsonl       — 157 rows, field names per ledger_row.schema.json
  snapshots.json     — one entry: t=1
  panel_bundle.json  — pair 1, all Panel Spec §6 values
  state.json         — STUB: real ids/creators, placeholder texts
  dialogue.json      — STUB: schema-valid, placeholder text
  README.md          — what's verified vs. reconstructed

IMPORTANT PARSING NOTES:
  - The markdown table has action_ids split across two lines:
    "U(1,\n1)" must be rejoined to "U(1,1)".
  - Within the same pair, U actions precede A actions in conversation order
    (user speaks first). This affects the "earliest creation action" rule
    for determining requirement creators.
  - The source chat's inline math contains errors (e.g., o1/r3 M(AI)=42,
    correct=37.0). The Stage 4 Results file documents all corrections.
    The raw ledger rows themselves are correct — the errors were only in
    the source's hand-computed sums.

Canonical numbers (AGENTS.md rule 5 — sacred):
  Δ_you=87.0, Δ_AI=314.0 → You 21.7% / AI 78.3%
  Decisions: 4 you · 10 AI
  HOW: COPILOT (w 4/10, h 47.0/239.0, substantive_user=true)
"""

import json
import os
import re
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# 0. Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "data" / "fixtures"
OUTPUT_DIR = REPO_ROOT / "data" / "chats" / "fixture_pair1"

LEDGER_INPUT = FIXTURES_DIR / "ledger_pair1.json"
STAGE4_INPUT = FIXTURES_DIR / "Stage 4 Pair 1 Results.md"


# ---------------------------------------------------------------------------
# 1. Parse the 157 ledger rows from the markdown table
# ---------------------------------------------------------------------------
def parse_ledger_table(filepath):
    """
    Parse Part 1 of ledger_pair1.json (a markdown table, not actual JSON).
    
    Challenge: action_ids are split across two lines due to copy-paste artifacts.
    e.g., "U(1,\\n1)" needs to become "U(1,1)".
    
    Strategy: read all lines between the table header and the first "---",
    collapse newlines, then regex-extract each row.
    """
    with open(filepath, "r") as f:
        content = f.read()

    # Extract Part 1 only — between header row and first "---" separator
    part1_match = re.search(
        r'\| pair_added \| action_id.*?\n\|[-|]+\|\n(.*?)(?=\n---)',
        content, re.DOTALL
    )
    if not part1_match:
        raise ValueError("Could not locate Part 1 table in ledger file")

    table_body = part1_match.group(1)

    # Collapse newlines to fix broken action_ids (U(1,\n1) → U(1, 1))
    joined = table_body.replace('\n', ' ')

    # Extract all rows with regex
    row_pattern = re.compile(
        r'\|\s*(\d+)\s*\|'           # pair_added
        r'\s*([^|]+?)\s*\|'          # action_id (may have spaces from line break)
        r'\s*([UA])\s*\|'            # speaker
        r'\s*(\w+)\s*\|'             # role
        r'\s*(outcome \d+)\s*\|'     # outcome_id
        r'\s*(req \d+)\s*\|'         # req_id
        r'\s*([\d.]+)\s*\|'          # score
        r'\s*(\w[\w-]*)\s*\|'        # kind
    )

    raw_rows = row_pattern.findall(joined)

    # Convert to schema-conformant dicts
    rows = []
    for pair, action_id, speaker, role, outcome_id, req_id, score, kind in raw_rows:
        # Clean up action_id: remove internal spaces from line-break artifacts
        # "U(1, 1)" → "U(1,1)"
        action_id = re.sub(r'\(\s*(\d+)\s*,\s*(\d+)\s*\)', r'(\1,\2)', action_id.strip())

        rows.append({
            "pair_added": int(pair),
            "action_id": action_id,
            "speaker": speaker.strip(),
            "role": role.strip(),
            "outcome_id": outcome_id.strip(),
            "req_id": req_id.strip(),
            "score": float(score),
            "kind": kind.strip(),
        })

    return rows


# ---------------------------------------------------------------------------
# 2. Derive values from the parsed ledger (for verification and state.json)
# ---------------------------------------------------------------------------
def derive_from_ledger(rows):
    """Compute all derived values from the 157 ledger rows."""

    info = {}

    # Per-requirement aggregation
    req_data = defaultdict(lambda: {
        "creation_action_ids": [],
        "labeled_action_ids": [],
        "m_you": 0.0,
        "m_ai": 0.0,
    })

    for row in rows:
        key = (row["outcome_id"], row["req_id"])
        if row["kind"] == "creation":
            req_data[key]["creation_action_ids"].append(
                (row["action_id"], row["speaker"])
            )
        req_data[key][f"m_{'you' if row['speaker'] == 'U' else 'ai'}"] += row["score"]

    # Delta sums
    delta_you = sum(r["score"] for r in rows if r["speaker"] == "U")
    delta_ai = sum(r["score"] for r in rows if r["speaker"] == "A")
    info["delta_you"] = delta_you
    info["delta_ai"] = delta_ai

    # Creator determination — within same pair, U actions precede A actions
    def action_sort_key(aid_speaker):
        aid, speaker = aid_speaker
        m = re.match(r'([UA])\((\d+),(\d+)\)', aid)
        if m:
            prefix = m.group(1)
            pair_num = int(m.group(2))
            seq = int(m.group(3))
            speaker_order = 0 if prefix == 'U' else 1
            return (pair_num, speaker_order, seq)
        return (999, 999, 999)

    creators = {}
    for key in req_data:
        sorted_creators = sorted(
            req_data[key]["creation_action_ids"],
            key=action_sort_key
        )
        creators[key] = sorted_creators[0][1] if sorted_creators else "?"

    info["creators"] = creators
    info["req_data"] = dict(req_data)
    info["you_count"] = sum(1 for c in creators.values() if c == "U")
    info["ai_count"] = sum(1 for c in creators.values() if c == "A")

    return info


# ---------------------------------------------------------------------------
# 3. Build per-requirement drawer rows (for panel_bundle timeline)
# ---------------------------------------------------------------------------
def build_drawer_rows(rows, creators):
    """Build the 14 drawer requirement rows for pair 1's timeline."""
    req_deltas = defaultdict(lambda: {"delta_you": 0.0, "delta_ai": 0.0})

    for row in rows:
        key = (row["outcome_id"], row["req_id"])
        if row["speaker"] == "U":
            req_deltas[key]["delta_you"] += row["score"]
        else:
            req_deltas[key]["delta_ai"] += row["score"]

    drawer_rows = []
    # Assign R-labels in creation order (sorted by outcome_id, req_id)
    label_counter = 0
    for key in sorted(req_deltas.keys()):
        label_counter += 1
        outcome_id, req_id = key
        d = req_deltas[key]

        # Chip color: blue if M(AI,r)=0, orange if M(you,r)=0, grey otherwise
        if d["delta_ai"] == 0:
            chip = "blue"
        elif d["delta_you"] == 0:
            chip = "orange"
        else:
            chip = "grey"

        drawer_rows.append({
            "outcome_id": outcome_id,
            "req_id": req_id,
            "label": f"R{label_counter}",
            "op": "create",  # All 14 are created at pair 1
            "delta_you": d["delta_you"],
            "delta_ai": d["delta_ai"],
            "chip": chip,
        })

    return drawer_rows


# ---------------------------------------------------------------------------
# 4. Write all output files
# ---------------------------------------------------------------------------
def write_fixture(rows, info, drawer_rows):
    """Write all 6 files to data/chats/fixture_pair1/."""

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- ledger.jsonl ---
    with open(OUTPUT_DIR / "ledger.jsonl", "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    # --- snapshots.json ---
    # One entry: t=1. For pair 1, cumulative = delta (only one pair).
    snapshots = [
        {
            "t": 1,
            "delta_you": info["delta_you"],
            "delta_ai": info["delta_ai"],
            "c_you": info["delta_you"],   # cumulative = delta for t=1
            "c_ai": info["delta_ai"],
        }
    ]
    with open(OUTPUT_DIR / "snapshots.json", "w") as f:
        json.dump(snapshots, f, indent=2)

    # --- panel_bundle.json ---
    # Uses ONLY verified values from Stage 4 Pair 1 Results.md
    # Direction: 21.7 / 78.3 (canonical, from 87.0 / 401.0 × 100)
    you_pct = round(info["delta_you"] / (info["delta_you"] + info["delta_ai"]) * 100, 1)
    ai_pct = round(info["delta_ai"] / (info["delta_you"] + info["delta_ai"]) * 100, 1)

    # Open slots — 5 open slots, all AI-origin (from Stage 4 Results)
    # Slot texts are reconstructed — we don't have the actual text from the fixture
    slots_data = [
        {"slot_id": "slot 1", "origin": "AI", "status": "open", "resolved_into": None},
        {"slot_id": "slot 1", "origin": "AI", "status": "open", "resolved_into": None},
        {"slot_id": "slot 2", "origin": "AI", "status": "open", "resolved_into": None},
        {"slot_id": "slot 1", "origin": "AI", "status": "open", "resolved_into": None},
        {"slot_id": "slot 2", "origin": "AI", "status": "open", "resolved_into": None},
    ]
    # NOTE: slot_ids above are per-outcome, matching the Stage 4 data:
    # outcome 1/slot 1, outcome 3/slot 1, outcome 3/slot 2,
    # outcome 5/slot 1, outcome 5/slot 2

    panel_bundle = {
        "pairs": [
            {
                "pair": 1,
                "direction": {
                    "you_pct": you_pct,
                    "ai_pct": ai_pct,
                },
                "decisions": {
                    "you_count": info["you_count"],
                    "ai_count": info["ai_count"],
                    "latest_ai_example": (
                        "Final production scene generations must use the Style "
                        "Anchor plus a texture crop plus a color swatch as "
                        "triple-references"
                    ),
                },
                "timeline": {
                    "pair": 1,
                    "delta_you": info["delta_you"],
                    "delta_ai": info["delta_ai"],
                    "summary": "adding Style DNA framework",
                    "drawer": {
                        "requirements": drawer_rows,
                        "slots": slots_data,
                    },
                },
                "goal": {
                    "default_view": [
                        {
                            "outcome_id": "outcome 1",
                            "text": "Style DNA & Production Bible",
                            "depth": 0,
                            "is_current": True,
                        }
                    ],
                    "full_tree": [
                        {
                            "outcome_id": "outcome 1",
                            "text": "Style DNA & Production Bible",
                            "depth": 0,
                            "parent": None,
                            "children": [
                                "outcome 2", "outcome 3", "outcome 4",
                                "outcome 5", "outcome 6",
                            ],
                        },
                        {
                            "outcome_id": "outcome 2",
                            "text": "(not captured in fixture)",
                            "depth": 1,
                            "parent": "outcome 1",
                            "children": [],
                        },
                        {
                            "outcome_id": "outcome 3",
                            "text": "(not captured in fixture)",
                            "depth": 1,
                            "parent": "outcome 1",
                            "children": [],
                        },
                        {
                            "outcome_id": "outcome 4",
                            "text": "(not captured in fixture)",
                            "depth": 1,
                            "parent": "outcome 1",
                            "children": [],
                        },
                        {
                            "outcome_id": "outcome 5",
                            "text": "(not captured in fixture)",
                            "depth": 1,
                            "parent": "outcome 1",
                            "children": [],
                        },
                        {
                            "outcome_id": "outcome 6",
                            "text": "(not captured in fixture)",
                            "depth": 1,
                            "parent": "outcome 1",
                            "children": [],
                        },
                    ],
                },
                "how": {
                    "mode": "COPILOT",
                    "signals": {
                        "w_you": info["you_count"],   # 4
                        "w_ai": info["ai_count"],     # 10
                        "h_you": 47.0,                # canonical
                        "h_ai": 239.0,                # canonical
                        "substantive_user": True,
                    },
                    "split": {
                        # Only one non-quiet pair, and it's COPILOT
                        "centaur_pct": 0.0,
                        "copilot_pct": 100.0,
                        "autopilot_pct": 0.0,
                    },
                },
            }
        ]
    }
    with open(OUTPUT_DIR / "panel_bundle.json", "w") as f:
        json.dump(panel_bundle, f, indent=2)

    # --- state.json (STUB) ---
    # Real: requirement ids, creation_action_ids, creators from the ledger.
    # Stub: action texts, evidence quotes, outcome descriptions, req texts.
    #
    # Build actions from all unique action_ids in the ledger
    unique_actions = {}
    for row in rows:
        aid = row["action_id"]
        if aid not in unique_actions:
            unique_actions[aid] = {
                "id": aid,
                "type": "(not captured in fixture)",
                "text": "(not captured in fixture)",
                "role": row["role"],
                "evidence_quote": "(not captured in fixture)",
            }

    # Build requirements from ledger data
    requirements = []
    req_keys = sorted(info["req_data"].keys())
    for outcome_id, req_id in req_keys:
        rd = info["req_data"][(outcome_id, req_id)]
        creation_aids = [a[0] for a in rd["creation_action_ids"]]
        requirements.append({
            "outcome_id": outcome_id,
            "req_id": req_id,
            "text": "(not captured in fixture)",
            "type": "other",  # placeholder — real type not in ledger
            "status": "active",
            "creation_action_ids": creation_aids,
            "contributing_action_ids": [],
            "implementation_action_ids": [],
            "revise_action_ids": [],
            "related_to": [],
            "explicit_or_implicit": "explicit",  # placeholder
            "rationale": "(not captured in fixture)",
            "created_at_pair": 1,
        })

    # Build slots — 5 open slots from Stage 4 Results
    slots = [
        {
            "slot_id": "slot 1", "outcome_id": "outcome 1",
            "text": "(not captured in fixture)", "type": "other",
            "origin": "AI", "status": "open",
            "creation_action_ids": [], "contributing_action_ids": [],
            "resolved_into": None,
        },
        {
            "slot_id": "slot 1", "outcome_id": "outcome 3",
            "text": "(not captured in fixture)", "type": "other",
            "origin": "AI", "status": "open",
            "creation_action_ids": [], "contributing_action_ids": [],
            "resolved_into": None,
        },
        {
            "slot_id": "slot 2", "outcome_id": "outcome 3",
            "text": "(not captured in fixture)", "type": "other",
            "origin": "AI", "status": "open",
            "creation_action_ids": [], "contributing_action_ids": [],
            "resolved_into": None,
        },
        {
            "slot_id": "slot 1", "outcome_id": "outcome 5",
            "text": "(not captured in fixture)", "type": "other",
            "origin": "AI", "status": "open",
            "creation_action_ids": [], "contributing_action_ids": [],
            "resolved_into": None,
        },
        {
            "slot_id": "slot 2", "outcome_id": "outcome 5",
            "text": "(not captured in fixture)", "type": "other",
            "origin": "AI", "status": "open",
            "creation_action_ids": [], "contributing_action_ids": [],
            "resolved_into": None,
        },
    ]

    # Build outcomes tree (stub — only ids and tree structure are real)
    # Root = outcome 1 "Style DNA & Production Bible" (from brief)
    # Outcomes 2–6 as children (flat structure, one level deep for fixture)
    outcomes = [
        {
            "id": "outcome 1",
            "text": "Style DNA & Production Bible",
            "turn_id": "U(1,1)",
            "parent": None,
            "children": ["outcome 2", "outcome 3", "outcome 4",
                         "outcome 5", "outcome 6"],
            "related": [],
        },
    ]
    for i in range(2, 7):
        outcomes.append({
            "id": f"outcome {i}",
            "text": "(not captured in fixture)",
            "turn_id": "(not captured in fixture)",
            "parent": "outcome 1",
            "children": [],
            "related": [],
        })

    # Build operations_log — all 14 requirement creates + 5 slot opens at pair 1
    operations_log = []
    for outcome_id, req_id in req_keys:
        operations_log.append({
            "pair": 1,
            "outcome_id": outcome_id,
            "op": "create",
            "target_id": req_id,
            "target_type": "requirement",
        })
    # Add slot open_slot operations
    slot_ops = [
        ("outcome 1", "slot 1"),
        ("outcome 3", "slot 1"),
        ("outcome 3", "slot 2"),
        ("outcome 5", "slot 1"),
        ("outcome 5", "slot 2"),
    ]
    for oid, sid in slot_ops:
        operations_log.append({
            "pair": 1,
            "outcome_id": oid,
            "op": "open_slot",
            "target_id": sid,
            "target_type": "slot",
        })

    state = {
        "actions": sorted(unique_actions.values(), key=lambda a: a["id"]),
        "outcomes": outcomes,
        "intentions": [
            {
                "intention_id": "I1",
                "intention": "(not captured in fixture)",
                "outcome_ids": [f"outcome {i}" for i in range(1, 7)],
            }
        ],
        "requirements": requirements,
        "slots": slots,
        "operations_log": operations_log,
    }
    with open(OUTPUT_DIR / "state.json", "w") as f:
        json.dump(state, f, indent=2)

    # --- dialogue.json (STUB) ---
    dialogue = [
        {
            "pair": 1,
            "speaker": "user",
            "text": "(not captured in fixture)",
            "attachments": [],
            "ts": "2025-01-01T00:00:00Z",
        },
        {
            "pair": 1,
            "speaker": "ai",
            "text": "(not captured in fixture)",
            "attachments": [],
            "ts": "2025-01-01T00:01:00Z",
        },
    ]
    with open(OUTPUT_DIR / "dialogue.json", "w") as f:
        json.dump(dialogue, f, indent=2)

    # --- README.md ---
    readme = """\
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
"""
    with open(OUTPUT_DIR / "README.md", "w") as f:
        f.write(readme)


# ---------------------------------------------------------------------------
# 5. Main — parse, derive, verify, write
# ---------------------------------------------------------------------------
def main():
    print("Parsing ledger table...")
    rows = parse_ledger_table(LEDGER_INPUT)
    print(f"  Parsed {len(rows)} rows")

    print("Deriving values...")
    info = derive_from_ledger(rows)
    print(f"  Δ_you = {info['delta_you']}")
    print(f"  Δ_AI  = {info['delta_ai']}")
    print(f"  Creators: {info['you_count']} U · {info['ai_count']} A")

    # Self-check against canonical numbers (AGENTS.md rule 5)
    assert len(rows) == 157, f"Expected 157 rows, got {len(rows)}"
    assert info["delta_you"] == 87.0, f"Δ_you={info['delta_you']}, expected 87.0"
    assert info["delta_ai"] == 314.0, f"Δ_ai={info['delta_ai']}, expected 314.0"
    assert info["you_count"] == 4, f"you_count={info['you_count']}, expected 4"
    assert info["ai_count"] == 10, f"ai_count={info['ai_count']}, expected 10"
    print("  ✓ All canonical numbers match")

    print("Building drawer rows...")
    drawer_rows = build_drawer_rows(rows, info["creators"])
    # Verify: 13 grey, 1 orange (o5/r2), 0 blue
    chip_counts = defaultdict(int)
    for dr in drawer_rows:
        chip_counts[dr["chip"]] += 1
    print(f"  Chips: {dict(chip_counts)}")
    assert chip_counts["grey"] == 13, f"Expected 13 grey, got {chip_counts['grey']}"
    assert chip_counts["orange"] == 1, f"Expected 1 orange, got {chip_counts['orange']}"

    print("Writing fixture files...")
    write_fixture(rows, info, drawer_rows)
    print(f"  Written to {OUTPUT_DIR}")

    # List output files
    for f in sorted(OUTPUT_DIR.iterdir()):
        size = f.stat().st_size
        print(f"    {f.name} ({size} bytes)")

    print("\nDone. Run pytest tests/test_phase0.py to validate.")


if __name__ == "__main__":
    main()
