"""S8(a) Verification Harnesses.

Implements the five mechanical checks defined in §11.4 of the spec
against any generated output folder.
"""
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from engine.state import State
from engine.pipeline import action_sort_key

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = REPO_ROOT / "data" / "chats" / "fixture_pair1"



def verify_output_folder(out_dir):
    """Executes the §11.4 mechanical checks on the specified output directory.
    Raises AssertionError on any failure.
    """
    out_dir = Path(out_dir)
    
    # 1. Schema validate files in output directory
    from engine.artifacts import validate_artifact
    
    with open(out_dir / "state.json") as f:
        state_data = validate_artifact(json.load(f), "state")
    with open(out_dir / "dialogue.json") as f:
        dialogue_data = validate_artifact(json.load(f), "dialogue")
    with open(out_dir / "snapshots.json") as f:
        snapshots_data = validate_artifact(json.load(f), "snapshots")
    with open(out_dir / "panel_bundle.json") as f:
        panel_bundle_data = validate_artifact(json.load(f), "panel_bundle")

    # Load State and internal run state
    state = State.load(out_dir)
    
    # If run/pipeline_state.json is missing, rebuild action_to_outcome from state & ledger
    if not (out_dir / "run" / "pipeline_state.json").exists():
        for req in state.requirements:
            for aid in req["creation_action_ids"]:
                state.run["action_to_outcome"][aid] = req["outcome_id"]
        for slot in state.slots:
            for aid in slot["creation_action_ids"]:
                state.run["action_to_outcome"][aid] = slot["outcome_id"]
        from engine.artifacts import read_ledger
        try:
            rows = read_ledger(out_dir / "ledger.jsonl")
            for r in rows:
                aid = r["action_id"]
                if aid not in state.run["action_to_outcome"]:
                    state.run["action_to_outcome"][aid] = r["outcome_id"]
        except Exception:
            pass


    
    # Check 1: Action coverage
    # every action ID in state.actions must appear exactly once in action_to_outcome mapping
    action_ids = {a["id"] for a in state.actions}
    mapped_actions = set(state.run["action_to_outcome"].keys())
    
    assert action_ids == mapped_actions, (
        f"Action coverage failure: Actions in state {action_ids} "
        f"do not match mapped actions {mapped_actions}"
    )

    # Check 2: Parent/child consistency
    for outcome in state.outcomes:
        oid = outcome["id"]
        parent = outcome["parent"]
        children = outcome["children"]
        
        if parent is not None:
            parent_node = state.get_outcome(parent)
            assert oid in parent_node["children"], (
                f"Parent/child inconsistency: Outcome {oid} lists {parent} "
                f"as parent, but parent does not list it as child"
            )
            
        for child_id in children:
            child_node = state.get_outcome(child_id)
            assert child_node["parent"] == oid, (
                f"Parent/child inconsistency: Outcome {oid} lists {child_id} "
                f"as child, but child lists parent as {child_node['parent']}"
            )

    # Check 3: req_id / slot_id isolation
    # no action ID cited in a requirement/slot belongs to a different outcome's action set
    for req in state.requirements:
        outcome_id = req["outcome_id"]
        req_actions = set(
            req["creation_action_ids"]
            + req.get("contributing_action_ids", [])
            + req.get("implementation_action_ids", [])
            + req.get("revise_action_ids", [])
        )
        for aid in req_actions:
            mapped_oid = state.run["action_to_outcome"].get(aid)
            assert mapped_oid == outcome_id, (
                f"Isolation failure: Action {aid} cited in requirement "
                f"{req['req_id']} under outcome {outcome_id} but mapped to {mapped_oid}"
            )
            
    for slot in state.slots:
        outcome_id = slot["outcome_id"]
        slot_actions = set(slot["creation_action_ids"] + slot.get("contributing_action_ids", []))
        for aid in slot_actions:
            mapped_oid = state.run["action_to_outcome"].get(aid)
            assert mapped_oid == outcome_id, (
                f"Isolation failure: Action {aid} cited in slot "
                f"{slot['slot_id']} under outcome {outcome_id} but mapped to {mapped_oid}"
            )

    # Check 4: req vs. slot disjointness
    # no action ID justifies both active requirement and open slot within same outcome
    for outcome in state.outcomes:
        oid = outcome["id"]
        active_reqs = [r for r in state.requirements_for_outcome(oid) if r["status"] in ("active", "revised")]
        open_slots = [s for s in state.slots_for_outcome(oid, status="open")]
        
        req_action_ids = set()
        for r in active_reqs:
            req_action_ids.update(r["creation_action_ids"] + r.get("contributing_action_ids", []))
            
        slot_action_ids = set()
        for s in open_slots:
            slot_action_ids.update(s["creation_action_ids"] + s.get("contributing_action_ids", []))
            
        overlap = req_action_ids & slot_action_ids
        assert not overlap, (
            f"Disjointness failure: Outcome {oid} has actions overlapping "
            f"between active requirements and open slots: {overlap}"
        )

    # Check 5: Step 3 origin-action exclusion
    # a requirement's creation_action_ids never appear in its preceding or subsequent blocks
    # or the ledger rows as labeled actions
    # We can check the ledger to verify that no row for this requirement has the action_id
    # in creation_action_ids when kind == "labeled" or "slot-origin"
    from engine.artifacts import read_ledger
    ledger_rows = read_ledger(out_dir / "ledger.jsonl")
    
    for req in state.requirements:
        creation_ids = set(req["creation_action_ids"])
        
        # Check that no labeled/slot-origin ledger row uses a creation action ID
        req_rows = [r for r in ledger_rows if r["outcome_id"] == req["outcome_id"] and r["req_id"] == req["req_id"]]
        for r in req_rows:
            if r["kind"] in ("labeled", "slot-origin"):
                assert r["action_id"] not in creation_ids, (
                    f"Exclusion failure: Requirement {req['req_id']} has creation action "
                    f"{r['action_id']} labeled in the ledger"
                )

    print("All §11.4 mechanical checks passed successfully!")


def test_fixture_pair1_mechanical_checks():
    """Verify that the frozen fixture output folder passes all §11.4 mechanical checks."""
    verify_output_folder(FIXTURE_DIR)
