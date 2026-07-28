"""Level 1 of the pipeline — Steps 1a → 1b → 1c, per pair (§9.1).

Exactly 3 LLM calls per pair, strictly sequential, no fan-out:
    1a(P)                   → new actions appended to STATE   [MODEL_FAST]
    1b(all actions so far)  → outcome tree re-emitted + action_to_outcome
                              + dialogue summary (SELF-REFERENCE)  [MODEL_MAIN]
    1c(outcomes so far)     → intentions re-emitted           [MODEL_MAIN]

All model output is parsed JSON only; blocks sent to prompts are re-serialized
by code (§11.5) — literal model formatting is never trusted or stored.

Every structural violation (bad turn-id format, wrong pair number, incomplete
action_to_outcome, incomplete outcome→intention) raises PipelineError — these
ids are the join keys for the entire downstream pipeline, so a violation here
is corruption, not a warning.
"""
import json
import re

from engine import prompts

ACTION_ID_RE = re.compile(r"^([UA])\((\d+),(\d+)\)$")


class PipelineError(Exception):
    """A step's response violated a structural contract."""


def action_sort_key(action_id):
    """Chronological order: pair, then U before A (one pair = one full user
    turn then one full AI turn), then intra-turn sequence. Same rule the
    Phase 0 canonical numbers were verified against (tests/test_phase0.py).
    """
    m = ACTION_ID_RE.match(action_id)
    if not m:
        raise PipelineError(f"malformed action id: {action_id!r}")
    speaker, pair, seq = m.group(1), int(m.group(2)), int(m.group(3))
    return (pair, 0 if speaker == "U" else 1, seq)


# ------------------------------------------------------------- formatting

def format_dialogue_block(pair_number, user_text, ai_text):
    """§3.3: real U/A text with an explicit pair-number label so the model
    reads x, never infers it.
    """
    return (f"PAIR {pair_number}\n"
            f"USER (this is the user turn of pair {pair_number}):\n{user_text}\n\n"
            f"AI (this is the AI turn of pair {pair_number}):\n{ai_text}")


def format_actions_block(actions):
    """Actions re-serialized code-side (§11.5) in the spec's key names."""
    spec_shaped = [{
        "turn id": a["id"],
        "action type": a["type"],
        "action text": a["text"],
        "role": a["role"],
        "evidence quote": a["evidence_quote"],
    } for a in actions]
    return json.dumps(spec_shaped, indent=2, ensure_ascii=False)


def format_outcomes_list(outcomes):
    return json.dumps([{"outcome id": o["id"], "outcome": o["text"]}
                       for o in outcomes], indent=2, ensure_ascii=False)


def _require(mapping, key, context):
    if key not in mapping:
        raise PipelineError(f"{context}: missing key {key!r} in {mapping!r}")
    return mapping[key]


# ---------------------------------------------------------------- Step 1a

def step_1a(client, config, state, pair_number, user_text, ai_text):
    prompt = prompts.fill(prompts.STEP_1A, {
        "dialogue block": format_dialogue_block(pair_number, user_text, ai_text),
    })
    response = client.call_json(f"1a:pair{pair_number}", config.model_fast, prompt)
    raw_actions = _require(response, "actions", "step 1a")
    if not isinstance(raw_actions, list) or not raw_actions:
        raise PipelineError(f"step 1a: 'actions' must be a non-empty list, got {raw_actions!r}")

    new_actions = []
    for raw in raw_actions:
        turn_id = _require(raw, "turn id", "step 1a action")
        m = ACTION_ID_RE.match(str(turn_id))
        if not m:
            raise PipelineError(
                f"step 1a: turn id {turn_id!r} violates U(x,y)/A(x,y) format")
        if int(m.group(2)) != pair_number:
            raise PipelineError(
                f"step 1a: turn id {turn_id!r} claims pair {m.group(2)}, "
                f"but this call is for pair {pair_number}")
        role = _require(raw, "role", "step 1a action")
        if role not in ("SHAPER", "EXECUTOR", "OTHER"):
            raise PipelineError(f"step 1a: invalid role {role!r} on {turn_id}")
        new_actions.append({
            "id": turn_id,
            "type": str(_require(raw, "action type", "step 1a action")),
            "text": str(_require(raw, "action text", "step 1a action")),
            "role": role,
            "evidence_quote": str(_require(raw, "evidence quote", "step 1a action")),
        })
    for action in new_actions:  # add after full validation — no partial appends
        state.add_action(action)
    return new_actions


# ---------------------------------------------------------------- Step 1b

def step_1b(client, config, state, pair_number):
    prompt = prompts.fill(prompts.STEP_1B, {
        "dialogue summary": state.run["dialogue_summary"],
        "all actions block": format_actions_block(state.actions),
    })
    response = client.call_json(f"1b:pair{pair_number}", config.model_main, prompt)

    raw_outcomes = _require(response, "outcomes", "step 1b")
    action_to_outcome = _require(response, "action to outcome", "step 1b")
    summary = _require(response, "dialogue summary", "step 1b")

    outcomes = []
    for raw in raw_outcomes:
        outcomes.append({
            "id": str(_require(raw, "outcome id", "step 1b outcome")),
            "text": str(_require(raw, "outcome", "step 1b outcome")),
            "turn_id": str(_require(raw, "turn id", "step 1b outcome")),
            "parent": raw.get("parent outcome id"),
            "children": [],   # rebuilt from parent pointers below (§11.4)
            "related": [str(x) for x in raw.get("related outcome ids", [])],
        })  # 'confidence' deliberately dropped — spec §4.4: ignore

    outcome_ids = [o["id"] for o in outcomes]
    if len(set(outcome_ids)) != len(outcome_ids):
        raise PipelineError(f"step 1b: duplicate outcome ids in {outcome_ids}")
    id_set = set(outcome_ids)

    # parent pointers are the single source of truth; children derived from
    # them so §11.4's bidirectional-consistency check holds by construction
    by_id = {o["id"]: o for o in outcomes}
    for o in outcomes:
        if o["parent"] is not None:
            if o["parent"] not in id_set:
                raise PipelineError(
                    f"step 1b: outcome {o['id']} has unknown parent {o['parent']!r}")
            by_id[o["parent"]]["children"].append(o["id"])

    # completeness: EVERY action mapped, no unknown action or outcome ids
    known_action_ids = {a["id"] for a in state.actions}
    mapped_ids = set(action_to_outcome.keys())
    if mapped_ids != known_action_ids:
        missing = sorted(known_action_ids - mapped_ids)
        unknown = sorted(mapped_ids - known_action_ids)
        raise PipelineError(
            f"step 1b: action_to_outcome incomplete — missing {missing}, unknown {unknown}")
    for action_id, outcome_id in action_to_outcome.items():
        if outcome_id not in id_set:
            raise PipelineError(
                f"step 1b: action {action_id} mapped to unknown outcome {outcome_id!r}")

    # full tree re-emitted each call (§4.7, taken literally): replace, not merge
    state.outcomes = outcomes
    state.run["action_to_outcome"] = dict(action_to_outcome)
    state.run["dialogue_summary"] = str(summary)
    return outcomes


# ---------------------------------------------------------------- Step 1c

def step_1c(client, config, state, pair_number):
    prompt = prompts.fill(prompts.STEP_1C, {
        "outcomes list": format_outcomes_list(state.outcomes),
    })
    response = client.call_json(f"1c:pair{pair_number}", config.model_main, prompt)

    raw_intentions = _require(response, "intentions", "step 1c")
    raw_mapping = _require(response, "outcome to intention", "step 1c")

    intention_ids = [str(_require(i, "intention id", "step 1c intention"))
                     for i in raw_intentions]
    if len(set(intention_ids)) != len(intention_ids):
        raise PipelineError(f"step 1c: duplicate intention ids in {intention_ids}")

    # completeness: every outcome id exactly once, every intention id known
    outcome_ids = {o["id"] for o in state.outcomes}
    mapping = {}
    for entry in raw_mapping:
        oid = str(_require(entry, "outcome id", "step 1c mapping"))
        iid = str(_require(entry, "intention id", "step 1c mapping"))
        if oid in mapping:
            raise PipelineError(f"step 1c: outcome {oid} mapped more than once")
        if oid not in outcome_ids:
            raise PipelineError(f"step 1c: unknown outcome id {oid!r} in mapping")
        if iid not in intention_ids:
            raise PipelineError(f"step 1c: unknown intention id {iid!r} in mapping")
        mapping[oid] = iid
    unmapped = sorted(outcome_ids - set(mapping))
    if unmapped:
        raise PipelineError(f"step 1c: outcomes left unmapped: {unmapped}")

    intentions = []
    for raw in raw_intentions:
        iid = str(raw["intention id"])
        intentions.append({
            "intention_id": iid,
            "intention": str(_require(raw, "intention", "step 1c intention")),
            "outcome_ids": sorted(o for o, i in mapping.items() if i == iid),
        })

    state.intentions = intentions  # re-emitted each call: replace
    state.run["outcome_to_intention"] = mapping
    return intentions


# ------------------------------------------------------------ orchestration

def run_level1(client, config, state, pair_number, user_text, ai_text):
    """§9.1: 1a → 1b → 1c for one pair. Returns the new actions (the pair's
    slice, which Level 2 uses to find touched outcomes).
    """
    new_actions = step_1a(client, config, state, pair_number, user_text, ai_text)
    step_1b(client, config, state, pair_number)
    step_1c(client, config, state, pair_number)
    return new_actions
