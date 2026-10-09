"""Test workspace bundle pure projection determinism and schema conformity.

Step S1.2 of Track S: validating that project_workspace is a pure, deterministic
function that produces byte-identical output for identical inputs, complies
strictly with workspace_bundle.schema.json, and maps engine artifacts into
the normalized UI shape.
"""
import json
from pathlib import Path

import pytest
from engine.artifacts import validate_artifact
from engine.projections.workspace import (
    compute_outcome_layout,
    export_workspace_bundle,
    project_workspace,
)

pytestmark = pytest.mark.tier1

REPO_ROOT = Path(__file__).resolve().parent.parent
CHATS_DIR = REPO_ROOT / "data" / "chats"
FIXTURE_DIR = CHATS_DIR / "fixture_pair1"


def _load_chat_inputs(chat_dir: Path):
    dlg = json.loads((chat_dir / "dialogue.json").read_text(encoding="utf-8"))
    st = json.loads((chat_dir / "state.json").read_text(encoding="utf-8"))
    ledger = [
        json.loads(line)
        for line in (chat_dir / "ledger.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return dlg, st, ledger


def test_projection_determinism_byte_identical():
    """Identical inputs must yield 100% byte-identical serialized JSON."""
    dlg, st, ledger = _load_chat_inputs(CHATS_DIR / "c05_research_medium")
    meta = {"category": "Research"}
    source_meta = {"title": "AI creativity · paper research", "source_kind": "claude"}

    b1 = project_workspace(
        dialogue=dlg,
        state=st,
        ledger=ledger,
        source_meta=source_meta,
        meta=meta,
        chat_id="c05_research_medium",
        summary="A test summary",
    )
    b2 = project_workspace(
        dialogue=dlg,
        state=st,
        ledger=ledger,
        source_meta=source_meta,
        meta=meta,
        chat_id="c05_research_medium",
        summary="A test summary",
    )

    s1 = json.dumps(b1, sort_keys=True, indent=2)
    s2 = json.dumps(b2, sort_keys=True, indent=2)
    assert s1 == s2, "Repeated projection runs must be byte-identical"


def test_projection_schema_valid_c05():
    """Projected bundle on c05 must pass Draft 2020-12 schema validation."""
    dlg, st, ledger = _load_chat_inputs(CHATS_DIR / "c05_research_medium")
    bundle = project_workspace(
        dialogue=dlg,
        state=st,
        ledger=ledger,
        chat_id="c05_research_medium",
        summary="Summary of paper research",
    )
    # validate_artifact raises jsonschema.ValidationError if invalid
    assert validate_artifact(bundle, "workspace_bundle") == bundle
    assert bundle["id"] == "c05_research_medium"
    assert bundle["totalPairs"] == 7
    assert len(bundle["snapshots"]) == 7
    assert len(bundle["nodes"]) == 6
    assert len(bundle["atoms"]) == 22
    assert bundle["status"] == "ready"


def test_projection_schema_valid_fixture_pair1():
    """Projected bundle on frozen fixture_pair1 must pass schema validation."""
    dlg, st, ledger = _load_chat_inputs(FIXTURE_DIR)
    bundle = project_workspace(
        dialogue=dlg,
        state=st,
        ledger=ledger,
        chat_id="fixture_pair1",
    )
    assert validate_artifact(bundle, "workspace_bundle") == bundle
    assert bundle["id"] == "fixture_pair1"
    assert bundle["totalPairs"] == 1
    assert len(bundle["snapshots"]) == 1
    assert len(bundle["nodes"]) == 6


def test_deterministic_layout_coordinates():
    """Root is at (0, 0), non-root are on rings with radii scaling by depth."""
    sample_nodes = [
        {"id": "outcome 1", "born": 1, "parent": None},
        {"id": "outcome 2", "born": 1, "parent": "outcome 1"},
        {"id": "outcome 3", "born": 2, "parent": "outcome 1"},
        {"id": "outcome 4", "born": 2, "parent": "outcome 2"},
    ]
    coords = compute_outcome_layout(sample_nodes, "outcome 1")
    assert coords["outcome 1"] == (0.0, 0.0)

    # depth 1 nodes have distance approx 160.0
    for oid in ("outcome 2", "outcome 3"):
        x, y = coords[oid]
        r = (x**2 + y**2)**0.5
        assert 159.0 <= r <= 161.0, f"Expected ring radius ~160, got {r}"

    # depth 2 node has distance approx 320.0
    x, y = coords["outcome 4"]
    r = (x**2 + y**2)**0.5
    assert 319.0 <= r <= 321.0, f"Expected ring radius ~320, got {r}"


def test_export_workspace_bundle(tmp_path):
    """export_workspace_bundle validates and writes JSON artifact."""
    dlg, st, ledger = _load_chat_inputs(FIXTURE_DIR)
    out_file = tmp_path / "workspace_bundle.json"
    exported = export_workspace_bundle(
        output_path=out_file,
        dialogue=dlg,
        state=st,
        ledger=ledger,
        chat_id="fixture_pair1",
    )
    assert out_file.exists()
    loaded = json.loads(out_file.read_text(encoding="utf-8"))
    assert loaded == exported


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
