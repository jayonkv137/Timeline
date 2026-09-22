"""Tier 0 replay tests against recorded cassettes.

Proves:
- Offline extraction execution using cached cassettes without network.
- Runtime invariants 1-9 and 21 pass on real corpus data.
- Idempotent re-execution produces 0 duplicate rows (inv_05, inv_17).
"""
import json
from pathlib import Path

import pytest

from engine.config import load_config
from engine.llm_cache import CachingLLMClient
from engine.pipeline import run_chat
from scripts.run_corpus import evaluate_chat_invariants

pytestmark = pytest.mark.tier0

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_tier0_replay_corpus_chat(tmp_path):
    """Run c10_research_short in offline replay mode and verify invariants."""
    chat_id = "c10_research_short"
    dialogue_path = REPO_ROOT / f"data/corpus/{chat_id}/dialogue.json"
    assert dialogue_path.exists(), f"Missing {dialogue_path}"

    config = load_config()

    # Client in replay mode (no inner client, cannot hit network)
    client = CachingLLMClient(inner_client=None, mode="replay")
    out_dir = tmp_path / chat_id

    # 1. First run
    report = run_chat(
        client=client,
        config=config,
        chat_id=chat_id,
        dialogue=dialogue_path,
        out_dir=out_dir,
        clear_existing=True,
    )

    assert report["pairs_processed"] == 1
    assert report["requirements_created"] > 0
    assert (out_dir / "state.json").exists()
    assert (out_dir / "ledger.jsonl").exists()
    assert (out_dir / "run/report.json").exists()

    # Verify invariants on output
    inv_results = evaluate_chat_invariants(out_dir)
    for inv_id, status in inv_results.items():
        assert status == "PASS", f"{inv_id} failed: {inv_results.get('violations')}"

    # 2. Re-run without clearing — verify idempotency and no duplicate ledger rows
    with open(out_dir / "ledger.jsonl") as f:
        first_run_rows = [json.loads(line) for line in f if line.strip()]

    report_rerun = run_chat(
        client=client,
        config=config,
        chat_id=chat_id,
        dialogue=dialogue_path,
        out_dir=out_dir,
        clear_existing=False,
    )

    with open(out_dir / "ledger.jsonl") as f:
        rerun_rows = [json.loads(line) for line in f if line.strip()]

    # Row count should be identical (no duplicate rows added)
    assert len(rerun_rows) == len(first_run_rows)

    inv_rerun = evaluate_chat_invariants(out_dir)
    assert inv_rerun.get("inv_05") == "PASS"
