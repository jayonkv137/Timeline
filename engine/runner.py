"""Pipeline execution runner.

Groups dialogue into pairs, runs Level 1, 2, and 3 steps,
manages caching, state persistence, CLI resume, and stubs Stage 4 outputs.
"""
import datetime
import json
from pathlib import Path

from engine.artifacts import LedgerWriter, write_json_artifact, validate_artifact
from engine.llm import LLMClient, CachedLLMClient
from engine.pipeline import PipelineError, run_level1, run_level2, run_level3
from engine.state import State


def load_dialogue_from_export(path):
    """Load and validate dialogue JSON. If generic format is supplied, converts
    it to conform to dialogue.schema.json.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Export file not found: {path}")

    with open(path) as f:
        data = json.load(f)

    # Already conformant dialogue
    if isinstance(data, list) and all(isinstance(x, dict) and "pair" in x and "speaker" in x and "text" in x for x in data):
        return validate_artifact(data, "dialogue")

    # Generic turns list conversion
    if not isinstance(data, list):
        for key in ("turns", "messages", "dialogue", "chat"):
            if key in data and isinstance(data[key], list):
                data = data[key]
                break
        else:
            raise ValueError(f"Could not find dialogue turns list in {path}")

    turns = []
    pair_idx = 1
    user_turn = None

    for item in data:
        role = item.get("role") or item.get("speaker") or ""
        content = item.get("content") or item.get("text") or ""
        attachments = item.get("attachments") or []
        ts = item.get("ts") or item.get("timestamp") or datetime.datetime.now(datetime.timezone.utc).isoformat()

        role = str(role).lower()
        if "user" in role:
            speaker = "user"
        elif "assistant" in role or "ai" in role:
            speaker = "ai"
        else:
            continue

        if speaker == "user":
            user_turn = {
                "pair": pair_idx,
                "speaker": "user",
                "text": content,
                "attachments": attachments,
                "ts": ts
            }
            turns.append(user_turn)
        elif speaker == "ai":
            if not user_turn:
                continue
            turns.append({
                "pair": pair_idx,
                "speaker": "ai",
                "text": content,
                "attachments": attachments,
                "ts": ts
            })
            user_turn = None
            pair_idx += 1

    return validate_artifact(turns, "dialogue")


def run_pipeline(config, dialogue, out_dir, limit_pairs=None, resume=False):
    """Orchestrates sequential run over all pairs, resuming or starting fresh."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save dialogue.json
    write_json_artifact(out_dir / "dialogue.json", dialogue, "dialogue")

    # 2. State loading
    if resume and (out_dir / "state.json").exists():
        state = State.load(out_dir)
    else:
        state = State()

    # 3. LedgerWriter initialization
    ledger_path = out_dir / "ledger.jsonl"
    if not resume and ledger_path.exists():
        ledger_path.unlink()

    ledger_writer = LedgerWriter(ledger_path)
    ledger_writer.path.touch(exist_ok=True)


    # 4. Group dialogue turns by pair index
    turns_by_pair = {}
    for turn in dialogue:
        p = turn["pair"]
        turns_by_pair.setdefault(p, {})[turn["speaker"]] = turn["text"]

    max_pair = max(turns_by_pair.keys()) if turns_by_pair else 0
    if limit_pairs is not None:
        max_pair = min(max_pair, limit_pairs)

    start_pair = state.run["last_completed_pair"] + 1 if resume else 1

    # 5. LLM Clients
    raw_client = LLMClient(config, out_dir)
    client = CachedLLMClient(raw_client, out_dir)

    # 6. Live-rail execution loop
    for P in range(start_pair, max_pair + 1):
        if P not in turns_by_pair or "user" not in turns_by_pair[P] or "ai" not in turns_by_pair[P]:
            raise PipelineError(f"Missing user or ai turn for pair {P}")

        user_text = turns_by_pair[P]["user"]
        ai_text = turns_by_pair[P]["ai"]

        # Level 1 (Steps 1a, 1b, 1c)
        new_actions = run_level1(client, config, state, P, user_text, ai_text)

        # Level 2 (Step 2 touched outcomes)
        new_reqs = run_level2(client, config, state, ledger_writer, P, new_actions)

        # Level 3 (Step 3 Trigger A + B)
        run_level3(client, config, state, ledger_writer, P, new_reqs, new_actions)

        # Update last completed pair and save state
        state.run["last_completed_pair"] = P
        state.save(out_dir)

    # 7. Write Stage 4 outputs
    from engine.quant import compute_stage4, write_stage4_artifacts
    snapshots, panel_bundle = compute_stage4(state, ledger_writer.rows)
    write_stage4_artifacts(out_dir, snapshots, panel_bundle)


    return state
