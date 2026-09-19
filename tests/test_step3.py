"""Tier 1 tests for Step 3 Trigger A — Influence Labeling (E1.S4).

Verifies preceding candidate filtering, prompt assembly, response parsing,
ledger row generation (kind="labeled"), and action exclusions.
"""
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from engine.artifacts import LedgerWriter
from engine.config import Config
from engine.pipeline import (
    action_sort_key,
    build_step3_trigger_a_prompt,
    step_3_trigger_a,
    step_3_trigger_b,
)
from engine.state import State
from tests.invariants import inv_05_no_duplicate_ledger_rows

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


def test_action_sort_key_order():
    actions = ["A(1,1)", "U(1,2)", "U(1,1)", "A(2,1)", "U(2,1)"]
    sorted_actions = sorted(actions, key=action_sort_key)
    # Order should be U(1,1), U(1,2), A(1,1), U(2,1), A(2,1)
    assert sorted_actions == ["U(1,1)", "U(1,2)", "A(1,1)", "U(2,1)", "A(2,1)"]


def test_build_step3_trigger_a_prompt_direct():
    req = {
        "outcome_id": "outcome 1",
        "req_id": "req 1",
        "text": "Must be 45-60s video",
        "creation_action_ids": ["U(2,1)"],
    }
    preceding = [
        {"id": "U(1,1)", "type": "Describe", "role": "SHAPER", "text": "About page", "evidence_quote": "about page"},
    ]
    prompt = build_step3_trigger_a_prompt(
        outcome_text="Portfolio Video",
        req=req,
        origin_turn="U(2,1)",
        preceding_actions=preceding,
        subsequent_actions=[],
        slot_info=None,
    )
    assert "Outcome: Portfolio Video" in prompt
    assert "req 1: Must be 45-60s video" in prompt
    assert "Origin: directly created" in prompt
    assert "=== KNOWN SLOT ORIGIN ===" not in prompt  # stripped when directly created
    assert "[0] U(1,1) | Describe | SHAPER | About page" in prompt
    assert "None" in prompt  # Subsequent block is None


def test_build_step3_trigger_a_prompt_resolved():
    req = {
        "outcome_id": "outcome 1",
        "req_id": "req 2",
        "text": "Use Attenborough voice narration",
        "creation_action_ids": ["U(3,1)"],
    }
    slot_info = {
        "slot_id": "slot 1",
        "origin": "AI",
        "creation_turn": "A(1,2)",
        "text": "Feasibility of voice clone",
        "actions": [
            {"id": "A(1,2)", "type": "Suggest", "role": "SHAPER", "text": "Voice clone", "evidence_quote": "voice clone"}
        ],
    }
    prompt = build_step3_trigger_a_prompt(
        outcome_text="Portfolio Video",
        req=req,
        origin_turn="U(3,1)",
        preceding_actions=[],
        subsequent_actions=[],
        slot_info=slot_info,
    )
    assert "Origin: resolved from open slot" in prompt
    assert "=== KNOWN SLOT ORIGIN ===" in prompt
    assert "open_slot slot 1" in prompt
    assert "[0] A(1,2) | Suggest | SHAPER" in prompt


def test_step_3_trigger_a_preceding_action_exclusions(tmp_path):
    state = State()
    state.add_action({"id": "U(1,1)", "type": "Describe", "text": "Page description", "role": "SHAPER", "evidence_quote": "desc"})
    state.add_action({"id": "A(1,1)", "type": "Suggest", "text": "Video idea", "role": "SHAPER", "evidence_quote": "video"})
    state.add_action({"id": "U(2,1)", "type": "Request", "text": "Make video 45s", "role": "SHAPER", "evidence_quote": "45s"})
    state.outcomes = [{"id": "outcome 1", "text": "Portfolio", "turn_id": "U(1,1)", "parent": None, "children": [], "related": []}]
    state.run["action_to_outcome"] = {"U(1,1)": "outcome 1", "A(1,1)": "outcome 1", "U(2,1)": "outcome 1"}

    req = {
        "outcome_id": "outcome 1",
        "req_id": "req 1",
        "text": "Must be 45s",
        "type": "constraint",
        "status": "active",
        "creation_action_ids": ["U(2,1)"],  # U(2,1) is creation action -> must be excluded
        "contributing_action_ids": [],
        "implementation_action_ids": [],
        "revise_action_ids": [],
        "related_to": [],
        "created_at_pair": 2,
    }

    client = MagicMock()
    client.call_json.return_value = {
        "preceding labels": [
            {"index": 0, "action id": "U(1,1)", "relationship type": "IMPLICIT CONNECTION", "relationship score": 2, "contribution role": "SHAPER"},
            {"index": 1, "action id": "A(1,1)", "relationship type": "NO CONNECTION", "relationship score": None, "contribution role": "SHAPER"},
        ],
        "subsequent labels": [],
    }

    ledger_path = tmp_path / "ledger.jsonl"
    writer = LedgerWriter(ledger_path)

    step_3_trigger_a(client, make_test_config(), state, pair_number=2, outcome_id="outcome 1", requirement=req, ledger_writer=writer)

    # Prompt check: U(2,1) must NEVER be in the prompt sent to LLM (§11.4)
    called_prompt = client.call_json.call_args[0][2]
    assert "U(1,1)" in called_prompt
    assert "A(1,1)" in called_prompt
    # U(2,1) is the origin turn, but it must NOT be in Section A or Section B
    assert "[0] U(2,1)" not in called_prompt
    assert "[1] U(2,1)" not in called_prompt

    # Ledger check:
    # U(1,1) got score 2.0 -> row written
    # A(1,1) got NO CONNECTION -> NO row written
    assert len(writer.rows) == 1
    row = writer.rows[0]
    assert row["action_id"] == "U(1,1)"
    assert row["speaker"] == "U"
    assert row["role"] == "SHAPER"
    assert row["score"] == 2.0
    assert row["kind"] == "labeled"
    assert row["outcome_id"] == "outcome 1"
    assert row["req_id"] == "req 1"

    # Labeled tracking updated
    assert state.run["labeled_action_ids"]["outcome 1||req 1"] == ["U(1,1)", "A(1,1)"]


def test_step_3_trigger_a_empty_candidates():
    state = State()
    # Req created in turn U(1,1) has no preceding actions
    state.add_action({"id": "U(1,1)", "type": "Request", "text": "Initial request", "role": "SHAPER", "evidence_quote": "req"})
    state.outcomes = [{"id": "outcome 1", "text": "Portfolio", "turn_id": "U(1,1)", "parent": None, "children": [], "related": []}]
    state.run["action_to_outcome"] = {"U(1,1)": "outcome 1"}

    req = {
        "outcome_id": "outcome 1",
        "req_id": "req 1",
        "text": "Initial requirement",
        "type": "task",
        "status": "active",
        "creation_action_ids": ["U(1,1)"],
        "contributing_action_ids": [],
        "implementation_action_ids": [],
        "revise_action_ids": [],
        "related_to": [],
        "created_at_pair": 1,
    }

    client = MagicMock()
    step_3_trigger_a(client, make_test_config(), state, pair_number=1, outcome_id="outcome 1", requirement=req)
    # Because there are 0 preceding actions and 0 subsequent actions, client.call_json should NOT be called
    assert client.call_json.call_count == 0


def test_step_3_trigger_b_incremental_subsequent_only(tmp_path):
    state = State()
    state.add_action({"id": "U(1,1)", "type": "Request", "text": "Build feature", "role": "SHAPER", "evidence_quote": "req"})
    state.add_action({"id": "A(1,1)", "type": "Plan", "text": "Plan feature", "role": "EXECUTOR", "evidence_quote": "plan"})
    state.add_action({"id": "A(2,1)", "type": "Implement", "text": "Implement feature code", "role": "EXECUTOR", "evidence_quote": "code"})
    state.outcomes = [{"id": "outcome 1", "text": "Feature development", "turn_id": "U(1,1)", "parent": None, "children": [], "related": []}]
    state.run["action_to_outcome"] = {"U(1,1)": "outcome 1", "A(1,1)": "outcome 1", "A(2,1)": "outcome 1"}

    # Req created at Pair 1
    req = {
        "outcome_id": "outcome 1",
        "req_id": "req 1",
        "text": "Build feature",
        "type": "task",
        "status": "active",
        "creation_action_ids": ["U(1,1)"],
        "contributing_action_ids": [],
        "implementation_action_ids": [],
        "revise_action_ids": [],
        "related_to": [],
        "created_at_pair": 1,
    }
    state.requirements.append(req)

    # Actions from Pair 1 were already labeled
    state.run["labeled_action_ids"]["outcome 1||req 1"] = ["U(1,1)", "A(1,1)"]

    client = MagicMock()
    client.call_json.return_value = {
        "subsequent labels": [
            {
                "index": 0,
                "action id": "A(2,1)",
                "relationship type": "IMPLEMENTS",
                "relationship score": 5,
                "contribution role": "EXECUTOR",
            }
        ]
    }

    ledger_path = tmp_path / "ledger.jsonl"
    writer = LedgerWriter(ledger_path)
    new_actions = [state.get_action("A(2,1)")]

    res = step_3_trigger_b(client, make_test_config(), state, pair_number=2, outcome_id="outcome 1", new_actions=new_actions, ledger_writer=writer)

    # 1. Prompt check: Section A was None, Section B contains ONLY A(2,1)
    called_prompt = client.call_json.call_args[0][2]
    assert "=== SECTION A: PRECEDING ACTIONS" in called_prompt
    assert "None\n\n=== SECTION B: SUBSEQUENT ACTIONS" in called_prompt
    assert "A(2,1) | Implement | EXECUTOR" in called_prompt
    assert "A(1,1)" not in called_prompt  # already labeled, must not be re-sent

    # 2. Ledger check: row written with score 5.0, kind="labeled", pair_added=2
    assert len(writer.rows) == 1
    row = writer.rows[0]
    assert row["action_id"] == "A(2,1)"
    assert row["speaker"] == "A"
    assert row["score"] == 5.0
    assert row["kind"] == "labeled"
    assert row["pair_added"] == 2

    # 3. Requirement updated with IMPLEMENTS action
    assert "A(2,1)" in req["implementation_action_ids"]

    # 4. Labeled action tracking updated
    assert "A(2,1)" in state.run["labeled_action_ids"]["outcome 1||req 1"]


def test_step_3_trigger_b_idempotency_zero_duplicate_rows(tmp_path):
    """Re-processing the same actions must add zero duplicate rows (inv_05)."""
    state = State()
    state.add_action({"id": "U(1,1)", "type": "Request", "text": "Feature", "role": "SHAPER", "evidence_quote": "f"})
    state.add_action({"id": "A(2,1)", "type": "Implement", "text": "Impl", "role": "EXECUTOR", "evidence_quote": "i"})
    state.outcomes = [{"id": "outcome 1", "text": "Feature", "turn_id": "U(1,1)", "parent": None, "children": [], "related": []}]
    state.run["action_to_outcome"] = {"U(1,1)": "outcome 1", "A(2,1)": "outcome 1"}

    req = {
        "outcome_id": "outcome 1",
        "req_id": "req 1",
        "text": "Feature",
        "type": "task",
        "status": "active",
        "creation_action_ids": ["U(1,1)"],
        "contributing_action_ids": [],
        "implementation_action_ids": [],
        "revise_action_ids": [],
        "related_to": [],
        "created_at_pair": 1,
    }
    state.requirements.append(req)

    client = MagicMock()
    client.call_json.return_value = {
        "subsequent labels": [
            {"index": 0, "action id": "A(2,1)", "relationship type": "IMPLEMENTS", "relationship score": 5}
        ]
    }
    ledger_path = tmp_path / "ledger.jsonl"
    writer = LedgerWriter(ledger_path)
    new_actions = [state.get_action("A(2,1)")]

    # First pass: adds row
    step_3_trigger_b(client, make_test_config(), state, pair_number=2, outcome_id="outcome 1", new_actions=new_actions, ledger_writer=writer)
    assert len(writer.rows) == 1

    # Second pass: identical new_actions -> already labeled -> zero calls, zero rows added
    client.reset_mock()
    step_3_trigger_b(client, make_test_config(), state, pair_number=2, outcome_id="outcome 1", new_actions=new_actions, ledger_writer=writer)
    assert client.call_json.call_count == 0
    assert len(writer.rows) == 1

    # Invariant 5 passes
    assert inv_05_no_duplicate_ledger_rows(writer.rows) == []


def test_step_3_trigger_b_batching_step3_batch_size():
    """Verify requirements are batched up to config.step3_batch_size."""
    state = State()
    state.add_action({"id": "U(1,1)", "type": "Request", "text": "Base", "role": "SHAPER", "evidence_quote": "b"})
    state.add_action({"id": "A(2,1)", "type": "Implement", "text": "Impl", "role": "EXECUTOR", "evidence_quote": "i"})
    state.outcomes = [{"id": "outcome 1", "text": "Feature", "turn_id": "U(1,1)", "parent": None, "children": [], "related": []}]
    state.run["action_to_outcome"] = {"U(1,1)": "outcome 1", "A(2,1)": "outcome 1"}

    # Create 5 existing requirements
    for i in range(1, 6):
        state.requirements.append({
            "outcome_id": "outcome 1",
            "req_id": f"req_{i}",
            "text": f"Requirement {i}",
            "type": "task",
            "status": "active",
            "creation_action_ids": ["U(1,1)"],
            "contributing_action_ids": [],
            "implementation_action_ids": [],
            "revise_action_ids": [],
            "related_to": [],
            "created_at_pair": 1,
        })

    config = Config(
        llm_api_key="key",
        llm_base_url="https://example.com",
        model_fast="fast",
        model_main="main",
        model_step2="step2",
        model_step3="step3",
        step3_batch_size=2,  # Batches of 2: [req1, req2], [req3, req4], [req5]
    )

    client = MagicMock()
    client.call_json.return_value = {
        "subsequent labels": [
            {"index": 0, "action id": "A(2,1)", "relationship type": "IMPLEMENTS", "relationship score": 4}
        ]
    }

    new_actions = [state.get_action("A(2,1)")]
    results = step_3_trigger_b(client, config, state, pair_number=2, outcome_id="outcome 1", new_actions=new_actions)

    # All 5 requirements evaluated
    assert len(results) == 5
    assert sorted(results.keys()) == ["req_1", "req_2", "req_3", "req_4", "req_5"]
    assert client.call_json.call_count == 5

