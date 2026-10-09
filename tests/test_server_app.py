"""Tests for server.app (Tier 1).

Covers FastAPI endpoints /health, /chats, /chats/{id}, PATCH, DELETE,
POST /chats/{id}/restore, and SSE events using TestClient.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.app import SSEBroadcaster, create_app
from server.library import Library, atomic_write_json


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
def test_health_endpoints(client: TestClient, library: Library) -> None:
    # Both /health and /api/health should respond
    res_root = client.get("/health")
    assert res_root.status_code == 200
    data_root = res_root.json()
    assert data_root["status"] == "ok"
    assert data_root["chatsCount"] == 0
    assert data_root["library"] == str(library.root)

    res_api = client.get("/api/health")
    assert res_api.status_code == 200
    assert res_api.json() == data_root


@pytest.mark.tier1
def test_list_chats_endpoint(client: TestClient, library: Library) -> None:
    # Empty list
    res = client.get("/api/chats")
    assert res.status_code == 200
    assert res.json() == []

    # Create chats
    library.create_chat("c01", title="Research Chat", category="Research")
    bundle = {
        "id": "c01",
        "title": "Research Chat",
        "category": "Research",
        "totalPairs": 2,
        "status": "ready",
        "snapshots": [
            {
                "pair": 2,
                "mass": {"outcome1": {"human": 30.0, "ai": 70.0, "delta": 0.0}},
            }
        ],
        "source": {"platform": "archive"},
    }
    atomic_write_json(library.chat_dir("c01") / "workspace_bundle.json", bundle)

    res2 = client.get("/api/chats")
    assert res2.status_code == 200
    chats = res2.json()
    assert len(chats) == 1
    assert chats[0]["id"] == "c01"
    assert chats[0]["title"] == "Research Chat"
    assert chats[0]["totalPairs"] == 2
    assert chats[0]["mass"]["total"] == 100.0
    assert chats[0]["share"]["you"] == 30.0
    assert chats[0]["share"]["ai"] == 70.0


@pytest.mark.tier1
def test_get_chat_bundle_endpoint(client: TestClient, library: Library) -> None:
    # Missing chat
    res_missing = client.get("/api/chats/unknown")
    assert res_missing.status_code == 404

    # Existing chat without bundle
    library.create_chat("c_nobundle", title="No Bundle")
    res_nobundle = client.get("/api/chats/c_nobundle")
    assert res_nobundle.status_code == 404

    # Existing chat with bundle
    bundle = {
        "id": "c_bundle",
        "title": "Bundle Chat",
        "totalPairs": 1,
        "nodes": [],
        "atoms": [],
    }
    library.create_chat("c_bundle", title="Bundle Chat")
    atomic_write_json(library.chat_dir("c_bundle") / "workspace_bundle.json", bundle)

    res_ok = client.get("/api/chats/c_bundle")
    assert res_ok.status_code == 200
    assert res_ok.json()["title"] == "Bundle Chat"


@pytest.mark.tier1
def test_update_chat_metadata_endpoint(client: TestClient, library: Library) -> None:
    library.create_chat("c_patch", title="Old Title", category="General")
    bundle = {"id": "c_patch", "title": "Old Title", "category": "General"}
    atomic_write_json(library.chat_dir("c_patch") / "workspace_bundle.json", bundle)

    # Patch title and category
    res = client.patch(
        "/api/chats/c_patch",
        json={"title": "New Title", "category": "Coding"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "New Title"
    assert data["category"] == "Coding"

    # Verify updated bundle
    bundle_updated = library.get_chat_bundle("c_patch")
    assert bundle_updated["title"] == "New Title"
    assert bundle_updated["category"] == "Coding"

    # Patch missing chat
    res_missing = client.patch("/api/chats/unknown", json={"title": "X"})
    assert res_missing.status_code == 404


@pytest.mark.tier1
def test_trash_and_restore_endpoints(client: TestClient, library: Library) -> None:
    library.create_chat("c_trash", title="Chat To Trash")

    # Trash chat
    res_delete = client.delete("/api/chats/c_trash")
    assert res_delete.status_code == 200
    assert res_delete.json() == {"status": "trashed", "id": "c_trash"}

    # Not in active list
    assert len(client.get("/api/chats").json()) == 0

    # Delete missing chat
    assert client.delete("/api/chats/unknown").status_code == 404

    # Restore chat
    res_restore = client.post("/api/chats/c_trash/restore")
    assert res_restore.status_code == 200
    assert res_restore.json() == {"status": "restored", "id": "c_trash"}

    # Back in active list
    assert len(client.get("/api/chats").json()) == 1

    # Restore missing
    assert client.post("/api/chats/not_trashed/restore").status_code == 404


@pytest.mark.tier1
def test_restore_conflict_returns_409(client: TestClient, library: Library) -> None:
    library.create_chat("conflict_id", title="Original")
    client.delete("/api/chats/conflict_id")

    # Create new active chat with same id
    library.create_chat("conflict_id", title="New Active")

    res_conflict = client.post("/api/chats/conflict_id/restore")
    assert res_conflict.status_code == 409


@pytest.mark.tier1
@pytest.mark.anyio
async def test_sse_broadcaster() -> None:
    broadcaster = SSEBroadcaster()
    queue = await broadcaster.subscribe()

    broadcaster.broadcast("pair_ready", {"chatId": "c01", "pair": 1})
    message = queue.get_nowait()
    assert message == 'event: pair_ready\ndata: {"chatId": "c01", "pair": 1}\n\n'

    await broadcaster.unsubscribe(queue)
    broadcaster.broadcast("chat_created", {"chatId": "c02"})
    assert queue.empty()
