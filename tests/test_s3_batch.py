"""Tests for scripts/run_s3_batch.py — S3.6 batch extraction & performance reporting."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from engine.estimator import estimate
from scripts.run_s3_batch import (
    REPORT_PATH,
    TARGET_CHATS,
    generate_report_markdown,
    parse_usage_records,
)


@pytest.mark.tier1
def test_target_chats_specification():
    """Verify target chats match Step S3.6: 3 never-processed chats (short, medium, long)."""
    assert len(TARGET_CHATS) == 3
    ids = [c["id"] for c in TARGET_CHATS]
    assert "c45_writing_medium" in ids
    assert "c38_planning_medium" in ids
    assert "c48_learning_long" in ids

    # Check dialogues exist in data/corpus
    repo_root = Path(__file__).resolve().parent.parent
    for c in TARGET_CHATS:
        d_path = repo_root / f"data/corpus/{c['id']}/dialogue.json"
        assert d_path.is_file(), f"Missing dialogue for {c['id']}"


@pytest.mark.tier1
def test_preflight_estimates_under_budget():
    """Verify combined pre-flight estimate across the 3 chats is under $0.50 (well below $1.00 ceiling)."""
    repo_root = Path(__file__).resolve().parent.parent
    total_expected_cost = 0.0
    total_pairs = 0

    for c in TARGET_CHATS:
        d_path = repo_root / f"data/corpus/{c['id']}/dialogue.json"
        est = estimate(d_path)
        total_expected_cost += est.expected_cost
        total_pairs += est.pairs

    assert total_pairs == 40
    # Expected cost must be between $0.20 and $0.40, and strictly below $1.00
    assert 0.20 <= total_expected_cost <= 0.40
    assert total_expected_cost < 1.00


@pytest.mark.tier1
def test_generate_report_markdown_formatting():
    """Verify S3 report markdown structure and required sections."""
    fake_results = [
        {
            "id": "c45_writing_medium",
            "length_category": "Short",
            "description": "Short test chat",
            "pairs_processed": 6,
            "total_time": 12.5,
            "wall_time_per_pair": [2.0] * 6,
            "tokens_per_pair": [1000] * 6,
            "reqs_created": 4,
            "slots": {"opened": 2, "resolved": 2, "abandoned": 0},
            "invariants_pass": True,
            "failed_invariants": [],
            "estimate_tokens": 200000,
            "estimate_cost": 0.040,
            "actual_tokens": 195000,
            "actual_cost": 0.038,
            "usage_records": [
                {
                    "step": "1a",
                    "model": "gemini-3.1-flash-lite",
                    "tokens": {"prompt": 500, "completion": 50, "total": 550},
                    "cost": {"total": 0.00005},
                    "duration_ms": 1200,
                },
                {
                    "step": "1b",
                    "model": "gemini-3.5-flash",
                    "tokens": {"prompt": 800, "completion": 100, "total": 900},
                    "cost": {"total": 0.00010},
                    "duration_ms": 1500,
                },
            ],
            "root_title": "Telefoninterview-Termin",
            "atoms_count": 8,
        },
        {
            "id": "c38_planning_medium",
            "length_category": "Medium",
            "description": "Medium test chat",
            "pairs_processed": 13,
            "total_time": 25.0,
            "wall_time_per_pair": [2.0] * 13,
            "tokens_per_pair": [2000] * 13,
            "reqs_created": 8,
            "slots": {"opened": 4, "resolved": 3, "abandoned": 1},
            "invariants_pass": True,
            "failed_invariants": [],
            "estimate_tokens": 450000,
            "estimate_cost": 0.085,
            "actual_tokens": 440000,
            "actual_cost": 0.082,
            "usage_records": [],
            "root_title": "Room rental",
            "atoms_count": 16,
        },
        {
            "id": "c48_learning_long",
            "length_category": "Long",
            "description": "Long test chat",
            "pairs_processed": 21,
            "total_time": 45.0,
            "wall_time_per_pair": [2.1] * 21,
            "tokens_per_pair": [3000] * 21,
            "reqs_created": 12,
            "slots": {"opened": 5, "resolved": 5, "abandoned": 0},
            "invariants_pass": True,
            "failed_invariants": [],
            "estimate_tokens": 900000,
            "estimate_cost": 0.165,
            "actual_tokens": 890000,
            "actual_cost": 0.160,
            "usage_records": [],
            "root_title": "German A1 review",
            "atoms_count": 28,
        },
    ]

    md = generate_report_markdown(
        batch_results=fake_results,
        global_spent=0.280,
        budget_cap=1.00,
        git_branch="s/standalone-v1",
        git_commit="abcdef",
    )

    assert "# S3 Cost and Performance Milestone Report (S3.6)" in md
    assert "§4 S3.6 Executive Scorecard" in md
    assert "Pre-Flight Estimate vs. Actual Measured Spend" in md
    assert "Cost & Latency Per Pair by Pipeline Step and Model" in md
    assert "Token Growth & Latency Curves Across Dialogue Pairs" in md
    assert "Per-Chat Structural & Quality Verification" in md
    assert "ALL S3.6 BUDGET & PERFORMANCE CRITERIA MET" in md
    assert "$0.2800" in md
    assert "c45_writing_medium" in md
    assert "c38_planning_medium" in md
    assert "c48_learning_long" in md


@pytest.mark.tier1
def test_parse_usage_records(tmp_path: Path):
    """Verify parse_usage_records reads jsonl rows correctly."""
    u_file = tmp_path / "usage.jsonl"
    entries = [
        {"step": "1a", "model": "gemini-3.1-flash-lite", "tokens": {"total": 100}, "cost": {"total": 0.0001}},
        {"step": "1b", "model": "gemini-3.5-flash", "tokens": {"total": 200}, "cost": {"total": 0.0002}},
    ]
    u_file.write_text("\n".join(json.dumps(e) for e in entries) + "\n")

    parsed = parse_usage_records(u_file)
    assert len(parsed) == 2
    assert parsed[0]["step"] == "1a"
    assert parsed[1]["tokens"]["total"] == 200
