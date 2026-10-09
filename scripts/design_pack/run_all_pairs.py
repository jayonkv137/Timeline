"""Run live extraction on all 8 pairs of c15_creative_medium end-to-end."""
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
            print(f"    [CACHE HIT] {step} -> {key[:8]}")
            with open(cassette_path, "r", encoding="utf-8") as f:
                return json.load(f)["response"]

        print(f"    [API CALL] {step} (model: {model})...")
        for attempt in range(6):
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
                    print(f"    [RATE LIMIT 429] Waiting {wait_time}s before retrying {step}...")
                    time.sleep(wait_time)
                else:
                    raise


def main():
    out_dir = REPO_ROOT / "design_pack" / "runs" / "c15_full"
    out_dir.mkdir(parents=True, exist_ok=True)
    cassettes_dir = REPO_ROOT / "tests" / "cassettes"

    config = load_config()
    raw_client = LLMClient(config, out_dir=out_dir)
    client = SmartCachingClient(raw_client, cassettes_dir=cassettes_dir)

    dialogue_path = REPO_ROOT / "data" / "corpus" / "c15_creative_medium" / "dialogue.json"
    with open(dialogue_path) as f:
        dialogue = json.load(f)

    # Get max pair
    pairs = sorted(list({t["pair"] for t in dialogue}))
    print(f"=== Running Full Pipeline on {len(pairs)} Pairs (c15_creative_medium) ===")

    state = State()
    ledger_path = out_dir / "ledger.jsonl"
    if ledger_path.exists():
        ledger_path.unlink()
    ledger_writer = LedgerWriter(ledger_path)

    snapshots = []

    for p in pairs:
        print(f"\n==================== PAIR {p} / {len(pairs)} ====================")
        p_turns = [t for t in dialogue if t.get("pair") == p]
        user_turn = next(t for t in p_turns if t.get("speaker") == "user")
        ai_turn = next(t for t in p_turns if t.get("speaker") == "ai")

        print(f"User: {len(user_turn['text'])} chars | AI: {len(ai_turn['text'])} chars")

        # 1a
        print(f"  Step 1a (Atomic Actions)...")
        new_actions = step_1a(client, config, state, p, user_turn["text"], ai_turn["text"])
        u_cnt = sum(1 for a in new_actions if a['id'].startswith('U'))
        a_cnt = sum(1 for a in new_actions if a['id'].startswith('A'))
        print(f"  -> Extracted {len(new_actions)} actions ({u_cnt} U, {a_cnt} A)")

        # 1b
        print(f"  Step 1b (Outcome Tree)...")
        step_1b(client, config, state, p)
        print(f"  -> Total outcomes in state: {len(state.outcomes)}")

        # 1c
        print(f"  Step 1c (Intentions)...")
        step_1c(client, config, state, p)
        print(f"  -> Total intentions in state: {len(state.intentions)}")

        # Level 2 (Step 2 + Step 3 Trigger A)
        print(f"  Level 2 (Step 2 Requirements/Slots & Step 3 Trigger A)...")
        run_level2(client, config, state, p, new_actions, ledger_writer=ledger_writer)

        all_ledger = read_ledger(ledger_path)
        p_rows = [r for r in all_ledger if r["pair_added"] == p]
        print(f"  -> Pair {p} added {len(p_rows)} ledger rows (Total: {len(all_ledger)})")

        # Stage 4 derivations
        delta_you = sum(r["score"] for r in p_rows if r["speaker"] == "U")
        delta_ai = sum(r["score"] for r in p_rows if r["speaker"] == "A")
        c_you = sum(r["score"] for r in all_ledger if r["speaker"] == "U")
        c_ai = sum(r["score"] for r in all_ledger if r["speaker"] == "A")
        tot_c = c_you + c_ai
        cum_you_pct = round((c_you / tot_c * 100.0), 1) if tot_c > 0 else 50.0
        cum_ai_pct = round((c_ai / tot_c * 100.0), 1) if tot_c > 0 else 50.0

        # Decisions
        req_creators = {}
        for r in state.requirements:
            c_aids = r.get("creation_action_ids", [])
            if c_aids:
                first_aid = sorted(c_aids)[0]
                speaker = "you" if first_aid.startswith("U") else "ai"
                req_creators[f"{r['outcome_id']}/{r['req_id']}"] = speaker

        you_dec = sum(1 for c in req_creators.values() if c == "you")
        ai_dec = sum(1 for c in req_creators.values() if c == "ai")

        p_snapshot = {
            "pair": p,
            "delta_you": delta_you,
            "delta_ai": delta_ai,
            "c_you": c_you,
            "c_ai": c_ai,
            "you_pct": cum_you_pct,
            "ai_pct": cum_ai_pct,
            "decisions": {"you": you_dec, "ai": ai_dec},
            "open_slots": sum(1 for s in state.slots if s.get("status") == "open"),
            "total_requirements": len(state.requirements),
            "summary": state.run.get("dialogue_summary", ""),
        }
        snapshots.append(p_snapshot)
        print(f"  -> Stage 4 @ P{p}: Delta=(U:{delta_you}, A:{delta_ai}) | Cumul=(U:{c_you}, A:{c_ai} -> {cum_you_pct}%/{cum_ai_pct}%) | Decisions={you_dec}U/{ai_dec}A")

        # Save per-pair checkpoint
        checkpoint = {
            "pair": p,
            "snapshot": p_snapshot,
            "state": {
                "actions": state.actions,
                "outcomes": state.outcomes,
                "intentions": state.intentions,
                "requirements": state.requirements,
                "slots": state.slots,
                "action_to_outcome": state.run.get("action_to_outcome", {}),
            }
        }
        with open(out_dir / f"checkpoint_p{p}.json", "w") as f:
            json.dump(checkpoint, f, indent=2)

    # Save full run result
    full_result = {
        "chat_id": "c15_creative_medium",
        "total_pairs": len(pairs),
        "snapshots": snapshots,
        "actions": state.actions,
        "outcomes": state.outcomes,
        "intentions": state.intentions,
        "requirements": state.requirements,
        "slots": state.slots,
        "action_to_outcome": state.run.get("action_to_outcome", {}),
        "dialogue_summary": state.run.get("dialogue_summary", ""),
        "total_ledger_rows": len(all_ledger),
    }

    with open(out_dir / "results_full.json", "w") as f:
        json.dump(full_result, f, indent=2)

    print(f"\n=== FULL RUN FINISHED ===")
    print(f"Output files written to: {out_dir}")


if __name__ == "__main__":
    main()
