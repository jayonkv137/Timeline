"""Tier 1 tests for the caching LLM client (E0_BRIEF.md S6).

Proves record and replay modes work without network access,
verifies cache key determinism, and checks hard errors on cache misses.
"""
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from engine.llm_cache import CachingLLMClient, LLMCacheMissError, compute_cache_key

pytestmark = pytest.mark.tier1


def test_cache_key_deterministic():
    """Cache key is a deterministic SHA-256 hash of model and exact prompt."""
    k1 = compute_cache_key("gemini-flash", "Extract requirements from turn 1")
    k2 = compute_cache_key("gemini-flash", "Extract requirements from turn 1")
    k3 = compute_cache_key("gemini-flash", "Extract requirements from turn 2")
    k4 = compute_cache_key("claude-sonnet", "Extract requirements from turn 1")

    assert k1 == k2
    assert k1 != k3
    assert k1 != k4
    assert len(k1) == 64


def test_record_and_replay_cycle(tmp_path):
    """Proves record mode saves to disk and replay mode serves without network."""
    cassettes_dir = tmp_path / "cassettes"
    mock_inner = MagicMock()
    mock_inner.call_json.return_value = {"requirements": ["req 1", "req 2"], "status": "ok"}

    # 1. Record mode
    recorder = CachingLLMClient(
        inner_client=mock_inner,
        mode="record",
        cassettes_dir=cassettes_dir,
    )
    res_rec = recorder.call_json("1a", "test-model", "test prompt text")
    assert res_rec == {"requirements": ["req 1", "req 2"], "status": "ok"}
    assert mock_inner.call_json.call_count == 1

    # Verify cassette file was written
    key = compute_cache_key("test-model", "test prompt text")
    cassette_file = cassettes_dir / f"{key}.json"
    assert cassette_file.exists()
    with open(cassette_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["step"] == "1a"
    assert data["model"] == "test-model"
    assert data["response"] == {"requirements": ["req 1", "req 2"], "status": "ok"}

    # 2. Replay mode — inner client is NONE (network completely unavailable)
    replayer = CachingLLMClient(
        inner_client=None,
        mode="replay",
        cassettes_dir=cassettes_dir,
    )
    res_rep = replayer.call_json("1a", "test-model", "test prompt text")
    # Response is identical
    assert res_rep == res_rec


def test_replay_cache_miss_raises_hard_error(tmp_path):
    """Replay mode raises LLMCacheMissError when cassette does not exist."""
    replayer = CachingLLMClient(
        inner_client=None,
        mode="replay",
        cassettes_dir=tmp_path / "empty_cassettes",
    )
    with pytest.raises(LLMCacheMissError) as exc_info:
        replayer.call_json("1a", "test-model", "unseen prompt")
    assert "cassette miss in replay mode" in str(exc_info.value)


def test_mode_off_passthrough():
    """Mode 'off' passes through directly to inner client."""
    mock_inner = MagicMock()
    mock_inner.call_json.return_value = {"mode": "passthrough"}

    client = CachingLLMClient(inner_client=mock_inner, mode="off")
    res = client.call_json("2", "fast-model", "prompt")
    assert res == {"mode": "passthrough"}
    assert mock_inner.call_json.call_count == 1


def test_invalid_mode_raises_value_error():
    """Invalid mode string raises ValueError immediately."""
    with pytest.raises(ValueError):
        CachingLLMClient(mode="invalid_mode")
