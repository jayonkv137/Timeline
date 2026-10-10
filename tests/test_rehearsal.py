"""Tests for S4.R Rehearsal Mode (docs/PROCESSING_UX_SPEC.md v1.1 §7).

Proves:
- Zero-spend replay through the real JobQueueManager
- Pre-recorded runs from data/chats correctly discovered and shortest-first ordered
- Initial state has full dialogue readable immediately with processedPairs=0
- Incremental pair projection on disk at each pair step
- Complete SSE event emissions (queue_changed, job_progress, pair_ready, chat_ready)
- REST API endpoints /jobs/rehearsal-presets and /jobs/rehearse
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from server.app import create_app
from server.jobs import JobQueueManager
from server.library import Library
from server.rehearsal import RehearsalRunner, get_available_rehearsal_fixtures

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def library(tmp_path: Path) -> Library:
    lib = Library(tmp_path)
    lib.ensure_layout()
    return lib


class MockBroadcaster:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    def broadcast(self, event: str, data: dict[str, Any]) -> None:
        self.events.append((event, data))


@pytest.mark.tier1
def test_rehearsal_fixture_discovery() -> None:
    """Rehearsal fixtures are discovered and ordered shortest-first; fixture_pair1 is excluded."""
    fixtures = get_available_rehearsal_fixtures(REPO_ROOT)
    assert len(fixtures) >= 5

    # fixture_pair1 must NEVER be in rehearsal presets (strictly frozen test fixture)
    chat_ids = [f["chatId"] for f in fixtures]
    assert "fixture_pair1" not in chat_ids
    assert "c03_coding_short" in chat_ids
    assert "c20_coding_short" in chat_ids

    # Sorted shortest-chats-first
    pairs = [f["totalPairs"] for f in fixtures]
    assert pairs == sorted(pairs)


@pytest.mark.tier1
@pytest.mark.anyio
async def test_rehearsal_setup_chat(library: Library) -> None:
    """Setup copies artifacts and writes initial pair 0 bundle with readable transcript."""
    runner = RehearsalRunner(library=library, repo_root=REPO_ROOT)
    info = await runner.setup_chat("c20_coding_short")

    assert info["chatId"] == "c20_coding_short"
    assert info["totalPairs"] == 3

    cdir = library.chat_dir("c20_coding_short")
    assert (cdir / "dialogue.json").is_file()
    assert (cdir / "state.json").is_file()
    assert (cdir / "ledger.jsonl").is_file()

    # Initial bundle at pair 0
    bundle_file = cdir / "workspace_bundle.json"
    assert bundle_file.is_file()
    bundle = json.loads(bundle_file.read_text(encoding="utf-8"))

    assert bundle["totalPairs"] == 3
    assert bundle["processedPairs"] == 0
    assert bundle["status"] == "processing"
    # Transcript is readable immediately (§3.3)
    assert len(bundle["dialogue"]) == 6
    # No graph nodes born yet
    assert len(bundle["nodes"]) == 0


@pytest.mark.tier1
@pytest.mark.anyio
async def test_rehearsal_incremental_batch_replay(library: Library) -> None:
    """End-to-end replay through real JobQueueManager with incremental pair updates and events."""
    broadcaster = MockBroadcaster()
    queue = JobQueueManager(library=library, broadcaster=broadcaster)
    runner = RehearsalRunner(library=library, broadcaster=broadcaster, repo_root=REPO_ROOT)
    queue.set_rehearsal_runner(runner)

    # Fast replay delay for tests
    enqueued = await runner.enqueue_rehearsal_batch(
        chat_ids=["c20_coding_short", "c27_creative_short"],
        delay_seconds=0.01,
        queue_manager=queue,
    )
    assert len(enqueued) == 2

    # Wait for completion
    timeout = time.time() + 5.0
    while time.time() < timeout:
        jobs = queue.get_jobs()
        if len(jobs) >= 2 and all(j["status"] == "completed" for j in jobs):
            break
        await asyncio.sleep(0.05)

    await queue.stop()

    jobs = queue.get_jobs()
    assert len(jobs) == 2
    assert all(j["status"] == "completed" for j in jobs)

    # Verify shortest-first execution: c27 (2 pairs) finishes before c20 (3 pairs)
    chat_ready_events = [data["chatId"] for event, data in broadcaster.events if event == "chat_ready"]
    assert chat_ready_events == ["c27_creative_short", "c20_coding_short"]

    # Verify event contract (§6) was broadcast
    event_names = [e[0] for e in broadcaster.events]
    assert "queue_changed" in event_names
    assert "job_progress" in event_names
    assert "pair_ready" in event_names
    assert "chat_ready" in event_names

    # Check pair_ready events for c27_creative_short
    c27_pair_events = [data["pair"] for event, data in broadcaster.events if event == "pair_ready" and data.get("chatId") == "c27_creative_short"]
    assert c27_pair_events == [1, 2]

    # Verify final workspace bundles on disk
    bundle_c27 = library.get_chat_bundle("c27_creative_short")
    assert bundle_c27["status"] == "ready"
    assert bundle_c27["processedPairs"] == 2
    assert len(bundle_c27["nodes"]) > 0

    bundle_c20 = library.get_chat_bundle("c20_coding_short")
    assert bundle_c20["status"] == "ready"
    assert bundle_c20["processedPairs"] == 3
    assert len(bundle_c20["nodes"]) > 0


@pytest.mark.tier1
def test_rehearsal_rest_endpoints(library: Library) -> None:
    """REST API endpoints /jobs/rehearsal-presets and /jobs/rehearse."""
    broadcaster = MockBroadcaster()
    queue = JobQueueManager(library=library, broadcaster=broadcaster)
    runner = RehearsalRunner(library=library, broadcaster=broadcaster, repo_root=REPO_ROOT)
    queue.set_rehearsal_runner(runner)

    app = create_app(library=library, job_queue=queue, rehearsal_runner=runner)
    client = TestClient(app)

    # GET /jobs/rehearsal-presets
    res_presets = client.get("/api/jobs/rehearsal-presets")
    assert res_presets.status_code == 200
    presets = res_presets.json()
    assert isinstance(presets, list)
    assert len(presets) >= 5
    assert any(p["chatId"] == "c03_coding_short" for p in presets)

    # POST /jobs/rehearse
    res_start = client.post(
        "/api/jobs/rehearse",
        json={"chatIds": ["c03_coding_short"], "delaySeconds": 0.01},
    )
    assert res_start.status_code == 200
    body = res_start.json()
    assert body["status"] == "rehearsal_started"
    assert body["enqueuedCount"] == 1
    assert body["jobs"][0]["chatId"] == "c03_coding_short"
    assert body["jobs"][0]["mode"] == "rehearsal"
