#!/usr/bin/env python3
"""scripts/run_chat.py — Run extraction pipeline on a chat with caching and runtime invariants.

Usage:
  python3 scripts/run_chat.py --chat-id golden_01 --mode record
  python3 scripts/run_chat.py --chat-id golden_01 --mode replay
"""
import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engine.config import load_config
from engine.llm import LLMClient
from engine.llm_cache import CachingLLMClient
from engine.pipeline import run_chat


def main():
    parser = argparse.ArgumentParser(description="Run full extraction pipeline on a dialogue.")
    parser.add_argument("--chat-id", type=str, default="golden_01", help="Chat identifier")
    parser.add_argument("--dialogue", type=str, default=None, help="Path to dialogue.json")
    parser.add_argument("--out-dir", type=str, default=None, help="Output folder")
    parser.add_argument("--mode", type=str, default="record", choices=["record", "replay", "off"], help="LLM cache mode")
    parser.add_argument("--clear", action="store_true", help="Clear existing artifacts before running")
    parser.add_argument("--budget-cap", type=float, default=1.0, help="Budget cap in USD (default: $1.00)")

    args = parser.parse_args()

    chat_id = args.chat_id
    dialogue_path = Path(args.dialogue) if args.dialogue else REPO_ROOT / f"data/corpus/{chat_id}/dialogue.json"
    if not dialogue_path.exists():
        alt = REPO_ROOT / f"data/chats/{chat_id}/dialogue.json"
        if alt.exists():
            dialogue_path = alt
        else:
            print(f"Error: Dialogue file not found at {dialogue_path} or {alt}", file=sys.stderr)
            sys.exit(1)

    out_dir = Path(args.out_dir) if args.out_dir else REPO_ROOT / f"data/chats/{chat_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    config = load_config()
    from engine.budget import BudgetGuard
    budget_guard = BudgetGuard(cap=args.budget_cap, chat_id=chat_id)

    inner = None
    if args.mode in ("record", "off"):
        inner = LLMClient(config, out_dir=out_dir, budget_guard=budget_guard)

    client = CachingLLMClient(inner_client=inner, mode=args.mode, out_dir=out_dir)
    client.set_budget_guard(budget_guard)

    print(f"Starting pipeline extraction for chat: {chat_id}")
    print(f"  Dialogue:   {dialogue_path}")
    print(f"  Out dir:    {out_dir}")
    print(f"  Mode:       {args.mode}")
    print(f"  Budget Cap: ${args.budget_cap:.2f}")

    try:
        report = run_chat(
            client=client,
            config=config,
            chat_id=chat_id,
            dialogue=dialogue_path,
            out_dir=out_dir,
            clear_existing=args.clear,
            budget_guard=budget_guard,
        )
        usage_sum = getattr(client, "usage_meter", None)
        meter_summary = usage_sum.summary() if usage_sum else {}

        print("\n=== RUN COMPLETE ===")
        print(f"Pairs processed: {report.get('pairs_processed')}")
        print(f"Wall times:      {report.get('wall_time_per_pair')}")
        print(f"Total time:      {sum(report.get('wall_time_per_pair', [])):.2f}s")
        print(f"Tokens:          {report.get('tokens_per_pair')}")
        print(f"Requirements:    {report.get('requirements_created')}")
        print(f"Slots:           {report.get('slots')}")
        print(f"Total Cost:      ${meter_summary.get('cost', 0.0):.6f}")
        print(f"Checks passed:   {len(report.get('checks', {}).get('passed', []))}")
        print(f"Checks failed:   {report.get('checks', {}).get('failed', [])}")
        return 0
    except Exception as exc:
        print(f"\nRun halted with error: {exc}", file=sys.stderr)
        status_path = out_dir / "run" / "status.json"
        if status_path.exists():
            with open(status_path) as f:
                print(f"status.json: {f.read()}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
