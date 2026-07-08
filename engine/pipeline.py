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


# ---------------------------------------------------------------- Step 2

def format_prior_requirements(requirements):
    """Format requirements to feed into Step 2 prompts block."""
    active_reqs = [r for r in requirements if r["status"] == "active"]
    if not active_reqs:
        return ""
    spec_shaped = [{
        "req id": r["req_id"],
        "bound outcome id": r["outcome_id"],
        "fields": {
            "text": r["text"],
            "type": r["type"],
        },
        "creation action ids": r["creation_action_ids"],
        "contributing action ids": r["contributing_action_ids"],
        "implementation action ids": r["implementation_action_ids"],
        "related to": r["related_to"],
        "explicit or implicit": r["explicit_or_implicit"],
        "rationale": r["rationale"],
    } for r in active_reqs]
    return json.dumps(spec_shaped, indent=2, ensure_ascii=False)


def format_prior_slots(slots):
    """Format open slots to feed into Step 2 prompts block."""
    open_slots = [s for s in slots if s["status"] == "open"]
    if not open_slots:
        return ""
    spec_shaped = [{
        "slot id": s["slot_id"],
        "bound outcome id": s["outcome_id"],
        "fields": {
            "text": s["text"],
            "type": s["type"],
        },
        "origin": s["origin"],
        "creation action ids": s["creation_action_ids"],
        "contributing action ids": s["contributing_action_ids"],
        "related to": [],
        "explicit or implicit": "explicit",
        "rationale": "",
    } for s in open_slots]
    return json.dumps(spec_shaped, indent=2, ensure_ascii=False)


def step_2(client, config, state, ledger_writer, pair_number, outcome_id):
    """Step 2: Requirement/Slot extraction per outcome.
    Validates model response, applies ops to STATE, and writes creation ledger rows.
    """
    outcome = state.get_outcome(outcome_id)
    actions = state.actions_for_outcome(outcome_id)
    prior_reqs = state.requirements_for_outcome(outcome_id)
    prior_slots = state.slots_for_outcome(outcome_id)

    prompt = prompts.fill(prompts.STEP_2, {
        "outcome id": outcome_id,
        "outcome description": outcome["text"],
        "outcome actions block": format_actions_block(actions),
        "prior requirements block": format_prior_requirements(prior_reqs),
        "prior open slots block": format_prior_slots(prior_slots),
    })

    model = config.model_step2 if config.model_step2 else config.model_main
    response = client.call_json(f"2:{outcome_id}:pair{pair_number}", model, prompt)

    req_ops = response.get("requirement ops") or []
    slot_ops = response.get("open_slot ops") or []

    # 1. Structural validation of response before applying any modifications
    for op in req_ops:
        op_type = _require(op, "op", "requirement op")
        if op_type not in ("create", "revise", "delete"):
            raise PipelineError(f"step 2: invalid requirement op type: {op_type!r}")
        
        req_id = _require(op, "req id", "requirement op")
        bound_outcome = _require(op, "bound outcome id", "requirement op")
        if bound_outcome != outcome_id:
            raise PipelineError(f"step 2: bound outcome id {bound_outcome!r} does not match {outcome_id!r}")

        if op_type in ("create", "revise"):
            fields = _require(op, "fields", "requirement op")
            _require(fields, "text", "requirement op fields")
            req_type = _require(fields, "type", "requirement op fields")
            if req_type not in ("constraint", "preference", "ranking", "task", "other"):
                raise PipelineError(f"step 2: invalid requirement type {req_type!r} for {req_id}")
            
            ex_or_im = _require(op, "explicit or implicit", "requirement op")
            if ex_or_im not in ("explicit", "implicit"):
                raise PipelineError(f"step 2: invalid explicit or implicit: {ex_or_im!r}")

            _require(op, "rationale", "requirement op")
            
            creation_ids = _require(op, "creation action ids", "requirement op")
            if not isinstance(creation_ids, list):
                raise PipelineError(f"step 2: creation action ids must be a list, got {creation_ids!r}")
            for a_id in creation_ids:
                if not state.has_action(a_id):
                    raise PipelineError(f"step 2: unknown creation action id: {a_id!r}")
                if state.run["action_to_outcome"].get(a_id) != outcome_id:
                    raise PipelineError(f"step 2: creation action {a_id!r} is not bound to outcome {outcome_id!r}")

            contrib_ids = _require(op, "contributing action ids", "requirement op")
            if not isinstance(contrib_ids, list):
                raise PipelineError(f"step 2: contributing action ids must be a list, got {contrib_ids!r}")
            for a_id in contrib_ids:
                if not state.has_action(a_id):
                    raise PipelineError(f"step 2: unknown contributing action id: {a_id!r}")
                if state.run["action_to_outcome"].get(a_id) != outcome_id:
                    raise PipelineError(f"step 2: contributing action {a_id!r} is not bound to outcome {outcome_id!r}")

            impl_ids = op.get("implementation action ids", [])
            if not isinstance(impl_ids, list):
                raise PipelineError(f"step 2: implementation action ids must be a list, got {impl_ids!r}")
            for a_id in impl_ids:
                if not state.has_action(a_id):
                    raise PipelineError(f"step 2: unknown implementation action id: {a_id!r}")
                if state.run["action_to_outcome"].get(a_id) != outcome_id:
                    raise PipelineError(f"step 2: implementation action {a_id!r} is not bound to outcome {outcome_id!r}")

        if op_type == "revise":
            related_to = op.get("related to", [])
            if not isinstance(related_to, list) or not related_to:
                raise PipelineError(f"step 2: revise op on {req_id} must have a non-empty 'related to'")

        if op_type == "delete":
            target = state.find_requirement(outcome_id, req_id)
            if not target:
                raise PipelineError(f"step 2: delete op targets unknown requirement: {req_id}")
            if target["status"] != "active":
                raise PipelineError(f"step 2: delete op targets non-active requirement: {req_id}")

    for op in slot_ops:
        op_type = _require(op, "op", "open_slot op")
        if op_type not in ("open_slot", "resolve", "abandon"):
            raise PipelineError(f"step 2: invalid open_slot op type: {op_type!r}")
        
        slot_id = _require(op, "slot id", "open_slot op")
        bound_outcome = _require(op, "bound outcome id", "open_slot op")
        if bound_outcome != outcome_id:
            raise PipelineError(f"step 2: bound outcome id {bound_outcome!r} does not match {outcome_id!r}")

        if op_type == "open_slot":
            fields = _require(op, "fields", "open_slot op")
            _require(fields, "text", "open_slot op fields")
            slot_type = _require(fields, "type", "open_slot op fields")
            if slot_type not in ("constraint", "preference", "ranking", "task", "other"):
                raise PipelineError(f"step 2: invalid slot type {slot_type!r} for {slot_id}")
            
            origin = _require(op, "origin", "open_slot op")
            if origin not in ("user", "AI"):
                raise PipelineError(f"step 2: invalid slot origin: {origin!r}")

            _require(op, "explicit or implicit", "open_slot op")
            _require(op, "rationale", "open_slot op")

            creation_ids = _require(op, "creation action ids", "open_slot op")
            if not isinstance(creation_ids, list):
                raise PipelineError(f"step 2: creation action ids must be a list, got {creation_ids!r}")
            for a_id in creation_ids:
                if not state.has_action(a_id):
                    raise PipelineError(f"step 2: unknown creation action id: {a_id!r}")
                if state.run["action_to_outcome"].get(a_id) != outcome_id:
                    raise PipelineError(f"step 2: creation action {a_id!r} is not bound to outcome {outcome_id!r}")

            contrib_ids = _require(op, "contributing action ids", "open_slot op")
            if not isinstance(contrib_ids, list):
                raise PipelineError(f"step 2: contributing action ids must be a list, got {contrib_ids!r}")
            for a_id in contrib_ids:
                if not state.has_action(a_id):
                    raise PipelineError(f"step 2: unknown contributing action id: {a_id!r}")
                if state.run["action_to_outcome"].get(a_id) != outcome_id:
                    raise PipelineError(f"step 2: contributing action {a_id!r} is not bound to outcome {outcome_id!r}")

        if op_type in ("resolve", "abandon"):
            target = state.find_slot(outcome_id, slot_id)
            if not target:
                raise PipelineError(f"step 2: slot op targets unknown slot: {slot_id}")
            if target["status"] != "open":
                raise PipelineError(f"step 2: slot op targets non-open slot: {slot_id}")

    # 2. Applying requirement ops to STATE & writing ledger
    new_reqs = []
    for op in req_ops:
        op_type = op["op"]
        req_id = op["req id"]
        
        if op_type == "create":
            fields = op["fields"]
            new_req = {
                "outcome_id": outcome_id,
                "req_id": req_id,
                "text": str(fields["text"]),
                "type": fields["type"],
                "status": "active",
                "creation_action_ids": op["creation action ids"],
                "contributing_action_ids": op["contributing action ids"],
                "implementation_action_ids": op.get("implementation action ids") or [],
                "revise_action_ids": [],
                "related_to": op.get("related to") or [],
                "explicit_or_implicit": op["explicit or implicit"],
                "rationale": op["rationale"],
                "created_at_pair": pair_number,
            }
            state.requirements.append(new_req)
            state.log_operation(pair_number, outcome_id, "create", req_id, "requirement")
            new_reqs.append(new_req)

            # Creation rows -> ledger (score=5.0, kind=creation)
            for a_id in new_req["creation_action_ids"]:
                act = state.get_action(a_id)
                ledger_writer.append({
                    "pair_added": pair_number,
                    "action_id": a_id,
                    "speaker": a_id[0],
                    "role": act["role"],
                    "outcome_id": outcome_id,
                    "req_id": req_id,
                    "score": 5.0,
                    "kind": "creation",
                })

        elif op_type == "revise":
            fields = op["fields"]
            new_req = {
                "outcome_id": outcome_id,
                "req_id": req_id,
                "text": str(fields["text"]),
                "type": fields["type"],
                "status": "active",
                "creation_action_ids": op["creation action ids"],
                "contributing_action_ids": op["contributing action ids"],
                "implementation_action_ids": op.get("implementation action ids") or [],
                "revise_action_ids": [],
                "related_to": op.get("related to") or [],
                "explicit_or_implicit": op["explicit or implicit"],
                "rationale": op["rationale"],
                "created_at_pair": pair_number,
            }
            # mark parents as revised
            for parent_id in new_req["related_to"]:
                parent_req = state.find_requirement(outcome_id, parent_id)
                if parent_req:
                    parent_req["status"] = "revised"
                    state.log_operation(pair_number, outcome_id, "revise", parent_id, "requirement")
            
            state.requirements.append(new_req)
            state.log_operation(pair_number, outcome_id, "create", req_id, "requirement")
            new_reqs.append(new_req)

            # Creation rows -> ledger (score=5.0, kind=creation)
            for a_id in new_req["creation_action_ids"]:
                act = state.get_action(a_id)
                ledger_writer.append({
                    "pair_added": pair_number,
                    "action_id": a_id,
                    "speaker": a_id[0],
                    "role": act["role"],
                    "outcome_id": outcome_id,
                    "req_id": req_id,
                    "score": 5.0,
                    "kind": "creation",
                })

        elif op_type == "delete":
            target = state.find_requirement(outcome_id, req_id)
            target["status"] = "deleted"
            state.log_operation(pair_number, outcome_id, "delete", req_id, "requirement")

    # 3. Applying open_slot ops to STATE
    for op in slot_ops:
        op_type = op["op"]
        slot_id = op["slot id"]

        if op_type == "open_slot":
            fields = op["fields"]
            new_slot = {
                "slot_id": slot_id,
                "outcome_id": outcome_id,
                "text": str(fields["text"]),
                "type": fields["type"],
                "origin": op["origin"],
                "status": "open",
                "creation_action_ids": op["creation action ids"],
                "contributing_action_ids": op["contributing action ids"],
                "resolved_into": None,
            }
            state.slots.append(new_slot)
            state.run["slot_opened_at_pair"][f"{outcome_id}||{slot_id}"] = pair_number
            state.log_operation(pair_number, outcome_id, "open_slot", slot_id, "slot")

        elif op_type == "resolve":
            target = state.find_slot(outcome_id, slot_id)
            target["status"] = "resolved"
            state.log_operation(pair_number, outcome_id, "resolve", slot_id, "slot")

        elif op_type == "abandon":
            target = state.find_slot(outcome_id, slot_id)
            target["status"] = "abandoned"
            state.log_operation(pair_number, outcome_id, "abandon", slot_id, "slot")

    # 4. Link resolved slots to requirements
    for slot in state.slots_for_outcome(outcome_id):
        if slot["status"] == "resolved" and slot["resolved_into"] is None:
            for req in new_reqs:
                if slot["slot_id"] in req.get("related_to", []):
                    slot["resolved_into"] = req["req_id"]
                    break
            if slot["resolved_into"] is None:
                raise PipelineError(
                    f"step 2: slot {slot['slot_id']} resolved but no active requirement in this pair references it in 'related_to'"
                )

    # 5. Disjointness check: no action ID justifies both active req and open slot
    active_req_actions = set()
    for r in state.requirements_for_outcome(outcome_id):
        if r["status"] == "active":
            active_req_actions.update(r["creation_action_ids"])
            active_req_actions.update(r["contributing_action_ids"])

    open_slot_actions = set()
    for s in state.slots_for_outcome(outcome_id, status="open"):
        open_slot_actions.update(s["creation_action_ids"])
        open_slot_actions.update(s["contributing_action_ids"])

    overlap = active_req_actions & open_slot_actions
    if overlap:
        raise PipelineError(f"step 2: action/slot action overlap in outcome {outcome_id}: {overlap}")

    return new_reqs


def run_level2(client, config, state, ledger_writer, pair_number, new_actions):
    """Level 2 iteration mechanism (§9.2):
    1. 3-pair abandonment sweep.
    2. Determine touched outcomes.
    3. Run Step 2 for each touched outcome.
    4. Return the list of newly created or resolved requirements (needed for Step 3 Trigger A).
    """
    # 1. 3-pair abandonment sweep
    for slot in list(state.slots):
        if slot["status"] == "open":
            slot_key = f"{slot['outcome_id']}||{slot['slot_id']}"
            opened_pair = state.run["slot_opened_at_pair"].get(slot_key)
            if opened_pair is not None and (pair_number - opened_pair) >= 3:
                slot["status"] = "abandoned"
                state.log_operation(pair_number, slot["outcome_id"], "abandon", slot["slot_id"], "slot")

    # 2. Determine touched outcomes
    touched_outcomes = set()
    for action in new_actions:
        oid = state.run["action_to_outcome"].get(action["id"])
        if oid:
            touched_outcomes.add(oid)

    sorted_touched = sorted(touched_outcomes)

    # 3. Run Step 2 per touched outcome
    all_new_reqs = []
    for outcome_id in sorted_touched:
        new_reqs = step_2(client, config, state, ledger_writer, pair_number, outcome_id)
        all_new_reqs.extend(new_reqs)

    return all_new_reqs


# ------------------------------------------------------------ orchestration

def run_level1(client, config, state, pair_number, user_text, ai_text):
    """§9.1: 1a → 1b → 1c for one pair. Returns the new actions (the pair's
    slice, which Level 2 uses to find touched outcomes).
    """
    new_actions = step_1a(client, config, state, pair_number, user_text, ai_text)
    step_1b(client, config, state, pair_number)
    step_1c(client, config, state, pair_number)
    return new_actions
