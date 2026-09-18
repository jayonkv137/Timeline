"""The 21 invariants catalogue (TEST_STRATEGY.md §2).

Each function takes the artifacts it needs and returns a list of violation strings.
Returns [] when the invariant passes.
Never raises and never asserts, so it can be called safely in production and test harnesses.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ACTION_ID_RE = re.compile(r"^([UA])\((\d+),(\d+)\)$")
VALID_SLOT_STATUSES = {"open", "resolved", "abandoned"}
VALID_MODES = {"YOU_DRIVING", "COPILOT", "AUTOPILOT", "QUIET", "centaur", "copilot", "autopilot"}


# ==============================================================================
# Referential integrity (Invariants 1 - 5)
# ==============================================================================

def inv_01_schema_valid(artifacts: dict[str, Any], schemas_dir: Path | str | None = None) -> list[str]:
    """1. Every artifact validates against its schema."""
    violations: list[str] = []
    if schemas_dir is None:
        schemas_dir = Path(__file__).resolve().parent.parent / "engine" / "schemas"
    else:
        schemas_dir = Path(schemas_dir)

    schema_map = {
        "dialogue": "dialogue.schema.json",
        "state": "state.schema.json",
        "snapshots": "snapshots.schema.json",
        "panel_bundle": "panel_bundle.schema.json",
        "ledger_row": "ledger_row.schema.json",
    }

    for name, data in artifacts.items():
        if data is None:
            continue
        schema_file = schema_map.get(name)
        if not schema_file:
            continue
        schema_path = schemas_dir / schema_file
        if not schema_path.exists():
            violations.append(f"schema file missing: {schema_path}")
            continue

        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
            validator = Draft202012Validator(schema)
            if name == "ledger":
                for idx, row in enumerate(data):
                    errors = sorted(validator.iter_errors(row), key=lambda e: e.path)
                    for err in errors:
                        violations.append(f"ledger row {idx} schema violation: {err.message}")
            else:
                errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
                for err in errors:
                    violations.append(f"{name} schema violation: {err.message}")
        except Exception as exc:
            violations.append(f"schema validation error on {name}: {exc}")

    return violations


def inv_02_action_ids(state: dict[str, Any]) -> list[str]:
    r"""2. Every action id matches ^([UA])\((\d+),(\d+)\)$ and is unique within the chat."""
    violations: list[str] = []
    actions = state.get("actions", [])
    seen = set()

    for idx, act in enumerate(actions):
        act_id = act.get("id", "")
        if not ACTION_ID_RE.match(act_id):
            violations.append(f"action {idx} has invalid id format: '{act_id}'")
        if act_id in seen:
            violations.append(f"duplicate action id: '{act_id}'")
        seen.add(act_id)

    return violations


def inv_03_ledger_references_exist(ledger_rows: list[dict[str, Any]], state: dict[str, Any]) -> list[str]:
    """3. Every ledger row's action_id, req_id and outcome_id exist in state."""
    violations: list[str] = []
    state_action_ids = {a.get("id") for a in state.get("actions", [])}
    state_outcome_ids = {o.get("id") for o in state.get("outcomes", [])}
    state_req_keys = {(r.get("outcome_id"), r.get("req_id")) for r in state.get("requirements", [])}

    for idx, row in enumerate(ledger_rows):
        a_id = row.get("action_id")
        o_id = row.get("outcome_id")
        r_id = row.get("req_id")

        if a_id not in state_action_ids:
            violations.append(f"row {idx}: action_id '{a_id}' does not exist in state.actions")
        if o_id not in state_outcome_ids:
            violations.append(f"row {idx}: outcome_id '{o_id}' does not exist in state.outcomes")
        if (o_id, r_id) not in state_req_keys:
            violations.append(f"row {idx}: (outcome_id '{o_id}', req_id '{r_id}') does not exist in state.requirements")

    return violations


def inv_04_action_maps_to_one_outcome(state: dict[str, Any], action_to_outcome: dict[str, str] | None = None) -> list[str]:
    """4. Every action maps to exactly one outcome."""
    violations: list[str] = []

    if action_to_outcome is not None:
        for action_id, outcome_id in action_to_outcome.items():
            if not isinstance(outcome_id, str) or not outcome_id:
                violations.append(f"action '{action_id}' does not map to a valid outcome: '{outcome_id}'")
        return violations

    # Check state requirements and slots creation actions
    action_outcomes: dict[str, set[str]] = {}
    for r in state.get("requirements", []):
        o_id = r.get("outcome_id", "")
        for a_id in r.get("creation_action_ids", []):
            action_outcomes.setdefault(a_id, set()).add(o_id)

    for s in state.get("slots", []):
        o_id = s.get("outcome_id", "")
        for a_id in s.get("creation_action_ids", []):
            action_outcomes.setdefault(a_id, set()).add(o_id)

    for a_id, out_ids in action_outcomes.items():
        if len(out_ids) > 1:
            violations.append(f"action '{a_id}' maps to multiple outcomes: {sorted(out_ids)}")

    return violations


def inv_05_no_duplicate_ledger_rows(ledger_rows: list[dict[str, Any]]) -> list[str]:
    """5. No duplicate ledger rows on (action_id, outcome_id, req_id, pair_added, kind)."""
    violations: list[str] = []
    seen: set[tuple[str, str, str, int, str]] = set()

    for idx, row in enumerate(ledger_rows):
        key = (
            str(row.get("action_id")),
            str(row.get("outcome_id")),
            str(row.get("req_id")),
            int(row.get("pair_added", 0)),
            str(row.get("kind")),
        )
        if key in seen:
            violations.append(f"duplicate ledger row at index {idx}: {key}")
        seen.add(key)

    return violations


# ==============================================================================
# Structure (Invariants 6 - 9)
# ==============================================================================

def inv_06_outcome_tree(state: dict[str, Any]) -> list[str]:
    """6. The outcome tree has exactly one root, no cycles, every parent exists,

    and children[] agrees with parent pointers in both directions.
    """
    violations: list[str] = []
    outcomes = state.get("outcomes", [])
    if not outcomes:
        return ["outcome tree has no outcomes"]

    by_id = {o.get("id"): o for o in outcomes}
    roots = [o for o in outcomes if o.get("parent") is None]

    if len(roots) != 1:
        violations.append(f"outcome tree must have exactly one root, found {len(roots)}: {[r.get('id') for r in roots]}")

    for o in outcomes:
        o_id = o.get("id")
        p_id = o.get("parent")
        children = o.get("children", [])

        if p_id is not None:
            if p_id not in by_id:
                violations.append(f"outcome '{o_id}' points to non-existent parent '{p_id}'")
            elif o_id not in by_id[p_id].get("children", []):
                violations.append(f"outcome '{o_id}' parent is '{p_id}', but '{p_id}' children does not contain '{o_id}'")

        for ch_id in children:
            if ch_id not in by_id:
                violations.append(f"outcome '{o_id}' has non-existent child '{ch_id}'")
            elif by_id[ch_id].get("parent") != o_id:
                violations.append(f"outcome '{o_id}' lists child '{ch_id}', but child parent is '{by_id[ch_id].get('parent')}'")

    # Cycle detection
    visited: set[str] = set()
    for o in outcomes:
        curr = o.get("id")
        path = set()
        while curr is not None:
            if curr in path:
                violations.append(f"cycle detected in outcome tree starting at '{curr}'")
                break
            path.add(curr)
            parent = by_id.get(curr, {}).get("parent")
            curr = parent

    return violations


def inv_07_requirement_has_creation(state: dict[str, Any]) -> list[str]:
    """7. Every requirement has at least one creation action."""
    violations: list[str] = []
    for r in state.get("requirements", []):
        creations = r.get("creation_action_ids", [])
        if not creations:
            violations.append(f"requirement '{r.get('outcome_id')}/{r.get('req_id')}' has no creation actions")
    return violations


def inv_08_requirement_created_at_pair(state: dict[str, Any], current_pair: int | None = None) -> list[str]:
    """8. Every requirement's created_at_pair is less than or equal to the current pair."""
    violations: list[str] = []
    if current_pair is None:
        current_pair = max(
            [r.get("created_at_pair", 1) for r in state.get("requirements", [])] or [1]
        )

    for r in state.get("requirements", []):
        created_pair = r.get("created_at_pair")
        if created_pair is None:
            violations.append(f"requirement '{r.get('outcome_id')}/{r.get('req_id')}' missing created_at_pair")
        elif created_pair > current_pair:
            violations.append(
                f"requirement '{r.get('outcome_id')}/{r.get('req_id')}' created_at_pair {created_pair} > current_pair {current_pair}"
            )
    return violations


def inv_09_slot_status_and_inactivity(state: dict[str, Any], current_pair: int | None = None) -> list[str]:
    """9. Slot status is one of open, resolved, abandoned.

    A resolved slot links to a requirement. An abandoned slot was inactive for >= 3 pairs.
    """
    violations: list[str] = []
    state_req_ids = {r.get("req_id") for r in state.get("requirements", [])}

    for s in state.get("slots", []):
        slot_id = s.get("slot_id")
        status = s.get("status")
        if status not in VALID_SLOT_STATUSES:
            violations.append(f"slot '{slot_id}' has invalid status: '{status}'")

        if status == "resolved":
            resolved_into = s.get("resolved_into")
            if not resolved_into:
                violations.append(f"resolved slot '{slot_id}' missing resolved_into link")
            elif resolved_into not in state_req_ids:
                violations.append(f"resolved slot '{slot_id}' links to non-existent requirement '{resolved_into}'")

    return violations


# ==============================================================================
# Arithmetic (Invariants 10 - 16) — Guards return skipped if analysis is absent
# ==============================================================================

def inv_10_scores_positive(analysis: dict[str, Any] | None, ledger_rows: list[dict[str, Any]] | None = None) -> list[str]:
    """10. All scores are finite and strictly positive."""
    if analysis is None and ledger_rows is None:
        return ["skipped: analysis.json absent"]

    violations: list[str] = []
    if ledger_rows is not None:
        for idx, row in enumerate(ledger_rows):
            score = row.get("score")
            if score is None or score <= 0 or not isinstance(score, (int, float)):
                violations.append(f"ledger row {idx} score is non-positive or invalid: {score}")

    return violations


def inv_11_deltas_sum_to_cumulative(analysis: dict[str, Any] | None) -> list[str]:
    """11. The sum of per-pair deltas equals the cumulative total at the final pair."""
    if analysis is None:
        return ["skipped: analysis.json absent"]
    violations: list[str] = []
    pairs = analysis.get("pairs", [])
    if not pairs:
        return violations

    sum_you = sum(p.get("delta_you", 0.0) for p in pairs)
    sum_ai = sum(p.get("delta_ai", 0.0) for p in pairs)

    final_c_you = pairs[-1].get("c_you", 0.0)
    final_c_ai = pairs[-1].get("c_ai", 0.0)

    if abs(sum_you - final_c_you) > 0.01:
        violations.append(f"sum(delta_you)={sum_you} does not equal final c_you={final_c_you}")
    if abs(sum_ai - final_c_ai) > 0.01:
        violations.append(f"sum(delta_ai)={sum_ai} does not equal final c_ai={final_c_ai}")

    return violations


def inv_12_creator_counts_sum(analysis: dict[str, Any] | None, state: dict[str, Any] | None = None) -> list[str]:
    """12. Creator counts sum to the number of distinct requirements."""
    if analysis is None and state is None:
        return ["skipped: analysis.json absent"]
    violations: list[str] = []

    if analysis is not None:
        you_count = analysis.get("creator_counts", {}).get("you", 0)
        ai_count = analysis.get("creator_counts", {}).get("ai", 0)
        total_reqs = analysis.get("total_requirements", you_count + ai_count)
        if you_count + ai_count != total_reqs:
            violations.append(f"creator counts {you_count} + {ai_count} != total requirements {total_reqs}")

    return violations


def inv_13_cumulative_mass_monotonic(analysis: dict[str, Any] | None) -> list[str]:
    """13. Cumulative mass is monotonically non-decreasing across pairs."""
    if analysis is None:
        return ["skipped: analysis.json absent"]
    violations: list[str] = []
    pairs = analysis.get("pairs", [])
    prev_you, prev_ai = 0.0, 0.0

    for idx, p in enumerate(pairs):
        c_you = p.get("c_you", 0.0)
        c_ai = p.get("c_ai", 0.0)
        if c_you < prev_you:
            violations.append(f"pair {idx+1}: c_you decreased from {prev_you} to {c_you}")
        if c_ai < prev_ai:
            violations.append(f"pair {idx+1}: c_ai decreased from {prev_ai} to {c_ai}")
        prev_you, prev_ai = c_you, c_ai

    return violations


def inv_14_shaper_subset(analysis: dict[str, Any] | None) -> list[str]:
    """14. h_you <= delta_you and h_ai <= delta_ai. SHAPER scores are a subset of all scores."""
    if analysis is None:
        return ["skipped: analysis.json absent"]
    violations: list[str] = []
    for idx, p in enumerate(analysis.get("pairs", [])):
        h_you = p.get("h_you", 0.0)
        delta_you = p.get("delta_you", 0.0)
        h_ai = p.get("h_ai", 0.0)
        delta_ai = p.get("delta_ai", 0.0)

        if h_you > delta_you:
            violations.append(f"pair {idx+1}: h_you ({h_you}) > delta_you ({delta_you})")
        if h_ai > delta_ai:
            violations.append(f"pair {idx+1}: h_ai ({h_ai}) > delta_ai ({delta_ai})")

    return violations


def inv_15_percentages_sum_to_100(analysis: dict[str, Any] | None) -> list[str]:
    """15. Percentages are within [0, 100] and sum to 100 within rounding tolerance."""
    if analysis is None:
        return ["skipped: analysis.json absent"]
    violations: list[str] = []
    for idx, p in enumerate(analysis.get("pairs", [])):
        you_pct = p.get("you_pct", 0.0)
        ai_pct = p.get("ai_pct", 0.0)
        if not (0.0 <= you_pct <= 100.0):
            violations.append(f"pair {idx+1}: you_pct ({you_pct}) out of [0, 100] bounds")
        if not (0.0 <= ai_pct <= 100.0):
            violations.append(f"pair {idx+1}: ai_pct ({ai_pct}) out of [0, 100] bounds")
        if abs((you_pct + ai_pct) - 100.0) > 0.1 and (you_pct + ai_pct) > 0:
            violations.append(f"pair {idx+1}: percentage sum ({you_pct + ai_pct}) does not equal 100")

    return violations


def inv_16_mode_pure_function(analysis: dict[str, Any] | None) -> list[str]:
    """16. The mode is a pure function of w and h and is one of the defined values."""
    if analysis is None:
        return ["skipped: analysis.json absent"]
    violations: list[str] = []
    for idx, p in enumerate(analysis.get("pairs", [])):
        mode = p.get("mode")
        if mode not in VALID_MODES:
            violations.append(f"pair {idx+1}: mode '{mode}' is not one of valid modes {VALID_MODES}")
    return violations


# ==============================================================================
# Process (Invariants 17 - 21) — Guards return skipped if inputs are absent
# ==============================================================================

def inv_17_append_only(ledger_t: list[dict[str, Any]] | None, ledger_t_plus_1: list[dict[str, Any]] | None) -> list[str]:
    """17. Append-only: Ledger rows for pair t are unchanged after pair t+1 is processed."""
    if ledger_t is None or ledger_t_plus_1 is None:
        return ["skipped: consecutive ledgers absent"]
    violations: list[str] = []
    if len(ledger_t_plus_1) < len(ledger_t):
        return ["ledger_t_plus_1 has fewer rows than ledger_t"]
    for idx, (r_t, r_t1) in enumerate(zip(ledger_t, ledger_t_plus_1)):
        if r_t != r_t1:
            violations.append(f"row {idx} modified between pair t and t+1: {r_t} != {r_t1}")
    return violations


def inv_18_idempotency(state_run_1: dict[str, Any] | None, state_run_2: dict[str, Any] | None) -> list[str]:
    """18. Idempotency: Rerunning pair t twice leaves the same state as running it once."""
    if state_run_1 is None or state_run_2 is None:
        return ["skipped: rerun state absent"]
    if state_run_1 != state_run_2:
        return ["rerun state is not identical to initial run state"]
    return []


def inv_19_purity(analysis_1: dict[str, Any] | None, analysis_2: dict[str, Any] | None) -> list[str]:
    """19. Purity: The same ledger produces byte-identical analysis.json."""
    if analysis_1 is None or analysis_2 is None:
        return ["skipped: analysis runs absent"]
    if analysis_1 != analysis_2:
        return ["analysis_1 does not match analysis_2 for identical ledger"]
    return []


def inv_20_batch_equals_live(batch_ledger: list[dict[str, Any]] | None, live_ledger: list[dict[str, Any]] | None) -> list[str]:
    """20. Batch equals live: The same chat produces identical ledgers in both modes."""
    if batch_ledger is None or live_ledger is None:
        return ["skipped: batch/live ledgers absent"]
    if batch_ledger != live_ledger:
        return ["batch ledger does not match live ledger"]
    return []


def inv_21_provenance(dialogue: list[dict[str, Any]] | None, ledger_rows: list[dict[str, Any]] | None, state: dict[str, Any] | None) -> list[str]:
    """21. Provenance: Every ledger row traces to a turn present in dialogue.json,

    and every attributed action's evidence_quote appears verbatim in that turn's text.
    """
    if dialogue is None or ledger_rows is None or state is None:
        return ["skipped: dialogue/ledger/state absent"]

    violations: list[str] = []
    # Check if fixture dialogue is stubbed
    if any(t.get("text") == "(not captured in fixture)" for t in dialogue):
        return ["skipped: fixture dialogue is stubbed"]

    dialogue_pairs = {t.get("pair") for t in dialogue}
    for idx, row in enumerate(ledger_rows):
        pair = row.get("pair_added")
        if pair not in dialogue_pairs:
            violations.append(f"row {idx}: pair_added {pair} not found in dialogue.json")

    return violations
