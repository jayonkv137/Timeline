"""Tier 1 tests for Stage 4b Projections (engine/projections/panel.py).

Verifies artifact writing through artifacts.py validation gate and exact
value-equivalence against the frozen canonical fixture.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import pytest
import jsonschema

from engine.projections.panel import (
    build_panel_bundle,
    build_snapshots,
    export_panel_projections,
    project_panel,
    write_panel_bundle,
    write_snapshots,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def deep_diff(actual: Any, expected: Any, path: str = "") -> list[str]:
    """Recursively compare two JSON-like structures and report all field differences."""
    diffs: list[str] = []

    # Handle bool separately because bool is a subclass of int in Python
    if isinstance(actual, bool) or isinstance(expected, bool):
        if not (isinstance(actual, bool) and isinstance(expected, bool)):
            diffs.append(f"{path}: type mismatch ({type(actual).__name__} vs {type(expected).__name__})")
        elif actual != expected:
            diffs.append(f"{path}: bool mismatch ({actual} vs {expected})")
        return diffs

    # Handle numbers (both float and int)
    if isinstance(actual, (float, int)) and isinstance(expected, (float, int)):
        if round(float(actual), 1) != round(float(expected), 1):
            diffs.append(f"{path}: number mismatch ({actual} vs {expected})")
        return diffs

    if type(actual) != type(expected):
        diffs.append(f"{path}: type mismatch ({type(actual).__name__} vs {type(expected).__name__})")
        return diffs

    if isinstance(actual, dict):
        all_keys = set(actual.keys()) | set(expected.keys())
        for k in sorted(all_keys):
            sub_path = f"{path}.{k}" if path else k
            if k not in actual:
                diffs.append(f"{sub_path}: missing in generated output")
            elif k not in expected:
                diffs.append(f"{sub_path}: extra in generated output")
            else:
                diffs.extend(deep_diff(actual[k], expected[k], sub_path))
    elif isinstance(actual, list):
        if len(actual) != len(expected):
            diffs.append(f"{path}: length mismatch ({len(actual)} vs {len(expected)})")
        else:
            for i, (a_item, e_item) in enumerate(zip(actual, expected)):
                diffs.extend(deep_diff(a_item, e_item, f"{path}[{i}]"))
    else:
        if actual != expected:
            diffs.append(f"{path}: value mismatch ({actual!r} vs {expected!r})")

    return diffs


@pytest.mark.tier1
def test_projections_value_equivalence_on_frozen_fixture(tmp_path: Path):
    """Verify generated panel_bundle.json and snapshots.json match the frozen fixture with 0 diffs."""
    fixture_dir = REPO_ROOT / "data/chats/fixture_pair1"
    ledger_path = fixture_dir / "ledger.jsonl"
    state_path = fixture_dir / "state.json"
    frozen_bundle_path = fixture_dir / "panel_bundle.json"
    frozen_snapshots_path = fixture_dir / "snapshots.json"

    assert ledger_path.exists()
    assert state_path.exists()
    assert frozen_bundle_path.exists()
    assert frozen_snapshots_path.exists()

    rows = []
    with open(ledger_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    with open(frozen_bundle_path, "r", encoding="utf-8") as f:
        frozen_bundle = json.load(f)

    with open(frozen_snapshots_path, "r", encoding="utf-8") as f:
        frozen_snapshots = json.load(f)

    # Project and write to scratch/tmp location
    gen_bundle, gen_snapshots = export_panel_projections(
        target_dir=tmp_path,
        ledger_rows=rows,
        state_dict=state,
    )

    # 1. Assert files were written on disk
    assert (tmp_path / "panel_bundle.json").exists()
    assert (tmp_path / "snapshots.json").exists()

    with open(tmp_path / "panel_bundle.json", "r", encoding="utf-8") as f:
        disk_bundle = json.load(f)

    with open(tmp_path / "snapshots.json", "r", encoding="utf-8") as f:
        disk_snapshots = json.load(f)

    # 2. Assert snapshots value equivalence (0 diffs)
    snap_diffs = deep_diff(disk_snapshots, frozen_snapshots)
    assert snap_diffs == [], f"Snapshots differences found: {snap_diffs}"

    # 3. Assert panel_bundle value equivalence (0 diffs)
    bundle_diffs = deep_diff(disk_bundle, frozen_bundle)
    assert bundle_diffs == [], f"Panel bundle differences found: {bundle_diffs}"


@pytest.mark.tier1
def test_projections_schema_validation_gate(tmp_path: Path):
    """Verify write_panel_bundle and write_snapshots raise ValidationError on invalid data."""
    # Invalid snapshots (missing required fields)
    bad_snapshots = [{"t": 1}]
    with pytest.raises(jsonschema.ValidationError):
        write_snapshots(tmp_path / "bad_snapshots.json", bad_snapshots)
    assert not (tmp_path / "bad_snapshots.json").exists()

    # Invalid bundle (extra disallowed property)
    bad_bundle = {"pairs": [], "unexpected_field": 123}
    with pytest.raises(jsonschema.ValidationError):
        write_panel_bundle(tmp_path / "bad_bundle.json", bad_bundle)
    assert not (tmp_path / "bad_bundle.json").exists()


@pytest.mark.tier1
def test_projections_multi_pair_synthetic(tmp_path: Path):
    """Verify projections correctly format multi-pair conversations and validate schemas."""
    rows = [
        # Pair 1: U creates r1
        {"pair_added": 1, "action_id": "U(1,1)", "speaker": "U", "role": "SHAPER", "outcome_id": "o1", "req_id": "r1", "score": 10.0, "kind": "creation"},
        # Pair 2: A adds mass to r1, creates r2
        {"pair_added": 2, "action_id": "A(2,1)", "speaker": "A", "role": "SHAPER", "outcome_id": "o1", "req_id": "r1", "score": 5.0, "kind": "labeled"},
        {"pair_added": 2, "action_id": "A(2,2)", "speaker": "A", "role": "SHAPER", "outcome_id": "o1", "req_id": "r2", "score": 15.0, "kind": "creation"},
    ]
    state = {
        "outcomes": [
            {"id": "o1", "text": "App Goal", "parent": None, "children": []}
        ],
        "requirements": [
            {"outcome_id": "o1", "req_id": "r1", "text": "User Login", "created_at_pair": 1, "creation_action_ids": ["U(1,1)"]},
            {"outcome_id": "o1", "req_id": "r2", "text": "AI Assistant Sidebar", "created_at_pair": 2, "creation_action_ids": ["A(2,2)"]},
        ],
        "slots": [],
        "operations_log": [
            {"pair": 1, "outcome_id": "o1", "target_id": "r1", "target_type": "requirement", "op": "create"},
            {"pair": 2, "outcome_id": "o1", "target_id": "r1", "target_type": "requirement", "op": "revise"},
            {"pair": 2, "outcome_id": "o1", "target_id": "r2", "target_type": "requirement", "op": "create"},
        ],
    }

    bundle, snapshots = export_panel_projections(
        target_dir=tmp_path,
        ledger_rows=rows,
        state_dict=state,
        max_pair=2,
    )

    # 1. Check snapshots
    assert len(snapshots) == 2
    assert snapshots[0]["t"] == 1
    assert snapshots[0]["delta_you"] == 10.0
    assert snapshots[0]["c_you"] == 10.0
    assert snapshots[1]["t"] == 2
    assert snapshots[1]["delta_ai"] == 20.0
    assert snapshots[1]["c_ai"] == 20.0

    # 2. Check bundle
    assert len(bundle["pairs"]) == 2
    p1 = bundle["pairs"][0]
    p2 = bundle["pairs"][1]

    assert p1["pair"] == 1
    assert p1["direction"]["you_pct"] == 100.0
    assert p1["decisions"]["you_count"] == 1
    assert p1["decisions"]["ai_count"] == 0
    assert len(p1["timeline"]["drawer"]["requirements"]) == 1

    assert p2["pair"] == 2
    assert p2["decisions"]["you_count"] == 1
    assert p2["decisions"]["ai_count"] == 1
    assert p2["decisions"]["latest_ai_example"] == "AI Assistant Sidebar"
    assert len(p2["timeline"]["drawer"]["requirements"]) == 2

    # 3. Check schema validation on written files
    with open(tmp_path / "panel_bundle.json") as f:
        disk_bundle = json.load(f)
    with open(tmp_path / "snapshots.json") as f:
        disk_snapshots = json.load(f)

    schema_dir = REPO_ROOT / "engine/schemas"
    with open(schema_dir / "panel_bundle.schema.json") as f:
        jsonschema.validate(instance=disk_bundle, schema=json.load(f))
    with open(schema_dir / "snapshots.schema.json") as f:
        jsonschema.validate(instance=disk_snapshots, schema=json.load(f))
