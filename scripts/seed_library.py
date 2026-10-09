#!/usr/bin/env python3
"""Seed the local COTRACE library with the 10 processed prototype chats.

Copies the 10 processed corpus chats into the local library under $COTRACE_HOME
(or a specified destination), projects their workspace_bundle.json artifacts
using the engine's deterministic projection with ZERO LLM calls, and ensures
metadata and layout contracts are satisfied per STANDALONE_V1_PLAN §2.3 & §3.4.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any

# Ensure repo root is on sys.path for direct script execution
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engine.projections.workspace import load_chat_metadata, project_chat_directory
from server.library import Library, atomic_write_json

logger = logging.getLogger("seed_library")

PROCESSED_CHATS: list[str] = [
    "c05_research_medium",
    "c04_writing_short",
    "c03_coding_short",
    "c07_research_short",
    "c20_coding_short",
    "c27_creative_short",
    "c30_creative_short",
    "c10_research_short",
    "c16_research_short",
    "c17_research_short",
]

DISPLAY_TITLES: dict[str, str] = {
    "c05_research_medium": "AI creativity · paper research",
    "c04_writing_short": "Human–AI interaction design",
    "c03_coding_short": "Interactive portfolio",
    "c07_research_short": "Co-creation research",
    "c20_coding_short": "Figma migration",
    "c27_creative_short": "Jellyfish motion study",
    "c30_creative_short": "Language-learning videos",
    "c10_research_short": "Project contribution",
    "c16_research_short": "Co-creative panel",
    "c17_research_short": "Datafied Society",
}


def seed_library(
    library_dir: str | Path | None = None,
    clean: bool = False,
    force: bool = True,
    source_chats_dir: str | Path | None = None,
) -> list[str]:
    """Seed the COTRACE library with processed chats and project their bundles."""
    repo_root = Path(__file__).resolve().parent.parent
    src_dir = Path(source_chats_dir) if source_chats_dir else (repo_root / "data" / "chats")
    corpus_dir = repo_root / "data" / "corpus"

    lib = Library(library_dir)
    lib.ensure_layout()

    if clean and lib.chats_dir.is_dir():
        for item in lib.chats_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)

    seeded_ids: list[str] = []

    for cid in PROCESSED_CHATS:
        chat_src = src_dir / cid
        if not chat_src.is_dir():
            logger.warning("Source chat directory %s does not exist, skipping.", chat_src)
            continue

        dest_dir = lib.chat_dir(cid)
        if dest_dir.exists() and not force:
            logger.info("Chat %s already exists in library, skipping (use --force to overwrite).", cid)
            seeded_ids.append(cid)
            continue

        if dest_dir.exists():
            shutil.rmtree(dest_dir)

        dest_dir.mkdir(parents=True, exist_ok=True)

        # Copy data files
        copy_files = [
            "dialogue.json",
            "state.json",
            "ledger.jsonl",
            "snapshots.json",
            "panel_bundle.json",
            "full_export.json",
            "source_meta.json",
            "meta.json",
        ]
        for fname in copy_files:
            src_file = chat_src / fname
            if not src_file.exists() and corpus_dir.is_dir():
                corpus_file = corpus_dir / cid / fname
                if corpus_file.exists():
                    src_file = corpus_file
            if src_file.is_file():
                shutil.copy2(src_file, dest_dir / fname)

        # Copy run directory if present
        if (chat_src / "run").is_dir():
            shutil.copytree(chat_src / "run", dest_dir / "run", dirs_exist_ok=True)
        else:
            (dest_dir / "run").mkdir(parents=True, exist_ok=True)

        # Generate / sync workspace bundle through engine projection
        bundle_path = dest_dir / "workspace_bundle.json"
        bundle = project_chat_directory(dest_dir, output_path=bundle_path)

        # Ensure meta.json exists and stays in sync with projected bundle
        display_title = DISPLAY_TITLES.get(cid, bundle.get("title", cid))
        if display_title != bundle.get("title"):
            bundle["title"] = display_title
            atomic_write_json(bundle_path, bundle)

        meta_path = dest_dir / "meta.json"
        meta: dict[str, Any] = {
            "id": cid,
            "title": display_title,
            "category": bundle.get("category", "General"),
            "totalPairs": bundle.get("totalPairs", 0),
            "source": bundle.get("source", {"platform": "archive"}),
            "status": bundle.get("status", "ready"),
        }
        if (dest_dir / "source_meta.json").is_file():
            try:
                sm = json.loads((dest_dir / "source_meta.json").read_text(encoding="utf-8"))
                meta["source"] = sm.get("source", meta["source"])
                meta["title"] = sm.get("title", meta["title"])
                meta["category"] = sm.get("category", meta["category"])
            except Exception:
                pass
        atomic_write_json(meta_path, meta)

        seeded_ids.append(cid)

    # Ensure descending modification timestamps so Library.list_chats()
    # sorts in canonical reference order (PROCESSED_CHATS[0] is newest).
    base_mtime = time.time()
    for idx, cid in enumerate(PROCESSED_CHATS):
        cdir = lib.chat_dir(cid)
        if cdir.is_dir():
            target_time = base_mtime - idx * 10
            for item in [cdir, cdir / "workspace_bundle.json", cdir / "meta.json"]:
                if item.exists():
                    os.utime(item, (target_time, target_time))

    return seeded_ids


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed COTRACE library with processed chats")
    parser.add_argument(
        "--library",
        "-l",
        type=str,
        default=None,
        help="Target library directory (default: $COTRACE_HOME or ~/Cotrace)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove existing chats from library before seeding",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=True,
        help="Overwrite existing chat directories",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Source directory for processed chats (default: data/chats)",
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    seeded = seed_library(
        library_dir=args.library,
        clean=args.clean,
        force=args.force,
        source_chats_dir=args.source,
    )

    lib = Library(args.library)
    chats = lib.list_chats()

    print(f"\nSuccessfully seeded {len(seeded)} chats into library at {lib.root}:\n")
    print(f"{'Chat ID':<22} | {'Pairs':<5} | {'Category':<10} | {'You % / AI %':<14} | {'Title'}")
    print("-" * 85)
    for c in chats:
        share_str = f"{c['share']['you']}% / {c['share']['ai']}%"
        print(f"{c['id']:<22} | {c['totalPairs']:<5} | {c['category']:<10} | {share_str:<14} | {c['title'][:32]}")
    print("\nAll chats ready and served by local library.")


if __name__ == "__main__":
    main()
