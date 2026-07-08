"""P2.S6 tests: Live-rail runner + recovery loop.

Tests loader format flexibility, sequential pipeline execution,
caching wrapper hits/misses, --resume state recovery, and CLI integration.
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from engine.config import Config
from engine.runner import load_dialogue_from_export, run_pipeline
from engine.state import State
from engine.pipeline import PipelineError
from tests.test_pipeline import MockConfig, MockLLMClient, PAIR1_STEP1A_RESPONSE, PAIR1_STEP1B_RESPONSE, PAIR1_STEP1C_RESPONSE


# ------------------------------------------------------------- test data

GENERIC_EXPORT = [
    {"role": "user", "content": "Can you build me a website?"},
    {"role": "assistant", "content": "Sure, I'll build a responsive website."},
    {"role": "user", "content": "Add dark mode please."},
    {"role": "assistant", "content": "I've added a dark mode toggle."}
]

CONFORMANT_EXPORT = [
    {
        "pair": 1, "speaker": "user", "text": "Can you build me a website?",
        "attachments": [], "ts": "2026-07-08T00:00:00Z"
    },
    {
        "pair": 1, "speaker": "ai", "text": "Sure, I'll build a responsive website.",
        "attachments": [], "ts": "2026-07-08T00:01:00Z"
    }
]


# -------------------------------------------------------- loader tests

def test_load_dialogue_from_export_conformant(tmp_path):
    path = tmp_path / "conformant.json"
    with open(path, "w") as f:
        json.dump(CONFORMANT_EXPORT, f)
        
    dialogue = load_dialogue_from_export(path)
    assert len(dialogue) == 2
    assert dialogue[0]["pair"] == 1
    assert dialogue[0]["speaker"] == "user"


def test_load_dialogue_from_export_generic(tmp_path):
    path = tmp_path / "generic.json"
    with open(path, "w") as f:
        json.dump(GENERIC_EXPORT, f)
        
    dialogue = load_dialogue_from_export(path)
    assert len(dialogue) == 4
    assert dialogue[0]["pair"] == 1
    assert dialogue[0]["speaker"] == "user"
    assert dialogue[0]["text"] == "Can you build me a website?"
    assert dialogue[1]["pair"] == 1
    assert dialogue[1]["speaker"] == "ai"
    
    assert dialogue[2]["pair"] == 2
    assert dialogue[2]["speaker"] == "user"
    assert dialogue[3]["pair"] == 2
    assert dialogue[3]["speaker"] == "ai"


# ---------------------------------------------------- caching & runner tests

def test_run_pipeline_fresh_and_resume(tmp_path):
    # 1. Setup dialogue path
    export_path = tmp_path / "export.json"
    with open(export_path, "w") as f:
        json.dump(GENERIC_EXPORT, f)
        
    dialogue = load_dialogue_from_export(export_path)
    out_dir = tmp_path / "out"

    # Mocks for pair 1 LLM calls
    mock_client_pair1 = MockLLMClient({
        "1a:pair1": PAIR1_STEP1A_RESPONSE,
        "1b:pair1": PAIR1_STEP1B_RESPONSE,
        "1c:pair1": PAIR1_STEP1C_RESPONSE,
        "2:outcome 1:pair1": {"requirement ops": [], "open_slot ops": []}
    })
    
    # Run first pair
    config = MockConfig()
    
    with patch("engine.runner.LLMClient", return_value=mock_client_pair1):
        state = run_pipeline(
            config=config,
            dialogue=dialogue,
            out_dir=out_dir,
            limit_pairs=1,
            resume=False
        )

    assert state.run["last_completed_pair"] == 1
    assert (out_dir / "state.json").exists()
    assert (out_dir / "dialogue.json").exists()
    assert (out_dir / "ledger.jsonl").exists()
    assert (out_dir / "snapshots.json").exists()
    assert (out_dir / "panel_bundle.json").exists()

    # Cache directory should contain cached calls
    cache_dir = out_dir / "run" / "cache"
    assert len(list(cache_dir.glob("*.json"))) > 0

    # 2. Resume with pair 2
    # Define responses for pair 2
    PAIR2_STEP1A_RESPONSE = {
        "actions": [
            {"turn id": "U(2,1)", "action type": "Request", "action text": "Add dark mode", "role": "SHAPER", "evidence quote": "Add dark mode"},
            {"turn id": "A(2,1)", "action type": "Ack", "action text": "added dark mode", "role": "EXECUTOR", "evidence quote": "added"}
        ]
    }
    PAIR2_STEP1B_RESPONSE = {
        "dialogue summary": "summary",
        "outcomes": [{"outcome id": "outcome 1", "outcome": "Responsive website with dark mode", "turn id": "U(1,1)", "parent outcome id": None, "child outcome ids": [], "related outcome ids": []}],
        "action to outcome": {"U(1,1)": "outcome 1", "U(1,2)": "outcome 1", "A(1,1)": "outcome 1", "U(2,1)": "outcome 1", "A(2,1)": "outcome 1"}

    }
    PAIR2_STEP1C_RESPONSE = {
        "intentions": [{"intention id": "I1", "intention": "build site"}],
        "outcome to intention": [{"outcome id": "outcome 1", "intention id": "I1"}]
    }

    mock_client_pair2 = MockLLMClient({
        # Since we use CachedLLMClient, pair 1 calls will hit the cache and NOT call mock_client_pair2.
        # So we only need to mock pair 2 calls.
        "1a:pair2": PAIR2_STEP1A_RESPONSE,
        "1b:pair2": PAIR2_STEP1B_RESPONSE,
        "1c:pair2": PAIR2_STEP1C_RESPONSE,
        "2:outcome 1:pair2": {"requirement ops": [], "open_slot ops": []}
    })

    with patch("engine.runner.LLMClient", return_value=mock_client_pair2):
        state_resumed = run_pipeline(
            config=config,
            dialogue=dialogue,
            out_dir=out_dir,
            limit_pairs=2,
            resume=True
        )

    assert state_resumed.run["last_completed_pair"] == 2
    # Verify that the resumed execution loaded state from state.json
    assert len(state_resumed.actions) == 5 # 3 from pair 1 + 2 from pair 2
    
    # Assert mock client 2 was never called for pair 1 steps (caching verification)
    assert not any(c[0].startswith("1a:pair1") for c in mock_client_pair2.calls)
    assert any(c[0].startswith("1a:pair2") for c in mock_client_pair2.calls)


# ------------------------------------------------------------ CLI parsing tests

def test_cli_parsing():
    from engine.__main__ import main
    
    # Mock sys.argv to run CLI parser
    test_args = ["engine", "run", "--input", "in.json", "--out", "out_dir", "--pairs", "5", "--resume"]
    
    with patch.object(sys, "argv", test_args):
        with patch("engine.__main__.load_config") as mock_load_config, \
             patch("engine.__main__.load_dialogue_from_export") as mock_load_dialogue, \
             patch("engine.__main__.run_pipeline") as mock_run_pipeline:
                 
            mock_load_dialogue.return_value = CONFORMANT_EXPORT
            main()
            
            mock_load_config.assert_called_once()
            mock_load_dialogue.assert_called_once_with("in.json")
            mock_run_pipeline.assert_called_once_with(
                config=mock_load_config.return_value,
                dialogue=CONFORMANT_EXPORT,
                out_dir="out_dir",
                limit_pairs=5,
                resume=True
            )
