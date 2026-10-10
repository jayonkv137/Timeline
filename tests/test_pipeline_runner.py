"""Tests for PipelineRunner (STANDALONE_V1_PLAN §4 Step S4.4 & docs/PROCESSING_UX_SPEC.md v1.1 §5, §6).

Covers:
- Auth guard halting before spend when no API key configured (§5)
- Rate-limit backoff handling and re-queueing without crash (§5)
- Budget cap halting, pause state with budget_reached, and re-queueing (§5)
- Invariant violation flagging (pair_flagged broadcast) without halting pipeline (§5)
- Replay execution with CachingLLMClient updating state, ledger, and workspace bundle
- End-to-end integration with JobQueueManager emitting all §6 events
"""

from __future__ import annotations

import asyncio
import json
import shutil
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from engine.budget import BudgetStopError
from engine.checks import InvariantViolationError
from engine.llm import RateLimitError
from engine.llm_cache import CachingLLMClient
from server.jobs import JobQueueManager
from server.library import Library
from server.pipeline_runner import PipelineRunner

REPO_ROOT = Path(__file__).resolve().parent.parent


class MockBroadcaster:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    def broadcast(self, event: str, data: dict[str, Any]) -> None:
        self.events.append((event, data))


@pytest.fixture
def library(tmp_path: Path) -> Library:
    lib = Library(tmp_path)
    lib.ensure_layout()
    return lib


def setup_test_chat(library: Library, chat_id: str = "c10_research_short") -> Path:
    """Copy corpus chat dialogue into library chat dir."""
    cdir = library.chat_dir(chat_id)
    cdir.mkdir(parents=True, exist_ok=True)
    src_dialogue = REPO_ROOT / f"data/corpus/{chat_id}/dialogue.json"
    shutil.copy2(src_dialogue, cdir / "dialogue.json")
    return cdir


@pytest.mark.tier1
@pytest.mark.anyio
async def test_pipeline_runner_auth_guard(library: Library, monkeypatch: pytest.MonkeyPatch) -> None:
    """When no API key is configured and no mock client is supplied, halt before spend (§5)."""
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    library.save_settings_and_secrets({"llm_api_key": ""})

    broadcaster = MockBroadcaster()
    runner = PipelineRunner(library=library, broadcaster=broadcaster)

    setup_test_chat(library, "c10_research_short")
    job = {"id": "job_1", "chatId": "c10_research_short", "totalPairs": 1}

    with pytest.raises(ValueError, match="No API key configured"):
        await runner.handle_pair(job, 1)

    # Verify job_error event with kind 'auth' was emitted
    auth_errors = [data for evt, data in broadcaster.events if evt == "job_error" and data.get("kind") == "auth"]
    assert len(auth_errors) == 1
    assert auth_errors[0]["chatId"] == "c10_research_short"


@pytest.mark.tier1
@pytest.mark.anyio
async def test_pipeline_runner_rate_limit_backoff(library: Library) -> None:
    """RateLimitError notifies queue to back off and re-raises so worker re-queues (§5)."""
    broadcaster = MockBroadcaster()
    queue = JobQueueManager(library=library, broadcaster=broadcaster)
    runner = PipelineRunner(library=library, broadcaster=broadcaster, job_queue=queue)

    setup_test_chat(library, "c10_research_short")
    job = {"id": "job_rl", "chatId": "c10_research_short", "totalPairs": 1}

    mock_client = MagicMock()
    mock_client.call_json.side_effect = RateLimitError(
        message="Rate limit reached",
        response=MagicMock(status_code=429),
        body=None,
    )
    runner.custom_client = mock_client

    with pytest.raises(RateLimitError):
        await runner.handle_pair(job, 1)

    # Queue should be in backoff mode
    status = queue.get_queue_status()
    assert status["isBackoff"] is True
    assert status["backoffRemaining"] > 0

    # Event contract: job_error with kind 'rate_limit'
    rl_events = [data for evt, data in broadcaster.events if evt == "job_error" and data.get("kind") == "rate_limit"]
    assert len(rl_events) == 1
    assert rl_events[0]["chatId"] == "c10_research_short"


@pytest.mark.tier1
@pytest.mark.anyio
async def test_pipeline_runner_budget_stop(library: Library) -> None:
    """BudgetStopError notifies queue to pause with reason 'budget_reached' (§5)."""
    broadcaster = MockBroadcaster()
    queue = JobQueueManager(library=library, broadcaster=broadcaster)
    runner = PipelineRunner(library=library, broadcaster=broadcaster, job_queue=queue)

    setup_test_chat(library, "c10_research_short")
    job = {"id": "job_bg", "chatId": "c10_research_short", "totalPairs": 1}

    mock_client = MagicMock()
    mock_client.call_json.side_effect = BudgetStopError("Budget cap reached: spent $50.25 >= cap $50.00")
    runner.custom_client = mock_client

    with pytest.raises(BudgetStopError):
        await runner.handle_pair(job, 1)

    # Queue should be paused with budget_reached
    status = queue.get_queue_status()
    assert status["isPaused"] is True
    assert status["pauseReason"] == "budget_reached"

    # Event contract: budget_stop emitted
    bg_events = [data for evt, data in broadcaster.events if evt == "budget_stop"]
    assert len(bg_events) == 1


@pytest.mark.tier1
@pytest.mark.anyio
async def test_pipeline_runner_invariant_flagged(library: Library) -> None:
    """Invariant violation flags the pair via SSE without halting the pipeline in product mode (§5)."""
    broadcaster = MockBroadcaster()
    runner = PipelineRunner(library=library, broadcaster=broadcaster)

    setup_test_chat(library, "c10_research_short")
    job = {"id": "job_inv", "chatId": "c10_research_short", "totalPairs": 1}
    runner.custom_client = MagicMock()

    # Simulate invariant violation in _execute_pair_sync
    inv_err = InvariantViolationError(
        violations=["inv_05 duplicate row"],
        failed_checks=["inv_05"],
    )
    with patch.object(runner, "_execute_pair_sync", side_effect=inv_err):
        await runner.handle_pair(job, 1)

    # Event contract: pair_flagged emitted
    flagged = [data for evt, data in broadcaster.events if evt == "pair_flagged"]
    assert len(flagged) == 1
    assert flagged[0]["chatId"] == "c10_research_short"
    assert flagged[0]["pair"] == 1
    assert "inv_05" in flagged[0]["reason"]


@pytest.mark.tier1
@pytest.mark.anyio
async def test_pipeline_runner_replay_execution(library: Library) -> None:
    """Execution with CachingLLMClient in replay mode produces full state, ledger, and workspace bundle."""
    broadcaster = MockBroadcaster()
    client = CachingLLMClient(
        inner_client=None,
        mode="replay",
        cassettes_dir=REPO_ROOT / "tests/cassettes",
    )
    runner = PipelineRunner(library=library, broadcaster=broadcaster, custom_client=client)

    cdir = setup_test_chat(library, "c10_research_short")
    job = {"id": "job_replay", "chatId": "c10_research_short", "totalPairs": 1}

    await runner.handle_pair(job, 1)

    # Verify artifacts produced on disk
    assert (cdir / "state.json").is_file()
    assert (cdir / "ledger.jsonl").is_file()
    assert (cdir / "run/pipeline_state.json").is_file()
    assert (cdir / "run/status.json").is_file()
    assert (cdir / "run/report.json").is_file()
    assert (cdir / "workspace_bundle.json").is_file()

    bundle = json.loads((cdir / "workspace_bundle.json").read_text(encoding="utf-8"))
    assert bundle["status"] == "ready"
    assert bundle["processedPairs"] == 1
    assert bundle["totalPairs"] == 1
    assert len(bundle["nodes"]) > 0
    assert len(bundle["dialogue"]) == 2


@pytest.mark.tier1
@pytest.mark.anyio
async def test_pipeline_runner_integrated_with_queue(library: Library) -> None:
    """Full end-to-end integration: JobQueueManager runs PipelineRunner with complete §6 events."""
    broadcaster = MockBroadcaster()
    queue = JobQueueManager(library=library, broadcaster=broadcaster)
    client = CachingLLMClient(
        inner_client=None,
        mode="replay",
        cassettes_dir=REPO_ROOT / "tests/cassettes",
    )
    runner = PipelineRunner(library=library, broadcaster=broadcaster, custom_client=client)
    queue.set_pipeline_runner(runner)

    setup_test_chat(library, "c10_research_short")

    # Enqueue job
    await queue.enqueue_job(
        chat_id="c10_research_short",
        title="Analysis",
        total_pairs=1,
    )

    # Wait for completion
    timeout = time.time() + 5.0
    while time.time() < timeout:
        j = queue.get_job("c10_research_short")
        if j and j.get("status") == "completed":
            break
        await asyncio.sleep(0.05)

    await queue.stop()

    job = queue.get_job("c10_research_short")
    assert job is not None
    assert job["status"] == "completed"
    assert job["completedPairs"] == 1
    assert len(job.get("timingLog", [])) == 1

    # Verify event contract (§6)
    event_names = [e[0] for e in broadcaster.events]
    assert "queue_changed" in event_names
    assert "job_progress" in event_names
    assert "pair_ready" in event_names
    assert "chat_ready" in event_names

    # Verify workspace bundle
    bundle = library.get_chat_bundle("c10_research_short")
    assert bundle["status"] == "ready"
    assert bundle["processedPairs"] == 1
