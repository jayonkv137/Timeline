#!/usr/bin/env python3
"""scripts/replay_stage4.py — Stage 4 Quantification & Projection Replay across E1 Corpus.

Executes Stage 4 quantification and projections offline across the 10 E1 corpus ledgers
(zero LLM calls, zero network). Validates runtime checks, writes snapshots.json and
panel_bundle.json, updates run/report.json with final metrics, and prints the summary
table required by E2.S8.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engine.checks import run_pair_checks
from engine.projections.panel import export_panel_projections
from engine.projections.workspace import project_chat_directory
from engine.quant import compute_decisions, compute_direction, compute_mode

DEFAULT_CORPUS_CHATS = [
    "c03_coding_short",
    "c04_writing_short",
    "c05_research_medium",
    "c07_research_short",
    "c10_research_short",
    "c16_research_short",
    "c17_research_short",
    "c20_coding_short",
    "c27_creative_short",
    "c30_creative_short",
]


def replay_chat(chat_id: str) -> dict[str, Any]:
    """Replay Stage 4 for one chat from existing ledger and state."""
    chat_dir = REPO_ROOT / "data" / "chats" / chat_id
    if not chat_dir.exists():
        raise FileNotFoundError(f"Chat directory not found: {chat_dir}")

    ledger_path = chat_dir / "ledger.jsonl"
    state_path = chat_dir / "state.json"
    dialogue_path = chat_dir / "dialogue.json"
    if not dialogue_path.exists():
        dialogue_path = REPO_ROOT / "data" / "corpus" / chat_id / "dialogue.json"

    with open(ledger_path, "r", encoding="utf-8") as f:
        ledger_rows = [json.loads(line) for line in f if line.strip()]

    with open(state_path, "r", encoding="utf-8") as f:
        state_dict = json.load(f)

    dialogue = []
    if dialogue_path.exists():
        with open(dialogue_path, "r", encoding="utf-8") as f:
            dialogue = json.load(f)

    # 1. Project panel_bundle.json and snapshots.json
    bundle, snapshots = export_panel_projections(
        target_dir=chat_dir,
        ledger_rows=ledger_rows,
        state_dict=state_dict,
    )

    # Workspace bundle projection
    project_chat_directory(chat_dir=chat_dir)

    num_pairs = len(bundle["pairs"])

    # 2. Compute Stage 4 facts directly for reporting
    dir_facts = compute_direction(ledger_rows, max_pair=num_pairs)
    dec_facts = compute_decisions(
        ledger_rows,
        state_requirements=state_dict.get("requirements", []),
        max_pair=num_pairs,
    )
    mode_facts = compute_mode(
        ledger_rows,
        state_requirements=state_dict.get("requirements", []),
        max_pair=num_pairs,
    )

    final_dir = dir_facts[-1] if dir_facts else None
    final_dec = dec_facts[-1] if dec_facts else None
    modes_list = [m.mode for m in mode_facts]

    final_info = {
        "direction": [final_dir.you_pct, final_dir.ai_pct] if final_dir else [0.0, 0.0],
        "decisions": [final_dec.you_count, final_dec.ai_count] if final_dec else [0, 0],
        "mode": modes_list[-1] if modes_list else "QUIET",
    }

    # 3. Run runtime invariant checks
    chk_res = run_pair_checks(
        state=state_dict,
        ledger_rows=ledger_rows,
        dialogue=dialogue,
        current_pair=num_pairs,
    )

    # 4. Update report.json with Stage 4 metrics
    report_path = chat_dir / "run" / "report.json"
    if report_path.exists():
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                rep_data = json.load(f)
            rep_data["final"] = final_info
            # Merge passed checks
            current_passed = set(rep_data.get("checks", {}).get("passed", []))
            current_passed.update(chk_res.passed)
            rep_data["checks"]["passed"] = sorted(list(current_passed))
            rep_data["checks"]["failed"] = sorted(list(set(chk_res.failed)))
            rep_data["quote_matches"] = {
                "exact": chk_res.quote_matches.get("exact", 0),
                "whitespace_normalised": chk_res.quote_matches.get("whitespace_normalised", 0),
                "segmented": chk_res.quote_matches.get("segmented", 0),
                "fuzzy": chk_res.quote_matches.get("fuzzy", 0),
            }
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(rep_data, f, indent=2)
                f.write("\n")
        except Exception as e:
            print(f"Warning: failed to update {report_path}: {e}", file=sys.stderr)

    exact_cnt = chk_res.quote_matches.get("exact", 0)
    fuzzy_cnt = chk_res.quote_matches.get("fuzzy", 0)

    return {
        "chat_id": chat_id,
        "pairs": num_pairs,
        "you_pct": final_dir.you_pct if final_dir else 0.0,
        "ai_pct": final_dir.ai_pct if final_dir else 0.0,
        "decisions_you": final_dec.you_count if final_dec else 0,
        "decisions_ai": final_dec.ai_count if final_dec else 0,
        "modes": modes_list,
        "exact_quotes": exact_cnt,
        "fuzzy_quotes": fuzzy_cnt,
        "quote_matches": chk_res.quote_matches,
        "checks_healthy": chk_res.healthy,
        "checks_failed": chk_res.failed,
        "requirements_count": len(state_dict.get("requirements", [])),
    }


def main():
    print("=" * 80)
    print("STAGE 4 CORPUS REPLAY (10 E1 CHATS — DETERMINISTIC ARITHMETIC)")
    print("=" * 80)

    results = []
    odd_chats = []

    for chat_id in DEFAULT_CORPUS_CHATS:
        res = replay_chat(chat_id)
        results.append(res)

        # Detect structural peculiarities per S8 brief:
        # zero requirements, 100/0 splits, every pair QUIET
        reasons = []
        if res["requirements_count"] == 0:
            reasons.append("zero requirements")
        if res["you_pct"] == 100.0 or res["ai_pct"] == 100.0 or res["you_pct"] == 0.0:
            reasons.append(f"extreme split ({res['you_pct']}% / {res['ai_pct']}%)")
        if all(m == "QUIET" for m in res["modes"]):
            reasons.append("every pair QUIET")

        if reasons:
            odd_chats.append((chat_id, ", ".join(reasons)))

    # Print markdown table
    print()
    print("| chat | pairs | you % | AI % | decisions you/AI | mode per pair | quote match exact/fuzzy |")
    print("|---|---|---|---|---|---|---|")
    for r in results:
        modes_str = "[" + ", ".join(r["modes"]) + "]"
        dec_str = f"{r['decisions_you']} / {r['decisions_ai']}"
        qm_str = f"{r['exact_quotes']} exact / {r['fuzzy_quotes']} fuzzy"
        print(f"| {r['chat_id']} | {r['pairs']} | {r['you_pct']}% | {r['ai_pct']}% | {dec_str} | {modes_str} | {qm_str} |")

    print()
    print("-" * 80)
    print("INVARIANT HEALTH STATUS:")
    all_healthy = True
    for r in results:
        status = "PASS" if r["checks_healthy"] else f"FAIL ({r['checks_failed']})"
        print(f"  {r['chat_id']:<25} : {status}")
        if not r["checks_healthy"]:
            all_healthy = False

    print("-" * 80)
    print("STRUCTURAL PECULIARITY AUDIT (flagged, not fixed, per brief):")
    if odd_chats:
        for cid, reason in odd_chats:
            print(f"  * {cid}: {reason}")
    else:
        print("  None. All chats produced active requirements, non-degenerate splits, and active modes.")

    print("=" * 80)
    print(f"STAGE 4 REPLAY STATUS: {'SUCCESS (ALL INVARIANTS PASS)' if all_healthy else 'FAILED'}")
    print("=" * 80)


if __name__ == "__main__":
    main()
