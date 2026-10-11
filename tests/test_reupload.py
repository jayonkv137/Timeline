"""Tests for Step S4.6: Re-upload deduplication and incremental extension.

Done when:
- Identical re-upload (same conversation ID + same content) -> skipped, 0 cost.
- Incremental extension (new messages appended) -> only new pairs processed starting
  from existing state.
- A test with a chat extended by 2 pairs costs exactly 2 pairs.
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from engine.config import Config
from engine.importer import (
    parse_claude_export,
    promote_conversation,
    scan_import,
)
from engine.models import get_model_price, load_price_table
from engine.state import State
from server.jobs import JobQueueManager
from server.library import Library, atomic_write_json
from server.pipeline_runner import PipelineRunner


REPO_ROOT = Path(__file__).resolve().parent.parent


class CountingLLMClient:
    """Mock LLM client that tracks exactly which pairs and steps were called."""

    def __init__(self, out_dir: Path | None = None) -> None:
        self.out_dir = out_dir
        self.calls: list[tuple[str, str]] = []  # (step_tag, model)
        self.pairs_processed: set[int] = set()

    def set_out_dir(self, out_dir: Path) -> None:
        self.out_dir = out_dir

    def call_json(self, step_tag: str, model: str, prompt: str, schema: Any = None) -> dict[str, Any]:
        self.calls.append((step_tag, model))
        # Extract pair number from step_tag (e.g. "1a:pair3" -> 3)
        if ":pair" in step_tag:
            p_str = step_tag.split(":pair")[1].split(":")[0]
            try:
                self.pairs_processed.add(int(p_str))
            except ValueError:
                pass

        if "1a" in step_tag:
            return {"user_mode": "EXPLORE", "intent": "Coding test extension", "has_code": True}
        elif "1b" in step_tag:
            return {
                "outcomes": [
                    {
                        "outcome_id": "outcome_test",
                        "title": "Extended Outcome",
                        "direction": "expand",
                        "action": "created",
                        "evidence": "Extended message test",
                    }
                ],
                "outcome_tree": [{"outcome_id": "outcome_test", "parent": None, "role": "root"}],
                "active_outcome": "outcome_test",
            }
        elif "1c" in step_tag:
            return {
                "requirements": [
                    {
                        "req_id": "req_test",
                        "text": "Extended requirement",
                        "outcome_id": "outcome_test",
                        "status": "active",
                        "action": "created",
                        "evidence": "Extended requirement test",
                    }
                ],
                "slots": [],
            }
        elif "2:" in step_tag or step_tag.startswith("2"):
            return {
                "scores": [
                    {
                        "action_id": "A(1,1)",
                        "outcome_id": "outcome_test",
                        "req_id": "req_test",
                        "score": 10.0,
                    }
                ]
            }
        elif "3a" in step_tag or "3b" in step_tag:
            return {"category": "test", "tags": ["unit-test"]}
        return {}


def create_sample_raw_conv(uuid_str: str, title: str, num_pairs: int) -> dict[str, Any]:
    """Create raw Claude export fixture with given number of pairs."""
    messages = []
    base_ts = 1704067200  # 2024-01-01 00:00:00
    for p in range(1, num_pairs + 1):
        u_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(base_ts + (p * 60)))
        a_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(base_ts + (p * 60) + 30))
        messages.append({"sender": "human", "text": f"User prompt for pair {p}", "created_at": u_ts})
        messages.append({"sender": "assistant", "text": f"Assistant response for pair {p}", "created_at": a_ts})

    return {
        "uuid": uuid_str,
        "name": title,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T01:00:00Z",
        "chat_messages": messages,
    }


@pytest.fixture
def library(tmp_path: Path) -> Library:
    lib = Library(tmp_path)
    lib.ensure_layout()
    return lib


@pytest.mark.tier1
def test_gemini_36_flash_in_price_table() -> None:
    """Verify gemini-3.6-flash pricing is registered and accessible."""
    table = load_price_table()
    assert "gemini-3.6-flash" in table
    in_price, out_price = get_model_price("gemini-3.6-flash")
    assert in_price == 0.750
    assert out_price == 3.750


@pytest.mark.tier1
def test_identical_reupload_detection_and_skip(library: Library, tmp_path: Path) -> None:
    """Same conversation ID + same content -> marked duplicate, 0 cost, skipped from queue."""
    conv_id = "test-conv-101"
    chat_id = f"claude_{conv_id}"

    # 1. Promote 2-pair chat into library and simulate completed state
    cdir = library.chat_dir(chat_id)
    raw_conv_2p = create_sample_raw_conv(conv_id, "Identical Chat Test", num_pairs=2)
    promote_conversation(raw_conv_2p, dest_dir=cdir, chat_id=chat_id)

    # Simulate completed run (state.json with 2 pairs completed)
    state = State()
    state.run["last_completed_pair"] = 2
    atomic_write_json(cdir / "state.json", state.to_dict())

    # 2. Re-upload identical 2-pair export in an import batch
    imp_dir = library.import_dir("imp_identical")
    raw_dir = imp_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    with open(raw_dir / "conversations.json", "w", encoding="utf-8") as f:
        json.dump([raw_conv_2p], f)

    report = scan_import(raw_dir, "imp_identical", library_root=library.root)

    # 3. Assert detection results
    assert report["duplicates"] == 1
    assert report["incremental"] == 0
    row = report["conversations"][0]
    assert row["isDuplicate"] is True
    assert row["isIncremental"] is False
    assert row["newPairs"] == 0
    assert row["estimate"]["cost"]["expected"] == 0.0

    # 4. Enqueueing batch skips identical conversation
    queue = JobQueueManager(library=library)
    loop = asyncio.new_event_loop()
    try:
        enqueued = loop.run_until_complete(
            queue.enqueue_import_batch("imp_identical", [f"claude_{conv_id}"])
        )
    finally:
        loop.close()

    assert len(enqueued) == 0  # Skipped! Zero jobs created.


@pytest.mark.tier1
def test_incremental_extension_detection_and_estimate(library: Library) -> None:
    """New messages appended -> detected as incremental extension, estimated for new pairs only."""
    conv_id = "test-conv-102"
    chat_id = f"claude_{conv_id}"

    # 1. Existing chat in library has 2 pairs completed
    cdir = library.chat_dir(chat_id)
    raw_conv_2p = create_sample_raw_conv(conv_id, "Extension Chat Test", num_pairs=2)
    promote_conversation(raw_conv_2p, dest_dir=cdir, chat_id=chat_id)
    state = State()
    state.run["last_completed_pair"] = 2
    atomic_write_json(cdir / "state.json", state.to_dict())

    # 2. Upload extended export with 4 pairs (2 existing + 2 new)
    raw_conv_4p = create_sample_raw_conv(conv_id, "Extension Chat Test", num_pairs=4)
    imp_dir = library.import_dir("imp_extension")
    raw_dir = imp_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    with open(raw_dir / "conversations.json", "w", encoding="utf-8") as f:
        json.dump([raw_conv_4p], f)

    report = scan_import(raw_dir, "imp_extension", library_root=library.root)

    # 3. Assert extension metadata
    assert report["duplicates"] == 0
    assert report["incremental"] == 1
    row = report["conversations"][0]
    assert row["isDuplicate"] is False
    assert row["isIncremental"] is True
    assert row["existingPairs"] == 2
    assert row["newPairs"] == 2
    assert row["estimate"]["cost"]["expected"] > 0.0


def make_test_state() -> State:
    """Construct a minimal valid State adhering to state.schema.json."""
    state = State()
    state.add_action({
        "id": "U(1,1)",
        "type": "Request",
        "text": "User asks for a thing.",
        "role": "SHAPER",
        "evidence_quote": "User prompt for pair 1",
    })
    state.add_action({
        "id": "A(1,1)",
        "type": "Draft",
        "text": "AI drafts the thing.",
        "role": "EXECUTOR",
        "evidence_quote": "Assistant response for pair 1",
    })
    state.outcomes.append({
        "id": "outcome 1",
        "text": "the thing",
        "turn_id": "U(1,1)",
        "parent": None,
        "children": [],
        "related": [],
    })
    state.intentions.append({
        "intention_id": "I1",
        "intention": "get the thing done",
        "outcome_ids": ["outcome 1"],
    })
    state.requirements.append({
        "outcome_id": "outcome 1",
        "req_id": "req 1",
        "text": "the thing must exist",
        "type": "constraint",
        "status": "active",
        "creation_action_ids": ["U(1,1)"],
        "contributing_action_ids": [],
        "implementation_action_ids": ["A(1,1)"],
        "revise_action_ids": [],
        "related_to": [],
        "explicit_or_implicit": "explicit",
        "rationale": "stated directly",
        "created_at_pair": 1,
    })
    state.slots.append({
        "slot_id": "slot 1",
        "outcome_id": "outcome 1",
        "text": "maybe a second thing",
        "type": "preference",
        "origin": "AI",
        "status": "open",
        "creation_action_ids": ["A(1,1)"],
        "contributing_action_ids": [],
        "resolved_into": None,
    })
    state.log_operation(1, "outcome 1", "create", "req 1", "requirement")
    state.run["action_to_outcome"] = {"U(1,1)": "outcome 1", "A(1,1)": "outcome 1"}
    state.run["dialogue_summary"] = "User and AI make a thing."
    state.run["last_completed_pair"] = 2
    return state


@pytest.mark.tier1
def test_incremental_promotion_preserves_existing_artifacts(library: Library) -> None:
    """Incremental promotion updates dialogue.json but preserves existing state.json and ledger."""
    conv_id = "test-conv-103"
    chat_id = f"claude_{conv_id}"

    # 1. Create existing chat with initial state and ledger
    cdir = library.chat_dir(chat_id)
    raw_conv_2p = create_sample_raw_conv(conv_id, "Preserve Artifacts Test", num_pairs=2)
    promote_conversation(raw_conv_2p, dest_dir=cdir, chat_id=chat_id)

    # Seed state and ledger with pair 1-2 work conforming to schemas
    state = make_test_state()
    state.save(cdir)

    ledger_file = cdir / "ledger.jsonl"
    ledger_row = {
        "pair_added": 1,
        "action_id": "U(1,1)",
        "speaker": "U",
        "role": "SHAPER",
        "outcome_id": "outcome 1",
        "req_id": "req 1",
        "score": 5.0,
        "kind": "creation",
    }
    ledger_file.write_text(json.dumps(ledger_row) + "\n", encoding="utf-8")

    # 2. Promote extended 4-pair conversation
    raw_conv_4p = create_sample_raw_conv(conv_id, "Preserve Artifacts Test", num_pairs=4)
    promote_conversation(raw_conv_4p, dest_dir=cdir, chat_id=chat_id)

    # 3. Verify dialogue updated to 4 pairs while state and ledger are intact
    dialogue = json.loads((cdir / "dialogue.json").read_text(encoding="utf-8"))
    assert len(dialogue) == 8  # 4 pairs * 2 turns
    assert max(t["pair"] for t in dialogue) == 4

    loaded_state = State.load(cdir)
    assert loaded_state.run["last_completed_pair"] == 2
    assert loaded_state.outcomes[0]["id"] == "outcome 1"

    loaded_ledger = (cdir / "ledger.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(loaded_ledger) == 1


@pytest.mark.tier1
@pytest.mark.anyio
async def test_chat_extended_by_2_pairs_costs_2_pairs(library: Library) -> None:
    """Primary done-when requirement:

    A test with a chat extended by 2 pairs costs exactly 2 pairs.
    Pairs 1 and 2 are skipped; only pairs 3 and 4 are processed starting from existing state.
    """
    conv_id = "test-conv-104"
    chat_id = f"claude_{conv_id}"

    # 1. Existing chat in library has 2 completed pairs
    cdir = library.chat_dir(chat_id)
    raw_conv_2p = create_sample_raw_conv(conv_id, "Cost Test", num_pairs=2)
    promote_conversation(raw_conv_2p, dest_dir=cdir, chat_id=chat_id)

    initial_state = make_test_state()
    atomic_write_json(cdir / "state.json", initial_state.to_dict())

    # Write initial pair 1-2 ledger rows conforming to schema
    ledger_file = cdir / "ledger.jsonl"
    with open(ledger_file, "w", encoding="utf-8") as lf:
        for p in (1, 2):
            row = {
                "pair_added": p,
                "action_id": "U(1,1)",
                "speaker": "U",
                "role": "SHAPER",
                "outcome_id": "outcome 1",
                "req_id": "req 1",
                "score": 5.0,
                "kind": "creation",
            }
            lf.write(json.dumps(row) + "\n")

    # 2. Upload extended export with 4 pairs
    raw_conv_4p = create_sample_raw_conv(conv_id, "Cost Test", num_pairs=4)
    imp_dir = library.import_dir("imp_cost_test")
    raw_dir = imp_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    with open(raw_dir / "conversations.json", "w", encoding="utf-8") as f:
        json.dump([raw_conv_4p], f)

    scan_import(raw_dir, "imp_cost_test", library_root=library.root)

    # 3. Setup PipelineRunner and mock process_pair to measure pair executions
    executed_pairs: list[int] = []

    def mock_process_pair(client, config, state, pair_number, user_text, ai_text, ledger_writer):
        executed_pairs.append(pair_number)
        u_act = f"U({pair_number},1)"
        a_act = f"A({pair_number},1)"
        state.add_action({
            "id": u_act,
            "type": "Request",
            "text": f"User asks for thing {pair_number}.",
            "role": "SHAPER",
            "evidence_quote": user_text or f"User prompt for pair {pair_number}",
        })
        state.add_action({
            "id": a_act,
            "type": "Draft",
            "text": f"AI drafts thing {pair_number}.",
            "role": "EXECUTOR",
            "evidence_quote": ai_text or f"Assistant response for pair {pair_number}",
        })
        new_out = f"outcome {pair_number}"
        state.outcomes.append({
            "id": new_out,
            "text": f"the thing {pair_number}",
            "turn_id": u_act,
            "parent": "outcome 1",
            "children": [],
            "related": [],
        })
        state.outcomes[0]["children"].append(new_out)
        req_id = f"req {pair_number}"
        state.requirements.append({
            "outcome_id": new_out,
            "req_id": req_id,
            "text": f"the thing {pair_number} must exist",
            "type": "constraint",
            "status": "active",
            "creation_action_ids": [u_act],
            "contributing_action_ids": [],
            "implementation_action_ids": [a_act],
            "revise_action_ids": [],
            "related_to": [],
            "explicit_or_implicit": "explicit",
            "rationale": "stated directly",
            "created_at_pair": pair_number,
        })
        state.log_operation(pair_number, new_out, "create", req_id, "requirement")
        ledger_writer.append({
            "pair_added": pair_number,
            "action_id": u_act,
            "speaker": "U",
            "role": "SHAPER",
            "outcome_id": new_out,
            "req_id": req_id,
            "score": 5.0,
            "kind": "creation",
        })
        return [], {}

    counting_client = CountingLLMClient(out_dir=cdir)
    runner = PipelineRunner(library=library, custom_client=counting_client)
    queue = JobQueueManager(library=library, pipeline_runner=runner)

    # 4. Enqueue import batch and run with patched process_pair
    with patch("server.pipeline_runner.process_pair", side_effect=mock_process_pair):
        enqueued = await queue.enqueue_import_batch("imp_cost_test", [f"claude_{conv_id}"])
        assert len(enqueued) == 1
        job = enqueued[0]
        assert job["completedPairs"] == 2
        assert job["totalPairs"] == 4

        # Wait for background queue worker to process the job
        timeout = time.time() + 5.0
        while time.time() < timeout:
            jobs = queue.get_jobs()
            target = next((j for j in jobs if j["chatId"] == chat_id), None)
            if target and target.get("status") == "completed":
                break
            await asyncio.sleep(0.05)

    # 5. Verify execution proof:
    # - Exactly pairs 3 and 4 were processed
    # - Pairs 1 and 2 were NEVER executed
    assert executed_pairs == [3, 4]
    assert len(executed_pairs) == 2  # Exactly 2 pairs cost!

    # Verify final state reflects 4 completed pairs
    final_state = State.load(cdir)
    assert final_state.run["last_completed_pair"] == 4
    # Root outcome from pair 1-2 was preserved
    assert any(o["id"] == "outcome 1" for o in final_state.outcomes)

    # Verify workspace bundle reflects ready status with 4 processed pairs
    bundle = json.loads((cdir / "workspace_bundle.json").read_text(encoding="utf-8"))
    assert bundle["status"] == "ready"
    assert bundle["totalPairs"] == 4
