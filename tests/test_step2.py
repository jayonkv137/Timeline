"""Tier 1 tests for Step 2 — Requirement & Slot Extraction (E1.S2).

Verifies step_2, formatters, validation errors, ledger creation rows, and fan-out.
"""
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from engine.artifacts import LedgerWriter
from engine.config import Config
from engine.pipeline import (
    PipelineError,
    format_prior_open_slots_block,
    format_prior_requirements_block,
    run_level2,
    step_2,
)
from engine.state import State

pytestmark = pytest.mark.tier1


def make_test_config():
    return Config(
        llm_api_key="test-key",
        llm_base_url="https://example.com/v1",
        model_fast="test-fast",
        model_main="test-main",
        model_step2="test-step2",
        model_step3="test-step3",
        step3_batch_size=3,
    )


def make_test_state():
    state = State()
    state.add_action({
        "id": "U(1,1)",
        "type": "request",
        "text": "User asks for 45-60s video",
        "role": "SHAPER",
        "evidence_quote": "make it 45 to 60 seconds",
    })
    state.add_action({
        "id": "A(1,1)",
        "type": "suggest",
        "text": "AI proposes three narrative pillars",
        "role": "SHAPER",
        "evidence_quote": "three structural pillars",
    })
    state.add_action({
        "id": "A(1,2)",
        "type": "suggest",
        "text": "AI suggests 3D specimen cylinder",
        "role": "EXECUTOR",
        "evidence_quote": "3D specimen cylinder",
    })
    state.outcomes = [
        {"id": "outcome 1", "text": "Portfolio About Page Video", "turn_id": "U(1,1)", "parent": None, "children": ["outcome 2"], "related": []},
        {"id": "outcome 2", "text": "Specimen Cylinder Feature", "turn_id": "A(1,2)", "parent": "outcome 1", "children": [], "related": []},
    ]
    state.run["action_to_outcome"] = {
        "U(1,1)": "outcome 1",
        "A(1,1)": "outcome 1",
        "A(1,2)": "outcome 2",
    }
    return state


def test_format_prior_blocks_empty():
    assert format_prior_requirements_block([]) == "[]"
    assert format_prior_open_slots_block([]) == "[]"


def test_format_prior_blocks_populated():
    reqs = [{
        "outcome_id": "outcome 1",
        "req_id": "req 1",
        "text": "Must be 45-60s",
        "type": "constraint",
        "status": "active",
        "creation_action_ids": ["U(1,1)"],
        "contributing_action_ids": [],
        "related_to": [],
    }]
    formatted_reqs = format_prior_requirements_block(reqs)
    assert '"req id": "req 1"' in formatted_reqs
    assert '"Must be 45-60s"' in formatted_reqs

    slots = [
        {"slot_id": "slot 1", "text": "Hedged cylinder idea", "type": "task", "origin": "AI", "status": "open", "creation_action_ids": ["A(1,2)"], "contributing_action_ids": []},
        {"slot_id": "slot 2", "text": "Abandoned idea", "type": "task", "origin": "AI", "status": "abandoned", "creation_action_ids": ["A(1,2)"], "contributing_action_ids": []},
    ]
    formatted_slots = format_prior_open_slots_block(slots)
    assert '"slot id": "slot 1"' in formatted_slots
    assert "Abandoned idea" not in formatted_slots  # abandoned slots are dropped


def test_step_2_create_requirement(tmp_path):
    state = make_test_state()
    config = make_test_config()
    client = MagicMock()

    client.call_json.return_value = {
        "requirement ops": [
            {
                "op": "create",
                "req id": "req 1",
                "bound outcome id": "outcome 1",
                "fields": {
                    "text": "The video duration must be between 45 and 60 seconds.",
                    "type": "constraint",
                },
                "creation action ids": ["U(1,1)"],
                "contributing action ids": [],
                "implementation action ids": [],
                "related to": [],
                "explicit or implicit": "explicit",
                "rationale": "Mandatory duration constraint specified by user.",
            }
        ],
        "open_slot ops": []
    }

    ledger_path = tmp_path / "ledger.jsonl"
    writer = LedgerWriter(ledger_path)

    result = step_2(client, config, state, pair_number=1, outcome_id="outcome 1", ledger_writer=writer)

    # State updated
    assert len(state.requirements) == 1
    req = state.requirements[0]
    assert req["req_id"] == "req 1"
    assert req["outcome_id"] == "outcome 1"
    assert req["created_at_pair"] == 1
    assert req["creation_action_ids"] == ["U(1,1)"]

    # Operations log updated
    assert len(state.operations_log) == 1
    assert state.operations_log[0]["op"] == "create"

    # Ledger row written: 5.0 score, kind="creation"
    assert len(writer.rows) == 1
    row = writer.rows[0]
    assert row["action_id"] == "U(1,1)"
    assert row["speaker"] == "U"
    assert row["role"] == "SHAPER"
    assert row["score"] == 5.0
    assert row["kind"] == "creation"
    assert row["outcome_id"] == "outcome 1"
    assert row["req_id"] == "req 1"

    # Verifies schema validation passes on save
    state.save(tmp_path)
    assert (tmp_path / "state.json").exists()


def test_step_2_open_slot_and_resolve(tmp_path):
    state = make_test_state()
    config = make_test_config()
    client = MagicMock()

    # Call 1: Open slot
    client.call_json.return_value = {
        "requirement ops": [],
        "open_slot ops": [
            {
                "op": "open_slot",
                "slot id": "slot 1",
                "bound outcome id": "outcome 1",
                "fields": {
                    "text": "Explore whether Attenborough narration voice cloning is feasible.",
                    "type": "constraint",
                },
                "origin": "AI",
                "creation action ids": ["A(1,1)"],
                "contributing action ids": [],
                "related to": [],
                "explicit or implicit": "explicit",
                "rationale": "Feasibility question raised as tentative.",
            }
        ]
    }

    ledger_path = tmp_path / "ledger.jsonl"
    writer = LedgerWriter(ledger_path)

    step_2(client, config, state, pair_number=1, outcome_id="outcome 1", ledger_writer=writer)
    assert len(state.slots) == 1
    slot = state.slots[0]
    assert slot["status"] == "open"
    assert slot["slot_id"] == "slot 1"
    assert len(writer.rows) == 0  # open slot adds zero ledger rows

    # Call 2: Resolve slot into requirement
    state.add_action({
        "id": "U(2,1)",
        "type": "decide",
        "text": "User decides to use TTS voice clone",
        "role": "SHAPER",
        "evidence_quote": "let us do the voice clone",
    })
    state.run["action_to_outcome"]["U(2,1)"] = "outcome 1"

    client.call_json.return_value = {
        "requirement ops": [],
        "open_slot ops": [
            {
                "op": "resolve",
                "slot id": "slot 1",
                "req id": "req 2",
                "bound outcome id": "outcome 1",
                "fields": {
                    "text": "Must use voice-cloned David Attenborough narration.",
                    "type": "constraint",
                },
                "creation action ids": ["U(2,1)"],
            }
        ]
    }

    step_2(client, config, state, pair_number=2, outcome_id="outcome 1", ledger_writer=writer)
    assert slot["status"] == "resolved"
    assert slot["resolved_into"] == "req 2"

    assert len(state.requirements) == 1
    res_req = state.requirements[0]
    assert res_req["req_id"] == "req 2"

    # 2 rows written: 1 creation row (5.0) for resolving action, 1 slot-origin row (3.0) for slot creator
    assert len(writer.rows) == 2
    creation_row = [r for r in writer.rows if r["kind"] == "creation"][0]
    assert creation_row["action_id"] == "U(2,1)"
    assert creation_row["score"] == 5.0

    slot_origin_row = [r for r in writer.rows if r["kind"] == "slot-origin"][0]
    assert slot_origin_row["action_id"] == "A(1,1)"
    assert slot_origin_row["score"] == 3.0


def test_step_2_validation_checks():
    state = make_test_state()
    config = make_test_config()
    client = MagicMock()

    # 1. Unknown action cited in creation action ids
    client.call_json.return_value = {
        "requirement ops": [{
            "op": "create", "req id": "req 1", "bound outcome id": "outcome 1",
            "fields": {"text": "Req", "type": "task"}, "creation action ids": ["U(99,99)"],
        }],
        "open_slot ops": []
    }
    with pytest.raises(PipelineError, match="unknown action id"):
        step_2(client, config, state, pair_number=1, outcome_id="outcome 1")

    # 2. Action from different outcome cited (isolation invariant)
    client.call_json.return_value = {
        "requirement ops": [{
            "op": "create", "req id": "req 1", "bound outcome id": "outcome 1",
            "fields": {"text": "Req", "type": "task"}, "creation action ids": ["A(1,2)"],  # A(1,2) is in outcome 2!
        }],
        "open_slot ops": []
    }
    with pytest.raises(PipelineError, match="belongs to 'outcome 2'"):
        step_2(client, config, state, pair_number=1, outcome_id="outcome 1")


def test_run_level2_fan_out():
    state = make_test_state()
    config = make_test_config()
    client = MagicMock()

    client.call_json.return_value = {
        "requirement ops": [],
        "open_slot ops": []
    }

    # If new_actions only touch outcome 1:
    new_actions = [state.get_action("U(1,1)")]
    results = run_level2(client, config, state, pair_number=1, new_actions=new_actions)
    assert list(results.keys()) == ["outcome 1"]
    assert client.call_json.call_count == 1

    # If new_actions touch both outcome 1 and outcome 2:
    client.reset_mock()
    new_actions_both = [state.get_action("U(1,1)"), state.get_action("A(1,2)")]
    results_both = run_level2(client, config, state, pair_number=1, new_actions=new_actions_both)
    assert sorted(results_both.keys()) == ["outcome 1", "outcome 2"]
    assert client.call_json.call_count == 2
