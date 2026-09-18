"""Tier 1 tests for the 21 invariants module (TEST_STRATEGY.md §2).

Verifies invariants 1-9 pass against data/chats/fixture_pair1/,
and that invariants 10-21 guard gracefully with skip indicators when data is absent.
"""
import json
from pathlib import Path

import pytest

from tests import invariants as inv

pytestmark = pytest.mark.tier1

FIXTURE_DIR = Path(__file__).parent.parent / "data" / "chats" / "fixture_pair1"


@pytest.fixture(scope="module")
def fixture_data():
    with open(FIXTURE_DIR / "dialogue.json", "r", encoding="utf-8") as f:
        dialogue = json.load(f)
    with open(FIXTURE_DIR / "state.json", "r", encoding="utf-8") as f:
        state = json.load(f)
    with open(FIXTURE_DIR / "snapshots.json", "r", encoding="utf-8") as f:
        snapshots = json.load(f)
    with open(FIXTURE_DIR / "panel_bundle.json", "r", encoding="utf-8") as f:
        panel_bundle = json.load(f)
    with open(FIXTURE_DIR / "ledger.jsonl", "r", encoding="utf-8") as f:
        ledger = [json.loads(line) for line in f if line.strip()]

    return {
        "dialogue": dialogue,
        "state": state,
        "snapshots": snapshots,
        "panel_bundle": panel_bundle,
        "ledger": ledger,
    }


def test_inv_01_schema_valid(fixture_data):
    """Invariant 1: Every fixture artifact validates against its schema."""
    artifacts = {
        "dialogue": fixture_data["dialogue"],
        "state": fixture_data["state"],
        "snapshots": fixture_data["snapshots"],
        "panel_bundle": fixture_data["panel_bundle"],
        "ledger": fixture_data["ledger"],
    }
    violations = inv.inv_01_schema_valid(artifacts)
    assert violations == []


def test_inv_02_action_ids(fixture_data):
    """Invariant 2: Every action id matches regex and is unique."""
    violations = inv.inv_02_action_ids(fixture_data["state"])
    assert violations == []


def test_inv_03_ledger_references_exist(fixture_data):
    """Invariant 3: Ledger action_id, req_id, outcome_id exist in state."""
    violations = inv.inv_03_ledger_references_exist(fixture_data["ledger"], fixture_data["state"])
    assert violations == []


def test_inv_04_action_maps_to_one_outcome(fixture_data):
    """Invariant 4: Every action maps to exactly one outcome."""
    violations = inv.inv_04_action_maps_to_one_outcome(fixture_data["state"])
    assert violations == []


def test_inv_05_no_duplicate_ledger_rows(fixture_data):
    """Invariant 5: No duplicate rows on (action_id, outcome_id, req_id, pair_added, kind)."""
    violations = inv.inv_05_no_duplicate_ledger_rows(fixture_data["ledger"])
    assert violations == []


def test_inv_06_outcome_tree(fixture_data):
    """Invariant 6: Outcome tree has 1 root, no cycles, mutual parent/child agreement."""
    violations = inv.inv_06_outcome_tree(fixture_data["state"])
    assert violations == []


def test_inv_07_requirement_has_creation(fixture_data):
    """Invariant 7: Every requirement has at least one creation action."""
    violations = inv.inv_07_requirement_has_creation(fixture_data["state"])
    assert violations == []


def test_inv_08_requirement_created_at_pair(fixture_data):
    """Invariant 8: Every requirement created_at_pair <= current_pair."""
    violations = inv.inv_08_requirement_created_at_pair(fixture_data["state"], current_pair=1)
    assert violations == []


def test_inv_09_slot_status_and_inactivity(fixture_data):
    """Invariant 9: Slot status is open, resolved, or abandoned."""
    violations = inv.inv_09_slot_status_and_inactivity(fixture_data["state"])
    assert violations == []


def test_inv_10_to_16_arithmetic_guards(fixture_data):
    """Invariants 10-16: Guard gracefully when analysis.json is absent."""
    # Inv 10 can also validate ledger rows directly if available
    assert inv.inv_10_scores_positive(None, fixture_data["ledger"]) == []
    assert inv.inv_10_scores_positive(None, None) == ["skipped: analysis.json absent"]

    assert inv.inv_11_deltas_sum_to_cumulative(None) == ["skipped: analysis.json absent"]
    assert inv.inv_12_creator_counts_sum(None) == ["skipped: analysis.json absent"]
    assert inv.inv_13_cumulative_mass_monotonic(None) == ["skipped: analysis.json absent"]
    assert inv.inv_14_shaper_subset(None) == ["skipped: analysis.json absent"]
    assert inv.inv_15_percentages_sum_to_100(None) == ["skipped: analysis.json absent"]
    assert inv.inv_16_mode_pure_function(None) == ["skipped: analysis.json absent"]


def test_inv_17_to_21_process_guards(fixture_data):
    """Invariants 17-21: Guard gracefully when comparison inputs are absent."""
    assert inv.inv_17_append_only(None, None) == ["skipped: consecutive ledgers absent"]
    assert inv.inv_18_idempotency(None, None) == ["skipped: rerun state absent"]
    assert inv.inv_19_purity(None, None) == ["skipped: analysis runs absent"]
    assert inv.inv_20_batch_equals_live(None, None) == ["skipped: batch/live ledgers absent"]

    # Inv 21 recognizes stubbed fixture dialogue
    assert inv.inv_21_provenance(
        fixture_data["dialogue"], fixture_data["ledger"], fixture_data["state"]
    ) == ["skipped: fixture dialogue is stubbed"]


def test_inv_21_verbatim_quote_check():
    """Verify inv_21 checks that action evidence_quote appears verbatim in turn text."""
    dialogue = [
        {"pair": 1, "speaker": "user", "text": "Can we build a portfolio website?", "attachments": [], "ts": "2026-09-18T10:00:00Z"},
        {"pair": 1, "speaker": "ai", "text": "Sure, I recommend Next.js and Tailwind.", "attachments": [], "ts": "2026-09-18T10:00:05Z"},
    ]
    ledger = [
        {"action_id": "U(1,1)", "outcome_id": "o1", "req_id": "r1", "pair_added": 1, "kind": "create"}
    ]
    state_valid = {
        "actions": [
            {"id": "U(1,1)", "type": "request", "text": "User asks for website", "role": "SHAPER", "evidence_quote": "portfolio website"},
            {"id": "A(1,1)", "type": "suggest", "text": "AI suggests stack", "role": "EXECUTOR", "evidence_quote": "Next.js and Tailwind"}
        ]
    }
    assert inv.inv_21_provenance(dialogue, ledger, state_valid) == []

    state_invalid = {
        "actions": [
            {"id": "U(1,1)", "type": "request", "text": "User asks for website", "role": "SHAPER", "evidence_quote": "invented quote not in text"}
        ]
    }
    violations = inv.inv_21_provenance(dialogue, ledger, state_invalid)
    assert len(violations) == 1
    assert "not found verbatim" in violations[0]

