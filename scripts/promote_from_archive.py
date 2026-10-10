#!/usr/bin/env python3
"""
scripts/promote_from_archive.py — Promote Canonical Archive Chats into Engine Corpus
Per IMPORT_SPEC v1.1 Amendment §B and C_TRACK_BRIEF.md §C3.

CLI frontend delegating to engine.importer library functions.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from engine.importer import (
    IMPORT_SPEC_VERSION,
    get_dialogue_schema_path,
    process_turns_to_dialogue,
    promote_conversation,
    validate_dialogue_json,
)

# 10 Medium + 10 Long target selections from archive
PRESET_20_CHATS = [
    # 10 Medium (6-20 pairs)
    {"conv_id": "claude_10d9c356-d170-441d-afcf-c954635e3fd3", "task_type": "learning", "domain": "German grammar prepositions"},
    {"conv_id": "claude_e37cf126-3537-4bd9-9b95-93b703fd3cd9", "task_type": "planning", "domain": "Bremen apartment search"},
    {"conv_id": "claude_edc5bc0a-4262-4fe5-88f9-db650a988ad6", "task_type": "writing", "domain": "profile bio feedback"},
    {"conv_id": "claude_2571bc83-722a-4638-8458-78cf36e56895", "task_type": "planning", "domain": "shared flat inquiry"},
    {"conv_id": "claude_aa1c8265-85e2-4087-ba4d-f290c8e5e2b9", "task_type": "planning", "domain": "study schedule planning"},
    {"conv_id": "claude_bc585cbf-5fb9-4116-b867-d72a7be837da", "task_type": "planning", "domain": "session structure planning"},
    {"conv_id": "claude_b8ec9e80-82b4-4d30-934d-24a6500cd68e", "task_type": "learning", "domain": "extended tutoring request"},
    {"conv_id": "claude_851e8cc8-3965-4b9c-8c89-daf9da35cf38", "task_type": "writing", "domain": "document proofreading and formatting"},
    {"conv_id": "claude_68fe697c-f629-4264-980b-6a43986cbe6e", "task_type": "writing", "domain": "German professional scheduling"},
    {"conv_id": "claude_beba7fc8-3364-46ac-8408-c7c417507b6d", "task_type": "coding", "domain": "SVG pipeline architecture diagram"},

    # 10 Long (21+ pairs)
    {"conv_id": "claude_7519cf98-266c-49e1-a871-539e713b5af2", "task_type": "writing", "domain": "cover letter drafting"},
    {"conv_id": "claude_8a2f0550-4588-4f06-b240-f90f6842dfa7", "task_type": "learning", "domain": "German vocabulary consolidation"},
    {"conv_id": "claude_8e7b589b-6ec5-4a72-a0bf-73430e450747", "task_type": "coding", "domain": "engineering project handover"},
    {"conv_id": "claude_cc569aed-bf2e-4f8a-b3c6-bc391ed254ce", "task_type": "planning", "domain": "administrative paperwork guidance"},
    {"conv_id": "claude_0efe01b6-7470-4769-995f-599dbc8ae077", "task_type": "writing", "domain": "AI master degree statement of purpose"},
    {"conv_id": "claude_cd03ee08-04e9-4331-b788-f2cf348d8a57", "task_type": "coding", "domain": "system architecture specifications"},
    {"conv_id": "claude_2eef82f5-6d02-43d5-88d1-a8471a776752", "task_type": "research", "domain": "aviation AI case study analysis"},
    {"conv_id": "claude_faba7c62-899c-4c51-84bd-e461a121dd91", "task_type": "planning", "domain": "software development workflow planning"},
    {"conv_id": "claude_c9bf6c91-570b-4c77-99b2-8c13c00ffea8", "task_type": "creative", "domain": "academic slide presentation design"},
    {"conv_id": "claude_bb740c1d-4eed-4dc6-9928-337b2d928dfc", "task_type": "coding", "domain": "project repository audit and refactor"},
]


def promote_chats(
    target_list: List[Dict[str, str]],
    archive_dir: Path,
    corpus_dir: Path,
    schema_path: Path,
):
    registry_file = archive_dir / "registry.json"

    if not registry_file.exists():
        print(f"Error: {registry_file} not found.", file=sys.stderr)
        sys.exit(1)

    with open(registry_file, "r", encoding="utf-8") as f:
        registry_map = {r["conv_id"]: r for r in json.load(f)}

    existing_folders = [p.name for p in corpus_dir.iterdir() if p.is_dir() and p.name.startswith("c")]
    existing_nums = []
    for f in existing_folders:
        m = re.match(r"^c(\d+)_", f)
        if m:
            existing_nums.append(int(m.group(1)))

    next_num = (max(existing_nums) + 1) if existing_nums else 1

    print(f"Preparing {len(target_list)} chats starting at c{next_num:02d}...\n")

    promoted_entries = []
    manifest_additions = []

    for item in target_list:
        cid = item["conv_id"]
        reg_info = registry_map.get(cid)
        if not reg_info:
            print(f"Warning: {cid} not found in registry. Skipping.")
            continue

        archive_json_path = archive_dir / "claude" / f"{cid}.json"
        if not archive_json_path.exists():
            print(f"Warning: File {archive_json_path} missing. Skipping.")
            continue

        with open(archive_json_path, "r", encoding="utf-8") as f:
            archive_data = json.load(f)

        pairs = reg_info.get("pairs", 0)
        if pairs == 0:
            print(f"Warning: {cid} has 0 pairs. Skipping.")
            continue

        length_band = "short" if pairs <= 5 else ("medium" if pairs <= 20 else "long")
        task_type = item.get("task_type", "planning")
        domain = item.get("domain", "")

        chat_id = f"c{next_num:02d}_{task_type}_{length_band}"
        next_num += 1

        dest_dir = corpus_dir / chat_id

        try:
            res = promote_conversation(
                conv_data=archive_data,
                dest_dir=dest_dir,
                chat_id=chat_id,
                category=task_type.capitalize(),
                task_type=task_type,
                domain=domain,
                schema_path=schema_path,
            )
        except Exception as exc:
            print(f"Error promoting {cid}: {exc}", file=sys.stderr)
            sys.exit(1)

        promoted_entries.append({
            "chat_id": chat_id,
            "conv_id": cid,
            "pairs": pairs,
            "grade": reg_info["fidelity_grade"],
            "task_type": task_type,
            "length_band": length_band,
            "title": reg_info["raw_title"],
        })

        img_dropped = reg_info["images_dropped"]
        manifest_additions.append({
            "id": chat_id,
            "source_file": "source.json",
            "pairs": pairs,
            "images_dropped": img_dropped,
            "injected_turns": 0,
            "tool_narration_turns": 0,
            "empty_turns": 0,
            "fidelity_grade": reg_info["fidelity_grade"],
            "title": reg_info["raw_title"],
        })

    # Update data/corpus/selection_manifest.json
    selection_manifest_path = corpus_dir / "selection_manifest.json"
    selection_record = {
        "selected_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "import_spec_version": IMPORT_SPEC_VERSION,
        "selection_name": "10_medium_10_long_benchmark_selection",
        "total_selected": len(promoted_entries),
        "entries": promoted_entries,
    }
    with open(selection_manifest_path, "w", encoding="utf-8") as f:
        json.dump(selection_record, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Synchronize data/corpus/manifest.json
    manifest_path = corpus_dir / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            full_manifest = json.load(f)

        existing_ids = set(c["id"] for c in full_manifest.get("chats", []))
        for m_add in manifest_additions:
            if m_add["id"] not in existing_ids:
                full_manifest.setdefault("chats", []).append(m_add)

        all_chats = full_manifest.get("chats", [])
        full_manifest["total_chats"] = len(all_chats)
        full_manifest["total_pairs"] = sum(c.get("pairs", 0) for c in all_chats)
        full_manifest["fidelity_totals"] = {
            "images_dropped": sum(c.get("images_dropped", 0) for c in all_chats),
            "injected_turns": sum(c.get("injected_turns", 0) for c in all_chats),
            "tool_narration_turns": sum(c.get("tool_narration_turns", 0) for c in all_chats),
            "empty_turns": sum(c.get("empty_turns", 0) for c in all_chats),
            "grades": {
                "clean": sum(1 for c in all_chats if c.get("fidelity_grade") == "clean"),
                "degraded": sum(1 for c in all_chats if c.get("fidelity_grade") == "degraded"),
                "unusable": sum(1 for c in all_chats if c.get("fidelity_grade") == "unusable"),
            },
        }

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(full_manifest, f, indent=2, ensure_ascii=False)
            f.write("\n")

    print("=" * 95)
    print("PROMOTION COMPLETE — 20 NEW CORPUS CHATS PREPARED")
    print("=" * 95)
    print(f"{'Chat ID':<22} {'Pairs':>5} {'Grade':<9} {'Type':<10} {'Title'}")
    print("-" * 95)
    for p in promoted_entries:
        print(f"{p['chat_id']:<22} {p['pairs']:>5} {p['grade']:<9} {p['task_type']:<10} {p['title'][:45]}")
    print("=" * 95)
    print(f"\nSelection manifest written -> {selection_manifest_path.resolve()}")
    print(f"Main manifest updated      -> {manifest_path.resolve()}")


def main():
    parser = argparse.ArgumentParser(description="Promote archive chats into data/corpus.")
    parser.add_argument("--archive", type=Path, default=Path("data/archive"), help="Archive directory")
    parser.add_argument("--corpus", type=Path, default=Path("data/corpus"), help="Corpus directory")
    parser.add_argument("--schema", type=Path, default=get_dialogue_schema_path(), help="Dialogue schema")
    args = parser.parse_args()

    promote_chats(PRESET_20_CHATS, args.archive, args.corpus, args.schema)


if __name__ == "__main__":
    main()
