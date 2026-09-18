"""Tier 1 importer tests per E0_BRIEF.md S3 and IMPORT_SPEC v1.0.

Covers role mapping, pairing rules 1-4, injected text origin tagging,
fidelity accounting (dropped media, tool narration), refusals, and idempotency.
"""
import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

import scripts.ingest_export as ie

pytestmark = pytest.mark.tier1

FIXTURES_DIR = Path(__file__).parent / "data" / "import"
SCHEMA_PATH = str(Path(__file__).parent.parent / "engine" / "schemas" / "dialogue.schema.json")


@pytest.fixture
def tmp_corpus(tmp_path):
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    return str(corpus_dir)


def test_role_mapping(tmp_corpus):
    """Role mapping: 'human'/'assistant' becomes 'user'/'ai'."""
    src = str(FIXTURES_DIR / "valid_web.json")
    rc = ie.ingest(src, "c_test_roles", tmp_corpus, dry_run=False, force=False, schema_path=SCHEMA_PATH)
    assert rc == 0

    dest = Path(tmp_corpus) / "c_test_roles"
    with open(dest / "dialogue.json", "r", encoding="utf-8") as f:
        dialogue = json.load(f)

    assert len(dialogue) == 4
    assert [t["speaker"] for t in dialogue] == ["user", "ai", "user", "ai"]
    assert dialogue[0]["text"] == "Hello assistant, write a quick outline."
    assert dialogue[1]["text"] == "Here is the quick outline for you."


def test_markdown_import(tmp_corpus):
    """Claude web markdown export parsing and import."""
    src = str(FIXTURES_DIR / "valid_web.md")
    rc = ie.ingest(src, "c_test_md", tmp_corpus, dry_run=False, force=False, schema_path=SCHEMA_PATH)
    assert rc == 0

    dest = Path(tmp_corpus) / "c_test_md"
    with open(dest / "dialogue.json", "r", encoding="utf-8") as f:
        dialogue = json.load(f)
    assert len(dialogue) == 2
    assert dialogue[0]["speaker"] == "user"
    assert dialogue[0]["text"] == "Can we review the budget?"
    assert dialogue[1]["speaker"] == "ai"
    assert dialogue[1]["text"] == "Yes, let's review the line items."


def test_pairing_rule_1_leading_ai_dropped(tmp_corpus):
    """Pairing rule 1: conversation starting with an AI turn drops the leading AI turn."""
    src = str(FIXTURES_DIR / "leading_ai.json")
    rc = ie.ingest(src, "c_test_r1", tmp_corpus, dry_run=False, force=False, schema_path=SCHEMA_PATH)
    assert rc == 0

    dest = Path(tmp_corpus) / "c_test_r1"
    with open(dest / "dialogue.json", "r", encoding="utf-8") as f:
        dialogue = json.load(f)
    with open(dest / "source_meta.json", "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert len(dialogue) == 2
    assert dialogue[0]["speaker"] == "user"
    assert dialogue[0]["text"] == "I need help with Python."
    assert dialogue[1]["speaker"] == "ai"
    assert meta["fidelity"]["dropped_leading_ai_turn"] is True


def test_pairing_rule_2_consecutive_user_merged(tmp_corpus):
    """Pairing rule 2: two consecutive user turns merged, 'merged:2' flag present."""
    src = str(FIXTURES_DIR / "consecutive_user.json")
    rc = ie.ingest(src, "c_test_r2", tmp_corpus, dry_run=False, force=False, schema_path=SCHEMA_PATH)
    assert rc == 0

    dest = Path(tmp_corpus) / "c_test_r2"
    with open(dest / "dialogue.json", "r", encoding="utf-8") as f:
        dialogue = json.load(f)
    with open(dest / "source_meta.json", "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert len(dialogue) == 2
    assert dialogue[0]["speaker"] == "user"
    assert "First message from user." in dialogue[0]["text"]
    assert "Second consecutive message from user." in dialogue[0]["text"]
    assert meta["fidelity"]["merged_turns"] == 1
    assert "merged:2" in meta["turn_meta"][0]["flags"]


def test_pairing_rule_3_trailing_user_dropped(tmp_corpus):
    """Pairing rule 3: trailing user turn with no reply is dropped."""
    src = str(FIXTURES_DIR / "trailing_user.json")
    rc = ie.ingest(src, "c_test_r3", tmp_corpus, dry_run=False, force=False, schema_path=SCHEMA_PATH)
    assert rc == 0

    dest = Path(tmp_corpus) / "c_test_r3"
    with open(dest / "dialogue.json", "r", encoding="utf-8") as f:
        dialogue = json.load(f)
    with open(dest / "source_meta.json", "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert len(dialogue) == 2
    assert meta["pairs"] == 1
    assert meta["fidelity"]["dropped_trailing_user_turn"] is True


def test_pairing_rule_4_empty_turn_kept(tmp_corpus):
    """Pairing rule 4: empty turn kept and flagged 'empty', pair structure intact."""
    src = str(FIXTURES_DIR / "empty_turn.json")
    rc = ie.ingest(src, "c_test_r4", tmp_corpus, dry_run=False, force=False, schema_path=SCHEMA_PATH)
    assert rc == 0

    dest = Path(tmp_corpus) / "c_test_r4"
    with open(dest / "dialogue.json", "r", encoding="utf-8") as f:
        dialogue = json.load(f)
    with open(dest / "source_meta.json", "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert len(dialogue) == 2
    assert dialogue[0]["text"] == ""
    assert meta["turn_meta"][0]["flags"] == ["empty"]
    assert meta["fidelity"]["empty_turns"] == 1


def test_injected_detection_all_five_rules(tmp_corpus):
    """Injected text detection for all 5 rules (IMPORT_SPEC §4).

    Rules: slash_command, task_notification, skill_preamble, auto_continue, system_note.
    Each is tagged 'injected' and text remains intact in dialogue.json.
    """
    src = str(FIXTURES_DIR / "injected_turns.json")
    rc = ie.ingest(src, "c_test_injected", tmp_corpus, dry_run=False, force=False, schema_path=SCHEMA_PATH)
    assert rc == 0

    dest = Path(tmp_corpus) / "c_test_injected"
    with open(dest / "dialogue.json", "r", encoding="utf-8") as f:
        dialogue = json.load(f)
    with open(dest / "source_meta.json", "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["pairs"] == 5
    assert meta["fidelity"]["injected_turns"] == 5

    user_turn_metas = [m for m in meta["turn_meta"] if m["speaker"] == "user"]
    expected_flags = [
        "slash_command",
        "task_notification",
        "skill_preamble",
        "auto_continue",
        "system_note",
    ]

    for m, flag in zip(user_turn_metas, expected_flags):
        assert m["origin"] == "injected"
        assert flag in m["flags"]

    # Verify text is intact in dialogue.json
    assert "<command-name>/help</command-name>" in dialogue[0]["text"]
    assert "<task-notification>" in dialogue[2]["text"]
    assert "Skill /data-analysis is already loaded" in dialogue[4]["text"]
    assert dialogue[6]["text"] == "continue"
    assert "[system] System notification." in dialogue[8]["text"]


def test_dropped_media_and_tool_narration(tmp_corpus):
    """Dropped media placeholders recorded and counted in fidelity, placeholder intact."""
    src = str(FIXTURES_DIR / "images_dropped.json")
    rc = ie.ingest(src, "c_test_media", tmp_corpus, dry_run=False, force=False, schema_path=SCHEMA_PATH)
    assert rc == 0

    dest = Path(tmp_corpus) / "c_test_media"
    with open(dest / "dialogue.json", "r", encoding="utf-8") as f:
        dialogue = json.load(f)
    with open(dest / "source_meta.json", "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["fidelity"]["images_dropped"] == 1
    assert meta["fidelity"]["attachments_dropped"] == 1
    assert meta["fidelity"]["tool_narration_turns"] == 1

    user_meta = meta["turn_meta"][0]
    assert user_meta["dropped_media"] == ["test_diagram.png", "spec_doc.pdf"]

    ai_meta = meta["turn_meta"][1]
    assert "tool_narration" in ai_meta["flags"]

    # Placeholders are kept in dialogue text
    assert "[Image: test_diagram.png]" in dialogue[0]["text"]
    assert "[Attachment: spec_doc.pdf]" in dialogue[0]["text"]
    assert "Used tool" in dialogue[1]["text"]


def test_claude_code_refusal():
    """Claude code .jsonl transcript is refused with exit code 2."""
    src = str(FIXTURES_DIR / "claude_code.jsonl")
    rc = ie.ingest(src, "c_test_code", "/tmp", dry_run=True, force=False, schema_path=SCHEMA_PATH)
    assert rc == 2


def test_malformed_json_refusal(tmp_corpus):
    """Malformed JSON is refused with exit code 2 and nothing is written."""
    src = str(FIXTURES_DIR / "malformed.json")
    rc = ie.ingest(src, "c_test_malformed", tmp_corpus, dry_run=False, force=False, schema_path=SCHEMA_PATH)
    assert rc == 2
    assert not (Path(tmp_corpus) / "c_test_malformed").exists()


def test_reimport_without_force_refused(tmp_corpus):
    """Re-importing into existing directory without --force is refused with exit code 1."""
    src = str(FIXTURES_DIR / "valid_web.json")
    rc1 = ie.ingest(src, "c_test_force", tmp_corpus, dry_run=False, force=False, schema_path=SCHEMA_PATH)
    assert rc1 == 0

    rc2 = ie.ingest(src, "c_test_force", tmp_corpus, dry_run=False, force=False, schema_path=SCHEMA_PATH)
    assert rc2 == 1

    rc3 = ie.ingest(src, "c_test_force", tmp_corpus, dry_run=False, force=True, schema_path=SCHEMA_PATH)
    assert rc3 == 0


def test_timestamp_parsing_and_assumed_utc(tmp_corpus):
    """Timestamp without timezone sets assumed_utc: True."""
    src = str(FIXTURES_DIR / "no_tz.json")
    rc = ie.ingest(src, "c_test_tz", tmp_corpus, dry_run=False, force=False, schema_path=SCHEMA_PATH)
    assert rc == 0

    dest = Path(tmp_corpus) / "c_test_tz"
    with open(dest / "dialogue.json", "r", encoding="utf-8") as f:
        dialogue = json.load(f)
    with open(dest / "source_meta.json", "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["assumed_utc"] is True
    assert dialogue[0]["ts"].endswith("Z")
    assert dialogue[1]["ts"].endswith("Z")


def test_artifacts_and_schema_validation(tmp_corpus):
    """Normalised dialogue.json strictly validates against dialogue.schema.json."""
    src = str(FIXTURES_DIR / "valid_web.json")
    rc = ie.ingest(src, "c_test_artifacts", tmp_corpus, dry_run=False, force=False, schema_path=SCHEMA_PATH)
    assert rc == 0

    dest = Path(tmp_corpus) / "c_test_artifacts"
    assert (dest / "dialogue.json").exists()
    assert (dest / "source_meta.json").exists()
    assert (dest / "meta.yaml").exists()
    assert (dest / "source.json").exists()

    with open(dest / "meta.yaml", "r", encoding="utf-8") as f:
        meta_yaml_text = f.read()
    assert "id: c_test_artifacts" in meta_yaml_text
    assert "source_kind: claude_web_json" in meta_yaml_text
    assert "length_band: short" in meta_yaml_text
