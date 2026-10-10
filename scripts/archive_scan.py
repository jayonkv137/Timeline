#!/usr/bin/env python3
"""
scripts/archive_scan.py — Multi-Platform Archive Ingestion & Triage Scanner
Per IMPORT_SPEC v1.1 Amendment and C_TRACK_BRIEF.md (Phases C0 & C1).

CLI frontend delegating to engine.importer library functions with zero LLM calls.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from engine.importer import (
    IMAGE_EXTENSIONS,
    IMPORT_SPEC_VERSION,
    SENSITIVE_KEYWORDS,
    STOPWORDS_DE,
    STOPWORDS_EN,
    check_sensitive,
    detect_language,
    extract_claude_message_content,
    parse_claude_export,
    scan_archive as lib_scan_archive,
    simulate_pairing,
)


def print_triage_report(registry: List[Dict[str, Any]]):
    """Prints formatted triage summary per C1 requirement."""
    print("\n" + "=" * 95)
    print("ARCHIVE TRIAGE REPORT (MECHANICAL METRICS — ZERO LLM CALLS)")
    print("=" * 95)

    total_convs = len(registry)
    total_pairs = sum(r["pairs"] for r in registry)
    total_chars = sum(r["total_chars"] for r in registry)
    clean_count = sum(1 for r in registry if r["fidelity_grade"] == "clean")
    degraded_count = sum(1 for r in registry if r["fidelity_grade"] == "degraded")
    unusable_count = sum(1 for r in registry if r["fidelity_grade"] == "unusable")
    sensitive_count = sum(1 for r in registry if r["sensitive"])
    code_count = sum(1 for r in registry if r["has_code"])

    short_band = sum(1 for r in registry if r["pairs"] <= 5 and r["pairs"] > 0)
    medium_band = sum(1 for r in registry if 6 <= r["pairs"] <= 20)
    long_band = sum(1 for r in registry if r["pairs"] >= 21)
    zero_pairs = sum(1 for r in registry if r["pairs"] == 0)

    print(f"Total Conversations Ingested : {total_convs}")
    print(f"Total Usable Dialogue Pairs  : {total_pairs:,}")
    print(f"Total Character Volume       : {total_chars:,}")
    print("-" * 95)
    print(f"Fidelity Grades Split        : Clean={clean_count} | Degraded={degraded_count} | Unusable={unusable_count}")
    print(f"Length Distributions         : Short(<=5)={short_band} | Medium(6-20)={medium_band} | Long(21+)={long_band} | Empty={zero_pairs}")
    print(f"Content Features             : With Code={code_count} | Flagged Sensitive={sensitive_count}")
    print("-" * 95)
    print(f"{'conv_id':<24} {'plat':<5} {'pairs':>5} {'chars':>8} {'img/p':>6} {'code':<5} {'lang':<4} {'grade':<9} {'title'}")
    print("-" * 95)

    sorted_rows = sorted(registry, key=lambda x: x["pairs"], reverse=True)
    for r in sorted_rows[:30]:
        code_str = "yes" if r["has_code"] else "no"
        title_disp = r["title"][:38]
        if r["sensitive"]:
            title_disp = "[REDACTED SENSITIVE]"
        print(
            f"{r['conv_id'][:23]:<24} {r['platform']:<5} {r['pairs']:>5} "
            f"{r['total_chars']:>8} {r['images_per_pair']:>6.2f} {code_str:<5} "
            f"{r['language']:<4} {r['fidelity_grade']:<9} {title_disp}"
        )

    print("=" * 95)


def scan_archive(
    source_path: Optional[Path],
    archive_dir: Path,
    report_only: bool = False,
):
    """Executes the ingestion scan using engine.importer."""
    try:
        registry = lib_scan_archive(source_path, archive_dir, report_only=report_only)
        if not report_only:
            print(f"Successfully archived {len(registry)} conversations to {(archive_dir / 'claude').resolve()}")
            print(f"Wrote master registry: {(archive_dir / 'registry.json').resolve()} ({len(registry)} rows)")
        print_triage_report(registry)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Multi-platform archive scan & triage tool.")
    parser.add_argument("--export", type=Path, default=None, help="Path to raw export zip or conversations.json")
    parser.add_argument("--out", type=Path, default=Path("data/archive"), help="Archive root directory")
    parser.add_argument("--report", action="store_true", help="Print triage report from existing registry")
    args = parser.parse_args()

    scan_archive(args.export, args.out, report_only=args.report)


if __name__ == "__main__":
    main()
