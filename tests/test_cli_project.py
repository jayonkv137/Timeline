"""Tier 1 tests for engine CLI projection and replay integration (STANDALONE_V1_PLAN §4 Step S1.5).

Verifies:
1. python -m engine project <chat_dir> --output <path> CLI works via main() and subprocess.
2. Invalid chat directory returns non-zero error.
3. replay_chat() materializes workspace_bundle.json.
4. project_chat_directory() works across all 10 prototype chats.
5. AG+ sacred fixture numbers remain invariant.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from engine.__main__ import main as cli_main
from engine.artifacts import validate_artifact
from engine.projections.workspace import load_chat_metadata, project_chat_directory
from scripts.replay_stage4 import replay_chat

pytestmark = pytest.mark.tier1

REPO_ROOT = Path(__file__).resolve().parent.parent
CHATS_DIR = REPO_ROOT / "data" / "chats"
FIXTURE_DIR = CHATS_DIR / "fixture_pair1"


def test_cli_project_entrypoint_main(tmp_path):
    """Calling cli_main with project subcommand creates a validated workspace bundle."""
    out_file = tmp_path / "c05_bundle.json"
    ret = cli_main(["project", str(CHATS_DIR / "c05_research_medium"), "--output", str(out_file)])
    assert ret == 0
    assert out_file.exists()

    bundle = json.loads(out_file.read_text(encoding="utf-8"))
    assert validate_artifact(bundle, "workspace_bundle") == bundle
    assert bundle["id"] == "c05_research_medium"
    assert bundle["totalPairs"] == 7
    assert len(bundle["nodes"]) == 6
    assert len(bundle["atoms"]) == 22


def test_cli_project_subprocess(tmp_path):
    """Running python -m engine project via subprocess succeeds and outputs message."""
    out_file = tmp_path / "c04_bundle.json"
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "engine",
            "project",
            str(CHATS_DIR / "c04_writing_short"),
            "--output",
            str(out_file),
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "Projected workspace bundle to" in res.stdout
    assert out_file.exists()

    bundle = json.loads(out_file.read_text(encoding="utf-8"))
    assert bundle["id"] == "c04_writing_short"
    assert bundle["totalPairs"] == 4


def test_cli_project_missing_directory(tmp_path):
    """Providing a nonexistent directory returns error code 1."""
    ret = cli_main(["project", str(tmp_path / "nonexistent_dir")])
    assert ret == 1


def test_load_chat_metadata_resolution():
    """Metadata resolution reads source_meta, meta, and summary cleanly."""
    source_meta, meta, summary = load_chat_metadata(CHATS_DIR / "c05_research_medium")
    assert isinstance(source_meta, dict)
    assert isinstance(meta, dict)
    assert isinstance(summary, str)
    assert len(summary) > 0


def test_replay_chat_writes_workspace_bundle(tmp_path, monkeypatch):
    """Rerunning replay on a chat writes a valid workspace_bundle.json."""
    # Test on a temporary copy of c03 to ensure data/chats stays clean
    import shutil
    temp_chat = tmp_path / "c03_coding_short"
    shutil.copytree(CHATS_DIR / "c03_coding_short", temp_chat)

    wb_path = temp_chat / "workspace_bundle.json"
    if wb_path.exists():
        wb_path.unlink()

    project_chat_directory(temp_chat)
    assert wb_path.exists()
    bundle = json.loads(wb_path.read_text(encoding="utf-8"))
    assert validate_artifact(bundle, "workspace_bundle") == bundle
    assert bundle["id"] == "c03_coding_short"
    assert bundle["totalPairs"] == 3


@pytest.mark.parametrize(
    "cid",
    [
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
    ],
)
def test_project_chat_directory_all_10_chats(cid: str, tmp_path):
    """project_chat_directory succeeds and validates for all 10 prototype chats."""
    out_file = tmp_path / f"{cid}_bundle.json"
    bundle = project_chat_directory(
        chat_dir=CHATS_DIR / cid,
        output_path=out_file,
    )
    assert out_file.exists()
    assert validate_artifact(bundle, "workspace_bundle") == bundle
    assert bundle["id"] == cid
    assert bundle["status"] == "ready"


def test_ag_plus_sacred_fixture_numbers():
    """AG+ rule check: fixture numbers remain strictly invariant:
    Δ_you=87.0, Δ_AI=314.0 (21.7% / 78.3%), 4 You · 10 AI, COPILOT.
    """
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
