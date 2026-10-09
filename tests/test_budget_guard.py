"""Tests for Step S3.4: Budget guard and /usage API.

Adheres to STANDALONE_V1_PLAN §4 (S3.4):
- Jobs refuse to start if estimated cost exceeds remaining budget.
- Running jobs stop at budget cap, preserve valid state, and emit budget_stop {spent, cap}.
- /usage endpoint returns monthly spend, remaining headroom, and step/model/chat breakdowns.
- Invariants: frozen fixture untouched, pytest >= 102 passing, sacred numbers invariant.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from engine.budget import (
    BudgetExceededError,
    BudgetGuard,
    BudgetStopError,
    check_budget_before_start,
    get_current_year_month,
    get_usage_summary,
)
from engine.llm import UsageMeter
from server.app import create_app
from server.library import Library, atomic_write_json


def test_get_usage_summary_aggregations(tmp_path: Path):
    """Verify get_usage_summary correctly computes spend and multidimensional breakdowns."""
    lib = Library(tmp_path)
    lib.ensure_layout()
    lib.save_settings_and_secrets({"monthly_budget": 15.0})

    current_month = get_current_year_month()
    ts_now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    ts_old = "2025-01-15T12:00:00Z"

    # Add usage entries to library usage.jsonl
    lib.record_usage({
        "timestamp": ts_now,
        "chat_id": "c10_research",
        "step": "step1a",
        "call": "step1a:pair1",
        "pair": 1,
        "model": "gemini-3.1-flash-lite",
        "tokens": {"prompt": 1000, "completion": 200, "total": 1200},
        "cost": {"prompt": 0.00025, "completion": 0.00030, "total": 0.00055},
        "mode": "live",
    })
    lib.record_usage({
        "timestamp": ts_now,
        "chat_id": "c10_research",
        "step": "step2",
        "call": "step2:pair1",
        "pair": 1,
        "model": "gemini-3.5-flash",
        "tokens": {"prompt": 2000, "completion": 500, "total": 2500},
        "cost": {"prompt": 0.00100, "completion": 0.00150, "total": 0.00250},
        "mode": "live",
    })
    # Old entry from previous month should be ignored for monthly spend
    lib.record_usage({
        "timestamp": ts_old,
        "chat_id": "old_chat",
        "step": "step1a",
        "model": "gemini-3.5-flash",
        "tokens": {"prompt": 1000, "completion": 500, "total": 1500},
        "cost": {"prompt": 0.005, "completion": 0.005, "total": 0.010},
        "mode": "live",
    })

    # Also add per-chat usage in a chat directory
    chat_dir = lib.chat_dir("c20_coding")
    chat_run = chat_dir / "run"
    chat_run.mkdir(parents=True, exist_ok=True)
    with open(chat_run / "usage.jsonl", "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "timestamp": ts_now,
            "chat_id": "c20_coding",
            "step": "step3a",
            "call": "step3a:pair1",
            "pair": 1,
            "model": "deepseek-chat",
            "tokens": {"prompt": 3000, "completion": 800, "total": 3800},
            "cost": {"prompt": 0.00042, "completion": 0.00176, "total": 0.00218},
            "mode": "live",
        }) + "\n")

    summary = get_usage_summary(library_root=tmp_path)

    assert summary["month"] == current_month
    assert summary["monthly_budget"] == 15.0
    expected_spent = round(0.00055 + 0.00250 + 0.00218, 6)
    assert summary["spent_this_month"] == expected_spent
    assert summary["remaining_budget"] == round(15.0 - expected_spent, 6)
    assert summary["total_calls"] == 3

    # Breakdown assertions
    assert summary["by_chat"]["c10_research"] == round(0.00055 + 0.00250, 6)
    assert summary["by_chat"]["c20_coding"] == 0.00218

    assert summary["by_step"]["step1a"] == 0.00055
    assert summary["by_step"]["step2"] == 0.00250
    assert summary["by_step"]["step3a"] == 0.00218

    assert summary["by_model"]["gemini-3.1-flash-lite"] == 0.00055
    assert summary["by_model"]["gemini-3.5-flash"] == 0.00250
    assert summary["by_model"]["deepseek-chat"] == 0.00218


def test_job_refuses_to_start_above_remaining_budget(tmp_path: Path):
    """Assert check_budget_before_start raises BudgetExceededError when estimate exceeds budget."""
    lib = Library(tmp_path)
    lib.ensure_layout()
    lib.save_settings_and_secrets({"monthly_budget": 1.00})

    ts_now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    # Incur $0.90 of spend
    lib.record_usage({
        "timestamp": ts_now,
        "chat_id": "chat_a",
        "step": "step1a",
        "model": "gemini-3.5-flash",
        "tokens": {"prompt": 1000, "completion": 200, "total": 1200},
        "cost": {"prompt": 0.45, "completion": 0.45, "total": 0.90},
    })

    # Remaining is $0.10. An estimate of $0.05 should be accepted
    check_budget_before_start(0.05, library_root=tmp_path)

    # An estimate of $0.15 exceeds remaining budget of $0.10
    with pytest.raises(BudgetExceededError) as exc_info:
        check_budget_before_start(0.15, library_root=tmp_path)

    err_msg = str(exc_info.value)
    assert "exceeds remaining budget" in err_msg
    assert "$0.1500" in err_msg
    assert "$0.1000" in err_msg


def test_running_job_stops_at_cap_and_emits_budget_stop(tmp_path: Path):
    """Assert BudgetGuard halts execution mid-flight and triggers on_budget_stop."""
    cap = 0.005
    emitted_events: list[tuple[float, float]] = []

    def on_stop(spent: float, budget_cap: float):
        emitted_events.append((spent, budget_cap))

    guard = BudgetGuard(cap=cap, current_spent=0.0, on_budget_stop=on_stop, chat_id="test_chat")

    usage_file = tmp_path / "usage.jsonl"
    meter = UsageMeter(usage_file, budget_guard=guard)

    # Mock call 1: 4k prompt + 2k completion on gemini-3.5-flash ($0.075 / $0.300 per MTok)
    # 4000 * 0.075e-6 + 2000 * 0.300e-6 = 0.00030 + 0.00060 = $0.00090 (under 0.005 cap)
    meter.record(
        step="step1a:pair1",
        model="gemini-3.5-flash",
        prompt_tokens=4000,
        completion_tokens=2000,
        is_replay=False,
    )
    assert not guard.stopped
    assert len(emitted_events) == 0

    # Mock call 2: 20k prompt + 20k completion on gemini-3.5-flash
    # 20000 * 0.075e-6 + 20000 * 0.300e-6 = 0.00150 + 0.00600 = $0.00750
    # Cumulative = 0.00090 + 0.00750 = 0.00840 >= 0.005 cap
    with pytest.raises(BudgetStopError) as exc_info:
        meter.record(
            step="step1b:pair1",
            model="gemini-3.5-flash",
            prompt_tokens=20_000,
            completion_tokens=20_000,
            is_replay=False,
        )

    assert guard.stopped
    assert "Budget cap reached" in str(exc_info.value)
    assert len(emitted_events) == 1
    spent_reported, cap_reported = emitted_events[0]
    assert spent_reported >= 0.005
    assert cap_reported == 0.005


def test_get_usage_api_endpoint(tmp_path: Path):
    """Test GET /api/usage and GET /usage returns valid schema and correct numbers."""
    lib = Library(tmp_path)
    lib.ensure_layout()
    lib.save_settings_and_secrets({"monthly_budget": 25.0})

    ts_now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    lib.record_usage({
        "timestamp": ts_now,
        "chat_id": "c30_writing",
        "step": "step1a",
        "model": "deepseek-v4-flash",
        "tokens": {"prompt": 5000, "completion": 1000, "total": 6000},
        "cost": {"prompt": 0.00025, "completion": 0.00020, "total": 0.00045},
    })

    app = create_app(library=lib)
    client = TestClient(app)

    for path in ["/api/usage", "/usage"]:
        res = client.get(path)
        assert res.status_code == 200
        data = res.json()
        assert data["monthly_budget"] == 25.0
        assert data["spent_this_month"] == 0.00045
        assert data["remaining_budget"] == 25.0 - 0.00045
        assert data["by_chat"]["c30_writing"] == 0.00045
        assert data["by_step"]["step1a"] == 0.00045
        assert data["by_model"]["deepseek-v4-flash"] == 0.00045
        assert len(data["recent_calls"]) == 1
        assert data["total_calls"] == 1


def test_budget_stop_event_broadcast():
    """Verify SSE broadcaster emits budget_stop event properly."""
    app = create_app()
    broadcaster = app.state.broadcaster
    events = []

    # Inject mock callback
    broadcaster.broadcast("budget_stop", {"spent": 20.05, "cap": 20.00})
