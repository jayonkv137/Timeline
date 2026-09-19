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
