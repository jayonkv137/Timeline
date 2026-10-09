"""Run live extraction on c15_creative_medium Pair 2 starting from Pair 1 state."""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from engine.config import load_config
from engine.llm import LLMClient
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
    p1_dir = REPO_ROOT / "design_pack" / "runs" / "c15_pair1"
    out_dir = REPO_ROOT / "design_pack" / "runs" / "c15_pair2"
    out_dir.mkdir(parents=True, exist_ok=True)
    cassettes_dir = REPO_ROOT / "tests" / "cassettes"

    config = load_config()
    raw_client = LLMClient(config, out_dir=out_dir)
    client = SmartCachingClient(raw_client, cassettes_dir=cassettes_dir)

    # 1. Rehydrate Pair 1 state
    with open(p1_dir / "results.json") as f:
        p1_data = json.load(f)

    state = State()
    for a in p1_data["actions"]:
        state.add_action(a)
    state.outcomes = p1_data["outcomes"]
    state.intentions = p1_data["intentions"]
    state.requirements = p1_data["requirements"]
    state.slots = p1_data["slots"]
    state.run["action_to_outcome"] = p1_data["action_to_outcome"]
    state.run["dialogue_summary"] = p1_data["dialogue_summary"]

    # Ledger writer appending to cumulative ledger
    ledger_path = out_dir / "ledger.jsonl"
    # Copy Pair 1 ledger rows first
    p1_ledger = read_ledger(p1_dir / "ledger.jsonl")
    with open(ledger_path, "w") as f:
        for r in p1_ledger:
            f.write(json.dumps(r) + "\n")
    ledger_writer = LedgerWriter(ledger_path)

    # 2. Load dialogue Pair 2
    dialogue_path = REPO_ROOT / "data" / "corpus" / "c15_creative_medium" / "dialogue.json"
    with open(dialogue_path) as f:
        dialogue = json.load(f)

    pair2_turns = [t for t in dialogue if t.get("pair") == 2]
    user_turn = next(t for t in pair2_turns if t.get("speaker") == "user")
    ai_turn = next(t for t in pair2_turns if t.get("speaker") == "ai")

    print(f"=== INPUT (Pair 2) ===")
    print(f"User turn length: {len(user_turn['text'])} chars")
    print(f"AI turn length: {len(ai_turn['text'])} chars")

    # Step 1a
    print("\n--- Running Step 1a (Atomic Actions for Pair 2) ---")
    new_actions = step_1a(client, config, state, 2, user_turn["text"], ai_turn["text"])
    print(f"Extracted {len(new_actions)} actions ({sum(1 for a in new_actions if a['id'].startswith('U'))} User, {sum(1 for a in new_actions if a['id'].startswith('A'))} AI)")

    # Step 1b
    print("\n--- Running Step 1b (Outcome Tree & Goal Hierarchy) ---")
    step_1b(client, config, state, 2)
    print(f"Outcomes in state: {len(state.outcomes)}")
    for o in state.outcomes:
        print(f"  - {o['id']}: {o['text']} (parent: {o.get('parent')})")
    print(f"Summary: {state.run.get('dialogue_summary', '')}")

    # Step 1c
    print("\n--- Running Step 1c (Intentions) ---")
    step_1c(client, config, state, 2)
    print(f"Intentions in state: {len(state.intentions)}")
    for i in state.intentions:
        print(f"  - {i['intention_id']}: {i['intention']} -> {i.get('outcome_ids')}")

    # Step 2 & Step 3 Trigger A via run_level2
    print("\n--- Running Level 2 (Step 2 Requirements/Slots & Step 3 Trigger A) ---")
    level2_results = run_level2(client, config, state, 2, new_actions, ledger_writer=ledger_writer)

    all_ledger_rows = read_ledger(ledger_path)
    p2_ledger_rows = [r for r in all_ledger_rows if r["pair_added"] == 2]
    print(f"\nLevel 2 complete. Total requirements: {len(state.requirements)}, Total slots: {len(state.slots)}")
    print(f"Total ledger rows: {len(all_ledger_rows)} (Pair 2 added: {len(p2_ledger_rows)})")

    # Stage 4 derivations for Pair 2
    delta_you = sum(r["score"] for r in p2_ledger_rows if r["speaker"] == "U")
    delta_ai = sum(r["score"] for r in p2_ledger_rows if r["speaker"] == "A")
    total_delta = delta_you + delta_ai
    you_pct = round((delta_you / total_delta * 100.0), 1) if total_delta > 0 else 50.0
    ai_pct = round((delta_ai / total_delta * 100.0), 1) if total_delta > 0 else 50.0

    # Cumulative C(2)
    c_you = sum(r["score"] for r in all_ledger_rows if r["speaker"] == "U")
    c_ai = sum(r["score"] for r in all_ledger_rows if r["speaker"] == "A")
    total_c = c_you + c_ai
    cum_you_pct = round((c_you / total_c * 100.0), 1) if total_c > 0 else 50.0
    cum_ai_pct = round((c_ai / total_c * 100.0), 1) if total_c > 0 else 50.0

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
        "ledger_rows": all_ledger_rows,
        "pair2_ledger_rows": p2_ledger_rows,
        "stage4": {
            "pair2_delta": {
                "delta_you": delta_you,
                "delta_ai": delta_ai,
                "you_pct": you_pct,
                "ai_pct": ai_pct,
            },
            "cumulative": {
                "c_you": c_you,
                "c_ai": c_ai,
                "you_pct": cum_you_pct,
                "ai_pct": cum_ai_pct,
            },
            "decisions": {
                "you_count": you_decisions,
                "ai_count": ai_decisions,
            }
        }
    }

    with open(out_dir / "results.json", "w") as f:
        json.dump(summary_data, f, indent=2)

    print("\n=== RUN SUMMARY WRITTEN TO design_pack/runs/c15_pair2/results.json ===")


if __name__ == "__main__":
    main()
