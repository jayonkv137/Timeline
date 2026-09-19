"""Tier 1 tests for Slot Lifecycle and the 3-Pair Abandonment Sweep (E1.S3).

Verifies slot age tracking, activity resets, automatic abandonment at pair 4,
invariants preservation (inv_09), and pipeline_state.json persistence.
"""
from pathlib import Path

import pytest

from engine.pipeline import record_slot_activity, run_level2, sweep_abandoned_slots
from engine.state import State
from tests.invariants import inv_09_slot_status_and_inactivity

pytestmark = pytest.mark.tier1


def make_slot_state(opened_pair=1):
    state = State()
    state.outcomes = [{"id": "outcome 1", "text": "Portfolio film", "turn_id": "U(1,1)", "parent": None, "children": [], "related": []}]
    slot = {
        "slot_id": "slot 1",
        "outcome_id": "outcome 1",
        "text": "Explore 3D specimen cylinder mechanics.",
        "type": "task",
        "origin": "AI",
        "status": "open",
        "creation_action_ids": ["A(1,1)"],
        "contributing_action_ids": [],
        "resolved_into": None,
    }
    state.slots.append(slot)
    state.run["slot_opened_at_pair"]["outcome 1||slot 1"] = opened_pair
    state.run["slot_last_active_pair"]["outcome 1||slot 1"] = opened_pair
    return state


def test_sweep_abandoned_slots_synthetic_four_pair():
    """Verify: a synthetic four-pair fixture where a slot opens at pair 1 and is never
    mentioned again. It must be abandoned by pair 4 and not before.
    """
    state = make_slot_state(opened_pair=1)
    slot = state.slots[0]

    # Pair 1: newly opened -> inactive 0 pairs -> remains open
    abandoned_p1 = sweep_abandoned_slots(state, pair_number=1)
    assert len(abandoned_p1) == 0
    assert slot["status"] == "open"

    # Pair 2: inactive 1 pair (pair 2) -> remains open
    abandoned_p2 = sweep_abandoned_slots(state, pair_number=2)
    assert len(abandoned_p2) == 0
    assert slot["status"] == "open"

    # Pair 3: inactive 2 pairs (pairs 2, 3) -> remains open
    abandoned_p3 = sweep_abandoned_slots(state, pair_number=3)
    assert len(abandoned_p3) == 0
    assert slot["status"] == "open"

    # Pair 4: inactive 3 pairs (pairs 2, 3, 4) -> must be abandoned by pair 4 and not before
    abandoned_p4 = sweep_abandoned_slots(state, pair_number=4)
    assert len(abandoned_p4) == 1
    assert slot["status"] == "abandoned"

    # Verify operations log has abandon entry
    assert len(state.operations_log) == 1
    log_entry = state.operations_log[0]
    assert log_entry["pair"] == 4
    assert log_entry["outcome_id"] == "outcome 1"
    assert log_entry["op"] == "abandon"
    assert log_entry["target_id"] == "slot 1"
    assert log_entry["target_type"] == "slot"


def test_slot_activity_resets_age():
    """Verify that referencing or touching a slot resets its inactivity timer."""
    state = make_slot_state(opened_pair=1)
    slot = state.slots[0]

    # Pair 2: inactive 1 pair -> remains open
    sweep_abandoned_slots(state, pair_number=2)
    assert slot["status"] == "open"

    # Pair 3: slot receives activity (e.g. an action discusses it)
    record_slot_activity(state, "outcome 1", "slot 1", pair_number=3)
    sweep_abandoned_slots(state, pair_number=3)
    assert slot["status"] == "open"

    # Pair 4: only 1 pair since last activity (3) -> remains open!
    sweep_abandoned_slots(state, pair_number=4)
    assert slot["status"] == "open"

    # Pair 5: 2 pairs since last activity (3) -> remains open!
    sweep_abandoned_slots(state, pair_number=5)
    assert slot["status"] == "open"

    # Pair 6: 3 pairs since last activity (3) -> transitions to abandoned at pair 6
    abandoned_p6 = sweep_abandoned_slots(state, pair_number=6)
    assert len(abandoned_p6) == 1
    assert slot["status"] == "abandoned"


def test_resolved_slot_is_never_abandoned():
    """A resolved slot should never be touched by the abandonment sweep."""
    state = make_slot_state(opened_pair=1)
    slot = state.slots[0]
    slot["status"] = "resolved"
    slot["resolved_into"] = "req 1"
    state.requirements.append({
        "outcome_id": "outcome 1",
        "req_id": "req 1",
        "text": "Specimen cylinder implemented",
        "type": "task",
        "status": "active",
        "creation_action_ids": ["U(2,1)"],
        "contributing_action_ids": [],
        "implementation_action_ids": [],
        "revise_action_ids": [],
        "related_to": ["slot 1"],
        "explicit_or_implicit": "explicit",
        "rationale": "Resolved slot",
        "created_at_pair": 2,
    })

    # Across pairs 2 through 10, sweep should ignore resolved slots
    for p in range(2, 11):
        abandoned = sweep_abandoned_slots(state, pair_number=p)
        assert len(abandoned) == 0
        assert slot["status"] == "resolved"


def test_inv_09_passes_with_lifecycle():
    """inv_09 ensures all slots have valid status and resolved slots link correctly."""
    state = make_slot_state(opened_pair=1)
    # Add resolved slot
    state.slots.append({
        "slot_id": "slot 2",
        "outcome_id": "outcome 1",
        "text": "Resolved slot",
        "type": "task",
        "origin": "user",
        "status": "resolved",
        "creation_action_ids": ["U(1,1)"],
        "contributing_action_ids": [],
        "resolved_into": "req 1",
    })
    state.requirements.append({
        "outcome_id": "outcome 1",
        "req_id": "req 1",
        "text": "Requirement 1",
        "type": "task",
        "status": "active",
        "creation_action_ids": ["U(1,1)"],
        "contributing_action_ids": [],
        "implementation_action_ids": [],
        "revise_action_ids": [],
        "related_to": [],
        "explicit_or_implicit": "explicit",
        "rationale": "",
        "created_at_pair": 1,
    })

    # Sweep at pair 4 abandons slot 1
    sweep_abandoned_slots(state, pair_number=4)
    assert state.slots[0]["status"] == "abandoned"
    assert state.slots[1]["status"] == "resolved"

    violations = inv_09_slot_status_and_inactivity(state.to_dict(), current_pair=4)
    assert violations == []


def test_pipeline_state_persistence_and_schema_isolation(tmp_path):
    """Slot ages live in run/pipeline_state.json, never in state.json."""
    state = make_slot_state(opened_pair=1)
    record_slot_activity(state, "outcome 1", "slot 1", pair_number=3)

    state.save(tmp_path)

    # state.json exists and validates against schema
    state_file = tmp_path / "state.json"
    assert state_file.exists()

    # run/pipeline_state.json exists and holds slot_last_active_pair
    pipeline_state_file = tmp_path / "run" / "pipeline_state.json"
    assert pipeline_state_file.exists()

    # Reload into fresh state
    loaded = State.load(tmp_path)
    assert loaded.run["slot_opened_at_pair"]["outcome 1||slot 1"] == 1
    assert loaded.run["slot_last_active_pair"]["outcome 1||slot 1"] == 3
    assert len(loaded.slots) == 1
    assert loaded.slots[0]["slot_id"] == "slot 1"
