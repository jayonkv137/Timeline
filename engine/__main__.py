"""Command line interface for the COTRACE engine.

Usage:
    python -m engine project <chat_dir> [--output <output_path>]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from engine.projections.workspace import project_chat_directory
from engine.report import generate_chat_report


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

    # Subcommand: report
    report_parser = subparsers.add_parser(
        "report",
        help="Generate a readable Markdown report for a chat",
    )
    report_parser.add_argument(
        "chat",
        type=str,
        help="Chat identifier or directory path (e.g. c05_research_medium or data/chats/c05_research_medium)",
    )
    report_parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Optional output file path to write Markdown (defaults to stdout)",
    )

    # Subcommand: brainmap (BRAIN_REGIONS_SPEC, track B1)
    brainmap_parser = subparsers.add_parser(
        "brainmap",
        help="Place chats in the Brain: regions by content, evidence-only links, flat-map layout (zero LLM)",
    )
    brainmap_parser.add_argument("paths", nargs="+", help="Chat folders or parents of chat folders (e.g. data/corpus or <library>/chats)")
    brainmap_parser.add_argument("--engine-root", default=None, help="Folder holding processed artifacts per chat id (e.g. data/chats) when they live apart from the dialogue")
    brainmap_parser.add_argument("--previous", default=None, help="Previous brain_map.json: placed chats stay pinned, owner names survive")
    brainmap_parser.add_argument("--output", "-o", default=None, help="Output path (defaults to stdout)")

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

    if args.subcommand == "report":
        try:
            report_md = generate_chat_report(args.chat)
        except Exception as e:
            print(f"Error generating report: {e}", file=sys.stderr)
            return 1

        if args.output:
            out_file = Path(args.output)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(report_md, encoding="utf-8")
            print(f"Report written to {out_file}")
        else:
            print(report_md)
        return 0

    if args.subcommand == "brainmap":
        from engine.brainmap import main as brainmap_main
        return brainmap_main(args.paths, args.output, args.engine_root, args.previous)

    return 0


if __name__ == "__main__":
    sys.exit(main())
