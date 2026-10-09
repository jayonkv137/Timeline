"""Tests for UsageMeter and models pricing table (STANDALONE_V1_PLAN §4 Step S3.1)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from engine.config import Config
from engine.llm import LLMClient, UsageMeter
from engine.llm_cache import CachingLLMClient
from engine.models import compute_token_cost, get_model_price, load_price_table


@pytest.mark.tier1
def test_models_yaml_loads_standard_models() -> None:
    table = load_price_table()
    assert "gemini-3.5-flash" in table
    assert "gemini-3.1-flash-lite" in table
    assert "claude-3-5-sonnet" in table
    assert "gpt-4o-mini" in table

    # Verify rates (Gemini 3.5 Flash: $0.075 / $0.30 per 1M)
    in_rate, out_rate = get_model_price("gemini-3.5-flash")
    assert in_rate == 0.075
    assert out_rate == 0.300


@pytest.mark.tier1
def test_compute_token_cost_live_and_replay() -> None:
    # 1,000,000 prompt tokens and 1,000,000 completion tokens on gemini-3.5-flash
    cost_live = compute_token_cost("gemini-3.5-flash", 1_000_000, 1_000_000, is_replay=False)
    assert cost_live["prompt"] == 0.075
    assert cost_live["completion"] == 0.300
    assert cost_live["total"] == 0.375

    # Replay mode must strictly be $0.00
    cost_replay = compute_token_cost("gemini-3.5-flash", 1_000_000, 1_000_000, is_replay=True)
    assert cost_replay["prompt"] == 0.0
    assert cost_replay["completion"] == 0.0
    assert cost_replay["total"] == 0.0


@pytest.mark.tier1
def test_usage_meter_records_to_jsonl() -> None:
    with tempfile.TemporaryDirectory() as td:
        usage_file = Path(td) / "run" / "usage.jsonl"
        meter = UsageMeter(usage_file)

        # Call 1: live
        rec1 = meter.record(
            step="1a:pair1",
            model="gemini-3.1-flash-lite",
            prompt_tokens=2000,
            completion_tokens=500,
            is_replay=False,
            mode="live",
        )
        assert rec1["step"] == "1a"
        assert rec1["pair"] == 1
        assert rec1["model"] == "gemini-3.1-flash-lite"
        assert rec1["tokens"]["total"] == 2500
        assert rec1["cost"]["total"] > 0.0

        # Call 2: replay
        rec2 = meter.record(
            step="2:pair3:outcome 2",
            model="gemini-3.5-flash",
            prompt_tokens=4000,
            completion_tokens=1000,
            is_replay=True,
            mode="replay",
        )
        assert rec2["step"] == "2"
        assert rec2["pair"] == 3
        assert rec2["tokens"]["total"] == 5000
        assert rec2["cost"]["total"] == 0.0

        assert usage_file.is_file()
        lines = [json.loads(line) for line in usage_file.read_text().splitlines() if line.strip()]
        assert len(lines) == 2
        assert lines[0]["step"] == "1a"
        assert lines[1]["step"] == "2"
        assert lines[1]["cost"]["total"] == 0.0

        summary = meter.summary()
        assert summary["calls"] == 2
        assert summary["tokens"]["total"] == 7500
        assert summary["cost"] == rec1["cost"]["total"]


@pytest.mark.tier1
def test_llm_client_live_usage_meter_mock() -> None:
    with tempfile.TemporaryDirectory() as td:
        out_dir = Path(td)
        cfg = Config(
            llm_api_key="fake-test-key",
            llm_base_url="https://fake.url/v1",
            model_fast="gemini-3.1-flash-lite",
            model_main="gemini-3.5-flash",
            model_step2="gemini-3.5-flash",
            model_step3="gemini-3.5-flash",
            step3_batch_size=3,
        )
        client = LLMClient(config=cfg, out_dir=out_dir)

        # Mock OpenAI chat completion
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"status": "ok"}'))]
        mock_response.usage = MagicMock(prompt_tokens=1000, completion_tokens=200, total_tokens=1200)

        client._client.chat.completions.create = MagicMock(return_value=mock_response)

        result = client.call_json("1a:pair1", "gemini-3.5-flash", "test prompt")
        assert result == {"status": "ok"}

        usage_file = out_dir / "run" / "usage.jsonl"
        assert usage_file.is_file()
        rows = [json.loads(line) for line in usage_file.read_text().splitlines() if line.strip()]
        assert len(rows) == 1
        assert rows[0]["step"] == "1a"
        assert rows[0]["pair"] == 1
        assert rows[0]["tokens"]["prompt"] == 1000
        assert rows[0]["tokens"]["completion"] == 200
        assert rows[0]["cost"]["total"] > 0.0


@pytest.mark.tier0
def test_replay_chat_writes_usage_jsonl_with_zero_cost() -> None:
    from engine.pipeline import run_chat

    with tempfile.TemporaryDirectory() as td:
        out_dir = Path(td) / "c10_research_short"
        dialogue_path = Path("data/corpus/c10_research_short/dialogue.json")
        cfg = Config(
            llm_api_key="fake",
            llm_base_url="fake",
            model_fast="gemini-3.1-flash-lite",
            model_main="gemini-3.5-flash",
            model_step2="gemini-3.5-flash",
            model_step3="gemini-3.5-flash",
            step3_batch_size=3,
        )
        client = CachingLLMClient(mode="replay", out_dir=out_dir)

        report = run_chat(
            client=client,
            config=cfg,
            chat_id="c10_research_short",
            dialogue=dialogue_path,
            out_dir=out_dir,
            clear_existing=True,
        )

        usage_file = out_dir / "run" / "usage.jsonl"
        assert usage_file.is_file(), "run/usage.jsonl must exist after replay"
        rows = [json.loads(line) for line in usage_file.read_text().splitlines() if line.strip()]
        assert len(rows) > 0, "usage.jsonl must contain call rows"

        for row in rows:
            assert "step" in row
            assert "model" in row
            assert "tokens" in row
            assert "cost" in row
            assert row["tokens"]["total"] > 0
            assert row["cost"]["total"] == 0.0, "All replay costs must be 0.0"
            assert row["mode"] == "replay"
