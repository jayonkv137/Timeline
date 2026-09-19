#!/usr/bin/env python3
"""scripts/grade_golden.py — Golden Chat Grading Harness (E1.S1).

Compares engine output for golden_01 (state.json) against data/corpus/golden_01/expected.md.
Emits a side-by-side alignment table and computes owner-judged match and spurious rates.

Grading Taxonomy (Owner-judged, not automated embedding similarity):
- match (m)    : extracted requirement captures the expected requirement (allowing different wording).
- miss (x)     : expected requirement was not extracted by the engine.
- spurious (s) : extracted item is not a binding requirement (advice, small talk, method detail).
- split (p)    : one expected requirement was fragmented into several extracted requirements.
- merged (g)   : several expected requirements were collapsed into one extracted requirement.

Usage:
  python3 scripts/grade_golden.py
  python3 scripts/grade_golden.py --run-dir data/chats/golden_01 --grades-file data/chats/golden_01/grading.json
  python3 scripts/grade_golden.py --interactive
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EXPECTED_PATH = REPO_ROOT / "data/corpus/golden_01/expected.md"
DEFAULT_RUN_DIR = REPO_ROOT / "data/chats/golden_01"


def parse_expected_requirements(expected_path: Path) -> List[Dict[str, str]]:
    """Parse ground-truth requirements from expected.md.

    Looks for Req_NN (Description) patterns or markdown table rows.
    """
    if not expected_path.exists():
        raise FileNotFoundError(f"Expected file not found: {expected_path}")

    with open(expected_path, "r", encoding="utf-8") as f:
        content = f.read()

    requirements: List[Dict[str, str]] = []
    seen_ids: Set[str] = set()

    # Match patterns like: Req_01 (Portfolio about page revision)
    pattern = r"(Req_\d+)\s*\(([^)]+)\)"
    matches = re.findall(pattern, content)

    for req_id, desc in matches:
        if req_id not in seen_ids:
            seen_ids.add(req_id)
            requirements.append({
                "id": req_id,
                "text": desc.strip(),
            })

    # Sort deterministically by id
    requirements.sort(key=lambda r: r["id"])
    return requirements


def load_extracted_requirements(state_path: Path) -> List[Dict[str, Any]]:
    """Load extracted requirements from state.json if present."""
    if not state_path.exists():
        return []

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        reqs = data.get("requirements", [])
        return reqs
    except Exception as exc:
        print(f"Warning: Failed to load {state_path}: {exc}", file=sys.stderr)
        return []


def compute_metrics(
    expected_reqs: List[Dict[str, str]],
    extracted_reqs: List[Dict[str, Any]],
    grades: Dict[str, Any],
) -> Dict[str, Any]:
    """Compute match, miss, spurious, split, merged counts and rates.

    grades mapping structure:
      "extracted_marks": { "<outcome_id>||<req_id>": {"status": "match|spurious|split|merged", "target": "Req_01"} }
    """
    total_expected = len(expected_reqs)
    total_found = len(extracted_reqs)

    if total_found == 0:
        return {
            "expected": total_expected,
            "found": 0,
            "match": 0,
            "miss": total_expected,
            "spurious": 0,
            "split": 0,
            "merged": 0,
            "match_rate": 0.0,
            "spurious_rate": 0.0,
        }

    extracted_marks = grades.get("extracted_marks", {})
    
    match_count = 0
    spurious_count = 0
    split_count = 0
    merged_count = 0

    accounted_expected_ids: Set[str] = set()

    for r in extracted_reqs:
        key = f"{r.get('outcome_id', '')}||{r.get('req_id', '')}"
        mark_info = extracted_marks.get(key, {})
        status = mark_info.get("status", "unreviewed")
        targets = mark_info.get("targets", [])
        target = mark_info.get("target")
        if target and not targets:
            targets = [target]

        if status == "match":
            match_count += 1
            for t in targets:
                accounted_expected_ids.add(t)
        elif status == "spurious":
            spurious_count += 1
        elif status == "split":
            split_count += 1
            for t in targets:
                accounted_expected_ids.add(t)
        elif status == "merged":
            merged_count += 1
            for t in targets:
                accounted_expected_ids.add(t)

    miss_count = total_expected - len(accounted_expected_ids)
    if miss_count < 0:
        miss_count = 0

    # match rate = (covered expected requirements) / total expected
    match_rate = (len(accounted_expected_ids) / total_expected * 100.0) if total_expected > 0 else 0.0
    spurious_rate = (spurious_count / total_found * 100.0) if total_found > 0 else 0.0

    return {
        "expected": total_expected,
        "found": total_found,
        "match": match_count,
        "miss": miss_count,
        "spurious": spurious_count,
        "split": split_count,
        "merged": merged_count,
        "match_rate": match_rate,
        "spurious_rate": spurious_rate,
    }


def format_side_by_side_table(
    expected_reqs: List[Dict[str, str]],
    extracted_reqs: List[Dict[str, Any]],
    grades: Dict[str, Any],
) -> str:
    """Format an aligned comparison table for owner review."""
    lines = []
    lines.append("=" * 100)
    lines.append("GOLDEN CHAT EXTRACTION REVIEW: expected.md vs state.json")
    lines.append("=" * 100)
    lines.append(f"{'STATUS':<10} | {'EXPECTED GROUND TRUTH':<42} | {'EXTRACTED FROM ENGINE':<42}")
    lines.append("-" * 100)

    extracted_marks = grades.get("extracted_marks", {})
    
    # Map expected target -> list of extracted keys
    target_to_extracted: Dict[str, List[Dict[str, Any]]] = {}
    spurious_items: List[Dict[str, Any]] = []
    unreviewed_items: List[Dict[str, Any]] = []

    for r in extracted_reqs:
        key = f"{r.get('outcome_id', '')}||{r.get('req_id', '')}"
        mark = extracted_marks.get(key, {})
        status = mark.get("status", "unreviewed")
        targets = mark.get("targets", [])
        target = mark.get("target")
        if target and not targets:
            targets = [target]

        if status == "spurious":
            spurious_items.append(r)
        elif status in ("match", "split", "merged"):
            for t in targets:
                target_to_extracted.setdefault(t, []).append(r)
        else:
            unreviewed_items.append(r)

    # Print expected rows first
    for exp in expected_reqs:
        exp_id = exp["id"]
        exp_desc = f"[{exp_id}] {exp['text']}"
        matched = target_to_extracted.get(exp_id, [])

        if not matched:
            lines.append(f"{'[MISS]':<10} | {exp_desc[:42]:<42} | {'(no matching extraction)':<42}")
        else:
            for idx, m in enumerate(matched):
                key = f"{m.get('outcome_id', '')}||{m.get('req_id', '')}"
                status = extracted_marks.get(key, {}).get("status", "match").upper()
                ext_desc = f"({m.get('outcome_id')}/{m.get('req_id')}) {m.get('text', '')}"
                exp_col = exp_desc[:42] if idx == 0 else ""
                lines.append(f"[{status:<8}] | {exp_col:<42} | {ext_desc[:42]:<42}")

    # Print spurious items
    for spur in spurious_items:
        ext_desc = f"({spur.get('outcome_id')}/{spur.get('req_id')}) {spur.get('text', '')}"
        lines.append(f"{'[SPURIOUS]':<10} | {'(none — spurious)':<42} | {ext_desc[:42]:<42}")

    # Print unreviewed items
    for unk in unreviewed_items:
        ext_desc = f"({unk.get('outcome_id')}/{unk.get('req_id')}) {unk.get('text', '')}"
        lines.append(f"{'[UNMARKED]':<10} | {'(unassigned)':<42} | {ext_desc[:42]:<42}")

    lines.append("-" * 100)
    return "\n".join(lines)


def format_summary_report(metrics: Dict[str, Any]) -> str:
    """Format summary report matching exact spec block."""
    lines = [
        f"requirements expected : {metrics['expected']}",
        f"requirements found    : {metrics['found']}",
        f"match                 : {metrics['match']}  (same meaning, allowing different wording)",
        f"miss                  : {metrics['miss']}",
        f"spurious              : {metrics['spurious']}",
        f"split                 : {metrics['split']}  (one expected requirement fragmented into several)",
        f"merged                : {metrics['merged']}  (several expected requirements collapsed into one)",
        f"match rate            : {metrics['match_rate']:.1f}%",
        f"spurious rate         : {metrics['spurious_rate']:.1f}%",
    ]
    return "\n".join(lines)


def interactive_marking(
    expected_reqs: List[Dict[str, str]],
    extracted_reqs: List[Dict[str, Any]],
    grades_file: Path,
) -> Dict[str, Any]:
    """Interactively walk the owner through marking each extracted requirement."""
    print("\n--- ENTERING INTERACTIVE MARKING SESSION ---")
    print("Available Expected Requirements:")
    for exp in expected_reqs:
        print(f"  {exp['id']}: {exp['text']}")
    print("\nMarking options per extracted requirement:")
    print("  m <Req_ID>       : Match expected requirement (e.g. 'm Req_02')")
    print("  s                : Spurious (advice, method detail, non-requirement)")
    print("  p <Req_ID>       : Split part of expected requirement")
    print("  g <Req_1,Req_2>  : Merged multiple expected requirements")
    print("  q                : Quit and save progress")

    extracted_marks = {}

    for idx, r in enumerate(extracted_reqs, 1):
        key = f"{r.get('outcome_id', '')}||{r.get('req_id', '')}"
        print(f"\n[{idx}/{len(extracted_reqs)}] Extracted: ({r.get('outcome_id')}/{r.get('req_id')})")
        print(f"Text: \"{r.get('text')}\"")
        print(f"Type: {r.get('type')} | Role: {r.get('explicit_or_implicit')}")

        while True:
            choice = input("Marking > ").strip()
            if not choice:
                continue
            if choice.lower() == "q":
                break
            if choice.lower() == "s":
                extracted_marks[key] = {"status": "spurious"}
                break
            elif choice.lower().startswith("m "):
                target = choice[2:].strip()
                extracted_marks[key] = {"status": "match", "target": target}
                break
            elif choice.lower().startswith("p "):
                target = choice[2:].strip()
                extracted_marks[key] = {"status": "split", "target": target}
                break
            elif choice.lower().startswith("g "):
                targets = [t.strip() for t in choice[2:].split(",") if t.strip()]
                extracted_marks[key] = {"status": "merged", "targets": targets}
                break
            else:
                print("Invalid input. Use m <ID>, s, p <ID>, g <ID,ID>, or q.")

    grades = {"extracted_marks": extracted_marks}
    grades_file.parent.mkdir(parents=True, exist_ok=True)
    with open(grades_file, "w", encoding="utf-8") as f:
        json.dump(grades, f, indent=2)
    print(f"\nSaved markings to {grades_file}")
    return grades


def main():
    parser = argparse.ArgumentParser(description="Grade golden_01 extraction against expected.md.")
    parser.add_argument(
        "--expected",
        type=Path,
        default=DEFAULT_EXPECTED_PATH,
        help=f"Path to expected.md (default: {DEFAULT_EXPECTED_PATH})",
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=DEFAULT_RUN_DIR,
        help=f"Path to run directory containing state.json (default: {DEFAULT_RUN_DIR})",
    )
    parser.add_argument(
        "--grades-file",
        type=Path,
        default=None,
        help="Optional path to grades JSON file. Defaults to <run-dir>/grading.json",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Launch interactive terminal marking session.",
    )

    args = parser.parse_args()

    grades_file = args.grades_file or (args.run_dir / "grading.json")

    # 1. Parse expected requirements
    expected_reqs = parse_expected_requirements(args.expected)

    # 2. Load extracted requirements from state.json
    state_file = args.run_dir / "state.json"
    extracted_reqs = load_extracted_requirements(state_file)

    # 3. Load or acquire grades
    grades = {}
    if args.interactive and extracted_reqs:
        grades = interactive_marking(expected_reqs, extracted_reqs, grades_file)
    elif grades_file.exists():
        try:
            with open(grades_file, "r", encoding="utf-8") as f:
                grades = json.load(f)
        except Exception as exc:
            print(f"Warning: Failed to load {grades_file}: {exc}", file=sys.stderr)

    # 4. Compute metrics
    metrics = compute_metrics(expected_reqs, extracted_reqs, grades)

    # 5. Output side-by-side table & summary report
    print(format_side_by_side_table(expected_reqs, extracted_reqs, grades))
    print()
    print(format_summary_report(metrics))

    return 0


if __name__ == "__main__":
    sys.exit(main())
