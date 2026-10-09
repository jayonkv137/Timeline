"""Tests for scripts/perf_report.py performance measurement and reporting."""

from __future__ import annotations

import pytest
from scripts.perf_report import generate_report_markdown, quantile


@pytest.mark.tier1
def test_quantile_computation() -> None:
    data = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert quantile(data, 0.5) == 20.0 or quantile(data, 0.5) == 30.0
    assert quantile([], 0.5) == 0.0
    assert quantile([42.0], 0.5) == 42.0


@pytest.mark.tier1
def test_generate_report_markdown_content() -> None:
    api_results = {
        "/api/health": {"count": 10, "mean": 1.5, "p50": 1.2, "p90": 2.0, "p95": 2.2, "max": 3.0},
        "/api/chats": {"count": 10, "mean": 3.5, "p50": 3.2, "p90": 4.0, "p95": 4.5, "max": 5.0},
        "/api/chats/c05_research_medium": {"count": 10, "mean": 4.5, "p50": 4.2, "p90": 5.0, "p95": 5.5, "max": 6.0},
    }
    ui_results = {
        "firstLoadMs": 280.0,
        "chatOpenMs": {
            "samples": [70.0, 50.0, 45.0],
            "mean": 55.0,
            "p50": 50.0,
            "p95": 68.0,
        },
        "brainFps": 58.0,
    }

    md = generate_report_markdown(
        api_results=api_results,
        ui_results=ui_results,
        git_branch="s/standalone-v1",
        git_commit="abcdef",
    )

    assert "# S2 Performance & Budget Report" in md
    assert "§6A T3 Budget Scorecard" in md
    assert "App first load" in md
    assert "Open a chat" in md
    assert "Brain frame rate" in md
    assert "280.0 ms" in md
    assert "50.0 ms" in md
    assert "58.0 fps" in md
    assert "PASS" in md
    assert "100% OF PERFORMANCE BUDGETS MET" in md
