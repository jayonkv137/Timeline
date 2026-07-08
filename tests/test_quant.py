"""Stage 4 tests.

Validates pure-computation Stage 4 metrics, exact reproduction of
canonical fixture numbers, and contributions-only CLI mode.
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from jsonschema import Draft202012Validator

from engine.artifacts import read_ledger, validate_artifact
from engine.quant import compute_stage4, write_stage4_artifacts
from engine.state import State


REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = REPO_ROOT / "data" / "chats" / "fixture_pair1"
SCHEMAS_DIR = REPO_ROOT / "engine" / "schemas"


def test_fixture_regression_exact():
    """S8(b) Fixture regression: must reproduce exact canonical numbers from pair 1."""
    # 1. Load state and ledger
    state = State.load(FIXTURE_DIR)
    ledger_rows = read_ledger(FIXTURE_DIR / "ledger.jsonl")

    # 2. Run computation
    snapshots, panel_bundle = compute_stage4(state, ledger_rows)

    # 3. Assert exact canonical values
    assert len(snapshots) == 1
    snap = snapshots[0]
    assert snap["t"] == 1
    assert snap["delta_you"] == 87.0
    assert snap["delta_ai"] == 314.0
    assert snap["c_you"] == 87.0
    assert snap["c_ai"] == 314.0

    assert len(panel_bundle["pairs"]) == 1
    pair = panel_bundle["pairs"][0]
    
    assert pair["pair"] == 1
    assert pair["direction"]["you_pct"] == 21.7
    assert pair["direction"]["ai_pct"] == 78.3
    
    assert pair["decisions"]["you_count"] == 4
    assert pair["decisions"]["ai_count"] == 10
    assert pair["decisions"]["latest_ai_example"] == (
        "Final production scene generations must use the Style Anchor plus "
        "a texture crop plus a color swatch as triple-references"
    )

    assert pair["timeline"]["pair"] == 1
    assert pair["timeline"]["delta_you"] == 87.0
    assert pair["timeline"]["delta_ai"] == 314.0
    assert pair["timeline"]["summary"] == "adding Style DNA framework"

    assert pair["how"]["mode"] == "COPILOT"
    assert pair["how"]["signals"]["w_you"] == 4
    assert pair["how"]["signals"]["w_ai"] == 10
    assert pair["how"]["signals"]["h_you"] == 47.0
    assert pair["how"]["signals"]["h_ai"] == 239.0
    assert pair["how"]["signals"]["substantive_user"] is True

    # Split percentages (since t=1 and it is COPILOT, split must be 100% copilot)
    assert pair["how"]["split"]["centaur_pct"] == 0.0
    assert pair["how"]["split"]["copilot_pct"] == 100.0
    assert pair["how"]["split"]["autopilot_pct"] == 0.0

    # Timeline drawer requirements check
    reqs = pair["timeline"]["drawer"]["requirements"]
    assert len(reqs) == 14

    chip_colors = [r["chip"] for r in reqs]
    assert chip_colors.count("grey") == 13
    assert chip_colors.count("orange") == 1
    assert chip_colors.count("blue") == 0

    # Ensure outcome 5 / req 2 is the orange chip
    orange_req = next(r for r in reqs if r["chip"] == "orange")
    assert orange_req["outcome_id"] == "outcome 5"
    assert orange_req["req_id"] == "req 2"
    assert orange_req["label"] == "R11"  # 11th requirement in creation order

    # 4. Schema validate
    validate_artifact(snapshots, "snapshots")
    validate_artifact(panel_bundle, "panel_bundle")


def test_contributions_only_cli(tmp_path):
    """Verify --contributions-only runs Stage 4 from existing files."""
    # Copy fixture state/ledger to tmp folder
    tmp_out = tmp_path / "out"
    tmp_out.mkdir()
    (tmp_out / "run").mkdir()
    
    import shutil
    shutil.copy(FIXTURE_DIR / "state.json", tmp_out / "state.json")
    shutil.copy(FIXTURE_DIR / "ledger.jsonl", tmp_out / "ledger.jsonl")

    # Run cli with mock args
    from engine.__main__ import main
    test_args = ["engine", "run", "--input", "mock.json", "--out", str(tmp_out), "--contributions-only"]
    
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0

    # Verify artifacts were generated and validated in tmp_out
    assert (tmp_out / "snapshots.json").exists()
    assert (tmp_out / "panel_bundle.json").exists()

    with open(tmp_out / "panel_bundle.json") as f:
        data = json.load(f)
    assert data["pairs"][0]["how"]["mode"] == "COPILOT"
