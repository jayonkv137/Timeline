#!/usr/bin/env python3
"""
scripts/archive_scan.py — Multi-Platform Archive Ingestion & Triage Scanner
Per IMPORT_SPEC v1.1 Amendment and C_TRACK_BRIEF.md (Phases C0 & C1).

Ingests raw export archives (Claude, ChatGPT, Gemini) into canonical Stage 1
archive records under data/archive/<platform>/<conv_id>.json and builds the
mechanical triage registry in data/archive/registry.json with zero LLM calls.
"""

import argparse
import json
import os
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

IMPORT_SPEC_VERSION = "1.1"

# Sensitive keywords per C_TRACK_BRIEF.md §5
SENSITIVE_KEYWORDS = {
    "health", "medical", "symptom", "doctor", "therapy", "physio", "hospital",
    "prescription", "clinic", "disease", "illness", "diagnosis", "pain", "bicep",
    "visa", "immigration", "residence permit", "embassy", "consulate", "passport", "citizenship",
    "salary", "rent", "landlord", "lease", "tenancy", "bank", "banking", "debt",
    "tax", "taxes", "mortgage", "payslip", "legal", "lawyer", "attorney",
    "contract termination", "termination", "severance"
}

# Stopword sets for language detection
STOPWORDS_EN = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it",
    "for", "not", "on", "with", "he", "as", "you", "do", "at", "this", "but",
    "his", "by", "from", "they", "we", "say", "her", "she", "or", "an", "will",
    "my", "one", "all", "would", "there", "their", "what", "so", "up", "out",
    "if", "about", "who", "get", "which", "go", "me", "can", "please", "help"
}

STOPWORDS_DE = {
    "der", "die", "das", "und", "ist", "in", "den", "von", "zu", "mit", "sich",
    "des", "auf", "für", "im", "dem", "nicht", "eine", "als", "auch", "es",
    "an", "werden", "aus", "er", "hat", "dass", "sie", "nach", "wird", "bei",
    "einer", "um", "am", "sind", "noch", "wie", "einem", "über", "einen", "so",
    "zum", "war", "haben", "nur", "oder", "aber", "vor", "zur", "bis", "mehr",
    "durch", "man", "sein", "wurde", "kann", "bitte", "deutsch", "ich"
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".tiff"}


def detect_language(sample_texts: List[str]) -> str:
    """Heuristic language detection on user text sample using stopword frequency."""
    combined = " ".join(sample_texts).lower()
    words = re.findall(r"\b[a-zA-ZäöüßÄÖÜ]+\b", combined)
    if not words:
        return "en"

    en_count = sum(1 for w in words if w in STOPWORDS_EN)
    de_count = sum(1 for w in words if w in STOPWORDS_DE)

    if de_count > en_count and de_count >= 2:
        return "de"
    return "en"


def check_sensitive(title: str, text_sample: str) -> Tuple[bool, List[str]]:
    """Checks if title or text contains sensitive personal keywords."""
    combined = f"{title} {text_sample}".lower()
    matched = []
    for kw in SENSITIVE_KEYWORDS:
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, combined):
            matched.append(kw)
    return (len(matched) > 0, sorted(matched))


def extract_claude_message_content(msg: Dict[str, Any]) -> Tuple[str, List[str], List[str]]:
    """
    Extracts text, flags, and dropped media from a raw claude_official message.
    Per IMPORT_SPEC v1.1 §C:
    Concatenate text blocks, record tool_use/narration, log non-text blocks to dropped_media.
    """
    flags: List[str] = []
    dropped_media: List[str] = []
    text_parts: List[str] = []

    content = msg.get("content")
    if isinstance(content, list) and content:
        for block in content:
            if not isinstance(block, dict):
                continue
            b_type = block.get("type")
            if b_type == "text":
                t = block.get("text", "")
                if t:
                    text_parts.append(t)
            elif b_type in ("tool_use", "tool_result"):
                if "tool_narration" not in flags:
                    flags.append("tool_narration")
            elif b_type == "thinking":
                if "thinking" not in flags:
                    flags.append("thinking")
            elif b_type in ("image", "image_url"):
                dropped_media.append(f"image_block:{block.get('name', 'image')}")
            else:
                dropped_media.append(f"{b_type}_block")
    else:
        raw_text = msg.get("text")
        if isinstance(raw_text, str) and raw_text.strip():
            text_parts.append(raw_text.strip())

    # Check attachments & files
    for att in msg.get("attachments", []):
        fn = att.get("file_name") or ""
        ft = att.get("file_type") or ""
        ext = Path(fn).suffix.lower() if fn else f".{ft}".lower()
        if ext in IMAGE_EXTENSIONS or ft.startswith("image"):
            dropped_media.append(fn or f"image_attachment{ext}")
        else:
            if fn:
                dropped_media.append(fn)

    for f_item in msg.get("files", []):
        fn = f_item.get("file_name") or ""
        ext = Path(fn).suffix.lower() if fn else ""
        if ext in IMAGE_EXTENSIONS:
            dropped_media.append(fn or "file_image")
        elif fn:
            dropped_media.append(fn)

    # Check for [Image: ...] placeholders in text
    cleaned_text = "\n\n".join(text_parts).strip()
    placeholder_matches = re.findall(r"\[Image:\s*([^\]]+)\]", cleaned_text)
    for ph in placeholder_matches:
        dropped_media.append(ph.strip())

    return cleaned_text, flags, dropped_media


def simulate_pairing(raw_turns: List[Dict[str, Any]]) -> Tuple[int, int, int]:
    """
    Applies IMPORT_SPEC v1.0 §6 pairing rules to compute exact pair count and dropped media.
    Returns: (pairs, merged_turns_count, dropped_trailing_user)
    """
    if not raw_turns:
        return 0, 0, 0

    # 1. Drop leading AI
    turns = list(raw_turns)
    while turns and turns[0]["speaker"] == "ai":
        turns.pop(0)

    if not turns:
        return 0, 0, 0

    # 2. Merge consecutive same-role turns
    merged: List[Dict[str, Any]] = []
    merged_count = 0
    for t in turns:
        if merged and merged[-1]["speaker"] == t["speaker"]:
            merged[-1]["text"] = f"{merged[-1]['text']}\n\n{t['text']}".strip()
            merged_count += 1
        else:
            merged.append(dict(t))

    # 3. Drop trailing user turn
    dropped_trailing = 0
    if merged and merged[-1]["speaker"] == "user":
        merged.pop()
        dropped_trailing = 1

    # Pairs count: exactly 1 user + 1 ai per pair
    pairs = len(merged) // 2
    return pairs, merged_count, dropped_trailing


def parse_claude_export(raw_conv: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Parses a single conversation from claude_official export.
    Returns: (canonical_archive_record, registry_row)
    """
    uuid_str = raw_conv.get("uuid", "")
    conv_id = f"claude_{uuid_str}"
    title = raw_conv.get("name") or raw_conv.get("summary") or "Untitled Conversation"
    created_at = raw_conv.get("created_at") or ""
    updated_at = raw_conv.get("updated_at") or ""

    chat_messages = raw_conv.get("chat_messages", [])
    turns: List[Dict[str, Any]] = []
    all_dropped_media: List[str] = []
    user_sample_texts: List[str] = []
    total_chars = 0
    max_turn_chars = 0
    has_code = False

    for m in chat_messages:
        raw_sender = m.get("sender", "human")
        speaker = "user" if raw_sender == "human" else "ai"
        ts = m.get("created_at", "")

        text, flags, dropped_media = extract_claude_message_content(m)
        all_dropped_media.extend(dropped_media)

        char_len = len(text)
        total_chars += char_len
        if char_len > max_turn_chars:
            max_turn_chars = char_len

        if "```" in text:
            has_code = True

        if speaker == "user" and len(user_sample_texts) < 3 and text:
            user_sample_texts.append(text[:300])

        turns.append({
            "speaker": speaker,
            "text": text,
            "ts": ts,
            "raw_role": raw_sender,
            "flags": flags,
            "dropped_media": dropped_media
        })

    # Pairing simulation
    pairs, merged_count, dropped_trailing = simulate_pairing(turns)

    # Images dropped calculation
    images_dropped = sum(
        1 for item in all_dropped_media
        if any(item.lower().endswith(ext) for ext in IMAGE_EXTENSIONS)
        or "image" in item.lower()
    )

    img_per_pair = round(images_dropped / pairs, 2) if pairs > 0 else 0.0

    # Fidelity Grade per spec:
    # clean <= 0.05, degraded <= 0.5, unusable > 0.5
    if img_per_pair <= 0.05:
        fidelity_grade = "clean"
    elif img_per_pair <= 0.50:
        fidelity_grade = "degraded"
    else:
        fidelity_grade = "unusable"

    language = detect_language(user_sample_texts)
    sensitive_flag, sensitive_triggers = check_sensitive(title, " ".join(user_sample_texts))

    # Canonical archive record
    archive_record = {
        "conv_id": conv_id,
        "platform": "claude",
        "source_kind": "claude_official",
        "title": title,
        "created_at": created_at,
        "updated_at": updated_at,
        "turns": turns,
        "platform_meta": {
            "account": raw_conv.get("account", {}),
            "raw_message_count": len(chat_messages),
            "merged_turns": merged_count,
            "dropped_trailing_user": bool(dropped_trailing),
        },
        "import_spec_version": IMPORT_SPEC_VERSION
    }

    # Registry row (mechanical metrics, zero LLM)
    display_title = "[REDACTED]" if sensitive_flag else title
    registry_row = {
        "conv_id": conv_id,
        "platform": "claude",
        "source_kind": "claude_official",
        "title": display_title,
        "raw_title": title,
        "created_at": created_at,
        "updated_at": updated_at,
        "raw_turns": len(chat_messages),
        "pairs": pairs,
        "total_chars": total_chars,
        "max_turn_chars": max_turn_chars,
        "images_dropped": images_dropped,
        "images_per_pair": img_per_pair,
        "regenerations": 0,
        "branches": None,
        "language": language,
        "has_code": has_code,
        "fidelity_grade": fidelity_grade,
        "sensitive": sensitive_flag,
        "sensitive_triggers": sensitive_triggers,
        "context_incomplete": False,
        "archive_file": f"claude/{conv_id}.json"
    }

    return archive_record, registry_row


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

    # Length bands
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

    # Sort by pairs descending, take top 30
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
    report_only: bool = False
):
    """Executes the ingestion scan and writes canonical archive records."""
    registry_file = archive_dir / "registry.json"

    if report_only:
        if not registry_file.exists():
            print(f"Error: {registry_file} not found. Run ingestion first.", file=sys.stderr)
            sys.exit(1)
        with open(registry_file, "r", encoding="utf-8") as f:
            registry = json.load(f)
        print_triage_report(registry)
        return

    # Determine export source
    if source_path is None:
        default_json = Path("data/calude/conversations.json")
        default_zip = Path("data/exports/claude/Claude Conversations.zip")
        if default_json.exists():
            source_path = default_json
        elif default_zip.exists():
            source_path = default_zip
        else:
            print("Error: No default Claude export found in data/calude/ or data/exports/claude/", file=sys.stderr)
            sys.exit(1)

    print(f"Scanning raw export: {source_path.resolve()}")
    if source_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(source_path, "r") as z:
            with z.open("conversations.json") as f:
                raw_convs = json.load(f)
    else:
        with open(source_path, "r", encoding="utf-8") as f:
            raw_convs = json.load(f)

    if not isinstance(raw_convs, list):
        print("Error: Expected top-level list of conversations in export JSON.", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(raw_convs)} conversations from export.\n")

    claude_archive_dir = archive_dir / "claude"
    claude_archive_dir.mkdir(parents=True, exist_ok=True)

    registry: List[Dict[str, Any]] = []
    written_count = 0

    for c in raw_convs:
        archive_rec, reg_row = parse_claude_export(c)
        conv_file = claude_archive_dir / f"{archive_rec['conv_id']}.json"

        with open(conv_file, "w", encoding="utf-8") as f:
            json.dump(archive_rec, f, indent=2, ensure_ascii=False)

        registry.append(reg_row)
        written_count += 1

    # Write master registry.json
    with open(registry_file, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print(f"Successfully archived {written_count} conversations to {claude_archive_dir.resolve()}")
    print(f"Wrote master registry: {registry_file.resolve()} ({len(registry)} rows)")

    # Print summary report
    print_triage_report(registry)


def main():
    parser = argparse.ArgumentParser(description="Multi-platform archive scan & triage tool.")
    parser.add_argument("--export", type=Path, default=None, help="Path to raw export zip or conversations.json")
    parser.add_argument("--out", type=Path, default=Path("data/archive"), help="Archive root directory")
    parser.add_argument("--report", action="store_true", help="Print triage report from existing registry")
    args = parser.parse_args()

    scan_archive(args.export, args.out, report_only=args.report)


if __name__ == "__main__":
    main()
