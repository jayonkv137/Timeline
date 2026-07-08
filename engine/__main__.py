"""CLI Entrypoint for the Offline CLI engine.

Supports:
  python -m engine run --input <file> --out <dir> [--pairs N] [--resume]
"""
import argparse
import sys
from pathlib import Path

from engine.config import load_config
from engine.runner import load_dialogue_from_export, run_pipeline


def main():
    parser = argparse.ArgumentParser(description="Offline CLI Engine for Cotrace")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the pipeline on an exported chat")
    run_parser.add_argument("--input", "-i", required=True, help="Path to exported chat JSON")
    run_parser.add_argument("--out", "-o", required=True, help="Path to output directory")
    run_parser.add_argument("--pairs", "-p", type=int, default=None, help="Limit processing to first N pairs")
    run_parser.add_argument("--resume", action="store_true", help="Resume from last completed pair")
    run_parser.add_argument(
        "--contributions-only",
        action="store_true",
        help="Recompute Stage 4 from existing ledger without LLM calls",
    )

    args = parser.parse_args()

    if args.command == "run":
        config = load_config()
        
        if args.contributions_only:
            from engine.state import State
            from engine.artifacts import read_ledger
            from engine.quant import compute_stage4, write_stage4_artifacts
            
            out_path = Path(args.out)
            state = State.load(out_path)
            ledger_rows = read_ledger(out_path / "ledger.jsonl")
            snapshots, panel_bundle = compute_stage4(state, ledger_rows)
            write_stage4_artifacts(out_path, snapshots, panel_bundle)
            print(f"Stage 4 recomputed from existing ledger. Outputs written to {args.out}")
            sys.exit(0)

            
        dialogue = load_dialogue_from_export(args.input)
        run_pipeline(
            config=config,
            dialogue=dialogue,
            out_dir=args.out,
            limit_pairs=args.pairs,
            resume=args.resume
        )
        print(f"Pipeline successfully completed for {args.input}. Outputs written to {args.out}")


if __name__ == "__main__":
    main()
