import json
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import server.main
from tests.test_pipeline import (
    MockConfig,
    MockLLMClient,
    PAIR1_STEP1A_RESPONSE,
    PAIR1_STEP1B_RESPONSE,
    PAIR1_STEP1C_RESPONSE,
)

# Initialize FastAPI test client
client = TestClient(server.main.app)


@pytest.fixture(autouse=True)
def setup_test_chats_dir(tmp_path):
    """Overrides CHATS_DIR to use a temporary directory for each test run."""
    original_chats_dir = server.main.CHATS_DIR
    test_chats_dir = tmp_path / "chats"
    test_chats_dir.mkdir(parents=True, exist_ok=True)
    server.main.CHATS_DIR = test_chats_dir
    yield
    server.main.CHATS_DIR = original_chats_dir


def test_create_chat():
    response = client.post("/chats")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["title"] == "New Chat"

    chat_dir = server.main.CHATS_DIR / data["id"]
    assert chat_dir.exists()
    assert (chat_dir / "dialogue.json").exists()
    assert (chat_dir / "state.json").exists()
    assert (chat_dir / "snapshots.json").exists()
    assert (chat_dir / "panel_bundle.json").exists()
    assert (chat_dir / "ledger.jsonl").exists()


def test_list_chats():
    # Start with empty
    response = client.get("/chats")
    assert response.status_code == 200
    assert response.json() == []

    # Create one chat
    res_create = client.post("/chats")
    chat_id = res_create.json()["id"]

    response = client.get("/chats")
    assert response.status_code == 200
    chats = response.json()
    assert len(chats) == 1
    assert chats[0]["id"] == chat_id
    assert chats[0]["title"] == "New Chat"


def test_get_chat_bundle_not_found():
    response = client.get("/chats/non-existent-id/bundle")
    assert response.status_code == 404


def test_full_message_flow_and_rerun_and_title_patch():
    # 1. Create chat
    res_create = client.post("/chats")
    chat_id = res_create.json()["id"]
    chat_dir = server.main.CHATS_DIR / chat_id

    # 2. Mock AsyncOpenAI for streaming
    mock_create = AsyncMock()
    class MockChunk:
        def __init__(self, content):
            self.choices = [MagicMock()]
            self.choices[0].delta = MagicMock()
            self.choices[0].delta.content = content

    async def mock_generator():
        yield MockChunk("I will build ")
        yield MockChunk("a responsive website.")

    mock_create.return_value = mock_generator()
    mock_async_client = MagicMock()
    mock_async_client.chat.completions.create = mock_create
    server.main.async_client = mock_async_client

    # 3. Mock engine's LLMClient for the background pipeline run
    mock_pipeline_client = MockLLMClient({
        "1a:pair1": PAIR1_STEP1A_RESPONSE,
        "1b:pair1": PAIR1_STEP1B_RESPONSE,
        "1c:pair1": PAIR1_STEP1C_RESPONSE,
        "2:outcome 1:pair1": {"requirement ops": [], "open_slot ops": []}
    })

    # Register an in-memory queue to capture SSE events
    event_queue = asyncio.Queue()
    server.main.chat_event_listeners.setdefault(chat_id, set()).add(event_queue)

    # Capture enqueued background tasks
    created_tasks = []
    def mock_create_task(coro, *args, **kwargs):
        created_tasks.append(coro)
        return MagicMock()

    # Patch engine LLM client globally
    with patch("engine.runner.LLMClient", return_value=mock_pipeline_client):
        with patch("asyncio.create_task", mock_create_task):
            # Post user message
            response = client.post(
                f"/chats/{chat_id}/messages",
                json={"text": "Can you build me a website?"}
            )
            assert response.status_code == 200
            
            # Verify message streaming tokens are returned in the response body
            text_response = response.text
            assert "I will build " in text_response
            assert "a responsive website." in text_response
            assert "[DONE]" in text_response

        # Execute the captured background task synchronously
        assert len(created_tasks) == 1
        asyncio.run(created_tasks[0])

        status_path = chat_dir / "run" / "status.json"
        assert status_path.exists()
        with open(status_path) as f:
            status_data = json.load(f)
        assert status_data["status"] == "done"
        assert status_data["pair"] == 1

        # 5. Assert dialogue grew on disk
        dialogue_path = chat_dir / "dialogue.json"
        with open(dialogue_path) as f:
            dlg = json.load(f)
        assert len(dlg) == 2
        assert dlg[0]["speaker"] == "user"
        assert dlg[0]["text"] == "Can you build me a website?"
        assert dlg[1]["speaker"] == "ai"
        assert dlg[1]["text"] == "I will build a responsive website."

        # 6. Assert bundle updates
        bundle_path = chat_dir / "panel_bundle.json"
        with open(bundle_path) as f:
            bundle = json.load(f)
        assert len(bundle["pairs"]) == 1
        assert bundle["pairs"][0]["pair"] == 1

        # 7. Pull and verify event stream logs
        events = []
        while not event_queue.empty():
            events.append(event_queue.get_nowait())

        # Assert correct order of pipeline events
        assert len(events) >= 3
        # Should contain pipeline_status running, done, and pair_ready
        running_event = [e for e in events if "pipeline_status" in e and "running" in e]
        done_event = [e for e in events if "pipeline_status" in e and "done" in e]
        ready_event = [e for e in events if "pair_ready" in e]
        assert len(running_event) == 1
        assert len(done_event) == 1
        assert len(ready_event) == 1

        # 8. Test rerun endpoint works idempotently
        # Delete status.json to check it gets rewritten
        status_path.unlink()
        created_tasks.clear()
        
        with patch("asyncio.create_task", mock_create_task):
            response_rerun = client.post(f"/chats/{chat_id}/pairs/1/rerun")
            assert response_rerun.status_code == 200
            assert response_rerun.json() == {"status": "queued", "pair": 1}

        # Run the rerun task
        assert len(created_tasks) == 1
        asyncio.run(created_tasks[0])

        assert status_path.exists()
        with open(status_path) as f:
            status_data_rerun = json.load(f)
        assert status_data_rerun["status"] == "done"

        # 9. Test title patch
        response_patch = client.patch(
            f"/chats/{chat_id}/title",
            json={"title": "Custom Production Website"}
        )
        assert response_patch.status_code == 200
        assert response_patch.json()["title"] == "Custom Production Website"

        # Verify title was updated in state.json
        state_path = chat_dir / "state.json"
        with open(state_path) as f:
            state_data = json.load(f)
        assert state_data["outcomes"][0]["text"] == "Custom Production Website"

        # Verify list chats uses the custom title now
        response_list = client.get("/chats")
        assert response_list.json()[0]["title"] == "Custom Production Website"

        # Verify bundle retrieval endpoint
        response_bundle = client.get(f"/chats/{chat_id}/bundle")
        assert response_bundle.status_code == 200
        bundle_res_data = response_bundle.json()
        assert "dialogue" in bundle_res_data
        assert "panel_bundle" in bundle_res_data
        assert bundle_res_data["panel_bundle"]["pairs"][0]["goal"]["default_view"][0]["text"] == "Custom Production Website"
