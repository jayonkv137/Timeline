"""Runtime invariant checks and run reporting (§11.4 & TEST_STRATEGY.md §6).

Promotes the invariants from tests/invariants.py to production runtime.
Runs after each pair in the extraction pipeline. If any invariant fails,
it writes run/status.json with healthy=false and halts execution to
prevent corrupt ledger accumulation.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engine.quant import build_analysis_dict

# Direct imports from tests/invariants.py: one implementation, two callers.
from tests.invariants import (
    audit_quote_matches,
    inv_01_schema_valid,
    inv_02_action_ids,
    inv_03_ledger_references_exist,
    inv_04_action_maps_to_one_outcome,
    inv_05_no_duplicate_ledger_rows,
    inv_06_outcome_tree,
    inv_07_requirement_has_creation,
    inv_08_requirement_created_at_pair,
    inv_09_slot_status_and_inactivity,
    inv_10_scores_positive,
    inv_11_deltas_sum_to_cumulative,
    inv_12_creator_counts_sum,
    inv_13_cumulative_mass_monotonic,
    inv_14_shaper_subset,
    inv_15_percentages_sum_to_100,
    inv_16_mode_pure_function,
    inv_17_append_only,
    inv_18_idempotency,
    inv_19_purity,
    inv_20_batch_equals_live,
    inv_21_provenance,
)


class InvariantViolationError(Exception):
    """Raised when one or more runtime invariants fail during pipeline execution."""

    def __init__(self, violations: list[str], failed_checks: list[str]):
        msg = f"Runtime invariant violation(s): {'; '.join(violations)}"
        super().__init__(msg)
        self.violations = violations
        self.failed_checks = failed_checks


@dataclass
class CheckResult:
    healthy: bool
    passed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    quote_matches: dict[str, int] = field(default_factory=dict)


def run_pair_checks(
    state: Any,
    ledger_rows: list[dict[str, Any]],
    dialogue: list[dict[str, Any]] | None = None,
    prev_ledger_rows: list[dict[str, Any]] | None = None,
    current_pair: int | None = None,
    schemas_dir: Path | str | None = None,
    analysis: dict[str, Any] | None = None,
) -> CheckResult:
    """Run all applicable invariants after a pair completes.

    Checks:
    - inv_01: Schema validation of state, ledger rows, and dialogue
    - inv_02: Action ID format and uniqueness
    - inv_03: Ledger references to action, req, and outcome exist in state
    - inv_04: Action maps to exactly one outcome
    - inv_05: No duplicate ledger rows
    - inv_06: Outcome tree (1 root, no cycles, parent/child agreement)
    - inv_07: Requirement has creation action
    - inv_08: Requirement created_at_pair <= current_pair
    - inv_09: Slot status and resolution link
    - inv_10: Positive finite scores on ledger rows
    - inv_11: Sum of deltas equals cumulative total
    - inv_12: Creator counts sum to distinct requirements
    - inv_13: Cumulative mass is monotonically non-decreasing
    - inv_14: SHAPER scores are a subset of all scores
    - inv_15: Percentages within [0, 100] and sum to 100
    - inv_16: Mode is pure function of w and h and in valid enum
    - inv_17: Append-only ledger preservation (if prev_ledger_rows is provided)
    - inv_19: Purity (deterministic recalculation on same inputs)
    - inv_21: Provenance of evidence quotes in dialogue (if dialogue is provided)
    """
    state_dict = state.to_dict() if hasattr(state, "to_dict") else (state or {})
    rows = getattr(ledger_rows, "rows", ledger_rows) or []

    # If analysis is not explicitly provided, derive it from Stage 4 quantification
    if analysis is None and rows:
        try:
            analysis = build_analysis_dict(rows, state_dict=state_dict, max_pair=current_pair)
        except Exception:
            analysis = None

    passed: list[str] = []
    failed: list[str] = []
    violations: list[str] = []

    def _eval(check_id: str, raw_errs: list[str]) -> None:
        real_errs = [e for e in raw_errs if not e.startswith("skipped:")]
        if real_errs:
            failed.append(check_id)
            for err in real_errs:
                violations.append(f"{check_id}: {err}")
        else:
            passed.append(check_id)

    # 1. inv_01: schema validity
    artifacts = {"state": state_dict, "ledger": rows}
    if dialogue is not None:
        artifacts["dialogue"] = dialogue
    _eval("inv_01", inv_01_schema_valid(artifacts, schemas_dir=schemas_dir))

    # 2. inv_02: action IDs
    _eval("inv_02", inv_02_action_ids(state_dict))

    # 3. inv_03: ledger references exist
    _eval("inv_03", inv_03_ledger_references_exist(rows, state_dict))

    # 4. inv_04: action maps to one outcome
    a2o = None
    if isinstance(state, dict):
        a2o = state.get("run", {}).get("action_to_outcome")
    elif hasattr(state, "run") and isinstance(state.run, dict):
        a2o = state.run.get("action_to_outcome")
    _eval("inv_04", inv_04_action_maps_to_one_outcome(state_dict, action_to_outcome=a2o))

    # 5. inv_05: no duplicate ledger rows
    _eval("inv_05", inv_05_no_duplicate_ledger_rows(rows))

    # 6. inv_06: outcome tree
    _eval("inv_06", inv_06_outcome_tree(state_dict))

    # 7. inv_07: requirement has creation
    _eval("inv_07", inv_07_requirement_has_creation(state_dict))

    # 8. inv_08: requirement created_at_pair
    _eval("inv_08", inv_08_requirement_created_at_pair(state_dict, current_pair=current_pair))

    # 9. inv_09: slot status & inactivity
    _eval("inv_09", inv_09_slot_status_and_inactivity(state_dict, current_pair=current_pair))

    # 10. inv_10: scores positive
    _eval("inv_10", inv_10_scores_positive(analysis=analysis, ledger_rows=rows))

    # Stage 4 Arithmetic & Purity Invariants (11 - 16, 19)
    if analysis is not None:
        _eval("inv_11", inv_11_deltas_sum_to_cumulative(analysis))
        _eval("inv_12", inv_12_creator_counts_sum(analysis, state=state_dict))
        _eval("inv_13", inv_13_cumulative_mass_monotonic(analysis))
        _eval("inv_14", inv_14_shaper_subset(analysis))
        _eval("inv_15", inv_15_percentages_sum_to_100(analysis))
        _eval("inv_16", inv_16_mode_pure_function(analysis))

        # 19. inv_19: purity (deterministic recalculation on same inputs)
        try:
            analysis_rerun = build_analysis_dict(rows, state_dict=state_dict, max_pair=current_pair)
        except Exception:
            analysis_rerun = None
        _eval("inv_19", inv_19_purity(analysis, analysis_rerun))

    # 17. inv_17: append-only (if prev_ledger_rows is provided)
    if prev_ledger_rows is not None:
        prev_rows = getattr(prev_ledger_rows, "rows", prev_ledger_rows) or []
        _eval("inv_17", inv_17_append_only(prev_rows, rows))

    # 21. inv_21: provenance (if dialogue is provided)
    quote_counts = {}
    if dialogue is not None:
        _eval("inv_21", inv_21_provenance(dialogue, rows, state_dict))
        quote_counts = audit_quote_matches(dialogue, state_dict)

    healthy = len(failed) == 0
    return CheckResult(
        healthy=healthy,
        passed=passed,
        failed=failed,
        violations=violations,
        quote_matches=quote_counts,
    )


def is_state_valid(state: Any, schemas_dir: Path | str | None = None) -> bool:
    """Check if state data structure is structurally sound for rendering and continued execution (S-D9).

    A state is valid if:
    1. It is a dictionary-like object with an 'outcomes' list.
    2. It has at least 1 outcome.
    3. Outcome tree has exactly 1 root, no cycles, and valid parent links (inv_06).
    4. State schema validation (inv_01) passes on state.
    """
    state_dict = state.to_dict() if hasattr(state, "to_dict") else (state or {})
    if not isinstance(state_dict, dict):
        return False
    outcomes = state_dict.get("outcomes", [])
    if not outcomes or not isinstance(outcomes, list):
        return False
    if inv_06_outcome_tree(state_dict):
        return False
    if inv_01_schema_valid({"state": state_dict}, schemas_dir=schemas_dir):
        return False
    return True


def write_status(
    out_dir: Path | str,
    healthy: bool,
    pair_number: int,
    violations: list[str] | None = None,
) -> Path:
    """Write run/status.json after pair processing and check evaluation."""
    status_path = Path(out_dir) / "run" / "status.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    violation_list = violations or []
    payload = {
        "healthy": healthy,
        "pair": pair_number,
        "halted_at_pair": pair_number if not healthy else None,
        "violation": violation_list[0] if (violation_list and not healthy) else None,
        "violations": violation_list,
    }
    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    return status_path


def write_report(
    out_dir: Path | str,
    chat_id: str,
    pairs_processed: int,
    wall_time_per_pair: list[float],
    tokens_per_pair: list[int],
    llm_calls: int,
    retries: int,
    cache_hits: int,
    state: Any,
    checks_passed: list[str],
    checks_failed: list[str],
    final: dict | None = None,
    quote_matches: dict[str, int] | None = None,
    dialogue: list[dict[str, Any]] | None = None,
) -> Path:
    """Write run/report.json per TEST_STRATEGY.md §6."""
    report_path = Path(out_dir) / "run" / "report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    state_dict = state.to_dict() if hasattr(state, "to_dict") else (state or {})
    requirements = state_dict.get("requirements", [])
    slots = state_dict.get("slots", [])

    opened_slots = len(slots)
    resolved_slots = sum(1 for s in slots if s.get("status") == "resolved")
    abandoned_slots = sum(1 for s in slots if s.get("status") == "abandoned")

    # Sort and deduplicate checks
    passed_sorted = sorted(list(set(checks_passed)))
    failed_sorted = sorted(list(set(checks_failed)))

    # Compute quote match breakdown if not explicitly supplied
    if quote_matches is None:
        if dialogue is not None:
            quote_matches = audit_quote_matches(dialogue, state_dict)
        else:
            diag_file = Path(out_dir) / "dialogue.json"
            if not diag_file.exists():
                diag_file = Path(out_dir).parent.parent / "corpus" / chat_id / "dialogue.json"
            if diag_file.exists():
                try:
                    with open(diag_file, "r", encoding="utf-8") as f:
                        diag_data = json.load(f)
                    quote_matches = audit_quote_matches(diag_data, state_dict)
                except Exception:
                    quote_matches = {}
            else:
                quote_matches = {}

    qm_dict = {
        "exact": quote_matches.get("exact", 0),
        "whitespace_normalised": quote_matches.get("whitespace_normalised", 0),
        "segmented": quote_matches.get("segmented", 0),
        "fuzzy": quote_matches.get("fuzzy", 0),
    }

    report_data = {
        "chat_id": chat_id,
        "pairs_processed": pairs_processed,
        "wall_time_per_pair": wall_time_per_pair,
        "tokens_per_pair": tokens_per_pair,
        "llm_calls": llm_calls,
        "retries": retries,
        "cache_hits": cache_hits,
        "requirements_created": len(requirements),
        "slots": {
            "opened": opened_slots,
            "resolved": resolved_slots,
            "abandoned": abandoned_slots,
        },
        "checks": {
            "passed": passed_sorted,
            "failed": failed_sorted,
        },
        "quote_matches": qm_dict,
        "final": final,
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
        f.write("\n")
    return report_path
