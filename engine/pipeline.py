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
from engine.config import Config
from engine.state import State


ACTION_ID_RE = re.compile(r"^([UA])\((\d+),\s*(\d+)\)$")





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


def format_prior_requirements_block(requirements):
    if not requirements:
        return "[]"
    spec_shaped = [{
        "req id": r["req_id"],
        "text": r["text"],
        "type": r["type"],
        "status": r["status"],
        "creation action ids": r["creation_action_ids"],
        "contributing action ids": r["contributing_action_ids"],
        "related to": r["related_to"],
    } for r in requirements]
    return json.dumps(spec_shaped, indent=2, ensure_ascii=False)


def format_prior_open_slots_block(slots):
    open_slots = [s for s in slots if s["status"] == "open"]
    if not open_slots:
        return "[]"
    spec_shaped = [{
        "slot id": s["slot_id"],
        "text": s["text"],
        "type": s["type"],
        "origin": s["origin"],
        "creation action ids": s["creation_action_ids"],
        "contributing action ids": s["contributing_action_ids"],
    } for s in open_slots]
    return json.dumps(spec_shaped, indent=2, ensure_ascii=False)


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


# ---------------------------------------------------------------- Step 2

def step_2(client, config, state, pair_number, outcome_id, ledger_writer=None):
    """Step 2: Requirement & Open-Slot Extraction for ONE outcome (§6).
    Cadence: once per outcome touched this pair (§9.2).
    """
    outcome = state.get_outcome(outcome_id)
    actions = state.actions_for_outcome(outcome_id)
    if not actions:
        raise PipelineError(f"step 2: no actions found bound to outcome {outcome_id!r}")

    prior_reqs = state.requirements_for_outcome(outcome_id)
    prior_slots = state.slots_for_outcome(outcome_id)

    prompt = prompts.fill(prompts.STEP_2, {
        "outcome id": outcome_id,
        "outcome description": outcome["text"],
        "outcome actions block": format_actions_block(actions),
        "prior requirements block": format_prior_requirements_block(prior_reqs),
        "prior open slots block": format_prior_open_slots_block(prior_slots),
    })

    response = client.call_json(f"2:pair{pair_number}:{outcome_id}", config.model_main, prompt)

    raw_req_ops = _require(response, "requirement ops", f"step 2 {outcome_id}")
    raw_slot_ops = _require(response, "open_slot ops", f"step 2 {outcome_id}")

    if not isinstance(raw_req_ops, list):
        raise PipelineError(f"step 2 {outcome_id}: 'requirement ops' must be a list")
    if not isinstance(raw_slot_ops, list):
        raise PipelineError(f"step 2 {outcome_id}: 'open_slot ops' must be a list")

    a2o = state.run.get("action_to_outcome", {})

    # 1. Process requirement operations
    req_ops_processed = []
    for raw in raw_req_ops:
        op = str(_require(raw, "op", f"step 2 {outcome_id} requirement op"))
        if op not in ("create", "revise", "delete"):
            raise PipelineError(f"step 2 {outcome_id}: invalid requirement op {op!r}")

        bound_oid = str(_require(raw, "bound outcome id", f"step 2 {outcome_id} requirement op"))
        if bound_oid != outcome_id:
            raise PipelineError(f"step 2 {outcome_id}: bound outcome id {bound_oid!r} != {outcome_id!r}")

        req_id = str(_require(raw, "req id", f"step 2 {outcome_id} requirement op"))

        if op == "create":
            existing = state.find_requirement(outcome_id, req_id)
            if existing is not None:
                raise PipelineError(f"step 2 {outcome_id}: duplicate requirement id {req_id!r}")

            fields = _require(raw, "fields", f"step 2 {outcome_id} req create")
            text = str(_require(fields, "text", f"step 2 {outcome_id} req fields"))
            req_type = str(_require(fields, "type", f"step 2 {outcome_id} req fields"))
            if req_type not in ("constraint", "preference", "ranking", "task", "other"):
                req_type = "other"

            creation_aids = [str(x) for x in _require(raw, "creation action ids", f"step 2 {outcome_id} req create")]
            if not creation_aids:
                raise PipelineError(f"step 2 {outcome_id}: req {req_id} create missing creation action ids")

            for aid in creation_aids:
                if not state.has_action(aid):
                    raise PipelineError(f"step 2 {outcome_id}: unknown action id {aid!r} in req {req_id}")
                if a2o.get(aid) != outcome_id:
                    raise PipelineError(
                        f"step 2 {outcome_id}: action {aid!r} cited in outcome {outcome_id} belongs to {a2o.get(aid)!r}"
                    )

            contributing_aids = [str(x) for x in raw.get("contributing action ids", [])]
            impl_aids = [str(x) for x in raw.get("implementation action ids", [])]
            related_to = [str(x) for x in raw.get("related to", [])]
            explicit_or_implicit = str(raw.get("explicit or implicit", "explicit"))
            if explicit_or_implicit not in ("explicit", "implicit"):
                explicit_or_implicit = "explicit"
            rationale = str(raw.get("rationale", ""))

            new_req = {
                "outcome_id": outcome_id,
                "req_id": req_id,
                "text": text,
                "type": req_type,
                "status": "active",
                "creation_action_ids": creation_aids,
                "contributing_action_ids": contributing_aids,
                "implementation_action_ids": impl_aids,
                "revise_action_ids": [],
                "related_to": related_to,
                "explicit_or_implicit": explicit_or_implicit,
                "rationale": rationale,
                "created_at_pair": pair_number,
            }
            state.requirements.append(new_req)
            state.log_operation(pair_number, outcome_id, "create", req_id, "requirement")

            # Reset slot age if requirement references an open slot in related_to
            for r_id in related_to:
                if state.find_slot(outcome_id, str(r_id)) is not None:
                    record_slot_activity(state, outcome_id, str(r_id), pair_number)

            # Write ledger rows with score 5.0, kind="creation" (§10.3)
            for aid in creation_aids:
                act = state.get_action(aid)
                speaker = "U" if act["id"].startswith("U") else "A"
                row = {
                    "pair_added": pair_number,
                    "action_id": act["id"],
                    "speaker": speaker,
                    "role": act["role"],
                    "outcome_id": outcome_id,
                    "req_id": req_id,
                    "score": 5.0,
                    "kind": "creation",
                }
                if ledger_writer is not None:
                    ledger_writer.append(row)

            req_ops_processed.append(new_req)

        elif op == "revise":
            related = [str(x) for x in raw.get("related to", [])]
            target_id = related[0] if related else req_id
            existing = state.find_requirement(outcome_id, target_id)
            if existing is None:
                existing = state.find_requirement(outcome_id, req_id)
            if existing is None:
                raise PipelineError(f"step 2 {outcome_id}: revise targets unknown req id {target_id!r}")

            existing["status"] = "revised"

            fields = raw.get("fields", {})
            revised_text = fields.get("text", existing["text"])
            revised_type = fields.get("type", existing["type"])
            new_req_id = req_id if req_id != existing["req_id"] else f"{req_id}_rev"
            creation_aids = [str(x) for x in raw.get("creation action ids", existing["creation_action_ids"])]

            revised_req = {
                "outcome_id": outcome_id,
                "req_id": new_req_id,
                "text": str(revised_text),
                "type": str(revised_type),
                "status": "active",
                "creation_action_ids": creation_aids,
                "contributing_action_ids": [str(x) for x in raw.get("contributing action ids", [])],
                "implementation_action_ids": [str(x) for x in raw.get("implementation action ids", [])],
                "revise_action_ids": [],
                "related_to": [existing["req_id"]],
                "explicit_or_implicit": str(raw.get("explicit or implicit", "explicit")),
                "rationale": str(raw.get("rationale", "")),
                "created_at_pair": pair_number,
            }
            state.requirements.append(revised_req)
            state.log_operation(pair_number, outcome_id, "revise", target_id, "requirement")
            req_ops_processed.append(revised_req)

        elif op == "delete":
            related = [str(x) for x in raw.get("related to", [])]
            target_id = related[0] if related else req_id
            existing = state.find_requirement(outcome_id, target_id)
            if existing is None:
                raise PipelineError(f"step 2 {outcome_id}: delete targets unknown req id {target_id!r}")
            existing["status"] = "deleted"
            state.log_operation(pair_number, outcome_id, "delete", target_id, "requirement")

    # 2. Process open slot operations
    slot_ops_processed = []
    for raw in raw_slot_ops:
        op = str(_require(raw, "op", f"step 2 {outcome_id} slot op"))
        if op not in ("open_slot", "resolve", "abandon"):
            raise PipelineError(f"step 2 {outcome_id}: invalid slot op {op!r}")

        bound_oid = str(_require(raw, "bound outcome id", f"step 2 {outcome_id} slot op"))
        if bound_oid != outcome_id:
            raise PipelineError(f"step 2 {outcome_id}: bound outcome id {bound_oid!r} != {outcome_id!r}")

        slot_id = str(_require(raw, "slot id", f"step 2 {outcome_id} slot op"))

        if op == "open_slot":
            existing = state.find_slot(outcome_id, slot_id)
            if existing is not None:
                raise PipelineError(f"step 2 {outcome_id}: duplicate slot id {slot_id!r}")

            fields = _require(raw, "fields", f"step 2 {outcome_id} open_slot")
            text = str(_require(fields, "text", f"step 2 {outcome_id} slot fields"))
            slot_type = str(fields.get("type", "other"))
            if slot_type not in ("constraint", "preference", "ranking", "task", "other"):
                slot_type = "other"

            origin = str(_require(raw, "origin", f"step 2 {outcome_id} slot origin"))
            if origin not in ("user", "AI"):
                origin = "AI"

            creation_aids = [str(x) for x in _require(raw, "creation action ids", f"step 2 {outcome_id} slot create")]
            if not creation_aids:
                raise PipelineError(f"step 2 {outcome_id}: slot {slot_id} missing creation action ids")

            for aid in creation_aids:
                if not state.has_action(aid):
                    raise PipelineError(f"step 2 {outcome_id}: unknown action id {aid!r} in slot {slot_id}")
                if a2o.get(aid) != outcome_id:
                    raise PipelineError(
                        f"step 2 {outcome_id}: action {aid!r} cited in outcome {outcome_id} belongs to {a2o.get(aid)!r}"
                    )

            new_slot = {
                "slot_id": slot_id,
                "outcome_id": outcome_id,
                "text": text,
                "type": slot_type,
                "origin": origin,
                "status": "open",
                "creation_action_ids": creation_aids,
                "contributing_action_ids": [str(x) for x in raw.get("contributing action ids", [])],
                "resolved_into": None,
            }
            state.slots.append(new_slot)
            record_slot_activity(state, outcome_id, slot_id, pair_number)
            state.run.setdefault("slot_opened_at_pair", {})[f"{outcome_id}||{slot_id}"] = pair_number
            state.log_operation(pair_number, outcome_id, "open_slot", slot_id, "slot")
            slot_ops_processed.append(new_slot)

        elif op == "resolve":
            existing = state.find_slot(outcome_id, slot_id)
            if existing is None:
                related = [str(x) for x in raw.get("related to", [])]
                for r_id in related:
                    existing = state.find_slot(outcome_id, r_id)
                    if existing is not None:
                        break
            if existing is None:
                raise PipelineError(f"step 2 {outcome_id}: resolve targets unknown slot {slot_id!r}")
            if existing["status"] != "open":
                raise PipelineError(f"step 2 {outcome_id}: cannot resolve slot {existing['slot_id']} with status {existing['status']!r}")

            new_req_id = raw.get("req id") or f"req_{existing['slot_id']}"
            existing["status"] = "resolved"
            existing["resolved_into"] = str(new_req_id)

            fields = raw.get("fields", {})
            text = str(fields.get("text", existing["text"]))
            req_type = str(fields.get("type", existing["type"]))
            creation_aids = [str(x) for x in raw.get("creation action ids", existing["creation_action_ids"])]

            resolved_req = {
                "outcome_id": outcome_id,
                "req_id": str(new_req_id),
                "text": text,
                "type": req_type,
                "status": "active",
                "creation_action_ids": creation_aids,
                "contributing_action_ids": [str(x) for x in raw.get("contributing action ids", [])],
                "implementation_action_ids": [],
                "revise_action_ids": [],
                "related_to": [existing["slot_id"]],
                "explicit_or_implicit": str(raw.get("explicit or implicit", "explicit")),
                "rationale": str(raw.get("rationale", "")),
                "created_at_pair": pair_number,
            }
            state.requirements.append(resolved_req)
            state.log_operation(pair_number, outcome_id, "resolve", existing["slot_id"], "slot")
            state.log_operation(pair_number, outcome_id, "create", str(new_req_id), "requirement")

            # Write ledger row for the resolving action (creation, 5.0)
            for aid in creation_aids:
                act = state.get_action(aid)
                speaker = "U" if act["id"].startswith("U") else "A"
                row = {
                    "pair_added": pair_number,
                    "action_id": act["id"],
                    "speaker": speaker,
                    "role": act["role"],
                    "outcome_id": outcome_id,
                    "req_id": str(new_req_id),
                    "score": 5.0,
                    "kind": "creation",
                }
                if ledger_writer is not None:
                    ledger_writer.append(row)

            # Write slot-origin row for the original slot creation actions
            for aid in existing["creation_action_ids"]:
                act = state.get_action(aid)
                speaker = "U" if act["id"].startswith("U") else "A"
                row = {
                    "pair_added": pair_number,
                    "action_id": act["id"],
                    "speaker": speaker,
                    "role": act["role"],
                    "outcome_id": outcome_id,
                    "req_id": str(new_req_id),
                    "score": 3.0,
                    "kind": "slot-origin",
                }
                if ledger_writer is not None:
                    ledger_writer.append(row)

            slot_ops_processed.append(existing)

        elif op == "abandon":
            existing = state.find_slot(outcome_id, slot_id)
            if existing is None:
                raise PipelineError(f"step 2 {outcome_id}: abandon targets unknown slot {slot_id!r}")
            existing["status"] = "abandoned"
            state.log_operation(pair_number, outcome_id, "abandon", slot_id, "slot")
            slot_ops_processed.append(existing)

    return {
        "requirement_ops": req_ops_processed,
        "open_slot_ops": slot_ops_processed,
    }


# ------------------------------------------------------------ slot lifecycle

def record_slot_activity(state, outcome_id, slot_id, pair_number):
    """Reset the slot's inactivity timer because an action or operation referenced it."""
    key = f"{outcome_id}||{slot_id}"
    state.run.setdefault("slot_last_active_pair", {})[key] = pair_number


def sweep_abandoned_slots(state, pair_number):
    """Automated 3-pair abandonment sweep (§9.3, §12.1).

    Any slot with status 'open' that has had no activity for 3 or more consecutive
    pairs (pair_number - last_active >= 3) transitions to 'abandoned'.
    """
    abandoned = []
    for slot in state.slots:
        if slot.get("status") != "open":
            continue
        outcome_id = slot["outcome_id"]
        slot_id = slot["slot_id"]
        key = f"{outcome_id}||{slot_id}"
        last_active = state.run.get("slot_last_active_pair", {}).get(
            key,
            state.run.get("slot_opened_at_pair", {}).get(key, pair_number),
        )
        if pair_number - last_active >= 3:
            slot["status"] = "abandoned"
            state.log_operation(pair_number, outcome_id, "abandon", slot_id, "slot")
            abandoned.append(slot)
    return abandoned


# ------------------------------------------------------------ step 3 (trigger a)

def format_step3_action_line(idx: int, action: dict) -> str:
    aid = action["id"]
    atype = action.get("type", "other")
    role = action.get("role", "OTHER")
    text = action.get("text", "")
    quote = action.get("evidence_quote", "")
    return f"[{idx}] {aid} | {atype} | {role} | {text} | evidence: \"{quote}\""


def format_step3_actions_block(actions: list[dict]) -> str:
    if not actions:
        return "None"
    return "\n".join(format_step3_action_line(i, a) for i, a in enumerate(actions))


def build_step3_trigger_a_prompt(
    outcome_text: str,
    req: dict,
    origin_turn: str,
    preceding_actions: list[dict],
    subsequent_actions: list[dict],
    slot_info: dict | None = None,
) -> str:
    template = prompts.STEP_3

    outcome_desc = outcome_text or req.get("outcome_id", "")
    req_id = req["req_id"]
    req_text = req["text"]
    preceding_block = format_step3_actions_block(preceding_actions)
    subsequent_block = format_step3_actions_block(subsequent_actions)

    if slot_info is not None:
        slot_actions_block = format_step3_actions_block(slot_info.get("actions", []))
        prompt = (
            template
            .replace("{outcome description}", outcome_desc)
            .replace("{req id}", req_id)
            .replace("{req text}", req_text)
            .replace("{req origin turn}", origin_turn)
            .replace("Origin: <directly created | resolved from open slot>", "Origin: resolved from open slot")
            .replace("{slot id}", slot_info.get("slot_id", ""))
            .replace("{user|AI}", slot_info.get("origin", "AI"))
            .replace("{slot creation turn}", slot_info.get("creation_turn", ""))
            .replace("{slot text}", slot_info.get("text", ""))
            .replace(
                "{slot's creation + contributing actions, each as: action_id | action_type |\nrole | action_text | evidence: \"quote\"}",
                slot_actions_block,
            )
            .replace("{preceding block}", preceding_block)
            .replace("{subsequent block}", subsequent_block)
        )
    else:
        # Origin = directly created: strip the conditional KNOWN SLOT ORIGIN block (§7.1, §7.3)
        start_marker = "=== KNOWN SLOT ORIGIN ==="
        end_marker = "=== SECTION A: PRECEDING ACTIONS"
        start_idx = template.find(start_marker)
        end_idx = template.find(end_marker)
        if start_idx != -1 and end_idx != -1:
            template = template[:start_idx] + template[end_idx:]

        prompt = (
            template
            .replace("{outcome description}", outcome_desc)
            .replace("{req id}", req_id)
            .replace("{req text}", req_text)
            .replace("{req origin turn}", origin_turn)
            .replace("Origin: <directly created | resolved from open slot>", "Origin: directly created")
            .replace("{preceding block}", preceding_block)
            .replace("{subsequent block}", subsequent_block)
        )

    return prompt


def step_3_trigger_a(
    client,
    config: Config,
    state: State,
    pair_number: int,
    outcome_id: str,
    requirement: dict,
    ledger_writer=None,
) -> dict:
    """Step 3 Trigger A (§9.3): Whole-dialogue influence scan for newly created/resolved requirement.

    Scans all actions across the entire dialogue preceding origin_turn (excluding creation actions
    and slot-origin actions). Scored actions (1-5) write kind='labeled' rows to the ledger.
    """
    creation_aids = requirement.get("creation_action_ids", [])
    if not creation_aids:
        raise PipelineError(f"step 3 Trigger A: req {requirement.get('req_id')} has no creation action ids")

    sorted_creation = sorted(creation_aids, key=action_sort_key)
    origin_turn = sorted_creation[0]
    origin_key = action_sort_key(origin_turn)

    # Invariant §11.4: requirement's own creation actions are excluded (pre-scored at 5.0)
    excluded_ids = set(creation_aids)

    slot_info = None
    resolved_slot_ids = requirement.get("related_to", [])
    if resolved_slot_ids:
        for sid in resolved_slot_ids:
            slot = state.find_slot(outcome_id, sid)
            if slot is not None:
                slot_actions = [
                    state.get_action(aid) for aid in (slot.get("creation_action_ids", []) + slot.get("contributing_action_ids", []))
                    if state.has_action(aid)
                ]
                slot_info = {
                    "slot_id": slot["slot_id"],
                    "origin": slot.get("origin", "AI"),
                    "creation_turn": slot.get("creation_action_ids", ["U(1,1)"])[0],
                    "text": slot["text"],
                    "actions": slot_actions,
                }
                excluded_ids.update(slot.get("creation_action_ids", []))
                excluded_ids.update(slot.get("contributing_action_ids", []))
                break

    # Section A: all actions across the whole dialogue before origin_turn
    preceding_actions = [
        a for a in state.actions
        if action_sort_key(a["id"]) < origin_key and a["id"] not in excluded_ids
    ]
    preceding_actions.sort(key=lambda a: action_sort_key(a["id"]))

    # Section B: actions in the same outcome after origin_turn (so far)
    a2o = state.run.get("action_to_outcome", {})
    subsequent_actions = [
        a for a in state.actions
        if action_sort_key(a["id"]) > origin_key
        and a2o.get(a["id"]) == outcome_id
        and a["id"] not in excluded_ids
    ]
    subsequent_actions.sort(key=lambda a: action_sort_key(a["id"]))

    if not preceding_actions and not subsequent_actions and not slot_info:
        return {"slot_origin_labels": [], "preceding_labels": [], "subsequent_labels": []}

    outcome = state.get_outcome(outcome_id)
    outcome_text = outcome["text"] if outcome else outcome_id

    prompt = build_step3_trigger_a_prompt(
        outcome_text=outcome_text,
        req=requirement,
        origin_turn=origin_turn,
        preceding_actions=preceding_actions,
        subsequent_actions=subsequent_actions,
        slot_info=slot_info,
    )

    call_label = f"3a:pair{pair_number}:{outcome_id}:{requirement['req_id']}"
    response = client.call_json(call_label, config.model_step3, prompt)

    slot_origin_labels = response.get("slot origin labels", [])
    preceding_labels = response.get("preceding labels", [])
    subsequent_labels = response.get("subsequent labels", [])

    all_labels = []
    if isinstance(slot_origin_labels, list):
        all_labels.extend(slot_origin_labels)
    if isinstance(preceding_labels, list):
        all_labels.extend(preceding_labels)
    if isinstance(subsequent_labels, list):
        all_labels.extend(subsequent_labels)

    req_id = requirement["req_id"]
    key = f"{outcome_id}||{req_id}"

    for lbl in all_labels:
        aid = lbl.get("action id")
        if not aid or not state.has_action(aid):
            continue

        rel_type = lbl.get("relationship type", "NO CONNECTION")
        score = lbl.get("relationship score")

        # Track that this action was labeled for this requirement
        state.run.setdefault("labeled_action_ids", {}).setdefault(key, []).append(aid)

        if rel_type == "NO CONNECTION" or score is None:
            continue

        try:
            numeric_score = float(score)
        except (ValueError, TypeError):
            continue

        if numeric_score <= 0:
            continue

        act = state.get_action(aid)
        speaker = "U" if act["id"].startswith("U") else "A"
        row = {
            "pair_added": pair_number,
            "action_id": act["id"],
            "speaker": speaker,
            "role": act["role"],
            "outcome_id": outcome_id,
            "req_id": req_id,
            "score": numeric_score,
            "kind": "labeled",
        }
        if ledger_writer is not None:
            ledger_writer.append(row)

        # Maintain relationship linkages on requirement
        if rel_type == "IMPLEMENTS" and aid not in requirement.get("implementation_action_ids", []):
            requirement.setdefault("implementation_action_ids", []).append(aid)
        elif rel_type == "REVISES" and aid not in requirement.get("revise_action_ids", []):
            requirement.setdefault("revise_action_ids", []).append(aid)
        elif aid not in requirement.get("contributing_action_ids", []):
            requirement.setdefault("contributing_action_ids", []).append(aid)

    return {
        "slot_origin_labels": slot_origin_labels,
        "preceding_labels": preceding_labels,
        "subsequent_labels": subsequent_labels,
    }


# ------------------------------------------------------------ orchestration

def run_level1(client, config, state, pair_number, user_text, ai_text):
    """§9.1: 1a → 1b → 1c for one pair. Returns the new actions (the pair's
    slice, which Level 2 uses to find touched outcomes).
    """
    new_actions = step_1a(client, config, state, pair_number, user_text, ai_text)
    step_1b(client, config, state, pair_number)
    step_1c(client, config, state, pair_number)
    return new_actions


def run_level2(client, config, state, pair_number, new_actions, ledger_writer=None):
    """Level 2: Step 2 per touched outcome (§9.2), followed by Trigger A for new reqs
    and the 3-pair abandonment sweep.
    """
    a2o = state.run.get("action_to_outcome", {})
    touched = sorted({a2o[a["id"]] for a in new_actions if a["id"] in a2o})
    results = {}
    for outcome_id in touched:
        step2_res = step_2(
            client, config, state, pair_number, outcome_id, ledger_writer=ledger_writer
        )
        results[outcome_id] = step2_res

        # Step 3 Trigger A: scan preceding actions for each newly created requirement
        for req in step2_res.get("requirement_ops", []):
            if req.get("created_at_pair") == pair_number:
                step_3_trigger_a(
                    client, config, state, pair_number, outcome_id, req, ledger_writer=ledger_writer
                )

    sweep_abandoned_slots(state, pair_number)
    return results
