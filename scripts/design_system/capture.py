#!/usr/bin/env python3
"""
scripts/design_system/capture.py

Extracts processed chat data from data/chats/<id>/ into self-contained, sanitized
JSON fixtures under mockups/captures/<short_id>.json for UI mockups and prototypes.
Adheres strictly to the DDR-000a Real-Data Design Protocol.
"""

import sys
import os
import json
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_CHATS = REPO_ROOT / "data" / "chats"
MOCKUPS_CAPTURES = REPO_ROOT / "mockups" / "captures"


def resolve_chat_dir(chat_identifier: str) -> Path:
    """Finds matching chat directory in data/chats/."""
    direct = DATA_CHATS / chat_identifier
    if direct.is_dir():
        return direct
    
    # Try prefix matching (e.g. "c05" matches "c05_research_medium")
    for d in DATA_CHATS.iterdir():
        if d.is_dir() and d.name.startswith(f"{chat_identifier}_"):
            return d
    
    raise FileNotFoundError(f"Chat '{chat_identifier}' not found in {DATA_CHATS}")


def capture_chat(chat_identifier: str) -> Path:
    """Extracts chat into mockups/captures/<short_id>.json."""
    chat_dir = resolve_chat_dir(chat_identifier)
    chat_id = chat_dir.name
    short_id = chat_id.split("_")[0]

    # Required files
    dialogue_file = chat_dir / "dialogue.json"
    panel_file = chat_dir / "panel_bundle.json"
    state_file = chat_dir / "state.json"
    report_file = chat_dir / "run" / "report.json"

    if not dialogue_file.exists():
        raise FileNotFoundError(f"Missing dialogue.json in {chat_dir}")
    if not panel_file.exists():
        raise FileNotFoundError(f"Missing panel_bundle.json in {chat_dir}. Run engine replay first.")
    if not state_file.exists():
        raise FileNotFoundError(f"Missing state.json in {chat_dir}")

    with open(dialogue_file, "r", encoding="utf-8") as f:
        dialogue = json.load(f)

    with open(panel_file, "r", encoding="utf-8") as f:
        panel_bundle = json.load(f)

    with open(state_file, "r", encoding="utf-8") as f:
        state = json.load(f)

    report = {}
    if report_file.exists():
        with open(report_file, "r", encoding="utf-8") as f:
            report = json.load(f)

    # Derive chat title
    title = chat_id.replace("_", " ").title()
    if state.get("outcomes"):
        root_outcomes = [o for o in state["outcomes"] if o.get("parent") is None]
        if root_outcomes and root_outcomes[0].get("text"):
            title = root_outcomes[0]["text"]

    pairs_data = panel_bundle.get("pairs", [])
    total_pairs = len(pairs_data)

    # Build dialogue turns lookup
    turns_by_pair = {}
    for msg in dialogue:
        p = msg.get("pair")
        if p is not None:
            turns_by_pair.setdefault(p, []).append({
                "speaker": msg.get("speaker"),
                "text": msg.get("text", ""),
                "ts": msg.get("ts")
            })

    # Combined fixture
    capture = {
        "schema_version": "1.0",
        "chat_id": chat_id,
        "short_id": short_id,
        "title": title,
        "total_pairs": total_pairs,
        "metrics": report.get("final", {}),
        "outcomes": state.get("outcomes", []),
        "pairs": pairs_data,
        "dialogue_by_pair": turns_by_pair,
        "captured_at": "2026-10-08T00:00:00Z",
        "provenance": {
            "source": f"data/chats/{chat_id}",
            "protocol": "DDR-000a Real-Data Design Protocol"
        }
    }

    MOCKUPS_CAPTURES.mkdir(parents=True, exist_ok=True)
    out_file = MOCKUPS_CAPTURES / f"{short_id}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(capture, f, indent=2, ensure_ascii=False)

    print(f"Captured {chat_id} -> {out_file} ({total_pairs} pairs, {len(state.get('outcomes', []))} outcomes)")
    return out_file


def main():
    parser = argparse.ArgumentParser(description="Capture chat data for design mockups.")
    parser.add_argument("chat_id", nargs="?", default="c05", help="Chat ID or prefix (default: c05)")
    parser.add_argument("--all", action="store_true", help="Capture all available corpus chats")

    args = parser.parse_args()

    if args.all:
        for d in sorted(DATA_CHATS.iterdir()):
            if d.is_dir() and (d / "panel_bundle.json").exists():
                try:
                    capture_chat(d.name)
                except Exception as e:
                    print(f"Error capturing {d.name}: {e}", file=sys.stderr)
    else:
        capture_chat(args.chat_id)


if __name__ == "__main__":
    main()
