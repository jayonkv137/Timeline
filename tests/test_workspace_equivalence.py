"""Tier 1 equivalence test across all 10 chats between engine projection and data.generated.json.

Step S1.3 of Track S (STANDALONE_V1_PLAN §4):
Validates that project_workspace() applied to the 10 chats in data/chats/
produces output identical to web/src/workspace/data.generated.json across all fields:
id, title, rootTitle, category, totalPairs, dialogue, atoms, snapshots, summary,
and nodes (excluding x, y which were upgraded in S1.2 from compile-workspace.py's
static 7-point layout to deterministic concentric rings).

Also verifies status and source metadata conform to schema, and total suite runs in <200ms.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest
from engine.artifacts import validate_artifact
from engine.projections.workspace import project_workspace

pytestmark = pytest.mark.tier1

REPO_ROOT = Path(__file__).resolve().parent.parent
CHATS_DIR = REPO_ROOT / "data" / "chats"
SAMPLE_DIR = REPO_ROOT / "design_pack" / "sample_data"
DATA_GENERATED_PATH = REPO_ROOT / "web" / "src" / "workspace" / "data.generated.json"
FIXTURE_DIR = CHATS_DIR / "fixture_pair1"


def _load_generated_data() -> dict[str, Any]:
    with open(DATA_GENERATED_PATH, encoding="utf-8") as f:
        return json.load(f)


GENERATED_DATA = _load_generated_data()
CHAT_IDS = [c["id"] for c in GENERATED_DATA["chats"]]
CHATS_BY_ID = {c["id"]: c for c in GENERATED_DATA["chats"]}


def _load_chat_inputs(cid: str) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], str]:
    chat_dir = CHATS_DIR / cid
    dialogue = json.loads((chat_dir / "dialogue.json").read_text(encoding="utf-8"))
    state = json.loads((chat_dir / "state.json").read_text(encoding="utf-8"))
    ledger = [
        json.loads(line)
        for line in (chat_dir / "ledger.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    sample_file = SAMPLE_DIR / f"{cid}.json"
    full_export_file = chat_dir / "full_export.json"
    if sample_file.exists():
        sample_data = json.loads(sample_file.read_text(encoding="utf-8"))
        summary = sample_data.get("dialogue_summary", "")
    elif full_export_file.exists():
        export_data = json.loads(full_export_file.read_text(encoding="utf-8"))
        summary = export_data.get("dialogue_summary", "")
    else:
        summary = CHATS_BY_ID[cid].get("summary", "")

    return dialogue, state, ledger, summary


def _project_for_cid(cid: str) -> tuple[dict[str, Any], dict[str, Any]]:
    expected = CHATS_BY_ID[cid]
    dialogue, state, ledger, summary = _load_chat_inputs(cid)

    projected = project_workspace(
        dialogue=dialogue,
        state=state,
        ledger=ledger,
        source_meta={"title": expected["title"]},
        meta={"category": expected["category"]},
        chat_id=cid,
        summary=summary,
    )
    return projected, expected


def test_ten_chats_present_in_generated():
    """Verify that exactly 10 chats are present in the reference workspace data."""
    assert len(CHAT_IDS) == 10
    expected_ids = [
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
    assert CHAT_IDS == expected_ids


@pytest.mark.parametrize("cid", CHAT_IDS)
def test_workspace_projection_equivalence(cid: str):
    """Projection matches data.generated.json for all non-layout fields and conforms to schema."""
    projected, expected = _project_for_cid(cid)

    # 1. Schema conformity
    validated = validate_artifact(projected, "workspace_bundle")
    assert validated == projected

    # 2. Scalar metadata equivalence
    assert projected["id"] == expected["id"], f"Mismatch on chat id for {cid}"
    assert projected["title"] == expected["title"], f"Mismatch on title for {cid}"
    assert projected["rootTitle"] == expected["rootTitle"], f"Mismatch on rootTitle for {cid}"
    assert projected["category"] == expected["category"], f"Mismatch on category for {cid}"
    assert projected["totalPairs"] == expected["totalPairs"], f"Mismatch on totalPairs for {cid}"
    assert projected["summary"] == expected["summary"], f"Mismatch on summary for {cid}"

    # 3. New contract fields defaulted
    assert projected["status"] == "ready"
    assert projected["source"]["platform"] == "archive"

    # 4. Dialogue sequence equivalence
    assert projected["dialogue"] == expected["dialogue"], f"Mismatch on dialogue for {cid}"

    # 5. Atoms (requirements & questions) equivalence
    assert len(projected["atoms"]) == len(expected["atoms"])
    assert projected["atoms"] == expected["atoms"], f"Mismatch on atoms for {cid}"

    # 6. Snapshots equivalence (pair, mass dicts, terminal node)
    assert len(projected["snapshots"]) == len(expected["snapshots"])
    assert projected["snapshots"] == expected["snapshots"], f"Mismatch on snapshots for {cid}"

    # 7. Nodes equivalence (ignoring x, y coordinate layout)
    assert len(projected["nodes"]) == len(expected["nodes"])
    proj_nodes_no_xy = [{k: v for k, v in n.items() if k not in ("x", "y")} for n in projected["nodes"]]
    exp_nodes_no_xy = [{k: v for k, v in n.items() if k not in ("x", "y")} for n in expected["nodes"]]
    assert proj_nodes_no_xy == exp_nodes_no_xy, f"Mismatch on node data for {cid}"

    # 8. Coordinate sanity check (deterministic concentric layout)
    root_node = next(n for n in projected["nodes"] if n["root"])
    assert root_node["x"] == 0.0 and root_node["y"] == 0.0
    for node in projected["nodes"]:
        assert isinstance(node["x"], (int, float))
        assert isinstance(node["y"], (int, float))


def test_suite_performance_under_200ms():
    """All 10 chats projected and asserted must execute in <200ms."""
    start = time.perf_counter()
    for cid in CHAT_IDS:
        projected, expected = _project_for_cid(cid)
        assert projected["id"] == expected["id"]
        assert len(projected["nodes"]) == len(expected["nodes"])
        assert len(projected["atoms"]) == len(expected["atoms"])
        assert len(projected["snapshots"]) == len(expected["snapshots"])
    elapsed = time.perf_counter() - start
    assert elapsed < 0.20, f"Expected 10 chat projections to complete in <200ms, took {elapsed * 1000:.1f}ms"


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
