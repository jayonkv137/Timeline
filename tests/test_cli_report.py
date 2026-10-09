"""Tier 1 tests for engine report generation and CLI (STANDALONE_V1_PLAN §4 Step S1.7).

Verifies:
1. generate_chat_report() succeeds across all 10 prototype chats and renders valid Markdown.
2. python -m engine report <chat> CLI prints report to stdout.
3. python -m engine report <chat> --output <path> CLI writes to file.
4. Nonexistent chat identifier returns error code 1.
5. AG+ sacred fixture numbers remain invariant.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from engine.__main__ import main as cli_main
from engine.report import generate_chat_report

pytestmark = pytest.mark.tier1

REPO_ROOT = Path(__file__).resolve().parent.parent
CHATS_DIR = REPO_ROOT / "data" / "chats"
FIXTURE_DIR = CHATS_DIR / "fixture_pair1"

PROTOTYPE_CHATS = [
    "c05_research_medium",
    "c04_writing_short",
    "c03_coding_short",
    "c07_research_short",
    "c20_coding_short",
    "c27_creative_short",
    "c30_creative_short",
    "c10_research_short",
    "c16_research_short",
    "c17_research_short",
]


@pytest.mark.parametrize("cid", PROTOTYPE_CHATS)
def test_report_generation_all_10_chats(cid: str):
    """generate_chat_report renders complete Markdown for all 10 prototype chats."""
    report_md = generate_chat_report(cid)
    assert f"**Chat ID**: `{cid}`" in report_md
    assert "# Chat Report:" in report_md
    assert "## 1. Overall Balance & Interaction Mode" in report_md
    assert "## 2. Outcome Map & Contribution Shares" in report_md
    assert "## 3. Key Decisions & Atoms" in report_md
    assert "## 4. Review & Invariant Health" in report_md
    assert len(report_md.splitlines()) >= 40


def test_cli_report_stdout(capsys):
    """Running CLI report outputs markdown report to stdout."""
    ret = cli_main(["report", "c05_research_medium"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "# Chat Report: Finding research papers on AI creativity and design" in captured.out
    assert "COPILOT" in captured.out


def test_cli_report_output_file(tmp_path):
    """Running CLI report with --output writes to the designated file path."""
    out_file = tmp_path / "c04_report.md"
    ret = cli_main(["report", "c04_writing_short", "--output", str(out_file)])
    assert ret == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "**Chat ID**: `c04_writing_short`" in content
    assert "Category**: Writing" in content


def test_cli_report_subprocess(tmp_path):
    """Running python -m engine report via subprocess succeeds with exit code 0."""
    res = subprocess.run(
        [sys.executable, "-m", "engine", "report", "c03_coding_short"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "**Chat ID**: `c03_coding_short`" in res.stdout


def test_cli_report_missing_chat():
    """Providing a nonexistent chat identifier returns error code 1."""
    ret = cli_main(["report", "nonexistent_chat_xyz"])
    assert ret == 1


def test_ag_plus_sacred_fixture_numbers():
    """AG+ rule check: fixture numbers remain strictly invariant:
    Δ_you=87.0, Δ_AI=314.0 (21.7% / 78.3%), 4 You · 10 AI, COPILOT.
    """
    import json
    with open(FIXTURE_DIR / "panel_bundle.json", encoding="utf-8") as f:
        panel_bundle = json.load(f)

    pair1 = panel_bundle["pairs"][0]
    direction = pair1["direction"]
    assert direction["you_pct"] == 21.7
    assert direction["ai_pct"] == 78.3

    timeline = pair1["timeline"]
    assert timeline["delta_you"] == 87.0
    assert timeline["delta_ai"] == 314.0

    decisions = pair1["decisions"]
    assert decisions["you_count"] == 4
    assert decisions["ai_count"] == 10

    how = pair1["how"]
    assert how["mode"] == "COPILOT"
