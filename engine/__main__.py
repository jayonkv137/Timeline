"""Command line interface for the COTRACE engine.

Usage:
    python -m engine project <chat_dir> [--output <output_path>]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from engine.projections.workspace import project_chat_directory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m engine",
        description="COTRACE engine CLI",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Subcommand: project
    project_parser = subparsers.add_parser(
        "project",
        help="Project chat directory into a validated workspace_bundle.json artifact",
    )
    project_parser.add_argument(
        "chat_dir",
        type=str,
        help="Path to chat directory (e.g. data/chats/c05_research_medium)",
    )
    project_parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Custom output file path (defaults to <chat_dir>/workspace_bundle.json)",
    )

    args = parser.parse_args(argv)

    if args.subcommand == "project":
        chat_path = Path(args.chat_dir)
        if not chat_path.exists():
            print(f"Error: chat directory not found: {chat_path}", file=sys.stderr)
            return 1

        bundle = project_chat_directory(
            chat_dir=chat_path,
            output_path=args.output,
        )
        dest = args.output or (chat_path / "workspace_bundle.json")
        print(
            f"Projected workspace bundle to {dest} "
            f"({bundle['id']}, {bundle['totalPairs']} pairs, "
            f"{len(bundle['nodes'])} nodes, {len(bundle['atoms'])} atoms)"
        )
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
