"""Tier 1 tests for workspace invariants W1-W6 (STANDALONE_V1_PLAN §4 Step S1.4).

Verifies invariants W1-W6 across all 10 prototype chats in data/chats/ and
the frozen fixture fixture_pair1:
- W1: per-pair snapshot mass sums equal ledger sums
- W2: an outcome is never born after its first ledger row
- W3: every atom's action ids exist in state.actions
- W4: len(snapshots) == totalPairs and pairs are 1..N
- W5: every non-root parent exists and no cycles exist
- W6: shares are in [0, 1] and sum to 1.0
Also includes guard tests (absent data returns skip indicator) and negative tests
(verifying each invariant detects corruptions).
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from engine.projections.workspace import project_workspace
from tests import invariants as inv

pytestmark = pytest.mark.tier1

REPO_ROOT = Path(__file__).resolve().parent.parent
CHATS_DIR = REPO_ROOT / "data" / "chats"
SAMPLE_DIR = REPO_ROOT / "design_pack" / "sample_data"
FIXTURE_DIR = CHATS_DIR / "fixture_pair1"
DATA_GENERATED_PATH = REPO_ROOT / "web" / "src" / "workspace" / "data.generated.json"

PROTOTYPE_CHAT_IDS = [
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


def _load_chat_artifacts(cid: str):
    cdir = CHATS_DIR / cid
    dialogue = json.loads((cdir / "dialogue.json").read_text(encoding="utf-8"))
    state = json.loads((cdir / "state.json").read_text(encoding="utf-8"))
    ledger = [
        json.loads(line)
        for line in (cdir / "ledger.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    bundle = project_workspace(dialogue, state, ledger, chat_id=cid)
    return bundle, ledger, state


@pytest.mark.parametrize("cid", PROTOTYPE_CHAT_IDS)
def test_workspace_invariants_across_10_chats(cid: str):
    """All 10 chats satisfy workspace invariants W1-W6 with zero violations."""
    bundle, ledger, state = _load_chat_artifacts(cid)

    # Individual invariants
    assert inv.inv_w1_snapshot_mass_sums_match_ledger(bundle, ledger) == []
    assert inv.inv_w2_outcome_born_before_or_at_first_ledger_row(bundle, ledger) == []
    assert inv.inv_w3_atom_action_ids_exist(bundle, state) == []
    assert inv.inv_w4_snapshots_count_equals_total_pairs(bundle) == []
    assert inv.inv_w5_non_root_parents_exist(bundle) == []
    assert inv.inv_w6_shares_in_bounds(bundle) == []

    # Combined runner
    assert inv.run_workspace_invariants(bundle, ledger, state) == []


def test_workspace_invariants_fixture_pair1():
    """Frozen fixture_pair1 satisfies workspace invariants W1-W6."""
    fdlg = json.loads((FIXTURE_DIR / "dialogue.json").read_text(encoding="utf-8"))
    fst = json.loads((FIXTURE_DIR / "state.json").read_text(encoding="utf-8"))
    fledger = [
        json.loads(line)
        for line in (FIXTURE_DIR / "ledger.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    fbundle = project_workspace(fdlg, fst, fledger, chat_id="fixture_pair1")

    assert inv.inv_w1(fbundle, fledger) == []
    assert inv.inv_w2(fbundle, fledger) == []
    assert inv.inv_w3(fbundle, fst) == []
    assert inv.inv_w4(fbundle) == []
    assert inv.inv_w5(fbundle) == []
    assert inv.inv_w6(fbundle) == []
    assert inv.run_workspace_invariants(fbundle, fledger, fst) == []


def test_workspace_invariants_graceful_guards():
    """Invariants return skip messages rather than raising when inputs are None."""
    assert inv.inv_w1(None, None) == ["skipped: bundle or ledger_rows absent"]
    assert inv.inv_w2(None, None) == ["skipped: bundle or ledger_rows absent"]
    assert inv.inv_w3(None, None) == ["skipped: state absent"]
    assert inv.inv_w4(None) == ["skipped: bundle absent"]
    assert inv.inv_w5(None) == ["skipped: bundle absent"]
    assert inv.inv_w6(None) == ["skipped: bundle absent"]


def test_w1_negative_detects_mass_mismatch():
    """W1 detects when snapshot mass sums deviate from cumulative ledger sums."""
    bundle, ledger, _ = _load_chat_artifacts("c05_research_medium")
    bad_bundle = copy.deepcopy(bundle)
    bad_bundle["snapshots"][0]["mass"]["outcome 1"]["human"] += 50.0
    violations = inv.inv_w1(bad_bundle, ledger)
    assert len(violations) > 0
    assert any("snapshot human mass" in v for v in violations)


def test_w2_negative_detects_born_after_first_ledger():
    """W2 detects when a node is marked born after its first ledger row."""
    bundle, ledger, _ = _load_chat_artifacts("c05_research_medium")
    bad_bundle = copy.deepcopy(bundle)
    bad_bundle["nodes"][1]["born"] = 99
    violations = inv.inv_w2(bad_bundle, ledger)
    assert len(violations) > 0
    assert any("born pair" in v for v in violations)


def test_w3_negative_detects_missing_action_id():
    """W3 detects when requirement creation action ID is not present in state.actions."""
    bundle, _, state = _load_chat_artifacts("c05_research_medium")
    bad_state = copy.deepcopy(state)
    bad_state["requirements"][0]["creation_action_ids"] = ["U(99,99)"]
    violations = inv.inv_w3(bundle, bad_state)
    assert len(violations) > 0
    assert any("not found in state.actions" in v for v in violations)


def test_w4_negative_detects_count_or_order_mismatch():
    """W4 detects when len(snapshots) != totalPairs or snapshot pairs are not 1..N."""
    bundle, _, _ = _load_chat_artifacts("c05_research_medium")
    bad_bundle = copy.deepcopy(bundle)
    bad_bundle["totalPairs"] = len(bad_bundle["snapshots"]) + 1
    violations = inv.inv_w4(bad_bundle)
    assert len(violations) > 0
    assert any("does not equal totalPairs" in v for v in violations)


def test_w5_negative_detects_bad_parent_or_cycles():
    """W5 detects non-existent parents and parent pointer cycles."""
    bundle, _, _ = _load_chat_artifacts("c05_research_medium")

    # Non-existent parent
    bad_bundle_parent = copy.deepcopy(bundle)
    bad_bundle_parent["nodes"][1]["parent"] = "ghost_node"
    violations = inv.inv_w5(bad_bundle_parent)
    assert any("references nonexistent parent" in v for v in violations)

    # Parent cycle
    bad_bundle_cycle = copy.deepcopy(bundle)
    bad_bundle_cycle["nodes"][0]["root"] = False
    bad_bundle_cycle["nodes"][0]["parent"] = bad_bundle_cycle["nodes"][1]["id"]
    bad_bundle_cycle["nodes"][1]["parent"] = bad_bundle_cycle["nodes"][0]["id"]
    # Add a dummy root to isolate cycle check
    bad_bundle_cycle["nodes"].append({"id": "dummy_root", "root": True, "parent": None})
    violations = inv.inv_w5(bad_bundle_cycle)
    assert any("cycle detected" in v for v in violations)


def test_w6_negative_detects_out_of_bounds_shares():
    """W6 detects negative masses or shares outside [0, 1]."""
    bundle, _, _ = _load_chat_artifacts("c05_research_medium")
    bad_bundle = copy.deepcopy(bundle)
    bad_bundle["snapshots"][0]["mass"]["outcome 1"]["human"] = -10.0
    violations = inv.inv_w6(bad_bundle)
    assert len(violations) > 0
    assert any("negative" in v for v in violations)


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
