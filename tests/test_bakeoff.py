"""Tier 1 tests for Model Bake-Off harness and S3_BAKEOFF.md report (Step S3.5).

Verifies:
- scripts/run_bakeoff.py executes correctly across all 3 golden chats and 3 configurations.
- Grade outputs for golden_01, c03_coding_short, and c20_coding_short achieve >= 90% match rate.
- Cost metrics adhere to engine/models.yaml price table.
- docs/plans/S3_BAKEOFF.md exists, is up-to-date, and contains required comparison tables.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from engine.models import get_model_price, load_price_table
from scripts.grade_golden import (
    compute_metrics,
    load_extracted_requirements,
    parse_expected_requirements,
)
from scripts.run_bakeoff import CONFIGURATIONS, GOLDEN_CHATS, run_bakeoff

pytestmark = pytest.mark.tier1

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_bakeoff_configurations_defined_in_price_table():
    """Verify every model in the bakeoff configs exists in engine/models.yaml."""
    price_table = load_price_table()
    for cfg_name, cfg in CONFIGURATIONS.items():
        fast_m = cfg["fast_model"]
        main_m = cfg["main_model"]
        in_f, out_f = get_model_price(fast_m, table=price_table)
        in_m, out_m = get_model_price(main_m, table=price_table)
        assert in_f > 0, f"Missing price for fast model {fast_m}"
        assert out_f > 0, f"Missing price for fast model {fast_m}"
        assert in_m > 0, f"Missing price for main model {main_m}"
        assert out_m > 0, f"Missing price for main model {main_m}"


def test_grade_all_three_golden_chats():
    """Verify all 3 golden chats achieve 100% requirement match rate."""
    for chat in GOLDEN_CHATS:
        expected = parse_expected_requirements(chat["expected_path"])
        assert len(expected) >= 6, f"Expected requirements for {chat['id']} must be >= 6"
        extracted = load_extracted_requirements(chat["run_dir"] / "state.json")
        assert len(extracted) >= len(expected), f"Extracted requirements for {chat['id']} must exist"

        grades_file = chat["run_dir"] / "grading.json"
        assert grades_file.is_file(), f"Missing grading.json for {chat['id']}"

        import json
        grades_data = json.loads(grades_file.read_text(encoding="utf-8"))
        metrics = compute_metrics(expected, extracted, grades_data)

        assert metrics["match_rate"] == 100.0, f"{chat['id']} match rate must be 100%"
        assert metrics["spurious_rate"] == 0.0, f"{chat['id']} spurious rate must be 0%"
        assert metrics["miss"] == 0, f"{chat['id']} misses must be 0"


def test_bakeoff_run_and_cost_order():
    """Verify run_bakeoff produces valid metrics and Config A is cheaper than Config C."""
    results = run_bakeoff()
    assert len(results["configurations"]) == 3

    cfg_a = results["configurations"]["Config A (Gemini Ultra-Cheap)"]
    cfg_b = results["configurations"]["Config B (DeepSeek Value)"]
    cfg_c = results["configurations"]["Config C (Quality Frontier Mixed)"]

    assert cfg_a["avg_cost_per_pair"] < 0.010, "Config A must cost under $0.010 per pair"
    assert cfg_b["avg_cost_per_pair"] < 0.015, "Config B must cost under $0.015 per pair"
    assert cfg_c["avg_cost_per_pair"] > cfg_a["avg_cost_per_pair"] * 5, "Config C must be > 5x Config A"

    assert cfg_a["total_pairs"] == 14
    assert cfg_b["total_pairs"] == 14
    assert cfg_c["total_pairs"] == 14


def test_bakeoff_report_file_integrity():
    """Verify docs/plans/S3_BAKEOFF.md exists and contains the required summary matrix."""
    report_path = REPO_ROOT / "docs/plans/S3_BAKEOFF.md"
    assert report_path.is_file(), f"Missing report file: {report_path}"

    content = report_path.read_text(encoding="utf-8")
    assert "# S3 Model Bake-Off Evaluation" in content
    assert "Config A (Gemini Ultra-Cheap)" in content
    assert "Config B (DeepSeek Value)" in content
    assert "Config C (Quality Frontier Mixed)" in content
    assert "golden_01" in content
    assert "c03_coding_short" in content
    assert "c20_coding_short" in content
    assert "gemini-3.1-flash-lite" in content
    assert "gemini-3.5-flash" in content
