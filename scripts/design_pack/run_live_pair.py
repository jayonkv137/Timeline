"""Run live extraction on c15_creative_medium Pair 1 and log all intermediate steps."""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from engine.config import load_config
from engine.llm import LLMClient, LLMError
from engine.llm_cache import compute_cache_key
from engine.state import State
from engine.artifacts import LedgerWriter, read_ledger
from engine.pipeline import step_1a, step_1b, step_1c, run_level2


class SmartCachingClient:
    def __init__(self, inner, cassettes_dir):
        self.inner = inner
        self.cassettes_dir = Path(cassettes_dir)
        self.cassettes_dir.mkdir(parents=True, exist_ok=True)

    def call_json(self, step: str, model: str, prompt: str):
        key = compute_cache_key(model, prompt)
        cassette_path = self.cassettes_dir / f"{key}.json"
        if cassette_path.exists():
            print(f"  [CACHE HIT] {step} -> {key[:8]}")
            with open(cassette_path, "r", encoding="utf-8") as f:
                return json.load(f)["response"]

        print(f"  [API CALL] {step} (model: {model})...")
        # Retry loop for rate limits
        for attempt in range(5):
            try:
                resp = self.inner.call_json(step, model, prompt)
                with open(cassette_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "key": key,
                        "step": step,
                        "model": model,
                        "prompt": prompt,
                        "response": resp,
                        "recorded_at": datetime.now(timezone.utc).isoformat(),
                    }, f, indent=2)
                return resp
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "quota" in err_str.lower():
                    wait_time = 45 + (attempt * 10)
                    print(f"  [RATE LIMIT 429] Waiting {wait_time}s before retrying {step}...")
                    time.sleep(wait_time)
                else:
                    raise


def main():
    out_dir = REPO_ROOT / "design_pack" / "runs" / "c15_pair1"
    out_dir.mkdir(parents=True, exist_ok=True)
    cassettes_dir = REPO_ROOT / "tests" / "cassettes"

    config = load_config()
    raw_client = LLMClient(config, out_dir=out_dir)
    client = SmartCachingClient(raw_client, cassettes_dir=cassettes_dir)

    # Load dialogue
    dialogue_path = REPO_ROOT / "data" / "corpus" / "c15_creative_medium" / "dialogue.json"
    with open(dialogue_path) as f:
        dialogue = json.load(f)

    pair1_turns = [t for t in dialogue if t.get("pair") == 1]
    user_turn = next(t for t in pair1_turns if t.get("speaker") == "user")
    ai_turn = next(t for t in pair1_turns if t.get("speaker") == "ai")

    print(f"=== INPUT (Pair 1) ===")
    print(f"User turn length: {len(user_turn['text'])} chars")
    print(f"AI turn length: {len(ai_turn['text'])} chars")

    state = State()
    ledger_path = out_dir / "ledger.jsonl"
    if ledger_path.exists():
        ledger_path.unlink()
    ledger_writer = LedgerWriter(ledger_path)

    # Step 1a
    print("\n--- Running Step 1a (Atomic Actions) ---")
    new_actions = step_1a(client, config, state, 1, user_turn["text"], ai_turn["text"])
    print(f"Extracted {len(new_actions)} actions ({sum(1 for a in new_actions if a['id'].startswith('U'))} User, {sum(1 for a in new_actions if a['id'].startswith('A'))} AI)")

    # Step 1b
    print("\n--- Running Step 1b (Outcome Tree & Goal Hierarchy) ---")
    step_1b(client, config, state, 1)
    print(f"Extracted {len(state.outcomes)} outcomes")
    print(f"Summary: {state.run.get('dialogue_summary', '')}")

    # Step 1c
    print("\n--- Running Step 1c (Intentions) ---")
    step_1c(client, config, state, 1)
    print(f"Extracted {len(state.intentions)} intentions")

    # Step 2 & Step 3 Trigger A via run_level2
    print("\n--- Running Level 2 (Step 2 Requirements/Slots & Step 3 Trigger A) ---")
    level2_results = run_level2(client, config, state, 1, new_actions, ledger_writer=ledger_writer)

    ledger_rows = read_ledger(ledger_path)
    print(f"\nLevel 2 complete. Requirements in state: {len(state.requirements)}, Slots in state: {len(state.slots)}")
    print(f"Ledger rows written: {len(ledger_rows)}")

    # Stage 4 derivations
    delta_you = sum(r["score"] for r in ledger_rows if r["speaker"] == "U")
    delta_ai = sum(r["score"] for r in ledger_rows if r["speaker"] == "A")
    total_delta = delta_you + delta_ai
    you_pct = round((delta_you / total_delta * 100.0), 1) if total_delta > 0 else 50.0
    ai_pct = round((delta_ai / total_delta * 100.0), 1) if total_delta > 0 else 50.0

    # Decision counts
    req_creators = {}
    for r in state.requirements:
        c_aids = r.get("creation_action_ids", [])
        if c_aids:
            first_aid = sorted(c_aids)[0]
            speaker = "you" if first_aid.startswith("U") else "ai"
            req_creators[f"{r['outcome_id']}/{r['req_id']}"] = speaker

    you_decisions = sum(1 for c in req_creators.values() if c == "you")
    ai_decisions = sum(1 for c in req_creators.values() if c == "ai")

    summary_data = {
        "actions": state.actions,
        "outcomes": state.outcomes,
        "intentions": state.intentions,
        "action_to_outcome": state.run.get("action_to_outcome", {}),
        "dialogue_summary": state.run.get("dialogue_summary", ""),
        "requirements": state.requirements,
        "slots": state.slots,
        "ledger_rows": ledger_rows,
        "stage4": {
            "delta_you": delta_you,
            "delta_ai": delta_ai,
            "you_pct": you_pct,
            "ai_pct": ai_pct,
            "decisions": {
                "you_count": you_decisions,
                "ai_count": ai_decisions,
            }
        }
    }

    with open(out_dir / "results.json", "w") as f:
        json.dump(summary_data, f, indent=2)

    print("\n=== RUN SUMMARY WRITTEN TO design_pack/runs/c15_pair1/results.json ===")


if __name__ == "__main__":
    main()
