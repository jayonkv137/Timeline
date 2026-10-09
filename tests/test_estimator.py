"""Tests for dialogue cost and token estimator (STANDALONE_V1_PLAN §4 Step S3.2).

Verifies that estimate(dialogue) -> {low, high} is calibrated within ±35% across
all 10 recorded corpus chats, and that interval bounds strictly cover ground truth.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from engine.estimator import estimate

REPO_ROOT = Path(__file__).resolve().parent.parent

CORPUS_CHATS = [
    "c03_coding_short",
    "c04_writing_short",
    "c05_research_medium",
    "c07_research_short",
    "c10_research_short",
    "c16_research_short",
    "c17_research_short",
    "c20_coding_short",
    "c27_creative_short",
    "c30_creative_short",
]


@pytest.mark.tier1
def test_estimator_within_35_pct_on_all_10_chats() -> None:
    """The estimate is within ±35% on the 10 chats, measured against recorded runs."""
    results = []

    for chat_id in CORPUS_CHATS:
        diag_path = REPO_ROOT / f"data/corpus/{chat_id}/dialogue.json"
        monitor_path = REPO_ROOT / f"data/chats/{chat_id}/run/llm_monitor.txt"

        assert diag_path.is_file(), f"Missing dialogue: {diag_path}"
        assert monitor_path.is_file(), f"Missing monitor: {monitor_path}"

        # Ground truth actual tokens from recorded run
        actual_tokens = sum(
            int(m) for m in re.findall(r"total=(\d+)", monitor_path.read_text(encoding="utf-8"))
        )
        assert actual_tokens > 0, f"Actual tokens for {chat_id} must be > 0"

        # Compute estimate
        est = estimate(diag_path)

        expected_tokens = est["expected"]["tokens"]
        low_tokens = est["low"]["tokens"]
        high_tokens = est["high"]["tokens"]

        error_pct = abs(expected_tokens - actual_tokens) / actual_tokens

        # Plan requirement: within ±35%
        assert (
            error_pct <= 0.35
        ), f"Chat {chat_id} error {error_pct * 100:.2f}% exceeds ±35% budget (actual={actual_tokens}, est={expected_tokens})"

        # Interval bounds check
        assert (
            low_tokens <= actual_tokens <= high_tokens
        ), f"Chat {chat_id} actual {actual_tokens} outside [{low_tokens}, {high_tokens}]"

        results.append((chat_id, actual_tokens, expected_tokens, error_pct))

    # Assert mean error across corpus is comfortably low (< 25%)
    mean_err = sum(r[3] for r in results) / len(results)
    assert mean_err < 0.25, f"Mean corpus error {mean_err * 100:.2f}% should be < 25%"


@pytest.mark.tier1
def test_estimator_schema_and_types() -> None:
    diag_path = REPO_ROOT / "data/corpus/c10_research_short/dialogue.json"
    est = estimate(diag_path)

    # Top-level contracts
    assert "low" in est
    assert "high" in est
    assert "expected" in est
    assert "tokens" in est
    assert "cost" in est
    assert "by_step" in est

    # Access patterns
    assert isinstance(est["low"]["tokens"], int)
    assert isinstance(est["low"]["cost"], float)
    assert isinstance(est["high"]["tokens"], int)
    assert isinstance(est["high"]["cost"], float)

    # Comparison / float-int conversion compatibility
    assert float(est["low"]) == est["low"]["cost"]
    assert int(est["low"]) == est["low"]["tokens"]
    assert est["low"] < est["high"]

    # Step breakdown presence
    for step in ["1a", "1b", "1c", "2", "3a", "3b"]:
        assert step in est["by_step"]
        assert "tokens" in est["by_step"][step]
        assert "cost" in est["by_step"][step]
        assert "model" in est["by_step"][step]


@pytest.mark.tier1
@pytest.mark.tier1
def test_estimator_cheap_models_reduce_cost() -> None:
    diag_path = REPO_ROOT / "data/corpus/c10_research_short/dialogue.json"

    est_standard = estimate(diag_path, model_fast="gemini-3.1-flash-lite", model_main="gemini-3.5-flash")
    est_lite = estimate(diag_path, model_fast="gemini-3.5-flash-lite", model_main="gemini-3.5-flash-lite")
    est_oss = estimate(diag_path, model_fast="gpt-oss-120b", model_main="gpt-oss-120b")
    est_claude = estimate(diag_path, model_fast="claude-3-5-haiku", model_main="claude-3-7-sonnet")

    assert est_standard["tokens"]["expected"] == est_lite["tokens"]["expected"] == est_claude["tokens"]["expected"]
    assert est_oss["cost"]["expected"] < est_standard["cost"]["expected"]
    assert est_lite["cost"]["expected"] < est_standard["cost"]["expected"]
    assert est_standard["cost"]["expected"] < est_claude["cost"]["expected"]


@pytest.mark.tier1
def test_estimator_input_types() -> None:
    diag_path = REPO_ROOT / "data/corpus/c17_research_short/dialogue.json"
    dialogue_list = json.loads(diag_path.read_text(encoding="utf-8"))
    dialogue_json_str = json.dumps(dialogue_list)

    est_path = estimate(diag_path)
    est_list = estimate(dialogue_list)
    est_str = estimate(dialogue_json_str)

    assert est_path["expected"]["tokens"] == est_list["expected"]["tokens"]
    assert est_path["expected"]["tokens"] == est_str["expected"]["tokens"]


@pytest.mark.tier1
def test_estimator_empty_dialogue() -> None:
    est = estimate([])
    assert est["tokens"]["expected"] == 0
    assert est["cost"]["expected"] == 0.0
    assert est["pairs"] == 0
