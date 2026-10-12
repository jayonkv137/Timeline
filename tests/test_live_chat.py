"""Tests for Live Chat Endpoints (S5.1).

Covers:
- POST /api/chats: live chat creation and layout initialization
- POST /api/chats/{chat_id}/messages: SSE token streaming, turn persistence
- Contiguous pair numbering invariant W1 (pair 1, pair 2, ...)
- Auto-titling from initial user prompt
- Background job queue enqueuing for graph mapping
- Error validations (missing chat 404, empty message 400, auth missing)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from server.app import create_app
from server.library import Library, atomic_write_json


@pytest.fixture
def library(tmp_path: Path) -> Library:
    lib = Library(tmp_path)
    lib.ensure_layout()
    # Configure mock key so unit test runs deterministically without external LLM calls
    lib.save_settings_and_secrets({
        "api_key": "mock-test-key",
        "chat_model": "gemini-3.6-flash",
    })
    return lib


@pytest.fixture
def client(library: Library) -> TestClient:
    app = create_app(library=library)
    return TestClient(app)


def parse_sse_events(raw_text: str) -> list[tuple[str, dict[str, Any]]]:
    """Parse raw SSE stream into list of (event_type, json_data)."""
    events = []
    blocks = raw_text.strip().split("\n\n")
    for block in blocks:
        if not block.strip() or block.strip().startswith(":"):
            continue
        event_type = "message"
        data_str = ""
        for line in block.split("\n"):
            line = line.strip()
            if line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("data:"):
                data_str = line[5:].strip()
        if data_str:
            try:
                parsed_data = json.loads(data_str)
            except Exception:
                parsed_data = {"raw": data_str}
            events.append((event_type, parsed_data))
    return events


@pytest.mark.tier1
def test_create_live_chat_endpoint(client: TestClient, library: Library) -> None:
    res = client.post("/api/chats", json={"title": "Interactive Design", "category": "Design"})
    assert res.status_code == 201
    data = res.json()
    chat_id = data["id"]
    assert chat_id.startswith("chat_")
    assert data["title"] == "Interactive Design"
    assert data["category"] == "Design"
    assert data["totalPairs"] == 0
    assert data["dialogue"] == []
    assert data["status"] == "ready"

    # Verify filesystem layout
    cdir = library.chat_dir(chat_id)
    assert cdir.is_dir()
    assert (cdir / "dialogue.json").is_file()
    assert (cdir / "meta.json").is_file()
    assert (cdir / "source_meta.json").is_file()
    assert (cdir / "workspace_bundle.json").is_file()

    # GET /api/chats/{id} returns the new bundle
    get_res = client.get(f"/api/chats/{chat_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == chat_id


@pytest.mark.tier1
def test_send_chat_message_streaming(client: TestClient, library: Library) -> None:
    # 1. Create a chat
    create_res = client.post("/api/chats", json={"title": "New conversation"})
    assert create_res.status_code == 201
    chat_id = create_res.json()["id"]

    # 2. Send message and stream reply
    user_prompt = "Hello assistant, how can COTRACE help analyze thinking?"
    res = client.post(
        f"/api/chats/{chat_id}/messages",
        json={"text": user_prompt},
    )
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]

    events = parse_sse_events(res.text)
    assert len(events) > 0

    token_events = [data for evt, data in events if evt == "token"]
    assert len(token_events) > 0
    assert all("token" in d for d in token_events)

    done_events = [data for evt, data in events if evt == "done"]
    assert len(done_events) == 1
    done_data = done_events[0]
    assert done_data["chatId"] == chat_id
    assert done_data["pair"] == 1
    assert done_data["text"] != ""

    # 3. Check dialogue.json turns and schema
    cdir = library.chat_dir(chat_id)
    with (cdir / "dialogue.json").open("r", encoding="utf-8") as f:
        dialogue = json.load(f)

    assert len(dialogue) == 2
    assert dialogue[0]["pair"] == 1
    assert dialogue[0]["speaker"] == "user"
    assert dialogue[0]["text"] == user_prompt

    assert dialogue[1]["pair"] == 1
    assert dialogue[1]["speaker"] == "ai"
    assert dialogue[1]["text"] == done_data["text"]

    # 4. Check workspace_bundle.json sync
    with (cdir / "workspace_bundle.json").open("r", encoding="utf-8") as f:
        bundle = json.load(f)

    assert bundle["totalPairs"] == 1
    assert len(bundle["dialogue"]) == 2

    # 5. Check auto-titling from initial user message
    with (cdir / "meta.json").open("r", encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["title"].startswith("Hello assistant")


@pytest.mark.tier1
def test_multi_turn_contiguous_pairs_invariant(client: TestClient, library: Library) -> None:
    create_res = client.post("/api/chats", json={"title": "Multi-turn Chat"})
    chat_id = create_res.json()["id"]

    # Turn 1
    res1 = client.post(f"/api/chats/{chat_id}/messages", json={"text": "Question 1"})
    assert res1.status_code == 200
    events1 = parse_sse_events(res1.text)
    done1 = [d for e, d in events1 if e == "done"][0]
    assert done1["pair"] == 1

    # Turn 2
    res2 = client.post(f"/api/chats/{chat_id}/messages", json={"text": "Question 2"})
    assert res2.status_code == 200
    events2 = parse_sse_events(res2.text)
    done2 = [d for e, d in events2 if e == "done"][0]
    assert done2["pair"] == 2

    # Turn 3
    res3 = client.post(f"/api/chats/{chat_id}/messages", json={"text": "Question 3"})
    assert res3.status_code == 200
    events3 = parse_sse_events(res3.text)
    done3 = [d for e, d in events3 if e == "done"][0]
    assert done3["pair"] == 3

    # Validate invariant W1: dialogue has contiguous pairs 1, 1, 2, 2, 3, 3
    cdir = library.chat_dir(chat_id)
    with (cdir / "dialogue.json").open("r", encoding="utf-8") as f:
        dialogue = json.load(f)

    assert len(dialogue) == 6
    expected_sequence = [
        (1, "user"), (1, "ai"),
        (2, "user"), (2, "ai"),
        (3, "user"), (3, "ai"),
    ]
    for turn, (expected_pair, expected_speaker) in zip(dialogue, expected_sequence):
        assert turn["pair"] == expected_pair
        assert turn["speaker"] == expected_speaker

    bundle = library.get_chat_bundle(chat_id)
    assert bundle["totalPairs"] == 3


@pytest.mark.tier1
def test_send_message_validation_errors(client: TestClient, library: Library) -> None:
    # 404 for non-existent chat
    res_404 = client.post("/api/chats/non_existent_chat_999/messages", json={"text": "Hello"})
    assert res_404.status_code == 404

    # Create chat
    create_res = client.post("/api/chats", json={"title": "Validation Test"})
    chat_id = create_res.json()["id"]

    # 400 for empty or whitespace-only message
    res_empty = client.post(f"/api/chats/{chat_id}/messages", json={"text": "   "})
    assert res_empty.status_code == 400


@pytest.mark.tier1
def test_send_message_missing_api_key_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Library with no secrets and no env var
    lib = Library(tmp_path)
    lib.ensure_layout()
    # Explicitly clear any key and mock get_api_key to return empty
    atomic_write_json(lib.secrets_path, {})
    monkeypatch.setattr(lib, "get_api_key", lambda: "")
    app = create_app(library=lib)
    cl = TestClient(app)

    create_res = cl.post("/api/chats", json={"title": "No Key Chat"})
    chat_id = create_res.json()["id"]

    res = cl.post(f"/api/chats/{chat_id}/messages", json={"text": "Hello without key"})
    assert res.status_code == 200
    events = parse_sse_events(res.text)
    error_events = [d for e, d in events if e == "error"]
    assert len(error_events) == 1
    assert "No API key configured" in error_events[0]["error"]


@pytest.mark.tier1
def test_on_demand_chat_mapping_endpoint(client: TestClient, library: Library) -> None:
    # 1. Create a live chat - starts with isMapped = False
    create_res = client.post("/api/chats", json={"title": "On-demand Mapping Chat"})
    assert create_res.status_code == 201
    chat_id = create_res.json()["id"]
    assert create_res.json().get("isMapped") is False

    # 2. Trying to map an empty conversation (0 exchanges) returns 400
    empty_map_res = client.post(f"/api/chats/{chat_id}/map")
    assert empty_map_res.status_code == 400
    assert "no exchanges" in empty_map_res.json()["detail"].lower()

    # 3. Add 1 exchange
    msg_res = client.post(f"/api/chats/{chat_id}/messages", json={"text": "Explain cognitive tracing"})
    assert msg_res.status_code == 200

    # Verify chat is still isMapped: False (decoupled eager mapping)
    bundle_before = library.get_chat_bundle(chat_id)
    assert bundle_before["totalPairs"] == 1
    assert bundle_before.get("isMapped") is False

    # 4. Trigger on-demand mapping explicitly
    map_res = client.post(f"/api/chats/{chat_id}/map")
    assert map_res.status_code == 200
    map_data = map_res.json()
    assert map_data["status"] == "queued"
    assert map_data["chatId"] == chat_id
    assert map_data["totalPairs"] == 1

    # Verify isMapped is now True
    bundle_after = library.get_chat_bundle(chat_id)
    assert bundle_after.get("isMapped") is True

