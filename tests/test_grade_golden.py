"""Tier 1 tests for the golden chat grading harness (E1.S1).

Verifies scripts/grade_golden.py:
- Parses expected requirements correctly from expected.md.
- Handles empty extraction runs without crashing, reporting 0 found and N missed.
- Computes match, miss, spurious, split, and merged metrics accurately.
"""
import json
from pathlib import Path

import pytest

from scripts import grade_golden

pytestmark = pytest.mark.tier1

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_EXPECTED = REPO_ROOT / "data/corpus/golden_01/expected.md"


def test_parse_expected_requirements():
    """Verify parsing of ground-truth requirements from expected.md."""
    reqs = grade_golden.parse_expected_requirements(GOLDEN_EXPECTED)
    assert len(reqs) == 6
    req_ids = [r["id"] for r in reqs]
    assert req_ids == ["Req_01", "Req_02", "Req_03", "Req_04", "Req_05", "Req_06"]
    assert "Portfolio about page revision" in reqs[0]["text"]
    assert "45–60s" in reqs[1]["text"]


def test_empty_extraction_run(tmp_path):
    """Verify empty extraction directory reports 0 found and all missed."""
    reqs = grade_golden.parse_expected_requirements(GOLDEN_EXPECTED)
    empty_state = tmp_path / "state.json"
    empty_state.write_text(json.dumps({"requirements": []}), encoding="utf-8")

    extracted = grade_golden.load_extracted_requirements(empty_state)
    assert extracted == []

    metrics = grade_golden.compute_metrics(reqs, extracted, {})
    assert metrics["expected"] == 6
    assert metrics["found"] == 0
    assert metrics["match"] == 0
    assert metrics["miss"] == 6
    assert metrics["spurious"] == 0
    assert metrics["match_rate"] == 0.0
    assert metrics["spurious_rate"] == 0.0

    summary = grade_golden.format_summary_report(metrics)
    assert "requirements expected : 6" in summary
    assert "requirements found    : 0" in summary
    assert "miss                  : 6" in summary


def test_compute_metrics_with_grades():
    """Verify metrics calculation across match, spurious, split, merged categories."""
    expected = [
        {"id": "Req_01", "text": "Requirement 1"},
        {"id": "Req_02", "text": "Requirement 2"},
        {"id": "Req_03", "text": "Requirement 3"},
        {"id": "Req_04", "text": "Requirement 4"},
    ]
    extracted = [
        {"outcome_id": "o1", "req_id": "r1", "text": "Matches Req 1"},
        {"outcome_id": "o1", "req_id": "r2", "text": "Split Req 2 Part A"},
        {"outcome_id": "o1", "req_id": "r3", "text": "Split Req 2 Part B"},
        {"outcome_id": "o1", "req_id": "r4", "text": "Spurious advice item"},
    ]
    grades = {
        "extracted_marks": {
            "o1||r1": {"status": "match", "target": "Req_01"},
            "o1||r2": {"status": "split", "target": "Req_02"},
            "o1||r3": {"status": "split", "target": "Req_02"},
            "o1||r4": {"status": "spurious"},
        }
    }
    metrics = grade_golden.compute_metrics(expected, extracted, grades)
    assert metrics["expected"] == 4
    assert metrics["found"] == 4
    assert metrics["match"] == 1
    assert metrics["split"] == 2
    assert metrics["spurious"] == 1
    # Req_01 and Req_02 are accounted for; Req_03 and Req_04 are missed
    assert metrics["miss"] == 2
    # match_rate = 2 accounted / 4 expected = 50.0%
    assert metrics["match_rate"] == 50.0
    # spurious_rate = 1 spurious / 4 found = 25.0%
    assert metrics["spurious_rate"] == 25.0
