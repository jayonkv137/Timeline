"""Phase 0 DoD: fixture schema validity + canonical-numbers recomputation.

Per docs/Phase 0 Brief.md Step 4 and AGENTS.md rule 5 (canonical fixture numbers
are sacred). data/chats/fixture_pair1/ is FROZEN — this file only reads it.
"""
import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = REPO_ROOT / "engine" / "schemas"
FIXTURE_DIR = REPO_ROOT / "data" / "chats" / "fixture_pair1"

ACTION_ID_RE = re.compile(r"^[UA]\(\d+,\d+\)$")


def load_json(path):
    with open(path) as f:
        return json.load(f)


def load_schema(name):
    return load_json(SCHEMAS_DIR / name)


def load_ledger_rows():
    with open(FIXTURE_DIR / "ledger.jsonl") as f:
        return [json.loads(line) for line in f if line.strip()]


def action_sort_key(action_id):
    """Chronological order within a pair: every U action precedes every A
    action (one pair = one full user turn, then one full AI turn), per the
    'earliest creation action, U-before-A within same pair' rule documented
    in data/chats/fixture_pair1/README.md and PIPELINE_SPEC §10.5.
    """
    m = ACTION_ID_RE.match(action_id)
    assert m, f"malformed action id: {action_id}"
    speaker = action_id[0]
    pair_str, seq_str = action_id[2:-1].split(",")
    return (int(pair_str), 0 if speaker == "U" else 1, int(seq_str))


# ---------------------------------------------------------------------------
# (a) schema validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "artifact_file,schema_file",
    [
        ("dialogue.json", "dialogue.schema.json"),
        ("state.json", "state.schema.json"),
        ("snapshots.json", "snapshots.schema.json"),
        ("panel_bundle.json", "panel_bundle.schema.json"),
    ],
)
def test_fixture_artifact_validates_against_schema(artifact_file, schema_file):
    instance = load_json(FIXTURE_DIR / artifact_file)
    schema = load_schema(schema_file)
    Draft202012Validator(schema).validate(instance)


def test_ledger_rows_validate_against_schema():
    schema = load_schema("ledger_row.schema.json")
    validator = Draft202012Validator(schema)
    rows = load_ledger_rows()
    assert len(rows) > 0
    for row in rows:
        validator.validate(row)


# ---------------------------------------------------------------------------
# (b) canonical-numbers recomputation (PIPELINE_SPEC §11.4 as executable checks)
# ---------------------------------------------------------------------------

def test_sum_of_u_scores_is_87():
    rows = load_ledger_rows()
    total = sum(r["score"] for r in rows if r["speaker"] == "U")
    assert total == 87.0


def test_sum_of_a_scores_is_314():
    rows = load_ledger_rows()
    total = sum(r["score"] for r in rows if r["speaker"] == "A")
    assert total == 314.0


def test_fourteen_distinct_requirements():
    rows = load_ledger_rows()
    distinct = {(r["outcome_id"], r["req_id"]) for r in rows}
    assert len(distinct) == 14


def test_creator_split_is_4_user_10_ai_by_earliest_creation_action():
    rows = load_ledger_rows()
    by_req = {}
    for r in rows:
        by_req.setdefault((r["outcome_id"], r["req_id"]), []).append(r)

    you_count = 0
    ai_count = 0
    for req_rows in by_req.values():
        creations = [r for r in req_rows if r["kind"] == "creation"]
        assert creations, "every requirement must have at least one creation row"
        earliest = min(creations, key=lambda r: action_sort_key(r["action_id"]))
        if earliest["speaker"] == "U":
            you_count += 1
        else:
            ai_count += 1

    assert you_count == 4
    assert ai_count == 10


def test_zero_creation_labeled_overlap_per_requirement():
    """No single action_id is both a 'creation' row and a 'labeled' row for
    the same (outcome_id, req_id) — creation and Step-3 labeling are
    mutually exclusive per action per requirement.
    """
    rows = load_ledger_rows()
    kinds_by_action_req = {}
    for r in rows:
        key = (r["action_id"], r["outcome_id"], r["req_id"])
        kinds_by_action_req.setdefault(key, set()).add(r["kind"])

    overlaps = [k for k, kinds in kinds_by_action_req.items()
                if "creation" in kinds and "labeled" in kinds]
    assert overlaps == []


def test_zero_duplicate_action_requirement_rows():
    """One row per (action_id, outcome_id, req_id) — no duplicate scoring."""
    rows = load_ledger_rows()
    seen = {}
    for r in rows:
        key = (r["action_id"], r["outcome_id"], r["req_id"])
        seen[key] = seen.get(key, 0) + 1

    duplicates = {k: c for k, c in seen.items() if c > 1}
    assert duplicates == {}


# ---------------------------------------------------------------------------
# (c) panel_bundle direction matches ledger-derived direction (Phase 0 Brief Step 4c)
# ---------------------------------------------------------------------------

def test_panel_bundle_direction_matches_ledger_within_tolerance():
    rows = load_ledger_rows()
    you_total = sum(r["score"] for r in rows if r["speaker"] == "U")
    ai_total = sum(r["score"] for r in rows if r["speaker"] == "A")
    you_pct = you_total / (you_total + ai_total) * 100
    ai_pct = ai_total / (you_total + ai_total) * 100

    bundle = load_json(FIXTURE_DIR / "panel_bundle.json")
    pair1 = bundle["pairs"][0]

    assert pair1["direction"]["you_pct"] == pytest.approx(you_pct, abs=0.1)
    assert pair1["direction"]["ai_pct"] == pytest.approx(ai_pct, abs=0.1)
