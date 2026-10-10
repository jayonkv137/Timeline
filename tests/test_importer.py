"""Tests for engine.importer (STANDALONE_V1_PLAN §4 Step S4.1).

Tests mechanical export ingestion, triage scanning, pairing rules,
duplicate detection, pre-flight estimation, and chat promotion with zero LLM calls.
"""

from __future__ import annotations

import json
import time
import zipfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from engine.importer import (
    check_sensitive,
    detect_language,
    extract_archive,
    extract_claude_message_content,
    get_dialogue_schema_path,
    parse_claude_export,
    promote_conversation,
    scan_import,
    simulate_pairing,
    validate_dialogue_json,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "data" / "import"


@pytest.mark.tier1
def test_detect_language() -> None:
    en_sample = ["This is a test of the English language detection routine.", "We want to see if it works."]
    de_sample = ["Wir möchten sehen, ob die deutsche Spracherkennung funktioniert.", "Das ist ein schöner Test."]
    assert detect_language(en_sample) == "en"
    assert detect_language(de_sample) == "de"


@pytest.mark.tier1
def test_check_sensitive() -> None:
    # Non-sensitive
    flag, triggers = check_sensitive("Python coding questions", "How do I sort a dictionary?")
    assert flag is False
    assert triggers == []

    # Sensitive medical/immigration/legal
    flag_med, triggers_med = check_sensitive("Doctor appointment for severe pain", "My symptom started yesterday in my bicep.")
    assert flag_med is True
    assert "doctor" in triggers_med
    assert "pain" in triggers_med
    assert "symptom" in triggers_med

    flag_visa, triggers_visa = check_sensitive("Appointment at consulate", "Applying for residence permit and visa.")
    assert flag_visa is True
    assert "consulate" in triggers_visa
    assert "visa" in triggers_visa


@pytest.mark.tier1
def test_extract_claude_message_content_and_flags() -> None:
    msg = {
        "sender": "assistant",
        "content": [
            {"type": "thinking", "thinking": "Let me consider..."},
            {"type": "text", "text": "Here is the result.\nUsed tool calculator"},
            {"type": "image", "name": "diagram.png"},
        ],
        "attachments": [{"file_name": "table.pdf", "file_type": "application/pdf"}],
        "files": [{"file_name": "screenshot.png"}],
    }
    text, flags, dropped_media = extract_claude_message_content(msg)
    assert "Here is the result." in text
    assert "thinking" in flags
    assert "tool_narration" in flags
    assert any("diagram.png" in m for m in dropped_media)
    assert any("screenshot.png" in m for m in dropped_media)


@pytest.mark.tier1
def test_simulate_pairing_rules() -> None:
    # Rule 1: Leading AI dropped
    # Rule 2: Consecutive user merged
    # Rule 3: Trailing user dropped
    turns = [
        {"speaker": "ai", "text": "Hello there"},
        {"speaker": "user", "text": "User part 1"},
        {"speaker": "user", "text": "User part 2"},
        {"speaker": "ai", "text": "AI response 1"},
        {"speaker": "user", "text": "User part 3"},
    ]
    pairs, merged, dropped_trailing = simulate_pairing(turns)
    assert pairs == 1
    assert merged == 1
    assert dropped_trailing == 1


@pytest.mark.tier1
def test_parse_claude_export_and_preflight_estimate() -> None:
    raw_conv = {
        "uuid": "test-uuid-1234",
        "name": "Planning German Trip",
        "created_at": "2026-05-01T10:00:00Z",
        "updated_at": "2026-05-01T10:30:00Z",
        "chat_messages": [
            {
                "sender": "human",
                "content": [{"type": "text", "text": "Can you help me plan a trip to Berlin?"}],
                "created_at": "2026-05-01T10:00:00Z",
            },
            {
                "sender": "assistant",
                "content": [{"type": "text", "text": "Certainly! Berlin has great sights."}],
                "created_at": "2026-05-01T10:01:00Z",
            },
        ],
    }
    archive_rec, row = parse_claude_export(raw_conv, estimate_costs=True)
    assert archive_rec["conv_id"] == "claude_test-uuid-1234"
    assert row["pairs"] == 1
    assert row["fidelityGrade"] == "clean"
    assert row["isDuplicate"] is False

    # Check estimate
    est = row["estimate"]
    assert est["tokens"]["expected"] > 0
    assert est["cost"]["expected"] > 0.0
    assert est["cost"]["low"] <= est["cost"]["expected"] <= est["cost"]["high"]


@pytest.mark.tier1
def test_promote_conversation_and_schema_validation(tmp_path: Path) -> None:
    raw_conv = {
        "uuid": "promoted-conv-999",
        "name": "Architecture Review",
        "created_at": "2026-06-01T12:00:00Z",
        "updated_at": "2026-06-01T12:10:00Z",
        "chat_messages": [
            {"sender": "human", "text": "Review this architecture.", "created_at": "2026-06-01T12:00:00Z"},
            {"sender": "assistant", "text": "Looks solid and modular.", "created_at": "2026-06-01T12:05:00Z"},
        ],
    }
    target_dir = tmp_path / "promoted_chat"
    res = promote_conversation(
        conv_data=raw_conv,
        dest_dir=target_dir,
        chat_id="c_arch_review",
        category="Architecture",
    )
    assert res["chatId"] == "c_arch_review"
    assert res["pairs"] == 1
    assert res["grade"] == "clean"

    # Verify 4 files on disk
    assert (target_dir / "dialogue.json").is_file()
    assert (target_dir / "source_meta.json").is_file()
    assert (target_dir / "meta.json").is_file()
    assert (target_dir / "source.json").is_file()

    # Verify dialogue contents against schema
    with open(target_dir / "dialogue.json", "r", encoding="utf-8") as f:
        dialogue = json.load(f)
    assert len(dialogue) == 2
    validate_dialogue_json(dialogue)


@pytest.mark.tier1
def test_scan_import_zip_archive(tmp_path: Path) -> None:
    # Prepare fixture zip with conversations.json
    raw_convs = [
        {
            "uuid": "conv-a",
            "name": "Chat A",
            "created_at": "2026-01-01T00:00:00Z",
            "chat_messages": [
                {"sender": "human", "text": "Hello A", "created_at": "2026-01-01T00:00:00Z"},
                {"sender": "assistant", "text": "Reply A", "created_at": "2026-01-01T00:01:00Z"},
            ],
        },
        {
            "uuid": "conv-b",
            "name": "Chat B with visa questions",
            "created_at": "2026-01-02T00:00:00Z",
            "chat_messages": [
                {"sender": "human", "text": "Where is the consulate?", "created_at": "2026-01-02T00:00:00Z"},
                {"sender": "assistant", "text": "In Frankfurt.", "created_at": "2026-01-02T00:01:00Z"},
            ],
        },
    ]

    import_batch_dir = tmp_path / "imp_test_batch"
    raw_dir = import_batch_dir / "raw"
    raw_dir.mkdir(parents=True)

    zip_path = raw_dir / "export.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("conversations.json", json.dumps(raw_convs))

    report = scan_import(raw_dir=raw_dir, import_id="imp_test_batch", library_root=tmp_path)
    assert report["importId"] == "imp_test_batch"
    assert report["status"] == "ready"
    assert report["totalConversations"] == 2
    assert report["totalPairs"] == 2
    assert report["fidelity"]["clean"] == 2
    assert report["sensitiveCount"] == 1
    assert report["estimate"]["tokens"]["expected"] > 0
    assert report["estimate"]["cost"]["expected"] > 0.0

    # Verify report was written to disk
    report_on_disk = import_batch_dir / "report.json"
    assert report_on_disk.is_file()
    with open(report_on_disk, "r", encoding="utf-8") as f:
        disk_data = json.load(f)
    assert disk_data["totalConversations"] == 2


@pytest.mark.tier1
def test_real_claude_export_313_conversations_zero_llm(tmp_path: Path) -> None:
    """Verifies that uploading / scanning the real Claude export lists exactly
    313 conversations with zero LLM calls in under 5 seconds.
    """
    real_export = Path("data/calude/conversations.json")
    if not real_export.is_file():
        pytest.skip("data/calude/conversations.json not found in workspace")

    batch_dir = tmp_path / "imp_real_313"
    raw_dir = batch_dir / "raw"
    raw_dir.mkdir(parents=True)

    # Place file in raw_dir
    import shutil
    shutil.copy2(real_export, raw_dir / "conversations.json")

    # Mock OpenAI client or network to strictly guarantee zero LLM calls
    with patch("openai.OpenAI") as mock_openai, patch("urllib.request.urlopen") as mock_url:
        t0 = time.time()
        report = scan_import(raw_dir=raw_dir, import_id="imp_real_313", library_root=tmp_path)
        t1 = time.time()

        # Zero LLM / network calls occurred
        mock_openai.assert_not_called()
        mock_url.assert_not_called()

    duration = t1 - t0
    # Must be under 5 seconds (well within the <= 30s budget)
    assert duration < 5.0, f"Scanning 313 chats took {duration:.2f}s, expected < 5.0s"

    assert report["importId"] == "imp_real_313"
    assert report["status"] == "ready"
    assert report["totalConversations"] == 313
    assert report["totalPairs"] == 2759
    assert report["fidelity"]["clean"] > 0
    assert report["estimate"]["cost"]["expected"] > 0.0
    assert len(report["conversations"]) == 313

    # Check report.json file on disk
    report_file = batch_dir / "report.json"
    assert report_file.is_file()
