"""Tests for JobQueueManager and /jobs endpoints (STANDALONE_V1_PLAN §4 Step S4.3).

Per docs/PROCESSING_UX_SPEC.md v1.1:
- Shortest-first ordering (§4)
- Bounded concurrency up to Settings (1–8)
- 'Map next' priority override (§4)
- Rate-limit exponential backoff (§5)
- Crash / restart recovery: resumes from last mapped exchange without re-paying (§5)
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
from server.library import Library, atomic_write_json


@pytest.fixture
def library(tmp_path: Path) -> Library:
    lib = Library(tmp_path)
    lib.ensure_layout()
    return lib


@pytest.mark.tier1
@pytest.mark.anyio
async def test_shortest_first_ordering(library: Library) -> None:
    """§4 Choice: Shortest chats first (1-exchange before 10-exchange)."""
    executed_order: list[str] = []

    async def mock_worker(job: dict[str, Any], pair: int) -> None:
        await asyncio.sleep(0.01)
        executed_order.append(f"{job['chatId']}_p{pair}")

    queue = JobQueueManager(library=library, worker_handler=mock_worker)
    # Set concurrency to 1 to guarantee strict sequential ordering check
    library.update_settings({"parallel_jobs": 1})

    # Enqueue a long chat (10 pairs), a medium chat (3 pairs), and a short chat (1 pair)
    await queue.enqueue_job("chat_long", "Long Chat", total_pairs=10)
    await queue.enqueue_job("chat_med", "Med Chat", total_pairs=3)
    await queue.enqueue_job("chat_short", "Short Chat", total_pairs=1)

    # Let workers finish
    timeout = time.time() + 3.0
    while time.time() < timeout:
        jobs = queue.get_jobs()
        if all(j["status"] == "completed" for j in jobs):
            break
        await asyncio.sleep(0.05)

    await queue.stop()

    # Shortest (1 pair) runs first, then med (3 pairs), then long (10 pairs)
    assert executed_order[0] == "chat_short_p1"
    assert executed_order[1] == "chat_med_p1"
    assert executed_order[3] == "chat_med_p3"
    assert "chat_long_p1" in executed_order[4:]


@pytest.mark.tier1
@pytest.mark.anyio
async def test_map_next_priority_override(library: Library) -> None:
    """§4 Choice: 'Map next' bumps chat to the front of the queue."""
    executed_order: list[str] = []

    async def mock_worker(job: dict[str, Any], pair: int) -> None:
        await asyncio.sleep(0.02)
        executed_order.append(job["chatId"])

    queue = JobQueueManager(library=library, worker_handler=mock_worker)
    library.update_settings({"parallel_jobs": 1})

    # Enqueue two chats
    await queue.enqueue_job("chat_first", "First Short", total_pairs=2)
    await queue.enqueue_job("chat_second", "Second Short", total_pairs=2)
    await queue.enqueue_job("chat_third", "Third Long", total_pairs=8)

    # 'Map next' on the third long chat
    await queue.map_next("chat_third")

    # Give workers time to finish
    timeout = time.time() + 4.0
    while time.time() < timeout:
        jobs = queue.get_jobs()
        if all(j["status"] == "completed" for j in jobs):
            break
        await asyncio.sleep(0.05)

    await queue.stop()

    # chat_third received priority bump, so it executes right after currently running task
    # or immediately if nothing was started yet
    assert executed_order.index("chat_third") < executed_order.index("chat_second")


@pytest.mark.tier1
@pytest.mark.anyio
async def test_concurrency_bounded_by_setting(library: Library) -> None:
    """§4 Choice: Concurrency bounded by Settings parallel_jobs (clamped 1–8)."""
    running_concurrency = 0
    max_observed_concurrency = 0

    async def mock_worker(job: dict[str, Any], pair: int) -> None:
        nonlocal running_concurrency, max_observed_concurrency
        running_concurrency += 1
        max_observed_concurrency = max(max_observed_concurrency, running_concurrency)
        await asyncio.sleep(0.05)
        running_concurrency -= 1

    library.update_settings({"parallel_jobs": 3})
    queue = JobQueueManager(library=library, worker_handler=mock_worker)

    # Enqueue 6 chats
    for i in range(6):
        await queue.enqueue_job(f"chat_{i}", f"Chat {i}", total_pairs=2)

    timeout = time.time() + 4.0
    while time.time() < timeout:
        jobs = queue.get_jobs()
        if all(j["status"] == "completed" for j in jobs):
            break
        await asyncio.sleep(0.05)

    await queue.stop()

    # Max concurrency should never exceed setting of 3
    assert max_observed_concurrency <= 3
    assert max_observed_concurrency >= 2


@pytest.mark.tier1
@pytest.mark.anyio
async def test_rate_limit_backoff(library: Library) -> None:
    """§5 Behaviour: Rate-limited → Back off and retry automatically."""
    queue = JobQueueManager(library=library)

    # Trigger rate limit
    assert queue.get_queue_status()["isBackoff"] is False
    queue.record_rate_limit("test_chat")

    status = queue.get_queue_status()
    assert status["isBackoff"] is True
    assert status["backoffRemaining"] > 0

    # Backoff doubles on consecutive limit
    queue.record_rate_limit("test_chat")
    status2 = queue.get_queue_status()
    assert status2["backoffRemaining"] >= 3.5

    # Reset
    queue.reset_rate_limit()
    assert queue._backoff_delay == 2.0


@pytest.mark.tier1
@pytest.mark.anyio
async def test_kill_and_restart_resumes_without_repaying(library: Library) -> None:
    """§5 Behaviour: App closed or laptop sleeps → Resume on restart from last mapped exchange; never pay twice."""
    pairs_executed: list[int] = []

    async def mock_worker_stage1(job: dict[str, Any], pair: int) -> None:
        pairs_executed.append(pair)
        await asyncio.sleep(0.02)
        if pair == 2:
            # Simulate sudden interruption / shutdown at pair 2
            raise asyncio.CancelledError()

    library.update_settings({"parallel_jobs": 1})
    queue1 = JobQueueManager(library=library, worker_handler=mock_worker_stage1)
    await queue1.enqueue_job("chat_resumable", "Resumable Chat", total_pairs=4)

    # Wait for pair 1 & 2 to run
    await asyncio.sleep(0.15)
    await queue1.stop()

    # Check state on disk in jobs.json
    disk_jobs = library.get_jobs()
    job_record = next(j for j in disk_jobs if j["chatId"] == "chat_resumable")
    assert job_record["completedPairs"] >= 1

    # SIMULATE SERVER RESTART: create new JobQueueManager instance from same library
    resumed_pairs_executed: list[int] = []

    async def mock_worker_stage2(job: dict[str, Any], pair: int) -> None:
        resumed_pairs_executed.append(pair)
        await asyncio.sleep(0.02)

    queue2 = JobQueueManager(library=library, worker_handler=mock_worker_stage2)

    # Verify startup reconciliation: job was reset from 'running' to 'queued' with completedPairs intact
    reconciled_job = queue2.get_job("chat_resumable")
    assert reconciled_job is not None
    assert reconciled_job["status"] == "queued"
    assert reconciled_job["completedPairs"] == job_record["completedPairs"]

    # Start queue2 to process remaining pairs
    queue2.start()

    timeout = time.time() + 3.0
    while time.time() < timeout:
        j = queue2.get_job("chat_resumable")
        if j and j["status"] == "completed":
            break
        await asyncio.sleep(0.05)

    await queue2.stop()

    # Verify that resumed execution picked up starting from completedPairs + 1 (never re-executed earlier pairs)
    assert 1 not in resumed_pairs_executed
    assert all(p > job_record["completedPairs"] for p in resumed_pairs_executed)

    final_job = queue2.get_job("chat_resumable")
    assert final_job is not None
    assert final_job["status"] == "completed"
    assert final_job["completedPairs"] == 4


@pytest.mark.tier1
def test_job_endpoints_api(library: Library) -> None:
    """Verify REST endpoints /jobs, /jobs/{id}/priority, /jobs/{id}/cancel, pause/resume."""
    queue = JobQueueManager(library=library)
    app = create_app(library=library, job_queue=queue)
    client = TestClient(app)

    # Initially empty
    res = client.get("/api/jobs")
    assert res.status_code == 200
    assert res.json()["runningCount"] == 0
    assert res.json()["waitingCount"] == 0

    # Add a job directly to library
    jobs = [
        {
            "id": "job_c1",
            "chatId": "c1",
            "title": "Chat 1",
            "status": "queued",
            "totalPairs": 3,
            "completedPairs": 0,
            "priority": 0,
        }
    ]
    library.save_jobs(jobs)

    # GET /jobs
    res2 = client.get("/api/jobs")
    assert res2.status_code == 200
    assert res2.json()["waitingCount"] == 1
    assert len(res2.json()["jobs"]) == 1

    # POST /jobs/job_c1/priority ("Map next")
    res_prio = client.post("/api/jobs/job_c1/priority")
    assert res_prio.status_code == 200
    assert res_prio.json()["priority"] >= 10

    # POST /jobs/pause-all and resume-all
    res_pause = client.post("/api/jobs/pause-all")
    assert res_pause.status_code == 200
    assert res_pause.json()["status"] == "paused"
    assert client.get("/api/jobs").json()["isPaused"] is True

    res_resume = client.post("/api/jobs/resume-all")
    assert res_resume.status_code == 200
    assert res_resume.json()["status"] == "resumed"
    assert client.get("/api/jobs").json()["isPaused"] is False

    # POST /jobs/job_c1/cancel
    res_cancel = client.post("/api/jobs/job_c1/cancel")
    assert res_cancel.status_code == 200
    assert res_cancel.json()["status"] == "canceled"
