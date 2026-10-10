"""Tests for Step S4.5: Product-mode invariants (Decision S-D9).

Verifies:
- is_state_valid correctly identifies sound vs corrupt states.
- Strict mode (stop_on_violation=True) raises InvariantViolationError on failure.
- Product mode (stop_on_violation=False) flags the pair ('needs_review'), keeps going
  across pairs when the state is valid, and writes a valid, renderable workspace_bundle.json
  carrying flaggedPairs.
- Product mode with a corrupt state halts gracefully at the last good pair without crashing,
  leaving the chat renderable up to that pair with flaggedPairs recorded.
- PipelineRunner integration projects status 'needs_review' and preserves renderability.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from engine.checks import (
    CheckResult,
    InvariantViolationError,
    is_state_valid,
)
from engine.config import Config
from engine.llm_cache import CachingLLMClient
from engine.pipeline import run_chat
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


def get_dummy_config() -> Config:
    return Config(
        llm_api_key="fake-test-key",
        llm_base_url="https://fake.url/v1",
        model_fast="gemini-3.1-flash-lite",
        model_main="gemini-3.5-flash",
        model_step2="gemini-3.5-flash",
        model_step3="gemini-3.5-flash",
        step3_batch_size=3,
    )


@pytest.mark.tier1
def test_is_state_valid_helper() -> None:
    """Sound state passes; empty outcomes or cyclic outcome trees fail."""
    # 1. Valid state from fixture
    with open(REPO_ROOT / "data/chats/fixture_pair1/state.json", "r", encoding="utf-8") as f:
        valid_state = json.load(f)
    assert is_state_valid(valid_state) is True

    # 2. Corrupt state: empty outcomes
    assert is_state_valid({"outcomes": []}) is False

    # 3. Corrupt state: cyclic outcome tree
    cyclic_state = {
        "outcomes": [
            {"id": "outcome 1", "parent": "outcome 2", "text": "Cycle 1", "children": ["outcome 2"]},
            {"id": "outcome 2", "parent": "outcome 1", "text": "Cycle 2", "children": ["outcome 1"]},
        ],
        "requirements": [],
        "slots": [],
        "actions": [],
    }
    assert is_state_valid(cyclic_state) is False

    # 4. Corrupt state: non-dict
    assert is_state_valid(None) is False
    assert is_state_valid([]) is False


@pytest.mark.tier1
def test_run_chat_stop_on_violation_true_raises(tmp_path: Path) -> None:
    """When stop_on_violation=True (strict mode), an invariant failure raises InvariantViolationError."""
    chat_id = "c10_research_short"
    dialogue_path = REPO_ROOT / f"data/corpus/{chat_id}/dialogue.json"
    out_dir = tmp_path / chat_id

    client = CachingLLMClient(
        inner_client=None,
        mode="replay",
        cassettes_dir=REPO_ROOT / "tests/cassettes",
    )
    config = get_dummy_config()

    # Injected violation in run_pair_checks
    with patch("engine.checks.run_pair_checks") as mock_checks:
        mock_checks.return_value = CheckResult(
            healthy=False,
            passed=["inv_01"],
            failed=["inv_05"],
            violations=["inv_05: duplicate ledger row at index 2"],
        )

        with pytest.raises(InvariantViolationError) as exc_info:
            run_chat(
                client=client,
                config=config,
                chat_id=chat_id,
                dialogue=dialogue_path,
                out_dir=out_dir,
                clear_existing=True,
                stop_on_violation=True,
            )

        assert "inv_05" in str(exc_info.value)


@pytest.mark.tier1
def test_run_chat_product_mode_keeps_going_with_valid_state(tmp_path: Path) -> None:
    """When stop_on_violation=False and state is valid, violation is recorded, pair is flagged,

    and bundle carries flaggedPairs with status 'needs_review' without crashing (S-D9).
    """
    chat_id = "c10_research_short"
    dialogue_path = REPO_ROOT / f"data/corpus/{chat_id}/dialogue.json"
    out_dir = tmp_path / chat_id

    client = CachingLLMClient(
        inner_client=None,
        mode="replay",
        cassettes_dir=REPO_ROOT / "tests/cassettes",
    )
    config = get_dummy_config()

    # Injected violation (e.g. inv_21 quote provenance check fails)
    with patch("engine.checks.run_pair_checks") as mock_checks:
        mock_checks.return_value = CheckResult(
            healthy=False,
            passed=["inv_01", "inv_06"],
            failed=["inv_21"],
            violations=["inv_21: quote not found in dialogue"],
        )

        report = run_chat(
            client=client,
            config=config,
            chat_id=chat_id,
            dialogue=dialogue_path,
            out_dir=out_dir,
            clear_existing=True,
            stop_on_violation=False,
        )

    # 1. Report captures violation
    assert report is not None
    assert report["status"] == "needs_review"
    assert len(report.get("flagged_pairs", [])) == 1
    assert report["flagged_pairs"][0]["invariant"] == "inv_21"

    # 2. workspace_bundle.json exists and is fully valid and renderable
    bundle_file = out_dir / "workspace_bundle.json"
    assert bundle_file.is_file()
    bundle = json.loads(bundle_file.read_text(encoding="utf-8"))

    assert bundle["status"] == "needs_review"
    assert "flaggedPairs" in bundle
    assert len(bundle["flaggedPairs"]) == 1
    assert bundle["flaggedPairs"][0]["pair"] == 1
    assert bundle["flaggedPairs"][0]["invariant"] == "inv_21"

    # 3. Chat content is still fully rendered
    assert len(bundle["dialogue"]) == 2
    assert len(bundle["nodes"]) > 0
    assert len(bundle["atoms"]) > 0


@pytest.mark.tier1
def test_run_chat_product_mode_halts_at_last_good_pair_if_state_corrupt(tmp_path: Path) -> None:
    """When an invariant violation corrupts the state structure, product mode gracefully

    halts at the last good pair, keeping the bundle renderable up to that pair (S-D9).
    """
    chat_id = "c10_research_short"
    dialogue_path = REPO_ROOT / f"data/corpus/{chat_id}/dialogue.json"
    out_dir = tmp_path / chat_id

    client = CachingLLMClient(
        inner_client=None,
        mode="replay",
        cassettes_dir=REPO_ROOT / "tests/cassettes",
    )
    config = get_dummy_config()

    # Injected violation with corrupted state (is_state_valid returns False)
    with patch("engine.checks.run_pair_checks") as mock_checks, patch(
        "engine.checks.is_state_valid", return_value=False
    ):
        mock_checks.return_value = CheckResult(
            healthy=False,
            passed=[],
            failed=["inv_06"],
            violations=["inv_06: cycle detected in outcome hierarchy"],
        )

        report = run_chat(
            client=client,
            config=config,
            chat_id=chat_id,
            dialogue=dialogue_path,
            out_dir=out_dir,
            clear_existing=True,
            stop_on_violation=False,
        )

    assert report["status"] == "needs_review"
    assert len(report.get("flagged_pairs", [])) == 1
    assert report["flagged_pairs"][0]["invariant"] == "inv_06"

    bundle_file = out_dir / "workspace_bundle.json"
    assert bundle_file.is_file()
    bundle = json.loads(bundle_file.read_text(encoding="utf-8"))
    assert bundle["status"] == "needs_review"
    assert len(bundle.get("flaggedPairs", [])) == 1


@pytest.mark.tier1
@pytest.mark.anyio
async def test_pipeline_runner_flags_pair_and_produces_needs_review_bundle(library: Library) -> None:
    """PipelineRunner in product mode writes status 'needs_review' with flaggedPairs

    and broadcasts 'pair_flagged' without terminating the queue worker.
    """
    broadcaster = MockBroadcaster()
    client = CachingLLMClient(
        inner_client=None,
        mode="replay",
        cassettes_dir=REPO_ROOT / "tests/cassettes",
    )
    runner = PipelineRunner(library=library, broadcaster=broadcaster, custom_client=client)

    cdir = library.chat_dir("c10_research_short")
    cdir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO_ROOT / "data/corpus/c10_research_short/dialogue.json", cdir / "dialogue.json")

    job = {"id": "job_flagged", "chatId": "c10_research_short", "totalPairs": 1}

    # Injected violation during run_pair_checks
    with patch("server.pipeline_runner.run_pair_checks") as mock_checks:
        mock_checks.return_value = CheckResult(
            healthy=False,
            passed=["inv_01", "inv_06"],
            failed=["inv_10"],
            violations=["inv_10: negative score in delta calculation"],
        )

        await runner.handle_pair(job, 1)

    # 1. pair_flagged was broadcast
    flagged_events = [data for evt, data in broadcaster.events if evt == "pair_flagged"]
    assert len(flagged_events) == 1
    assert flagged_events[0]["chatId"] == "c10_research_short"
    assert flagged_events[0]["pair"] == 1
    assert "inv_10" in flagged_events[0]["reason"]

    # 2. workspace_bundle.json on disk has status 'needs_review' and flaggedPairs
    bundle = library.get_chat_bundle("c10_research_short")
    assert bundle["status"] == "needs_review"
    assert len(bundle.get("flaggedPairs", [])) == 1
    assert bundle["flaggedPairs"][0]["invariant"] == "inv_10"

    # 3. Chat summary in library list reflects flaggedPairs
    chats = library.list_chats()
    c = next((item for item in chats if item["id"] == "c10_research_short"), None)
    assert c is not None
    assert c["status"] == "needs_review"
    assert len(c.get("flaggedPairs", [])) == 1
