"""P2.S2 tests: STATE round-trip, ledger append-only writer, validation gate.

Also proves the loaders are compatible with the FROZEN Phase 0 fixture
(read-only — nothing here writes into data/chats/fixture_pair1/).
"""
import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

pytestmark = pytest.mark.tier1

from engine.artifacts import (LedgerWriter, read_ledger, validate_artifact,
                              write_json_artifact)
from engine.state import State

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = REPO_ROOT / "data" / "chats" / "fixture_pair1"

GOOD_ROW = {
    "pair_added": 1, "action_id": "U(1,1)", "speaker": "U", "role": "SHAPER",
    "outcome_id": "outcome 1", "req_id": "req 1", "score": 5.0,
    "kind": "creation",
}


def make_state():
    state = State()
    state.add_action({
        "id": "U(1,1)", "type": "Request",
        "text": "User asks for a thing.", "role": "SHAPER",
        "evidence_quote": "please do the thing",
    })
    state.add_action({
        "id": "A(1,1)", "type": "Draft",
        "text": "AI drafts the thing.", "role": "EXECUTOR",
        "evidence_quote": "here is the thing",
    })
    state.outcomes.append({
        "id": "outcome 1", "text": "the thing", "turn_id": "U(1,1)",
        "parent": None, "children": [], "related": [],
    })
    state.intentions.append({
        "intention_id": "I1", "intention": "get the thing done",
        "outcome_ids": ["outcome 1"],
    })
    state.requirements.append({
        "outcome_id": "outcome 1", "req_id": "req 1",
        "text": "the thing must exist", "type": "constraint",
        "status": "active", "creation_action_ids": ["U(1,1)"],
        "contributing_action_ids": [], "implementation_action_ids": ["A(1,1)"],
        "revise_action_ids": [], "related_to": [],
        "explicit_or_implicit": "explicit", "rationale": "stated directly",
        "created_at_pair": 1,
    })
    state.slots.append({
        "slot_id": "slot 1", "outcome_id": "outcome 1",
        "text": "maybe a second thing", "type": "preference", "origin": "AI",
        "status": "open", "creation_action_ids": ["A(1,1)"],
        "contributing_action_ids": [], "resolved_into": None,
    })
    state.log_operation(1, "outcome 1", "create", "req 1", "requirement")
    state.run["action_to_outcome"] = {"U(1,1)": "outcome 1", "A(1,1)": "outcome 1"}
    state.run["dialogue_summary"] = "User and AI make a thing."
    return state


# ---------------------------------------------------------------- STATE

def test_state_round_trip(tmp_path):
    state = make_state()
    state.save(tmp_path)
    reloaded = State.load(tmp_path)
    assert reloaded.to_dict() == state.to_dict()
    assert reloaded.run == state.run


def test_state_save_validates_and_raises(tmp_path):
    state = make_state()
    state.actions[0]["role"] = "BOSS"  # not in SHAPER|EXECUTOR|OTHER
    with pytest.raises(ValidationError):
        state.save(tmp_path)
    assert not (tmp_path / "state.json").exists()  # nothing written on failure


def test_state_lookups():
    state = make_state()
    assert state.get_action("U(1,1)")["role"] == "SHAPER"
    assert [a["id"] for a in state.actions_for_outcome("outcome 1")] == ["U(1,1)", "A(1,1)"]
    assert state.find_requirement("outcome 1", "req 1")["status"] == "active"
    assert state.find_requirement("outcome 1", "req 99") is None
    assert len(state.slots_for_outcome("outcome 1", status="open")) == 1
    with pytest.raises(ValueError):
        state.add_action(dict(state.actions[0]))  # duplicate id


# ---------------------------------------------------------------- ledger

def test_ledger_append_and_reload(tmp_path):
    path = tmp_path / "ledger.jsonl"
    writer = LedgerWriter(path)
    writer.append(dict(GOOD_ROW))
    writer.append(dict(GOOD_ROW, action_id="A(1,2)", speaker="A", kind="labeled", score=3))

    reopened = LedgerWriter(path)  # picks up existing rows
    assert len(reopened.rows) == 2
    reopened.append(dict(GOOD_ROW, action_id="A(1,3)", speaker="A", kind="labeled", score=1))
    assert [r["action_id"] for r in read_ledger(path)] == ["U(1,1)", "A(1,2)", "A(1,3)"]


def test_ledger_append_only_never_rewrites(tmp_path):
    path = tmp_path / "ledger.jsonl"
    writer = LedgerWriter(path)
    writer.append(dict(GOOD_ROW))
    first_line = path.read_text()
    writer.append(dict(GOOD_ROW, action_id="A(1,2)", speaker="A"))
    assert path.read_text().startswith(first_line)  # prior bytes untouched


def test_ledger_rejects_invalid_row(tmp_path):
    writer = LedgerWriter(tmp_path / "ledger.jsonl")
    with pytest.raises(ValidationError):
        writer.append(dict(GOOD_ROW, kind="bogus"))
    with pytest.raises(ValidationError):
        writer.append({k: v for k, v in GOOD_ROW.items() if k != "score"})
    assert writer.rows == []  # nothing recorded on failure


# ------------------------------------------------------------ snapshots

def test_snapshots_writer(tmp_path):
    snapshots = [{"t": 1, "delta_you": 87.0, "delta_ai": 314.0,
                  "c_you": 87.0, "c_ai": 314.0}]
    write_json_artifact(tmp_path / "snapshots.json", snapshots, "snapshots")
    assert json.loads((tmp_path / "snapshots.json").read_text()) == snapshots

    with pytest.raises(ValidationError):
        write_json_artifact(tmp_path / "snapshots.json",
                            [{"t": 1, "delta_you": 87.0}], "snapshots")


def test_validate_artifact_returns_instance():
    assert validate_artifact(GOOD_ROW, "ledger_row") is GOOD_ROW


# ------------------------------------------- frozen fixture compatibility

def test_fixture_state_loads_read_only():
    state = State.load(FIXTURE_DIR)
    assert len(state.requirements) == 14
    assert len(state.slots) == 5
    assert state.run["last_completed_pair"] == 0  # no run/ dir → fresh run state


def test_fixture_ledger_reads_read_only():
    rows = read_ledger(FIXTURE_DIR / "ledger.jsonl")
    assert len(rows) == 157
