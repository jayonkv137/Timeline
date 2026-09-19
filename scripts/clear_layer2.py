#!/usr/bin/env python3
"""scripts/clear_layer2.py - Clear machine-assigned Layer 2 predictive fields from meta.yaml.

Separates:
- Layer 1 (descriptive facts, machine-assignable): id, title, source_file,
  source_kind, pairs, length_band, fidelity_grade, provenance, contains,
  language, task_type, descriptive notes.
- Layer 2 (evaluative / predictive / ground-truth fields): prompt_style,
  expected (mode_hint, direction_hint, min/max_requirements).

Layer 2 fields are cleared to null / unassigned to avoid circular LLM-vs-LLM
evaluation in downstream phases (E1-E3).
"""

import glob
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = REPO_ROOT / "data/corpus"


def clear_meta_file(meta_path: Path):
    with open(meta_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Extract importer / header block (everything before # OWNER METADATA or # Layer 1)
    # Or parse individual fields:
    cid_m = re.search(r"^id:\s*(.+)$", text, re.MULTILINE)
    title_m = re.search(r"^title:\s*(.+)$", text, re.MULTILINE)
    sf_m = re.search(r"^source_file:\s*(.+)$", text, re.MULTILINE)
    sk_m = re.search(r"^source_kind:\s*(.+)$", text, re.MULTILINE)
    pairs_m = re.search(r"^pairs:\s*(\d+)$", text, re.MULTILINE)
    lb_m = re.search(r"^length_band:\s*(.+)$", text, re.MULTILINE)
    fg_m = re.search(r"^fidelity_grade:\s*(.+)$", text, re.MULTILINE)
    prov_m = re.search(r"^provenance:\s*(.+)$", text, re.MULTILINE)
    contains_m = re.search(r"^contains:\s*(.+)$", text, re.MULTILINE)

    # Layer 1
    lang_m = re.search(r"^language:\s*(.+)$", text, re.MULTILINE)
    tt_m = re.search(r"^task_type:\s*(.+)$", text, re.MULTILINE)
    notes_m = re.search(r"^notes:\s*>\s*\n((?:[ \t]+[^\n]*\n?)+)", text, re.MULTILINE)

    cid = cid_m.group(1).strip() if cid_m else ""
    title = title_m.group(1).strip() if title_m else ""
    source_file = sf_m.group(1).strip() if sf_m else ""
    source_kind = sk_m.group(1).strip() if sk_m else "claude_web_json"
    pairs = pairs_m.group(1).strip() if pairs_m else "0"
    length_band = lb_m.group(1).strip() if lb_m else "short"
    fidelity_grade = fg_m.group(1).strip() if fg_m else "clean"
    provenance = prov_m.group(1).strip() if prov_m else None
    contains = contains_m.group(1).strip() if contains_m else "[]"

    language = lang_m.group(1).strip() if lang_m else "en"
    task_type = tt_m.group(1).strip() if tt_m else ""
    notes = notes_m.group(1).strip() if notes_m else ""

    prov_line = f"provenance: {provenance}\n" if provenance else ""

    new_content = f"""# filled by importer
id: {cid}
title: {title}
source_file: {source_file}
source_kind: {source_kind}
pairs: {pairs}
length_band: {length_band}
fidelity_grade: {fidelity_grade}
{prov_line}contains: {contains}

# Layer 1: Descriptive facts (verified)
language: {language}
task_type: {task_type}
notes: >
  {notes}

# Layer 2: Judgement & predictive fields (HUMAN-LABELED ONLY — cleared to prevent circularity)
prompt_style: null       # specified | vague | mixed (owner ground truth for E3)
expected:
  mode_hint: null        # centaur | copilot | autopilot
  direction_hint: null   # user_heavy | balanced | ai_heavy
  min_requirements: null
  max_requirements: null
"""

    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(new_content)


def main():
    chat_dirs = sorted([d for d in glob.glob(str(CORPUS_DIR / "c*")) if os.path.isdir(d)])
    count = 0
    for cd in chat_dirs:
        meta_path = Path(cd) / "meta.yaml"
        if meta_path.exists():
            clear_meta_file(meta_path)
            count += 1

    print(f"Cleared Layer 2 predictive fields from {count} corpus meta.yaml files.")


if __name__ == "__main__":
    main()
