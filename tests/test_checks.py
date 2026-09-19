"""Tier 1 tests for engine/checks.py and production runtime invariants (§11.4, TEST_STRATEGY §6).

Verifies:
1. engine/checks.py imports invariant functions directly from tests/invariants.py (no duplication).
2. run_pair_checks passes on valid state and ledger rows.
3. run_pair_checks catches deliberate invariant violations (inv_02, inv_05, inv_06, inv_07, inv_10).
4. write_status and write_report generate exact schema-compliant files.
5. run_chat executes multi-pair pipeline with checks after each pair.
6. Deliberate invariant violation immediately halts the pipeline, writes run/status.json
   naming the invariant, and emits run/report.json with the failure.
"""
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from engine import checks
from engine.checks import (
    CheckResult,
    InvariantViolationError,
    run_pair_checks,
    write_report,
    write_status,
)
from engine.config import Config
from engine.pipeline import process_pair, run_chat
from engine.state import State
from tests import invariants

pytestmark = pytest.mark.tier1

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "data" / "chats" / "fixture_pair1"


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


def test_invariants_direct_import():
    """Verify engine/checks imports the exact same function objects from tests/invariants."""
    check_pairs = [
        ("inv_01_schema_valid", checks.inv_01_schema_valid, invariants.inv_01_schema_valid),
        ("inv_02_action_ids", checks.inv_02_action_ids, invariants.inv_02_action_ids),
        ("inv_03_ledger_references_exist", checks.inv_03_ledger_references_exist, invariants.inv_03_ledger_references_exist),
        ("inv_04_action_maps_to_one_outcome", checks.inv_04_action_maps_to_one_outcome, invariants.inv_04_action_maps_to_one_outcome),
        ("inv_05_no_duplicate_ledger_rows", checks.inv_05_no_duplicate_ledger_rows, invariants.inv_05_no_duplicate_ledger_rows),
        ("inv_06_outcome_tree", checks.inv_06_outcome_tree, invariants.inv_06_outcome_tree),
        ("inv_07_requirement_has_creation", checks.inv_07_requirement_has_creation, invariants.inv_07_requirement_has_creation),
        ("inv_08_requirement_created_at_pair", checks.inv_08_requirement_created_at_pair, invariants.inv_08_requirement_created_at_pair),
        ("inv_09_slot_status_and_inactivity", checks.inv_09_slot_status_and_inactivity, invariants.inv_09_slot_status_and_inactivity),
        ("inv_10_scores_positive", checks.inv_10_scores_positive, invariants.inv_10_scores_positive),
        ("inv_17_append_only", checks.inv_17_append_only, invariants.inv_17_append_only),
        ("inv_21_provenance", checks.inv_21_provenance, invariants.inv_21_provenance),
    ]
    for name, func_chk, func_inv in check_pairs:
        assert func_chk is func_inv, f"{name} in engine/checks is not the identical object from tests/invariants"


def test_run_pair_checks_passes_on_fixture():
    """Verify run_pair_checks returns healthy=True and empty violations on fixture_pair1."""
    with open(FIXTURE_DIR / "state.json", "r", encoding="utf-8") as f:
        state = json.load(f)
    with open(FIXTURE_DIR / "ledger.jsonl", "r", encoding="utf-8") as f:
        ledger = [json.loads(line) for line in f if line.strip()]
    with open(FIXTURE_DIR / "dialogue.json", "r", encoding="utf-8") as f:
        dialogue = json.load(f)

    result = run_pair_checks(
        state=state,
        ledger_rows=ledger,
        dialogue=dialogue,
        current_pair=1,
    )
    assert result.healthy is True
    assert result.failed == []
    assert result.violations == []
    assert "inv_01" in result.passed
    assert "inv_02" in result.passed
    assert "inv_03" in result.passed
    assert "inv_05" in result.passed
    assert "inv_06" in result.passed
    assert "inv_07" in result.passed
    assert "inv_08" in result.passed
    assert "inv_09" in result.passed
    assert "inv_10" in result.passed


def test_run_pair_checks_detects_deliberate_violations():
    """Verify run_pair_checks flags violations when data is deliberately corrupted."""
    with open(FIXTURE_DIR / "state.json", "r", encoding="utf-8") as f:
        state = json.load(f)
    with open(FIXTURE_DIR / "ledger.jsonl", "r", encoding="utf-8") as f:
        ledger = [json.loads(line) for line in f if line.strip()]

    # 1. Deliberate duplicate ledger row (inv_05)
    corrupted_ledger = ledger + [ledger[0]]
    res_inv05 = run_pair_checks(state=state, ledger_rows=corrupted_ledger, current_pair=1)
    assert res_inv05.healthy is False
    assert "inv_05" in res_inv05.failed
    assert any("inv_05:" in v for v in res_inv05.violations)

    # 2. Deliberate bad action ID format (inv_02)
    corrupted_state = json.loads(json.dumps(state))
    corrupted_state["actions"].append({"id": "BAD_ID", "type": "Describe", "role": "SHAPER", "text": "bad", "evidence_quote": "bad"})
    res_inv02 = run_pair_checks(state=corrupted_state, ledger_rows=ledger, current_pair=1)
    assert res_inv02.healthy is False
    assert "inv_02" in res_inv02.failed

    # 3. Deliberate non-positive score (inv_10)
    corrupted_scores_ledger = json.loads(json.dumps(ledger))
    corrupted_scores_ledger[0]["score"] = -1.0
    res_inv10 = run_pair_checks(state=state, ledger_rows=corrupted_scores_ledger, current_pair=1)
    assert res_inv10.healthy is False
    assert "inv_10" in res_inv10.failed

    # 4. Deliberate missing creation action (inv_07)
    corrupted_reqs_state = json.loads(json.dumps(state))
    corrupted_reqs_state["requirements"].append({
        "outcome_id": "outcome 1",
        "req_id": "req 99",
        "text": "orphaned requirement",
        "created_at_pair": 1,
        "creation_action_ids": [],
    })
    res_inv07 = run_pair_checks(state=corrupted_reqs_state, ledger_rows=ledger, current_pair=1)
    assert res_inv07.healthy is False
    assert "inv_07" in res_inv07.failed


def test_write_status_and_read(tmp_path):
    """Verify write_status correctly formats healthy and unhealthy status.json files."""
    # Healthy status
    p1 = write_status(tmp_path, healthy=True, pair_number=1, violations=[])
    assert p1.exists()
    with open(p1) as f:
        data = json.load(f)
    assert data["healthy"] is True
    assert data["pair"] == 1
    assert data["halted_at_pair"] is None
    assert data["violation"] is None
    assert data["violations"] == []

    # Unhealthy status
    p2 = write_status(
        tmp_path,
        healthy=False,
        pair_number=2,
        violations=["inv_05: duplicate ledger row at index 5"],
    )
    with open(p2) as f:
        data = json.load(f)
    assert data["healthy"] is False
    assert data["pair"] == 2
    assert data["halted_at_pair"] == 2
    assert data["violation"] == "inv_05: duplicate ledger row at index 5"
    assert data["violations"] == ["inv_05: duplicate ledger row at index 5"]


def test_write_report_schema_and_contents(tmp_path):
    """Verify write_report adheres to TEST_STRATEGY §6 schema."""
    state = State()
    state.requirements = [
        {"outcome_id": "o1", "req_id": "r1", "text": "req 1", "created_at_pair": 1, "creation_action_ids": ["U(1,1)"]},
        {"outcome_id": "o1", "req_id": "r2", "text": "req 2", "created_at_pair": 2, "creation_action_ids": ["U(2,1)"]},
    ]
    state.slots = [
        {"slot_id": "s1", "outcome_id": "o1", "status": "open", "created_at_pair": 1, "creation_action_ids": ["U(1,2)"]},
        {"slot_id": "s2", "outcome_id": "o1", "status": "resolved", "created_at_pair": 1, "creation_action_ids": ["U(1,3)"], "resolved_into": "r1"},
        {"slot_id": "s3", "outcome_id": "o1", "status": "abandoned", "created_at_pair": 1, "creation_action_ids": ["U(1,4)"]},
    ]

    report_path = write_report(
        out_dir=tmp_path,
        chat_id="test_chat",
        pairs_processed=2,
        wall_time_per_pair=[1.5, 2.1],
        tokens_per_pair=[1200, 1850],
        llm_calls=8,
        retries=1,
        cache_hits=0,
        state=state,
        checks_passed=["inv_01", "inv_02", "inv_03"],
        checks_failed=[],
        final={"direction": [30.0, 70.0], "decisions": [2, 4], "mode": "COPILOT"},
    )

    assert report_path.exists()
    with open(report_path) as f:
        rep = json.load(f)

    assert rep["chat_id"] == "test_chat"
    assert rep["pairs_processed"] == 2
    assert rep["wall_time_per_pair"] == [1.5, 2.1]
    assert rep["tokens_per_pair"] == [1200, 1850]
    assert rep["llm_calls"] == 8
    assert rep["retries"] == 1
    assert rep["cache_hits"] == 0
    assert rep["requirements_created"] == 2
    assert rep["slots"] == {"opened": 3, "resolved": 1, "abandoned": 1}
    assert rep["checks"] == {"passed": ["inv_01", "inv_02", "inv_03"], "failed": []}
    assert rep["final"] == {"direction": [30.0, 70.0], "decisions": [2, 4], "mode": "COPILOT"}


def test_run_chat_end_to_end_healthy(tmp_path):
    """Verify run_chat processes a 2-pair chat, runs checks after each pair, and generates report.json."""
    config = make_test_config()
    mock_client = MagicMock()
    mock_client.call_count = 6
    mock_client.retry_count = 0
    mock_client.total_tokens = 3200
    mock_client.cache_hits = 0

    dialogue = [
        {"pair": 1, "speaker": "user", "text": "I want to build a portfolio website."},
        {"pair": 1, "speaker": "ai", "text": "I can help build a portfolio website."},
        {"pair": 2, "speaker": "user", "text": "Make it dark mode with neon accents."},
        {"pair": 2, "speaker": "ai", "text": "Added dark mode with neon accents."},
    ]

    # Pair 1 mock responses
    p1_step1a = {
        "actions": [{
            "turn id": "U(1,1)",
            "action type": "Describe",
            "action text": "Portfolio website",
            "role": "SHAPER",
            "evidence quote": "portfolio website",
        }]
    }
    p1_step1b = {
        "outcomes": [{
            "outcome id": "outcome 1",
            "outcome": "Portfolio Website",
            "turn id": "U(1,1)",
            "parent outcome id": None,
            "related outcome ids": [],
        }],
        "action to outcome": {"U(1,1)": "outcome 1"},
        "dialogue summary": "User wants a portfolio website.",
    }
    p1_step1c = {
        "intentions": [{"intention id": "intention 1", "intention": "Build the portfolio"}],
        "outcome to intention": [{"outcome id": "outcome 1", "intention id": "intention 1"}],
    }
    p1_step2 = {
        "requirement ops": [{
            "op": "create",
            "bound outcome id": "outcome 1",
            "req id": "req 1",
            "creation action ids": ["U(1,1)"],
            "fields": {
                "text": "Portfolio site",
                "type": "task",
            },
        }],
        "open_slot ops": [],
    }
    # Step 3 Trigger A for req 1 (no preceding actions since U(1,1) is origin)
    p1_step3a = {"preceding labels": [], "subsequent labels": []}

    # Pair 2 mock responses
    p2_step1a = {
        "actions": [{
            "turn id": "U(2,1)",
            "action type": "Describe",
            "action text": "Dark mode neon",
            "role": "SHAPER",
            "evidence quote": "dark mode with neon accents",
        }]
    }
    p2_step1b = {
        "outcomes": [{
            "outcome id": "outcome 1",
            "outcome": "Portfolio Website",
            "turn id": "U(1,1)",
            "parent outcome id": None,
            "related outcome ids": [],
        }],
        "action to outcome": {"U(1,1)": "outcome 1", "U(2,1)": "outcome 1"},
        "dialogue summary": "User wants dark mode with neon accents.",
    }
    p2_step1c = {
        "intentions": [{"intention id": "intention 1", "intention": "Add dark mode"}],
        "outcome to intention": [{"outcome id": "outcome 1", "intention id": "intention 1"}],
    }
    p2_step2 = {
        "requirement ops": [{
            "op": "create",
            "bound outcome id": "outcome 1",
            "req id": "req 2",
            "creation action ids": ["U(2,1)"],
            "fields": {
                "text": "Dark mode with neon",
                "type": "task",
            },
        }],
        "open_slot ops": [],
    }
    # Step 3 Trigger A for req 2
    p2_step3a = {
        "preceding labels": [
            {"index": 0, "action id": "U(1,1)", "relationship type": "IMPLICIT CONNECTION", "relationship score": 1.0, "contribution role": "SHAPER"}
        ],
        "subsequent labels": [],
    }
    # Step 3 Trigger B for req 1
    p2_step3b = {
        "labels": [
            {"req id": "req 1", "action id": "U(2,1)", "relationship type": "SUBSEQUENT IMPL", "relationship score": 2.0, "contribution role": "SHAPER"}
        ]
    }

    mock_client.call_json.side_effect = [
        # Pair 1: 1a, 1b, 1c, 2
        p1_step1a, p1_step1b, p1_step1c, p1_step2,
        # Pair 2: 1a, 1b, 1c, 2, 3a, 3b
        p2_step1a, p2_step1b, p2_step1c, p2_step2, p2_step3a, p2_step3b,
    ]

    out_dir = tmp_path / "chat_run"
    report = run_chat(
        client=mock_client,
        config=config,
        chat_id="test_healthy_run",
        dialogue=dialogue,
        out_dir=out_dir,
    )

    # Status file
    status_path = out_dir / "run" / "status.json"
    assert status_path.exists()
    with open(status_path) as f:
        status_data = json.load(f)
    assert status_data["healthy"] is True
    assert status_data["pair"] == 2
    assert status_data["violations"] == []

    # Report file
    report_path = out_dir / "run" / "report.json"
    assert report_path.exists()
    with open(report_path) as f:
        rep_data = json.load(f)
    assert rep_data["chat_id"] == "test_healthy_run"
    assert rep_data["pairs_processed"] == 2
    assert len(rep_data["wall_time_per_pair"]) == 2
    assert rep_data["requirements_created"] == 2
    assert rep_data["checks"]["failed"] == []
    assert "inv_01" in rep_data["checks"]["passed"]
    assert "inv_05" in rep_data["checks"]["passed"]


def test_deliberate_violation_halts_pipeline_and_names_invariant(tmp_path):
    """Verify that a deliberate invariant violation injected during pair 2:

    1. Stops the pipeline run immediately.
    2. Raises InvariantViolationError.
    3. Writes run/status.json with healthy=false naming the invariant.
    4. Emits run/report.json noting the failed check.
    """
    config = make_test_config()
    mock_client = MagicMock()
    mock_client.call_count = 8
    mock_client.retry_count = 0
    mock_client.total_tokens = 2500
    mock_client.cache_hits = 0

    dialogue = [
        {"pair": 1, "speaker": "user", "text": "Build a game."},
        {"pair": 1, "speaker": "ai", "text": "Game plan ready."},
        {"pair": 2, "speaker": "user", "text": "Add a scoreboard."},
        {"pair": 2, "speaker": "ai", "text": "Scoreboard added."},
        {"pair": 3, "speaker": "user", "text": "Add multiplayer."},
        {"pair": 3, "speaker": "ai", "text": "Multiplayer added."},
    ]

    # Pair 1 mock responses (healthy)
    p1_step1a = {
        "actions": [{
            "turn id": "U(1,1)",
            "action type": "Describe",
            "action text": "Game",
            "role": "SHAPER",
            "evidence quote": "game",
        }]
    }
    p1_step1b = {
        "outcomes": [{
            "outcome id": "outcome 1",
            "outcome": "Game Project",
            "turn id": "U(1,1)",
            "parent outcome id": None,
            "related outcome ids": [],
        }],
        "action to outcome": {"U(1,1)": "outcome 1"},
        "dialogue summary": "Game project.",
    }
    p1_step1c = {
        "intentions": [{"intention id": "intention 1", "intention": "Make game"}],
        "outcome to intention": [{"outcome id": "outcome 1", "intention id": "intention 1"}],
    }
    p1_step2 = {
        "requirement ops": [{
            "op": "create",
            "bound outcome id": "outcome 1",
            "req id": "req 1",
            "creation action ids": ["U(1,1)"],
            "fields": {
                "text": "Core game loop",
                "type": "task",
            },
        }],
        "open_slot ops": [],
    }

    # Pair 2 mock responses with DELIBERATE VIOLATION:
    # We deliberately create a duplicate ledger row at pair 2 in step 3 trigger a (violating inv_05)
    p2_step1a = {
        "actions": [{
            "turn id": "U(2,1)",
            "action type": "Propose",
            "action text": "Scoreboard",
            "role": "EXECUTOR",
            "evidence quote": "scoreboard",
        }]
    }
    p2_step1b = {
        "outcomes": [{
            "outcome id": "outcome 1",
            "outcome": "Game Project",
            "turn id": "U(1,1)",
            "parent outcome id": None,
            "related outcome ids": [],
        }],
        "action to outcome": {"U(1,1)": "outcome 1", "U(2,1)": "outcome 1"},
        "dialogue summary": "Add scoreboard.",
    }
    p2_step1c = {
        "intentions": [{"intention id": "intention 1", "intention": "Scoreboard"}],
        "outcome to intention": [{"outcome id": "outcome 1", "intention id": "intention 1"}],
    }
    p2_step2 = {
        "requirement ops": [{
            "op": "create",
            "bound outcome id": "outcome 1",
            "req id": "req 2",
            "creation action ids": ["U(2,1)"],
            "fields": {
                "text": "Scoreboard requirement",
                "type": "task",
            },
        }],
        "open_slot ops": [],
    }
    # Deliberately return two identical scores for the exact same action and requirement
    p2_step3a = {
        "preceding labels": [
            {"index": 0, "action id": "U(1,1)", "relationship type": "IMPLICIT CONNECTION", "relationship score": 1.0, "contribution role": "SHAPER"},
            {"index": 0, "action id": "U(1,1)", "relationship type": "IMPLICIT CONNECTION", "relationship score": 1.0, "contribution role": "SHAPER"},
        ],
        "subsequent labels": [],
    }
    p2_step3b = {"labels": []}

    mock_client.call_json.side_effect = [
        # Pair 1: 1a, 1b, 1c, 2
        p1_step1a, p1_step1b, p1_step1c, p1_step2,
        # Pair 2: 1a, 1b, 1c, 2, 3a, 3b
        p2_step1a, p2_step1b, p2_step1c, p2_step2, p2_step3a, p2_step3b,
    ]

    out_dir = tmp_path / "chat_corrupt"

    with pytest.raises(InvariantViolationError) as exc_info:
        run_chat(
            client=mock_client,
            config=config,
            chat_id="test_corrupt_run",
            dialogue=dialogue,
            out_dir=out_dir,
            stop_on_violation=True,
        )

    # InvariantViolationError must name the failed check
    assert "inv_05" in exc_info.value.failed_checks

    # Verify status.json was written and names the invariant
    status_path = out_dir / "run" / "status.json"
    assert status_path.exists(), "status.json must exist"
    with open(status_path) as f:
        status_data = json.load(f)

    assert status_data["healthy"] is False
    assert status_data["halted_at_pair"] == 2
    assert status_data["violation"] is not None
    assert "inv_05" in status_data["violation"]

    # Verify report.json was emitted noting the failure
    report_path = out_dir / "run" / "report.json"
    assert report_path.exists(), "report.json must be emitted even when halted"
    with open(report_path) as f:
        rep_data = json.load(f)

    assert rep_data["chat_id"] == "test_corrupt_run"
    assert rep_data["pairs_processed"] == 1  # pair 1 succeeded, halted at pair 2
    assert "inv_05" in rep_data["checks"]["failed"]
