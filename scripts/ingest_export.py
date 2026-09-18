#!/usr/bin/env python3
"""
ingest_export.py - turn a raw chat export into a corpus entry.

Implements IMPORT_SPEC v1.0 (text only).

Usage
-----
Single file:
    python scripts/ingest_export.py path/to/export.json --id c01_coding_short

Whole folder (every .json and .md inside, ids auto-assigned c01.., c02..):
    python scripts/ingest_export.py --batch path/to/testing_chats/

Options:
    --out DIR        corpus root, default data/corpus
    --id ID          chat id for single-file mode
    --prefix P       id prefix in batch mode, default "c"
    --dry-run        analyse and report, write nothing
    --force          overwrite an existing corpus entry

Exit codes: 0 ok, 1 validation failure, 2 unsupported format, 3 usage error.

Standard library only. No third-party imports required.
jsonschema is used if installed, skipped with a warning if not.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone

IMPORT_SPEC_VERSION = "1.0"

# --------------------------------------------------------------------------
# injected-text rules (IMPORT_SPEC section 4)
# tagged, never stripped. origin becomes "injected".
# --------------------------------------------------------------------------

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
IMAGE_PLACEHOLDER = re.compile(r"\[Image:\s*([^\]]+)\]")
ATTACHMENT_PLACEHOLDER = re.compile(r"\[(?:Attachment|File|Document):\s*([^\]]+)\]", re.I)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def norm_ts(raw: str) -> tuple[str, bool]:
    """Return (iso8601, assumed_utc). Falls back to empty string on failure."""
    if not raw:
        return "", True
    raw = raw.strip()
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                return dt.strftime("%Y-%m-%dT%H:%M:%SZ"), True
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), False
        except ValueError:
            continue
    return "", True


def classify_origin(speaker: str, text: str) -> tuple[str, list[str]]:
    """Return (origin, flags). Per IMPORT_SPEC section 4: tag, never strip."""
    flags: list[str] = []
    if speaker == "ai":
        if TOOL_NARRATION.search(text):
            flags.append("tool_narration")
        return "model", flags

    for name, pattern in INJECTED_RULES:
        if pattern.search(text):
            flags.append(name)
    if text.strip().lower() in AUTO_CONTINUE:
        flags.append("auto_continue")

    origin = "injected" if flags else "typed"
    return origin, flags


def dropped_media(text: str) -> list[str]:
    out = [m.strip() for m in IMAGE_PLACEHOLDER.findall(text)]
    out += [m.strip() for m in ATTACHMENT_PLACEHOLDER.findall(text)]
    return out


def clean_text(text: str) -> str:
    """Strip leading/trailing blank lines only. Never alter the body."""
    return (text or "").strip("\n").rstrip()


# --------------------------------------------------------------------------
# format detection and parsing
# --------------------------------------------------------------------------

def detect_format(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".jsonl":
        return "claude_code"
    if ext == ".json":
        try:
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
        except Exception:
            return "unknown"
        if isinstance(obj, dict) and "messages" in obj and isinstance(obj["messages"], list):
            msgs = obj["messages"]
            if msgs and isinstance(msgs[0], dict) and "role" in msgs[0]:
                return "claude_web_json"
        return "unknown"
    if ext in (".md", ".markdown"):
        with open(path, "r", encoding="utf-8") as f:
            head = f.read(8000)
        if re.search(r"^##\s+(User|Assistant):", head, re.M):
            return "claude_web_md"
        return "unknown"
    return "unknown"


def parse_claude_web_json(path: str) -> tuple[list[dict], dict]:
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    meta = obj.get("metadata", {}) or {}
    raw_turns = []
    for m in obj.get("messages", []):
        role = (m.get("role") or "").lower()
        speaker = "user" if role in ("human", "user") else "ai"
        raw_turns.append({
            "speaker": speaker,
            "text": clean_text(m.get("say", "")),
            "ts_raw": m.get("time", ""),
        })
    header = {
        "source_title": meta.get("title", ""),
        "source_link": meta.get("link", ""),
        "exporter": meta.get("powered_by", ""),
        "source_dates": meta.get("dates", {}),
    }
    return raw_turns, header


def parse_claude_web_md(path: str) -> tuple[list[dict], dict]:
    with open(path, "r", encoding="utf-8") as f:
        body = f.read()

    title = ""
    mt = re.search(r"^#\s+(.+)$", body, re.M)
    if mt:
        title = mt.group(1).strip()

    parts = re.split(r"^##\s+(User|Assistant):\s*$", body, flags=re.M)
    raw_turns = []
    # parts = [preamble, role, chunk, role, chunk, ...]
    for i in range(1, len(parts) - 1, 2):
        role = parts[i].strip().lower()
        chunk = parts[i + 1]
        ts_raw = ""
        mts = re.match(r"\s*>\s*([0-9/: ]+)\s*\n", chunk)
        if mts:
            ts_raw = mts.group(1).strip()
            chunk = chunk[mts.end():]
        raw_turns.append({
            "speaker": "user" if role == "user" else "ai",
            "text": clean_text(chunk),
            "ts_raw": ts_raw,
        })
    return raw_turns, {"source_title": title, "source_link": "", "exporter": "",
                       "source_dates": {}}


# --------------------------------------------------------------------------
# pairing (IMPORT_SPEC section 6)
# --------------------------------------------------------------------------

def apply_pairing(raw_turns: list[dict]) -> tuple[list[dict], dict]:
    notes = {
        "dropped_leading_ai_turn": False,
        "dropped_trailing_user_turn": False,
        "merged_turns": 0,
    }

    turns = list(raw_turns)

    # rule 1: leading AI turn
    while turns and turns[0]["speaker"] == "ai":
        turns.pop(0)
        notes["dropped_leading_ai_turn"] = True

    # rule 2: merge consecutive same-role turns
    merged: list[dict] = []
    for t in turns:
        if merged and merged[-1]["speaker"] == t["speaker"]:
            merged[-1]["text"] = (merged[-1]["text"] + "\n\n" + t["text"]).strip("\n")
            merged[-1]["_merged"] = merged[-1].get("_merged", 1) + 1
            notes["merged_turns"] += 1
        else:
            merged.append(dict(t))
    turns = merged

    # rule 3: trailing user turn with no reply
    if turns and turns[-1]["speaker"] == "user":
        turns.pop()
        notes["dropped_trailing_user_turn"] = True

    return turns, notes


def build_artifacts(turns: list[dict]) -> tuple[list[dict], list[dict], dict]:
    dialogue: list[dict] = []
    turn_meta: list[dict] = []
    fid = {
        "images_dropped": 0,
        "attachments_dropped": 0,
        "tool_narration_turns": 0,
        "injected_turns": 0,
        "empty_turns": 0,
    }
    assumed_utc_any = False

    pair = 0
    for idx, t in enumerate(turns):
        if t["speaker"] == "user":
            pair += 1
        ts, assumed = norm_ts(t.get("ts_raw", ""))
        assumed_utc_any = assumed_utc_any or assumed

        text = t["text"]
        origin, flags = classify_origin(t["speaker"], text)
        media = dropped_media(text)

        if t.get("_merged"):
            flags.append(f"merged:{t['_merged']}")
        if not text.strip():
            flags.append("empty")
            fid["empty_turns"] += 1
        if origin == "injected":
            fid["injected_turns"] += 1
        if "tool_narration" in flags:
            fid["tool_narration_turns"] += 1
        fid["images_dropped"] += len(IMAGE_PLACEHOLDER.findall(text))
        fid["attachments_dropped"] += len(ATTACHMENT_PLACEHOLDER.findall(text))

        dialogue.append({
            "pair": pair,
            "speaker": t["speaker"],
            "text": text,
            "attachments": [],          # T1: always empty, see IMPORT_SPEC section 2
            "ts": ts,
        })
        turn_meta.append({
            "pair": pair,
            "speaker": t["speaker"],
            "origin": origin,
            "flags": flags,
            "dropped_media": media,
        })

    return dialogue, turn_meta, {"fidelity": fid, "assumed_utc": assumed_utc_any}


# --------------------------------------------------------------------------
# validation (IMPORT_SPEC section 7)
# --------------------------------------------------------------------------

def validate(dialogue: list[dict], turn_meta: list[dict], schema_path: str | None) -> list[str]:
    errors: list[str] = []

    if not dialogue:
        errors.append("check 2: no turns after pairing")
        return errors

    pairs = sorted({t["pair"] for t in dialogue})
    if pairs != list(range(1, len(pairs) + 1)):
        errors.append(f"check 2: pair numbers not contiguous from 1: {pairs[:10]}")

    by_pair: dict[int, list[str]] = {}
    for t in dialogue:
        by_pair.setdefault(t["pair"], []).append(t["speaker"])
    for p, speakers in by_pair.items():
        if speakers != ["user", "ai"]:
            errors.append(f"check 3: pair {p} is {speakers}, expected ['user', 'ai']")

    if len(turn_meta) != len(dialogue):
        errors.append("check 4: turn_meta length does not match dialogue length")

    if schema_path and os.path.exists(schema_path):
        try:
            import jsonschema  # type: ignore
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
            jsonschema.validate(instance=dialogue, schema=schema)
        except ImportError:
            print("  ! jsonschema not installed, schema check skipped", file=sys.stderr)
        except Exception as exc:  # jsonschema.ValidationError and friends
            errors.append(f"check 1: dialogue.json failed schema validation: {exc}")

    return errors


# --------------------------------------------------------------------------
# meta.yaml skeleton (IMPORT_SPEC section 8)
# --------------------------------------------------------------------------

def meta_yaml(chat_id: str, source_kind: str, pairs: int, contains: list[str]) -> str:
    if pairs <= 5:
        band = "short"
    elif pairs <= 20:
        band = "medium"
    else:
        band = "long"
    contains_str = "[" + ", ".join(sorted(set(contains))) + "]" if contains else "[]"
    return f"""# filled by importer
id: {chat_id}
source_kind: {source_kind}
pairs: {pairs}
length_band: {band}
contains: {contains_str}

# TO BE COMPLETED BY THE OWNER
language:            # en | de | mixed
task_type:           # coding | writing | planning | research | creative | debugging
prompt_style:        # specified | vague | mixed
expected:
  mode_hint:         # centaur | copilot | autopilot
  direction_hint:    # user_heavy | balanced | ai_heavy
  min_requirements:
  max_requirements:
notes: >
  One paragraph: what this conversation was, who drove it, and anything that
  makes it an unusual test case.
"""


# --------------------------------------------------------------------------
# main ingest
# --------------------------------------------------------------------------

def ingest(path: str, chat_id: str, out_root: str, dry_run: bool, force: bool,
           schema_path: str | None, manifest_collector: list[dict] | None = None) -> int:
    fmt = detect_format(path)
    print(f"\n=== {os.path.basename(path)}")
    print(f"  format : {fmt}")

    if fmt == "claude_code":
        print("  REFUSED: Claude Code transcripts are out of scope in IMPORT_SPEC v1.")
        print("           They need the T3 pairing model. See IMPORT_SPEC section 5.3.")
        return 2
    if fmt == "unknown":
        print("  REFUSED: unrecognised format. Supported: claude_web_json, claude_web_md.")
        return 2

    if fmt == "claude_web_json":
        raw_turns, header = parse_claude_web_json(path)
    else:
        raw_turns, header = parse_claude_web_md(path)

    turns, notes = apply_pairing(raw_turns)
    dialogue, turn_meta, extra = build_artifacts(turns)
    fid = extra["fidelity"]
    fid.update({
        "merged_turns": notes["merged_turns"],
        "dropped_trailing_user_turn": notes["dropped_trailing_user_turn"],
        "dropped_leading_ai_turn": notes["dropped_leading_ai_turn"],
    })

    errors = validate(dialogue, turn_meta, schema_path)

    n_pairs = max((t["pair"] for t in dialogue), default=0)
    print(f"  turns in source : {len(raw_turns)}")
    print(f"  pairs after rules: {n_pairs}")
    print(f"  typed / injected : "
          f"{sum(1 for m in turn_meta if m['origin'] == 'typed')} / "
          f"{sum(1 for m in turn_meta if m['origin'] == 'injected')}")
    print(f"  images dropped   : {fid['images_dropped']}")
    print(f"  tool narration   : {fid['tool_narration_turns']} AI turns")
    print(f"  merged turns     : {fid['merged_turns']}")
    if fid["empty_turns"]:
        print(f"  empty turns      : {fid['empty_turns']}")

    if errors:
        print("  FAILED validation, nothing written:")
        for e in errors:
            print(f"    - {e}")
        return 1

    if manifest_collector is not None:
        manifest_collector.append({
            "id": chat_id,
            "source_kind": fmt,
            "pairs": n_pairs,
            "images_dropped": fid["images_dropped"],
            "injected_turns": fid["injected_turns"],
            "tool_narration_turns": fid["tool_narration_turns"],
        })

    if dry_run:
        print("  dry run, nothing written")
        return 0

    dest = os.path.join(out_root, chat_id)
    if os.path.exists(dest) and not force:
        print(f"  REFUSED: {dest} already exists. Use --force to overwrite.")
        return 1
    os.makedirs(dest, exist_ok=True)

    src_ext = os.path.splitext(path)[1].lower()
    shutil.copy2(path, os.path.join(dest, f"source{src_ext}"))

    with open(os.path.join(dest, "dialogue.json"), "w", encoding="utf-8") as f:
        json.dump(dialogue, f, indent=2, ensure_ascii=False)
        f.write("\n")

    source_meta = {
        "chat_id": chat_id,
        "source_kind": fmt,
        "source_file": f"source{src_ext}",
        "exporter": header.get("exporter", ""),
        "source_title": header.get("source_title", ""),
        "source_link": header.get("source_link", ""),
        "source_dates": header.get("source_dates", {}),
        "imported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "import_spec_version": IMPORT_SPEC_VERSION,
        "pairs": n_pairs,
        "turns": len(dialogue),
        "assumed_utc": extra["assumed_utc"],
        "fidelity": fid,
        "turn_meta": turn_meta,
    }
    with open(os.path.join(dest, "source_meta.json"), "w", encoding="utf-8") as f:
        json.dump(source_meta, f, indent=2, ensure_ascii=False)
        f.write("\n")

    contains = []
    if fid["images_dropped"]:
        contains.append("images")
    if any("```" in t["text"] for t in dialogue):
        contains.append("code_blocks")
    if any(len(t["text"]) > 5000 for t in dialogue):
        contains.append("long_message")

    meta_path = os.path.join(dest, "meta.yaml")
    if not os.path.exists(meta_path) or force:
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(meta_yaml(chat_id, fmt, n_pairs, contains))

    print(f"  written -> {dest}")
    print("  NEXT: open meta.yaml and fill in the owner fields.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest chat exports into the corpus (IMPORT_SPEC v1.0)")
    ap.add_argument("source", nargs="?", help="a single export file")
    ap.add_argument("--batch", help="a folder of export files")
    ap.add_argument("--id", help="chat id for single-file mode")
    ap.add_argument("--prefix", default="c", help="id prefix in batch mode")
    ap.add_argument("--out", default="data/corpus", help="corpus root")
    ap.add_argument("--schema", default="engine/schemas/dialogue.schema.json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if args.batch:
        files = sorted(
            os.path.join(args.batch, fn)
            for fn in os.listdir(args.batch)
            if os.path.splitext(fn)[1].lower() in (".json", ".md", ".markdown", ".jsonl")
        )
        if not files:
            print("no export files found", file=sys.stderr)
            return 3
        worst = 0
        n = 0
        manifest_chats: list[dict] = []
        for path in files:
            fmt = detect_format(path)
            if fmt in ("unknown", "claude_code"):
                ingest(path, "unused", args.out, True, args.force, args.schema)
                continue
            n += 1
            chat_id = f"{args.prefix}{n:02d}_unsorted"
            rc = ingest(path, chat_id, args.out, args.dry_run, args.force, args.schema, manifest_chats)
            worst = max(worst, rc if rc != 2 else 0)
        
        if not args.dry_run and manifest_chats:
            manifest = {
                "import_spec_version": IMPORT_SPEC_VERSION,
                "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "chats": manifest_chats,
            }
            manifest_path = os.path.join(args.out, "manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
                f.write("\n")
            print(f"  manifest written -> {manifest_path}")

        print(f"\n{n} file(s) ingested into {args.out}")
        print("Rename each folder to c<NN>_<task_type>_<length> once meta.yaml is filled in.")
        return worst

    if not args.source:
        ap.print_help()
        return 3
    chat_id = args.id or os.path.splitext(os.path.basename(args.source))[0].lower()
    chat_id = re.sub(r"[^a-z0-9_]+", "_", chat_id).strip("_")
    return ingest(args.source, chat_id, args.out, args.dry_run, args.force, args.schema)


if __name__ == "__main__":
    sys.exit(main())
