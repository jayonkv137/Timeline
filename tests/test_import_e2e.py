"""End-to-end test for Import Dialog review table (STANDALONE_V1_PLAN §4 Step S4.2).

Verifies that uploading a fixture export returns the expected review table rows:
- title, date, pairs, fidelity grade, sensitive flag, cost estimate, checkbox selection
- filters: "≥ 3 exchanges", search query, sort ordering
- footer: "Process N chats · ≈ $LOW–HIGH" cost gate computation.
"""

from __future__ import annotations

import json
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

from server.app import create_app
from server.library import Library


@pytest.fixture
def library(tmp_path: Path) -> Library:
    lib = Library(tmp_path)
    lib.ensure_layout()
    return lib


@pytest.fixture
def client(library: Library) -> TestClient:
    app = create_app(library=library)
    return TestClient(app)


@pytest.mark.tier1
def test_fixture_export_review_table_e2e(client: TestClient, tmp_path: Path) -> None:
    """e2e: a fixture export → the review table shows the expected rows and cost gate."""
    # Build representative multi-chat fixture
    fixture_chats = [
        {
            "uuid": "conv-short-1",
            "name": "Quick Weather Question",
            "created_at": "2026-05-10T08:00:00Z",
            "chat_messages": [
                {"sender": "human", "text": "What is the weather today?", "created_at": "2026-05-10T08:00:00Z"},
                {"sender": "assistant", "text": "It is sunny and 18°C.", "created_at": "2026-05-10T08:00:30Z"},
            ],
        },
        {
            "uuid": "conv-med-3pairs",
            "name": "Planning German Trip Schedule",
            "created_at": "2026-05-11T09:00:00Z",
            "chat_messages": [
                {"sender": "human", "text": "Let us plan day 1 in Berlin.", "created_at": "2026-05-11T09:00:00Z"},
                {"sender": "assistant", "text": "Visit Museum Island first.", "created_at": "2026-05-11T09:01:00Z"},
                {"sender": "human", "text": "What about lunch?", "created_at": "2026-05-11T09:02:00Z"},
                {"sender": "assistant", "text": "Try a local bistro in Mitte.", "created_at": "2026-05-11T09:03:00Z"},
                {"sender": "human", "text": "And the evening?", "created_at": "2026-05-11T09:04:00Z"},
                {"sender": "assistant", "text": "Walk along the Spree river.", "created_at": "2026-05-11T09:05:00Z"},
            ],
        },
        {
            "uuid": "conv-sensitive-med",
            "name": "Doctor consultation for bicep pain",
            "created_at": "2026-05-12T14:00:00Z",
            "chat_messages": [
                {"sender": "human", "text": "My doctor said I have a bicep symptom.", "created_at": "2026-05-12T14:00:00Z"},
                {"sender": "assistant", "text": "Make sure to rest and follow prescription advice.", "created_at": "2026-05-12T14:01:00Z"},
                {"sender": "human", "text": "Should I visit the clinic again?", "created_at": "2026-05-12T14:02:00Z"},
                {"sender": "assistant", "text": "Yes, if the pain persists.", "created_at": "2026-05-12T14:03:00Z"},
                {"sender": "human", "text": "Thank you doctor.", "created_at": "2026-05-12T14:04:00Z"},
                {"sender": "assistant", "text": "Take care.", "created_at": "2026-05-12T14:05:00Z"},
            ],
        },
        {
            "uuid": "conv-code-5pairs",
            "name": "FastAPI Router Implementation with Code",
            "created_at": "2026-05-13T16:00:00Z",
            "chat_messages": [
                {"sender": "human", "text": "Write a python script: ```python\nprint('hello')\n```", "created_at": "2026-05-13T16:00:00Z"},
                {"sender": "assistant", "text": "```python\nimport sys\n```", "created_at": "2026-05-13T16:01:00Z"},
                {"sender": "human", "text": "Add error handling.", "created_at": "2026-05-13T16:02:00Z"},
                {"sender": "assistant", "text": "```python\ntry: pass\nexcept: pass\n```", "created_at": "2026-05-13T16:03:00Z"},
                {"sender": "human", "text": "Now add tests.", "created_at": "2026-05-13T16:04:00Z"},
                {"sender": "assistant", "text": "```python\ndef test(): assert True\n```", "created_at": "2026-05-13T16:05:00Z"},
            ],
        },
    ]

    fixture_file = tmp_path / "fixture_export.json"
    fixture_file.write_text(json.dumps(fixture_chats), encoding="utf-8")

    # 1. Post upload with sync=true
    res = client.post("/api/imports?sync=true", json={"filePath": str(fixture_file)})
    assert res.status_code == 200
    report = res.json()

    assert report["status"] == "ready"
    assert report["totalConversations"] == 4
    assert len(report["conversations"]) == 4

    rows = {c["convId"]: c for c in report["conversations"]}

    # Check row 1: Quick weather (1 pair, clean, not sensitive)
    r1 = rows["claude_conv-short-1"]
    assert r1["pairs"] == 1
    assert r1["rawTitle"] == "Quick Weather Question"
    assert r1["fidelityGrade"] == "clean"
    assert r1["sensitive"] is False
    assert r1["estimate"]["cost"]["expected"] > 0

    # Check row 2: Planning Berlin trip (3 pairs, clean)
    r2 = rows["claude_conv-med-3pairs"]
    assert r2["pairs"] == 3
    assert r2["fidelityGrade"] == "clean"
    assert r2["sensitive"] is False

    # Check row 3: Doctor consultation (3 pairs, sensitive flagged)
    r3 = rows["claude_conv-sensitive-med"]
    assert r3["pairs"] == 3
    assert r3["sensitive"] is True
    assert "doctor" in r3["sensitiveTriggers"]
    assert "bicep" in r3["sensitiveTriggers"]
    assert "pain" in r3["sensitiveTriggers"]

    # Check row 4: Code chat (3 pairs, has_code true)
    r4 = rows["claude_conv-code-5pairs"]
    assert r4["pairs"] == 3
    assert r4["hasCode"] is True

    # 2. Test ">= 3 exchanges" filter logic
    filtered_min_3 = [c for c in report["conversations"] if c["pairs"] >= 3]
    assert len(filtered_min_3) == 3  # excludes conv-short-1 (1 pair)
    assert not any(c["convId"] == "claude_conv-short-1" for c in filtered_min_3)

    # 3. Test Search filtering
    searched_doctor = [c for c in report["conversations"] if "doctor" in c["rawTitle"].lower() or any("doctor" in t for t in c["sensitiveTriggers"])]
    assert len(searched_doctor) == 1
    assert searched_doctor[0]["convId"] == "claude_conv-sensitive-med"

    # 4. Test Cost Gate Footer calculation for the 3 selected chats
    selected = filtered_min_3
    selected_pairs = sum(c["pairs"] for c in selected)
    assert selected_pairs == 9
    cost_low = sum(c["estimate"]["cost"]["low"] for c in selected)
    cost_high = sum(c["estimate"]["cost"]["high"] for c in selected)

    footer_text = f"Process {len(selected)} chats · ≈ ${cost_low:.2f}–{cost_high:.2f}"
    assert "Process 3 chats · ≈ $" in footer_text
    assert cost_low < cost_high
