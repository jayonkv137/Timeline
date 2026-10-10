"""COTRACE archive ingestion, triage scanner, and chat promoter.
STANDALONE_V1_PLAN §4 Step S4.1 (per IMPORT_SPEC v1.1 and C_TRACK_BRIEF §C0-C3).

Provides pure library functions for:
- Safe archive extraction (zip, json, md)
- Mechanical parsing and triage of exports with zero LLM calls
- Pre-flight token and cost estimation via engine.estimator
- Duplicate detection against local library
- Full chat promotion to dialogue.json, source_meta.json, meta.json, and source.json
  with dialogue.schema.json validation.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine.estimator import estimate

try:
    from engine.schemas import load_validator
except ImportError:
    load_validator = None

IMPORT_SPEC_VERSION = "1.1"

# Sensitive keywords per C_TRACK_BRIEF.md §5
SENSITIVE_KEYWORDS = {
    "health", "medical", "symptom", "doctor", "therapy", "physio", "hospital",
    "prescription", "clinic", "disease", "illness", "diagnosis", "pain", "bicep",
    "visa", "immigration", "residence permit", "embassy", "consulate", "passport", "citizenship",
    "salary", "rent", "landlord", "lease", "tenancy", "bank", "banking", "debt",
    "tax", "taxes", "mortgage", "payslip", "legal", "lawyer", "attorney",
    "contract termination", "termination", "severance",
}

# Stopword sets for language detection
STOPWORDS_EN = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it",
    "for", "not", "on", "with", "he", "as", "you", "do", "at", "this", "but",
    "his", "by", "from", "they", "we", "say", "her", "she", "or", "an", "will",
    "my", "one", "all", "would", "there", "their", "what", "so", "up", "out",
    "if", "about", "who", "get", "which", "go", "me", "can", "please", "help",
}

STOPWORDS_DE = {
    "der", "die", "das", "und", "ist", "in", "den", "von", "zu", "mit", "sich",
    "des", "auf", "für", "im", "dem", "nicht", "eine", "als", "auch", "es",
    "an", "werden", "aus", "er", "hat", "dass", "sie", "nach", "wird", "bei",
    "einer", "um", "am", "sind", "noch", "wie", "einem", "über", "einen", "so",
    "zum", "war", "haben", "nur", "oder", "aber", "vor", "zur", "bis", "mehr",
    "durch", "man", "sein", "wurde", "kann", "bitte", "deutsch", "ich",
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".tiff"}

# Injected-text rules per IMPORT_SPEC §4
INJECTED_RULES = [
    ("slash_command", re.compile(r"<command-(message|name)>", re.I)),
    ("task_notification", re.compile(r"<task-notification>.*?<task-id>", re.I | re.S)),
    ("skill_preamble", re.compile(r"Skill\s+/[\w-]+\s+is already loaded", re.I)),
    ("system_note", re.compile(r"^\s*(<system-|\[system\])", re.I)),
]

AUTO_CONTINUE = {
    "continue",
    "continue.",
    "try again",
    "continue from where you left off.",
    "continue from where you left off",
}

TOOL_NARRATION = re.compile(r"\bUsed tool\b", re.I)


def get_dialogue_schema_path() -> Path:
    """Return path to engine/schemas/dialogue.schema.json."""
    return Path(__file__).resolve().parent / "schemas" / "dialogue.schema.json"


def validate_dialogue_json(dialogue_turns: list[dict[str, Any]], schema_path: Path | None = None) -> None:
    """Validate dialogue turn list against dialogue.schema.json using jsonschema."""
    schema_file = schema_path or get_dialogue_schema_path()
    if not schema_file.is_file():
        return

    try:
        from jsonschema import Draft202012Validator
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = json.load(f)
        validator = Draft202012Validator(schema)
        errors = list(validator.iter_errors(dialogue_turns))
        if errors:
            raise ValueError(f"Dialogue schema validation failed: {errors[0].message}")
    except ImportError:
        pass


def detect_language(sample_texts: list[str]) -> str:
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


def check_sensitive(title: str, text_sample: str) -> tuple[bool, list[str]]:
    """Checks if title or text contains sensitive personal keywords."""
    combined = f"{title} {text_sample}".lower()
    matched = []
    for kw in SENSITIVE_KEYWORDS:
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, combined):
            matched.append(kw)
    return (len(matched) > 0, sorted(matched))


def extract_claude_message_content(msg: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    """Extracts text, flags, and dropped media from a raw claude_official message.
    Per IMPORT_SPEC v1.1 §C:
    Concatenate text blocks, record tool_use/narration, log non-text blocks to dropped_media.
    """
    flags: list[str] = []
    dropped_media: list[str] = []
    text_parts: list[str] = []

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

    # Injected text and tool narration regex checks
    raw_sender = msg.get("sender", "human")
    speaker = "user" if raw_sender == "human" else "ai"
    if speaker == "ai" and TOOL_NARRATION.search(cleaned_text):
        if "tool_narration" not in flags:
            flags.append("tool_narration")
    elif speaker == "user":
        for name, pattern in INJECTED_RULES:
            if pattern.search(cleaned_text) and name not in flags:
                flags.append(name)
        if cleaned_text.strip().lower() in AUTO_CONTINUE and "auto_continue" not in flags:
            flags.append("auto_continue")

    return cleaned_text, flags, dropped_media


def simulate_pairing(raw_turns: list[dict[str, Any]]) -> tuple[int, int, int]:
    """Applies IMPORT_SPEC v1.0 §6 pairing rules to compute exact pair count.
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
    merged: list[dict[str, Any]] = []
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


def process_turns_to_dialogue(
    raw_turns: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Applies pairing rules from IMPORT_SPEC v1.0 §6 to create normalized dialogue.json
    and matching turn_meta for source_meta.json.
    """
    turns = list(raw_turns)
    dropped_leading_ai = False
    while turns and turns[0]["speaker"] == "ai":
        turns.pop(0)
        dropped_leading_ai = True

    merged: list[dict[str, Any]] = []
    merged_count = 0
    for t in turns:
        if merged and merged[-1]["speaker"] == t["speaker"]:
            prev_txt = merged[-1]["text"]
            curr_txt = t["text"]
            merged[-1]["text"] = (prev_txt + "\n\n" + curr_txt).strip()
            merged[-1]["dropped_media"].extend(t.get("dropped_media", []))
            merged[-1]["flags"].extend(t.get("flags", []))
            merged_count += 1
        else:
            merged.append(dict(t))

    dropped_trailing_user = False
    if merged and merged[-1]["speaker"] == "user":
        merged.pop()
        dropped_trailing_user = True

    pairs = len(merged) // 2
    dialogue_json: list[dict[str, Any]] = []
    turn_meta: list[dict[str, Any]] = []
    pair_idx = 1

    for i in range(0, len(merged), 2):
        u_turn = merged[i]
        a_turn = merged[i + 1]

        u_text = u_turn.get("text", "") or " "
        a_text = a_turn.get("text", "") or " "

        dialogue_json.append({
            "pair": pair_idx,
            "speaker": "user",
            "text": u_text,
            "attachments": [],
            "ts": u_turn.get("ts") or "2026-01-01T00:00:00Z",
        })
        dialogue_json.append({
            "pair": pair_idx,
            "speaker": "ai",
            "text": a_text,
            "attachments": [],
            "ts": a_turn.get("ts") or "2026-01-01T00:00:00Z",
        })

        turn_meta.append({
            "pair": pair_idx,
            "speaker": "user",
            "origin": "injected" if ("injected" in u_turn.get("flags", []) or any(f in u_turn.get("flags", []) for f in ["slash_command", "task_notification", "skill_preamble", "system_note", "auto_continue"])) else "typed",
            "flags": u_turn.get("flags", []),
            "dropped_media": u_turn.get("dropped_media", []),
        })
        turn_meta.append({
            "pair": pair_idx,
            "speaker": "ai",
            "origin": "model",
            "flags": a_turn.get("flags", []),
            "dropped_media": a_turn.get("dropped_media", []),
        })

        pair_idx += 1

    fidelity_stats = {
        "merged_turns": merged_count,
        "dropped_leading_ai": dropped_leading_ai,
        "dropped_trailing_user": dropped_trailing_user,
        "pairs": pairs,
        "turns": pairs * 2,
    }

    return dialogue_json, turn_meta, fidelity_stats


def parse_claude_export(
    raw_conv: dict[str, Any],
    estimate_costs: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Parses a single conversation from claude_official export.
    Returns: (canonical_archive_record, summary_row)
    """
    uuid_str = raw_conv.get("uuid", "")
    conv_id = f"claude_{uuid_str}" if uuid_str else f"conv_{int(datetime.now(timezone.utc).timestamp())}"
    title = raw_conv.get("name") or raw_conv.get("summary") or "Untitled Conversation"
    created_at = raw_conv.get("created_at") or ""
    updated_at = raw_conv.get("updated_at") or ""

    chat_messages = raw_conv.get("chat_messages", [])
    turns: list[dict[str, Any]] = []
    all_dropped_media: list[str] = []
    user_sample_texts: list[str] = []
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
            "dropped_media": dropped_media,
        })

    # Pairing simulation
    dialogue_json, turn_meta, fstats = process_turns_to_dialogue(turns)
    pairs = fstats["pairs"]

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

    # Pre-flight estimate (zero LLM calls)
    est_data: dict[str, Any] = {
        "tokens": {"low": 0, "high": 0, "expected": 0},
        "cost": {"low": 0.0, "high": 0.0, "expected": 0.0},
    }
    if estimate_costs and dialogue_json:
        est = estimate(dialogue_json)
        est_data = {
            "tokens": {
                "low": est.low.tokens,
                "high": est.high.tokens,
                "expected": est.expected_tokens,
            },
            "cost": {
                "low": est.low.cost,
                "high": est.high.cost,
                "expected": est.expected_cost,
            },
        }

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
            "merged_turns": fstats["merged_turns"],
            "dropped_trailing_user": bool(fstats["dropped_trailing_user"]),
            "dropped_leading_ai": bool(fstats["dropped_leading_ai"]),
        },
        "import_spec_version": IMPORT_SPEC_VERSION,
    }

    display_title = "[REDACTED]" if sensitive_flag else title
    summary_row = {
        "convId": conv_id,
        "platform": "claude",
        "sourceKind": "claude_official",
        "title": display_title,
        "rawTitle": title,
        "createdAt": created_at,
        "updatedAt": updated_at,
        "rawTurns": len(chat_messages),
        "pairs": pairs,
        "totalChars": total_chars,
        "maxTurnChars": max_turn_chars,
        "imagesDropped": images_dropped,
        "imagesPerPair": img_per_pair,
        "language": language,
        "hasCode": has_code,
        "fidelityGrade": fidelity_grade,
        "sensitive": sensitive_flag,
        "sensitiveTriggers": sensitive_triggers,
        "isDuplicate": False,
        "duplicateOf": None,
        "estimate": est_data,
    }

    return archive_record, summary_row


def extract_archive(raw_path: Path, target_dir: Path) -> list[Path]:
    """Safely extracts a zip archive or copies a single file to target_dir.
    Guards against Zip Slip vulnerabilities.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    resolved_target = target_dir.resolve()

    if raw_path.suffix.lower() == ".zip":
        extracted_files: list[Path] = []
        with zipfile.ZipFile(raw_path, "r") as zf:
            for member in zf.infolist():
                # Prevent Zip Slip directory traversal
                member_target = (resolved_target / member.filename).resolve()
                if not member_target.is_relative_to(resolved_target):
                    raise ValueError(f"Unsafe path in zip archive: {member.filename}")
                zf.extract(member, resolved_target)
                extracted_files.append(member_target)
        return extracted_files
    else:
        dest = resolved_target / raw_path.name
        if raw_path.resolve() != dest.resolve():
            shutil.copy2(raw_path, dest)
        return [dest]


def find_export_file(raw_dir: Path) -> tuple[Path, str]:
    """Locates the primary conversation file inside raw_dir.
    Returns: (file_path, format_type)
    """
    # 1. Check for conversations.json (Claude or ChatGPT)
    for p in raw_dir.rglob("conversations.json"):
        if p.is_file():
            return p, "claude_official"

    # 2. Check for any JSON files
    json_files = list(raw_dir.glob("*.json"))
    if json_files:
        return json_files[0], "claude_official"

    # 3. Check for Markdown files
    md_files = list(raw_dir.glob("*.md"))
    if md_files:
        return md_files[0], "markdown"

    raise FileNotFoundError(f"No export conversation files found in {raw_dir}")


def scan_import(
    raw_dir: Path,
    import_id: str,
    library_root: Path | None = None,
) -> dict[str, Any]:
    """Scans raw export files in raw_dir, builds triage metrics and pre-flight
    estimates with zero LLM calls, detects duplicates, and writes report.json.
    """
    raw_dir = Path(raw_dir).resolve()
    batch_dir = raw_dir.parent
    report_path = batch_dir / "report.json"

    # Check for any zip files in raw_dir to extract
    for zip_file in list(raw_dir.glob("*.zip")):
        extract_dir = raw_dir / zip_file.stem
        extract_archive(zip_file, extract_dir)

    primary_file, fmt = find_export_file(raw_dir)

    # Load conversations
    with open(primary_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    if not isinstance(raw_data, list):
        if isinstance(raw_data, dict):
            raw_data = [raw_data]
        else:
            raise ValueError(f"Expected list of conversations in {primary_file}")

    # Build known chat IDs from existing library to detect duplicates
    existing_chats: set[str] = set()
    existing_titles: set[str] = set()
    if library_root is not None:
        chats_dir = Path(library_root) / "chats"
        if chats_dir.is_dir():
            for c_path in chats_dir.iterdir():
                if c_path.is_dir():
                    existing_chats.add(c_path.name)
                    meta_p = c_path / "meta.json"
                    if meta_p.is_file():
                        try:
                            with open(meta_p, "r", encoding="utf-8") as mf:
                                mdata = json.load(mf)
                                if mdata.get("conv_id"):
                                    existing_chats.add(mdata["conv_id"])
                                if mdata.get("title"):
                                    existing_titles.add(mdata["title"])
                        except Exception:
                            pass

    conversations: list[dict[str, Any]] = []
    seen_conv_ids: set[str] = set()
    total_pairs = 0
    total_chars = 0
    clean_count = 0
    degraded_count = 0
    unusable_count = 0
    duplicates_count = 0
    sensitive_count = 0

    total_est_tokens_low = 0
    total_est_tokens_high = 0
    total_est_tokens_exp = 0
    total_est_cost_low = 0.0
    total_est_cost_high = 0.0
    total_est_cost_exp = 0.0

    for raw_conv in raw_data:
        archive_rec, row = parse_claude_export(raw_conv, estimate_costs=True)
        cid = row["convId"]

        # Duplicate detection
        is_dup = False
        dup_of = None
        if cid in seen_conv_ids:
            is_dup = True
            dup_of = cid
        elif cid in existing_chats:
            is_dup = True
            dup_of = cid
        elif row["rawTitle"] in existing_titles and row["rawTitle"] != "Untitled Conversation":
            is_dup = True
            dup_of = row["rawTitle"]

        if is_dup:
            duplicates_count += 1
            row["isDuplicate"] = True
            row["duplicateOf"] = dup_of
        else:
            seen_conv_ids.add(cid)

        if row["sensitive"]:
            sensitive_count += 1

        grade = row["fidelityGrade"]
        if grade == "clean":
            clean_count += 1
        elif grade == "degraded":
            degraded_count += 1
        else:
            unusable_count += 1

        total_pairs += row["pairs"]
        total_chars += row["totalChars"]

        est = row["estimate"]
        total_est_tokens_low += est["tokens"]["low"]
        total_est_tokens_high += est["tokens"]["high"]
        total_est_tokens_exp += est["tokens"]["expected"]
        total_est_cost_low += est["cost"]["low"]
        total_est_cost_high += est["cost"]["high"]
        total_est_cost_exp += est["cost"]["expected"]

        conversations.append(row)

    report: dict[str, Any] = {
        "importId": import_id,
        "status": "ready",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "sourceFilename": primary_file.name,
        "sourceFormat": fmt,
        "totalConversations": len(conversations),
        "totalPairs": total_pairs,
        "totalChars": total_chars,
        "fidelity": {
            "clean": clean_count,
            "degraded": degraded_count,
            "unusable": unusable_count,
        },
        "duplicates": duplicates_count,
        "sensitiveCount": sensitive_count,
        "estimate": {
            "tokens": {
                "low": total_est_tokens_low,
                "high": total_est_tokens_high,
                "expected": total_est_tokens_exp,
            },
            "cost": {
                "low": round(total_est_cost_low, 4),
                "high": round(total_est_cost_high, 4),
                "expected": round(total_est_cost_exp, 4),
            },
        },
        "conversations": conversations,
        "error": None,
    }

    # Write report.json atomically
    temp_report = report_path.with_suffix(".tmp")
    with open(temp_report, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(temp_report, report_path)

    return report


def promote_conversation(
    conv_data: dict[str, Any],
    dest_dir: Path | str,
    chat_id: str | None = None,
    category: str = "General",
    task_type: str = "planning",
    domain: str = "",
    schema_path: Path | None = None,
) -> dict[str, Any]:
    """Promotes a raw or archive conversation into a canonical 4-file directory:
    - dialogue.json (validated against dialogue.schema.json)
    - source_meta.json
    - meta.json
    - meta.yaml
    - source.json
    """
    dest = Path(dest_dir).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "run").mkdir(parents=True, exist_ok=True)

    # If raw export conversation, parse it first
    if "chat_messages" in conv_data:
        archive_rec, reg_info = parse_claude_export(conv_data, estimate_costs=False)
    elif "turns" in conv_data:
        archive_rec = conv_data
        cid = archive_rec.get("conv_id", "conv_unknown")
        reg_info = {
            "convId": cid,
            "rawTitle": archive_rec.get("title", cid),
            "fidelityGrade": "clean",
            "imagesDropped": 0,
            "imagesPerPair": 0.0,
            "hasCode": False,
            "language": "en",
        }
    else:
        raise ValueError("Invalid conversation data format for promotion")

    raw_turns = archive_rec.get("turns", [])
    dialogue_json, turn_meta, fstats = process_turns_to_dialogue(raw_turns)

    # Validate against schema
    validate_dialogue_json(dialogue_json, schema_path=schema_path)

    cid = archive_rec.get("conv_id", "")
    target_chat_id = chat_id or cid
    title = reg_info.get("rawTitle") or archive_rec.get("title") or "Untitled Conversation"
    pairs = fstats["pairs"]
    length_band = "short" if pairs <= 5 else ("medium" if pairs <= 20 else "long")

    # 1. source.json
    with open(dest / "source.json", "w", encoding="utf-8") as f:
        json.dump(archive_rec, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # 2. dialogue.json
    with open(dest / "dialogue.json", "w", encoding="utf-8") as f:
        json.dump(dialogue_json, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # 3. source_meta.json
    source_meta = {
        "chat_id": target_chat_id,
        "conv_id": cid,
        "source_kind": archive_rec.get("source_kind", "claude_official"),
        "source_file": "source.json",
        "source_title": title,
        "imported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "import_spec_version": IMPORT_SPEC_VERSION,
        "pairs": pairs,
        "turns": fstats["turns"],
        "assumed_utc": True,
        "fidelity": {
            "images_dropped": reg_info.get("imagesDropped", 0),
            "attachments_dropped": 0,
            "tool_narration_turns": sum(1 for tm in turn_meta if "tool_narration" in tm["flags"]),
            "injected_turns": sum(1 for tm in turn_meta if tm["origin"] == "injected"),
            "empty_turns": 0,
            "merged_turns": fstats["merged_turns"],
            "dropped_trailing_user_turn": fstats["dropped_trailing_user"],
            "dropped_leading_ai_turn": fstats["dropped_leading_ai"],
            "grade": reg_info.get("fidelityGrade", "clean"),
            "image_ratio": reg_info.get("imagesPerPair", 0.0),
        },
        "turn_meta": turn_meta,
    }
    with open(dest / "source_meta.json", "w", encoding="utf-8") as f:
        json.dump(source_meta, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # 4. meta.json
    meta_json = {
        "id": target_chat_id,
        "conv_id": cid,
        "title": title,
        "category": category,
        "createdAt": archive_rec.get("created_at") or datetime.now(timezone.utc).isoformat(),
        "updatedAt": archive_rec.get("updated_at") or datetime.now(timezone.utc).isoformat(),
        "pairs": pairs,
        "length_band": length_band,
        "fidelity_grade": reg_info.get("fidelityGrade", "clean"),
        "source": {
            "platform": archive_rec.get("platform", "claude"),
            "format": archive_rec.get("source_kind", "claude_official"),
        },
    }
    with open(dest / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta_json, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # 5. meta.yaml
    clean_title = title.replace('"', '\\"')
    meta_yaml = f"""# filled by importer
id: {target_chat_id}
conv_id: {cid}
title: "{clean_title}"
source_file: "source.json"
source_kind: {archive_rec.get('source_kind', 'claude_official')}
provenance: owner
pairs: {pairs}
length_band: {length_band}
fidelity_grade: {reg_info.get('fidelityGrade', 'clean')}
contains: []

# Layer 1: Descriptive facts (verified)
language: {reg_info.get('language', 'en')}
task_type: {task_type}
domain: "{domain}"
notes: >
  {clean_title} — promoted for standalone chat processing.

# Layer 2: Judgement & predictive fields
prompt_style: null
expected:
  mode_hint: null
  direction_hint: null
  min_requirements: null
  max_requirements: null
"""
    with open(dest / "meta.yaml", "w", encoding="utf-8") as f:
        f.write(meta_yaml)

    return {
        "chatId": target_chat_id,
        "convId": cid,
        "title": title,
        "pairs": pairs,
        "grade": reg_info.get("fidelityGrade", "clean"),
        "dir": str(dest),
    }


def scan_archive(
    source_path: Path | None,
    archive_dir: Path,
    report_only: bool = False,
) -> list[dict[str, Any]]:
    """Library implementation of archive_scan.py."""
    archive_dir = Path(archive_dir)
    registry_file = archive_dir / "registry.json"

    if report_only:
        if not registry_file.exists():
            raise FileNotFoundError(f"{registry_file} not found. Run ingestion first.")
        with open(registry_file, "r", encoding="utf-8") as f:
            return json.load(f)

    if source_path is None:
        default_json = Path("data/calude/conversations.json")
        default_zip = Path("data/exports/claude/Claude Conversations.zip")
        if default_json.exists():
            source_path = default_json
        elif default_zip.exists():
            source_path = default_zip
        else:
            raise FileNotFoundError("No default Claude export found")

    source_path = Path(source_path)
    if source_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(source_path, "r") as z:
            with z.open("conversations.json") as f:
                raw_convs = json.load(f)
    else:
        with open(source_path, "r", encoding="utf-8") as f:
            raw_convs = json.load(f)

    claude_archive_dir = archive_dir / "claude"
    claude_archive_dir.mkdir(parents=True, exist_ok=True)

    registry: list[dict[str, Any]] = []
    for c in raw_convs:
        archive_rec, row = parse_claude_export(c, estimate_costs=False)
        conv_file = claude_archive_dir / f"{archive_rec['conv_id']}.json"
        with open(conv_file, "w", encoding="utf-8") as f:
            json.dump(archive_rec, f, indent=2, ensure_ascii=False)

        # Build registry row
        reg_row = {
            "conv_id": row["convId"],
            "platform": row["platform"],
            "source_kind": row["sourceKind"],
            "title": row["title"],
            "raw_title": row["rawTitle"],
            "created_at": row["createdAt"],
            "updated_at": row["updatedAt"],
            "raw_turns": row["rawTurns"],
            "pairs": row["pairs"],
            "total_chars": row["totalChars"],
            "max_turn_chars": row["maxTurnChars"],
            "images_dropped": row["imagesDropped"],
            "images_per_pair": row["imagesPerPair"],
            "regenerations": 0,
            "branches": None,
            "language": row["language"],
            "has_code": row["hasCode"],
            "fidelity_grade": row["fidelityGrade"],
            "sensitive": row["sensitive"],
            "sensitive_triggers": row["sensitiveTriggers"],
            "context_incomplete": False,
            "archive_file": f"claude/{row['convId']}.json",
        }
        registry.append(reg_row)

    with open(registry_file, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    return registry


def promote_chats(
    target_list: list[dict[str, str]],
    archive_dir: Path,
    corpus_dir: Path,
    schema_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Library implementation of promote_from_archive.py."""
    archive_dir = Path(archive_dir)
    corpus_dir = Path(corpus_dir)
    schema_file = schema_path or get_dialogue_schema_path()

    registry_file = archive_dir / "registry.json"
    if not registry_file.exists():
        raise FileNotFoundError(f"{registry_file} not found.")

    with open(registry_file, "r", encoding="utf-8") as f:
        registry_map = {r["conv_id"]: r for r in json.load(f)}

    existing_folders = [p.name for p in corpus_dir.iterdir() if p.is_dir() and p.name.startswith("c")]
    existing_nums = []
    for f_name in existing_folders:
        m = re.match(r"^c(\d+)_", f_name)
        if m:
            existing_nums.append(int(m.group(1)))

    next_num = (max(existing_nums) + 1) if existing_nums else 1
    promoted_entries: list[dict[str, Any]] = []

    for item in target_list:
        cid = item["conv_id"]
        reg_info = registry_map.get(cid)
        if not reg_info:
            continue

        archive_json_path = archive_dir / "claude" / f"{cid}.json"
        if not archive_json_path.exists():
            continue

        with open(archive_json_path, "r", encoding="utf-8") as f:
            archive_data = json.load(f)

        task_type = item.get("task_type", "planning")
        domain = item.get("domain", "")
        pairs = reg_info.get("pairs", 0)
        length_band = "short" if pairs <= 5 else ("medium" if pairs <= 20 else "long")
        chat_id = f"c{next_num:02d}_{task_type}_{length_band}"
        next_num += 1

        dest_dir = corpus_dir / chat_id
        res = promote_conversation(
            conv_data=archive_data,
            dest_dir=dest_dir,
            chat_id=chat_id,
            category=task_type.capitalize(),
            task_type=task_type,
            domain=domain,
            schema_path=schema_file,
        )
        promoted_entries.append(res)

    return promoted_entries
