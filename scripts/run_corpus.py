#!/usr/bin/env python3
"""scripts/run_corpus.py — Multi-chat extraction runner and timing/token curve analysis.

Executes the full extraction pipeline (Steps 1a->1b->1c->2->3) across the classified
corpus chats, evaluates Invariants 1-9 on every output, records per-pair wall time
and token curves, and generates the Step E1.S8 verification report.

Usage:
  .venv/bin/python3 scripts/run_corpus.py --mode record
  .venv/bin/python3 scripts/run_corpus.py --mode replay
"""
import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engine.config import load_config
from engine.llm import LLMClient
from engine.llm_cache import CachingLLMClient
from engine.pipeline import run_chat
from tests.invariants import (
    inv_01_schema_valid,
    inv_02_action_ids,
    inv_03_ledger_references_exist,
    inv_04_action_maps_to_one_outcome,
    inv_05_no_duplicate_ledger_rows,
    inv_06_outcome_tree,
    inv_07_requirement_has_creation,
    inv_08_requirement_created_at_pair,
    inv_09_slot_status_and_inactivity,
    inv_21_provenance,
)

DEFAULT_CORPUS_CHATS = [
    "c10_research_short",
    "c16_research_short",
    "c17_research_short",
    "c27_creative_short",
    "c30_creative_short",
    "c03_coding_short",
    "c20_coding_short",
    "c04_writing_short",
    "c07_research_short",
    "c05_research_medium",
]


from engine.checks import run_pair_checks
from engine.state import State


def evaluate_chat_invariants(chat_dir: Path) -> dict[str, str]:
    """Evaluate invariants 1-9, 10, and 21 against a chat's generated artifacts."""
    state_path = chat_dir / "state.json"
    ledger_path = chat_dir / "ledger.jsonl"
    dialogue_path = chat_dir / "dialogue.json"

    if not state_path.exists() or not ledger_path.exists():
        return {"error": "Missing state.json or ledger.jsonl"}

    state = State.load(chat_dir)

    ledger_rows = []
    with open(ledger_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                ledger_rows.append(json.loads(line))

    dialogue = []
    if dialogue_path.exists():
        with open(dialogue_path, "r", encoding="utf-8") as f:
            dialogue = json.load(f)

    chk = run_pair_checks(
        state=state,
        ledger_rows=ledger_rows,
        dialogue=dialogue,
        current_pair=None,
    )

    results = {}
    for p in chk.passed:
        results[p] = "PASS"
    for f in chk.failed:
        results[f] = "FAIL"
    if chk.violations:
        results["violations"] = "; ".join(chk.violations)

    return results


def main():
    parser = argparse.ArgumentParser(description="Run full corpus extraction and timing analysis.")
    parser.add_argument("--chats", nargs="+", default=DEFAULT_CORPUS_CHATS, help="Chat IDs to run")
    parser.add_argument("--mode", type=str, default="record", choices=["record", "replay", "off"], help="LLM cache mode")
    parser.add_argument("--clear", action="store_true", help="Clear existing artifacts before running")
    parser.add_argument("--out-dir", type=str, default=None, help="Root folder for chat outputs")

    args = parser.parse_args()
    chats_to_run = args.chats
    base_out_dir = Path(args.out_dir) if args.out_dir else REPO_ROOT / "data/chats"

    print("================================================================================")
    print("CORPUS EXTRACTION PIPELINE RUNNER (STEP E1.S8)")
    print(f"Target Chats : {len(chats_to_run)} chats")
    print(f"Cache Mode   : {args.mode}")
    print(f"Output Root  : {base_out_dir}")
    print("================================================================================\n")

    config = load_config()
    chat_summaries = []
    wall_times_by_pair = defaultdict(list)
    tokens_by_pair = defaultdict(list)

    total_start = time.monotonic()

    for idx, chat_id in enumerate(chats_to_run, 1):
        dialogue_path = REPO_ROOT / f"data/corpus/{chat_id}/dialogue.json"
        if not dialogue_path.exists():
            print(f"[{idx}/{len(chats_to_run)}] Skipping {chat_id}: dialogue.json not found.")
            continue

        with open(dialogue_path, "r", encoding="utf-8") as f:
            raw_dialogue = json.load(f)
        pair_count = len({t.get("pair") for t in raw_dialogue if t.get("pair") is not None})

        out_dir = base_out_dir / chat_id
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n--- [{idx}/{len(chats_to_run)}] Running {chat_id} ({pair_count} pairs) ---")
        chat_start = time.monotonic()

        inner = None
        if args.mode in ("record", "off"):
            inner = LLMClient(config, out_dir=out_dir)
        client = CachingLLMClient(inner_client=inner, mode=args.mode, out_dir=out_dir)

        try:
            report = run_chat(
                client=client,
                config=config,
                chat_id=chat_id,
                dialogue=dialogue_path,
                out_dir=out_dir,
                clear_existing=True,
            )
            chat_elapsed = round(time.monotonic() - chat_start, 2)
            pairs_done = report.get("pairs_processed", pair_count)
            reqs_created = report.get("requirements_created", 0)
            slots_data = report.get("slots", {})
            wall_times = report.get("wall_time_per_pair", [])
            tokens = report.get("tokens_per_pair", [])

            for p_idx, wt in enumerate(wall_times, 1):
                wall_times_by_pair[p_idx].append(wt)
            for p_idx, tk in enumerate(tokens, 1):
                tokens_by_pair[p_idx].append(tk)

            # Invariant checks
            inv_results = evaluate_chat_invariants(out_dir)
            all_invs_pass = all(v == "PASS" for v in inv_results.values())

            summary = {
                "chat_id": chat_id,
                "pairs": pairs_done,
                "total_time": chat_elapsed,
                "reqs": reqs_created,
                "slots": slots_data,
                "invariants_pass": all_invs_pass,
                "inv_results": inv_results,
                "wall_times": wall_times,
                "tokens": tokens,
            }
            chat_summaries.append(summary)

            inv_status = "ALL PASS" if all_invs_pass else "FAILURES DETECTED"
            print(f"Completed {chat_id}: {pairs_done} pairs in {chat_elapsed}s | Reqs: {reqs_created} | Invariants: {inv_status}")

        except Exception as exc:
            print(f"Error running {chat_id}: {exc}", file=sys.stderr)
            chat_summaries.append({
                "chat_id": chat_id,
                "pairs": 0,
                "total_time": round(time.monotonic() - chat_start, 2),
                "error": str(exc),
                "invariants_pass": False,
            })

    total_elapsed = round(time.monotonic() - total_start, 2)

    # Print Summary Table
    print("\n" + "=" * 90)
    print("CORPUS EXTRACTION EXECUTION SUMMARY")
    print("=" * 90)
    print(f"{'CHAT ID':<25} | {'PAIRS':<5} | {'TIME(s)':<8} | {'REQS':<5} | {'SLOTS (O/R/A)':<15} | {'INVARIANTS (1-9,21)':<15}")
    print("-" * 90)
    for s in chat_summaries:
        if "error" in s:
            print(f"{s['chat_id']:<25} | {'ERR':<5} | {s['total_time']:<8.1f} | {'-':<5} | {'-':<15} | ERROR: {s['error']}")
        else:
            slots_str = f"{s['slots'].get('opened', 0)}/{s['slots'].get('resolved', 0)}/{s['slots'].get('abandoned', 0)}"
            inv_str = "PASS (10/10)" if s["invariants_pass"] else "FAIL"
            print(f"{s['chat_id']:<25} | {s['pairs']:<5} | {s['total_time']:<8.1f} | {s['reqs']:<5} | {slots_str:<15} | {inv_str:<15}")
    print("=" * 90)
    print(f"Total Chats Processed: {len(chat_summaries)} | Total Elapsed Time: {total_elapsed}s\n")

    # Print Timing and Token Curves
    print("=" * 90)
    print("SCALING ANALYSIS: TIMING AND TOKEN CURVES BY PAIR INDEX")
    print("=" * 90)
    print(f"{'PAIR INDEX':<12} | {'CHATS COUNT':<12} | {'AVG TIME (s)':<15} | {'AVG TOKENS':<15}")
    print("-" * 90)
    max_pair = max(wall_times_by_pair.keys()) if wall_times_by_pair else 0
    for p in range(1, max_pair + 1):
        times = wall_times_by_pair.get(p, [])
        toks = tokens_by_pair.get(p, [])
        avg_time = sum(times) / len(times) if times else 0.0
        avg_tok = sum(toks) / len(toks) if toks else 0.0
        print(f"Pair {p:<7} | {len(times):<12} | {avg_time:<15.2f} | {avg_tok:<15.1f}")
    print("=" * 90)


if __name__ == "__main__":
    main()
