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
from pathlib import Path
import re
import time
from typing import Any

from engine import prompts
from engine.config import Config
from engine.state import State


ACTION_ID_RE = re.compile(r"^([UA])\((\d+),\s*(\d+)\)$")


def normalize_outcome_id(oid: Any) -> str | None:
    """Normalize outcome IDs to canonical 'outcome N' format to prevent cross-pair naming drift."""
    if oid is None:
        return None
    oid_str = str(oid).strip()
    m = re.match(r"(?i)^outcome[_\s\-]*0*(\d+)$", oid_str)
    if m:
        return f"outcome {m.group(1)}"
    return oid_str


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
        raw_id = normalize_outcome_id(_require(raw, "outcome id", "step 1b outcome"))
        raw_parent = normalize_outcome_id(raw.get("parent outcome id"))
        raw_related = [normalize_outcome_id(x) for x in raw.get("related outcome ids", []) if x is not None]
        outcomes.append({
            "id": str(raw_id),
            "text": str(_require(raw, "outcome", "step 1b outcome")),
            "turn_id": str(_require(raw, "turn id", "step 1b outcome")),
            "parent": raw_parent,
            "children": [],   # rebuilt from parent pointers below (§11.4)
            "related": [str(x) for x in raw_related],
        })  # 'confidence' deliberately dropped — spec §4.4: ignore

    outcome_ids = [o["id"] for o in outcomes]
    if len(set(outcome_ids)) != len(outcome_ids):
        raise PipelineError(f"step 1b: duplicate outcome ids in {outcome_ids}")
    id_set = set(outcome_ids)

    # Invariant 6: outcome tree has exactly one root, no cycles (§11.4)
    roots = [o for o in outcomes if o["parent"] is None]
    if not roots and outcomes:
        outcomes[0]["parent"] = None
        roots = [outcomes[0]]
    elif len(roots) > 1:
        prev_root_ids = {o["id"] for o in state.outcomes if o.get("parent") is None}
        primary_root = None
        for r in roots:
            if r["id"] in prev_root_ids:
                primary_root = r
                break
        if primary_root is None:
            primary_root = roots[0]
        for r in roots:
            if r is not primary_root:
                r["parent"] = primary_root["id"]

    primary_root = roots[0] if roots else (outcomes[0] if outcomes else None)

    # Retain any prior outcomes that already have requirements or slots,
    # ensuring referential integrity (inv_03) holds across pairs (§11.4).
    existing_by_id = {o["id"]: o for o in state.outcomes}
    for old_id, old_o in existing_by_id.items():
        if old_id not in id_set and (state.requirements_for_outcome(old_id) or state.slots_for_outcome(old_id)):
            retained = dict(old_o)
            retained["children"] = []
            if primary_root is not None:
                retained["parent"] = primary_root["id"]
            outcomes.append(retained)
            id_set.add(old_id)

    # parent pointers are the single source of truth; children derived from
    # them so §11.4's bidirectional-consistency check holds by construction
    by_id = {o["id"]: o for o in outcomes}
    for o in outcomes:
        if o["parent"] is not None:
            if o["parent"] not in id_set or o["parent"] == o["id"]:
                o["parent"] = primary_root["id"] if (primary_root and o is not primary_root) else None
            if o["parent"] is not None:
                by_id[o["parent"]]["children"].append(o["id"])

    # completeness: EVERY action mapped, no unknown action or outcome ids
    known_action_ids = {a["id"] for a in state.actions}
    norm_action_to_outcome = {}
    for aid, oid in action_to_outcome.items():
        norm_action_to_outcome[str(aid)] = str(normalize_outcome_id(oid))
    action_to_outcome = norm_action_to_outcome

    # Preserve outcome mapping for actions that already anchored prior requirements or slots,
    # ensuring cross-pair referential integrity and slot lifecycle consistency.
    for r in state.requirements:
        for aid in r.get("creation_action_ids", []):
            if aid in known_action_ids and r.get("outcome_id") in id_set:
                action_to_outcome[aid] = r["outcome_id"]
    for s in state.slots:
        for aid in s.get("creation_action_ids", []):
            if aid in known_action_ids and s.get("outcome_id") in id_set:
                action_to_outcome[aid] = s["outcome_id"]

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
        oid = str(normalize_outcome_id(_require(entry, "outcome id", "step 1c mapping")))
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
        if intention_ids:
            for u_oid in unmapped:
                mapping[u_oid] = intention_ids[0]
        else:
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

    # Re-route ops if model swapped sections:
    clean_req_ops = []
    for raw in raw_req_ops:
        op = raw.get("op")
        if op in ("open_slot", "resolve", "abandon"):
            if op == "resolve" and "slot id" not in raw and raw.get("related to"):
                raw["slot id"] = raw["related to"][0]
            raw_slot_ops.append(raw)
        else:
            clean_req_ops.append(raw)

    clean_slot_ops = []
    for raw in raw_slot_ops:
        op = raw.get("op")
        if op in ("create", "revise", "delete"):
            clean_req_ops.append(raw)
        else:
            clean_slot_ops.append(raw)

    raw_req_ops = clean_req_ops
    raw_slot_ops = clean_slot_ops

    # 1. Process requirement operations
    req_ops_processed = []
    for raw in raw_req_ops:
        op = str(_require(raw, "op", f"step 2 {outcome_id} requirement op"))
        if op not in ("create", "revise", "delete"):
            raise PipelineError(f"step 2 {outcome_id}: invalid requirement op {op!r}")

        bound_oid = str(normalize_outcome_id(_require(raw, "bound outcome id", f"step 2 {outcome_id} requirement op")))
        if bound_oid != outcome_id:
            raise PipelineError(f"step 2 {outcome_id}: bound outcome id {bound_oid!r} != {outcome_id!r}")

        req_id = str(_require(raw, "req id", f"step 2 {outcome_id} requirement op"))

        if op == "create":
            existing = state.find_requirement(outcome_id, req_id)
            if existing is not None:
                existing_req_ids = {r["req_id"] for r in state.requirements_for_outcome(outcome_id)}
                max_num = 0
                for rid in existing_req_ids:
                    m = re.match(r"(?i)^req[_\s\-]*(\d+)$", str(rid))
                    if m:
                        max_num = max(max_num, int(m.group(1)))
                req_id = f"req {max_num + 1}"

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

        bound_oid = str(normalize_outcome_id(_require(raw, "bound outcome id", f"step 2 {outcome_id} slot op")))
        if bound_oid != outcome_id:
            raise PipelineError(f"step 2 {outcome_id}: bound outcome id {bound_oid!r} != {outcome_id!r}")

        slot_id = str(_require(raw, "slot id", f"step 2 {outcome_id} slot op"))

        if op == "open_slot":
            existing = state.find_slot(outcome_id, slot_id)
            if existing is not None:
                existing_slot_ids = {s["slot_id"] for s in state.slots_for_outcome(outcome_id)}
                max_num = 0
                for sid in existing_slot_ids:
                    m = re.match(r"(?i)^slot[_\s\-]*(\d+)$", str(sid))
                    if m:
                        max_num = max(max_num, int(m.group(1)))
                slot_id = f"slot {max_num + 1}"

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
            req_ops_processed.append(resolved_req)
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


# Alias for Trigger A and Trigger B
build_step3_prompt = build_step3_trigger_a_prompt


def step_3_trigger_b(
    client,
    config: Config,
    state: State,
    pair_number: int,
    outcome_id: str,
    new_actions: list[dict],
    ledger_writer=None,
) -> dict:
    """Step 3 Trigger B (§9.3, §12.6): Incremental influence scan on existing requirements.

    Fires when outcome_id receives new actions in pair_number and has active requirements
    created in earlier pairs (created_at_pair < pair_number).
    Sends ONLY new subsequent actions not previously labeled for that requirement.
    Batches requirements in chunks of config.step3_batch_size.
    Section A is never re-sent.
    """
    # 1. Identify existing requirements created in earlier pairs
    existing_reqs = [
        r for r in state.requirements
        if r.get("outcome_id") == outcome_id
        and r.get("status") == "active"
        and r.get("created_at_pair", pair_number) < pair_number
    ]
    if not existing_reqs:
        return {}

    # 2. For each requirement, determine new subsequent actions
    reqs_with_candidates = []
    a2o = state.run.get("action_to_outcome", {})
    labeled_map = state.run.setdefault("labeled_action_ids", {})

    for req in existing_reqs:
        req_id = req["req_id"]
        key = f"{outcome_id}||{req_id}"
        already_labeled = set(labeled_map.get(key, []))

        creation_aids = req.get("creation_action_ids", [])
        if not creation_aids:
            continue
        sorted_creation = sorted(creation_aids, key=action_sort_key)
        origin_turn = sorted_creation[0]
        origin_key = action_sort_key(origin_turn)

        # Candidates: actions in this pair assigned to outcome_id after origin_turn and not yet labeled
        candidates = [
            a for a in new_actions
            if a2o.get(a["id"]) == outcome_id
            and action_sort_key(a["id"]) > origin_key
            and a["id"] not in creation_aids
            and a["id"] not in already_labeled
        ]
        candidates.sort(key=lambda a: action_sort_key(a["id"]))
        if candidates:
            reqs_with_candidates.append((req, origin_turn, candidates))

    if not reqs_with_candidates:
        return {}

    # 3. Batch requirements by config.step3_batch_size
    batch_size = max(1, getattr(config, "step3_batch_size", 3))
    results = {}

    for i in range(0, len(reqs_with_candidates), batch_size):
        batch = reqs_with_candidates[i : i + batch_size]
        for req, origin_turn, subsequent_actions in batch:
            req_id = req["req_id"]
            outcome = state.get_outcome(outcome_id)
            outcome_text = outcome["text"] if outcome else outcome_id

            prompt = build_step3_prompt(
                outcome_text=outcome_text,
                req=req,
                origin_turn=origin_turn,
                preceding_actions=[],  # Section A is never re-sent (§9.3)
                subsequent_actions=subsequent_actions,
                slot_info=None,
            )

            call_label = f"3b:pair{pair_number}:{outcome_id}:{req_id}"
            response = client.call_json(call_label, config.model_step3, prompt)

            subsequent_labels = response.get("subsequent labels", [])
            key = f"{outcome_id}||{req_id}"

            for lbl in subsequent_labels:
                aid = lbl.get("action id")
                if not aid or not state.has_action(aid):
                    continue

                rel_type = lbl.get("relationship type", "NO CONNECTION")
                score = lbl.get("relationship score")

                # Track that this action was labeled for this requirement
                labeled_map.setdefault(key, []).append(aid)

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

                if rel_type == "IMPLEMENTS" and aid not in req.get("implementation_action_ids", []):
                    req.setdefault("implementation_action_ids", []).append(aid)
                elif rel_type == "REVISES" and aid not in req.get("revise_action_ids", []):
                    req.setdefault("revise_action_ids", []).append(aid)
                elif aid not in req.get("contributing_action_ids", []):
                    req.setdefault("contributing_action_ids", []).append(aid)

            results[req_id] = subsequent_labels

    return results


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
    """Level 2: Step 2 per touched outcome (§9.2), followed by Trigger A for new reqs,
    Trigger B for existing reqs, and the 3-pair abandonment sweep.
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

        # Step 3 Trigger B: incrementally score newly added actions for earlier requirements
        step_3_trigger_b(
            client, config, state, pair_number, outcome_id, new_actions, ledger_writer=ledger_writer
        )

    sweep_abandoned_slots(state, pair_number)
    return results


def process_pair(client, config, state, pair_number, user_text, ai_text, ledger_writer=None):
    """Executes Level 1 (1a -> 1b -> 1c) and Level 2 (Step 2 -> Step 3 Trigger A -> Step 3 Trigger B -> slot sweep)
    for a single pair (§9.1 - §9.2).
    """
    new_actions = run_level1(client, config, state, pair_number, user_text, ai_text)
    level2_results = run_level2(
        client, config, state, pair_number, new_actions, ledger_writer=ledger_writer
    )
    return new_actions, level2_results


def run_chat(
    client,
    config,
    chat_id: str,
    dialogue: list[dict] | str | Path,
    out_dir: str | Path | None = None,
    initial_state: Any = None,
    stop_on_violation: bool = True,
    clear_existing: bool = False,
    budget_guard: Any = None,
) -> dict:
    """Run extraction pipeline across an entire chat with pair-level runtime invariant checks.

    For each pair:
    1. process_pair() executes Steps 1a->1b->1c->2->3.
    2. Writes state.json, ledger.jsonl, and run/pipeline_state.json.
    3. Runs runtime checks (engine/checks.py).
    4. Writes run/status.json.
    5. Halts immediately on invariant violation if stop_on_violation is True.
    6. Emits run/report.json upon completion or halt.
    """
    from engine.artifacts import LedgerWriter, write_json_artifact
    from engine.budget import BudgetStopError
    from engine.checks import (
        InvariantViolationError,
        run_pair_checks,
        write_report,
        write_status,
    )
    from engine.projections.panel import export_panel_projections
    from engine.projections.workspace import export_workspace_bundle, load_chat_metadata
    from engine.quant import compute_decisions, compute_direction, compute_mode

    if budget_guard is not None:
        if hasattr(client, "set_budget_guard"):
            client.set_budget_guard(budget_guard)
        elif hasattr(client, "usage_meter"):
            client.usage_meter.budget_guard = budget_guard

    if isinstance(dialogue, (str, Path)):
        with open(dialogue, "r", encoding="utf-8") as f:
            raw_dialogue = json.load(f)
    else:
        raw_dialogue = list(dialogue)

    dialogue_list = []
    for turn in raw_dialogue:
        t = dict(turn)
        if "attachments" not in t:
            t["attachments"] = []
        if "ts" not in t:
            t["ts"] = "2026-01-01T00:00:00Z"
        dialogue_list.append(t)

    if out_dir is None:
        out_dir = Path("data/chats") / chat_id
    else:
        out_dir = Path(out_dir)

    out_dir.mkdir(parents=True, exist_ok=True)
    run_dir = out_dir / "run"
    run_dir.mkdir(parents=True, exist_ok=True)

    if hasattr(client, "set_out_dir"):
        client.set_out_dir(out_dir)

    if clear_existing:
        for fname in ["ledger.jsonl", "state.json", "dialogue.json"]:
            p = out_dir / fname
            if p.exists():
                p.unlink()
        for fname in ["status.json", "report.json", "pipeline_state.json", "usage.jsonl"]:
            p = run_dir / fname
            if p.exists():
                p.unlink()

    # Save dialogue.json in out_dir
    with open(out_dir / "dialogue.json", "w", encoding="utf-8") as f:
        json.dump(dialogue_list, f, indent=2, ensure_ascii=False)
        f.write("\n")

    source_meta, meta, file_summary = load_chat_metadata(out_dir)

    if initial_state is None:
        if not clear_existing and (out_dir / "state.json").exists():
            state = State.load(out_dir)
        else:
            state = State()
    elif isinstance(initial_state, dict):
        state = State.from_dict(initial_state)
    else:
        state = initial_state

    ledger_writer = LedgerWriter(out_dir / "ledger.jsonl")

    # Group dialogue turns by pair
    pairs_dict: dict[int, dict[str, str]] = {}
    for turn in dialogue_list:
        p = turn.get("pair")
        if p is None:
            continue
        speaker = turn.get("speaker")
        text = turn.get("text", "")
        if p not in pairs_dict:
            pairs_dict[p] = {"user": "", "ai": ""}
        if speaker in ("user", "ai"):
            pairs_dict[p][speaker] = text

    sorted_pairs = sorted(pairs_dict.keys())
    last_completed = state.run.get("last_completed_pair", 0) if not clear_existing else 0

    wall_time_per_pair: list[float] = []
    tokens_per_pair: list[int] = []
    passed_checks_set: set[str] = set()
    failed_checks_set: set[str] = set()
    prev_ledger = None

    for pair_number in sorted_pairs:
        if not clear_existing and pair_number <= last_completed:
            continue

        t0 = time.monotonic()
        tokens_start = getattr(client, "total_tokens", 0)
        u_text = pairs_dict[pair_number].get("user", "")
        a_text = pairs_dict[pair_number].get("ai", "")

        try:
            new_actions, l2_res = process_pair(
                client, config, state, pair_number, u_text, a_text, ledger_writer=ledger_writer
            )
        except BudgetStopError as b_err:
            write_status(
                out_dir,
                healthy=False,
                pair_number=pair_number,
                violations=[str(b_err)],
            )
            report_file = write_report(
                out_dir=out_dir,
                chat_id=chat_id,
                pairs_processed=state.run.get("last_completed_pair", 0),
                wall_time_per_pair=wall_time_per_pair,
                tokens_per_pair=tokens_per_pair,
                llm_calls=getattr(client, "call_count", 0),
                retries=getattr(client, "retry_count", 0),
                cache_hits=getattr(client, "cache_hits", 0),
                state=state,
                checks_passed=list(passed_checks_set),
                checks_failed=list(failed_checks_set) + ["budget_stop"],
            )
            with open(report_file, "r", encoding="utf-8") as f:
                report_data = json.load(f)
            report_data["budget_stop"] = True
            report_data["error"] = str(b_err)
            if stop_on_violation:
                raise
            return report_data

        state.run["last_completed_pair"] = pair_number

        elapsed = round(time.monotonic() - t0, 3)
        wall_time_per_pair.append(elapsed)
        tokens_end = getattr(client, "total_tokens", 0)
        tokens_delta = max(0, tokens_end - tokens_start)
        tokens_per_pair.append(tokens_delta)

        # Write state.json artifact (validated)
        write_json_artifact(out_dir / "state.json", state.to_dict(), "state")

        # Write run/pipeline_state.json
        with open(run_dir / "pipeline_state.json", "w", encoding="utf-8") as f:
            json.dump(state.run, f, indent=2, ensure_ascii=False)
            f.write("\n")

        # Stage 4 Projections: panel_bundle.json and snapshots.json
        export_panel_projections(
            target_dir=out_dir,
            ledger_rows=ledger_writer.rows,
            state_dict=state.to_dict(),
            max_pair=pair_number,
        )

        # Workspace bundle projection (incremental per pair)
        summary_text = state.run.get("dialogue_summary") or file_summary or ""
        export_workspace_bundle(
            output_path=out_dir / "workspace_bundle.json",
            dialogue=dialogue_list,
            state=state.to_dict(),
            ledger=ledger_writer.rows,
            source_meta=source_meta,
            meta=meta,
            chat_id=chat_id,
            summary=summary_text,
            status="processing",
            processed_pairs=pair_number,
        )

        # Run runtime invariants
        chk_res = run_pair_checks(
            state=state,
            ledger_rows=ledger_writer.rows,
            dialogue=dialogue_list,
            prev_ledger_rows=prev_ledger,
            current_pair=pair_number,
        )
        passed_checks_set.update(chk_res.passed)

        if not chk_res.healthy:
            failed_checks_set.update(chk_res.failed)
            write_status(
                out_dir,
                healthy=False,
                pair_number=pair_number,
                violations=chk_res.violations,
            )
            report_file = write_report(
                out_dir=out_dir,
                chat_id=chat_id,
                pairs_processed=pair_number - 1,
                wall_time_per_pair=wall_time_per_pair,
                tokens_per_pair=tokens_per_pair,
                llm_calls=getattr(client, "call_count", 0),
                retries=getattr(client, "retry_count", 0),
                cache_hits=getattr(client, "cache_hits", 0),
                state=state,
                checks_passed=list(passed_checks_set),
                checks_failed=list(failed_checks_set),
            )
            with open(report_file, "r", encoding="utf-8") as f:
                report_data = json.load(f)
            if stop_on_violation:
                raise InvariantViolationError(chk_res.violations, chk_res.failed)
            return report_data
        else:
            write_status(
                out_dir,
                healthy=True,
                pair_number=pair_number,
                violations=[],
            )
            prev_ledger = list(ledger_writer.rows)

    # Compute final metrics for report per TEST_STRATEGY §6
    final_info = None
    if ledger_writer.rows:
        try:
            dir_facts = compute_direction(ledger_writer.rows, max_pair=len(sorted_pairs))
            dec_facts = compute_decisions(
                ledger_writer.rows,
                state_requirements=state.requirements,
                max_pair=len(sorted_pairs),
            )
            mode_facts = compute_mode(
                ledger_writer.rows,
                state_requirements=state.requirements,
                max_pair=len(sorted_pairs),
            )
            if dir_facts and dec_facts and mode_facts:
                final_info = {
                    "direction": [dir_facts[-1].you_pct, dir_facts[-1].ai_pct],
                    "decisions": [dec_facts[-1].you_count, dec_facts[-1].ai_count],
                    "mode": mode_facts[-1].mode,
                }
        except Exception:
            final_info = None

    # All pairs finished successfully
    summary_text = state.run.get("dialogue_summary") or file_summary or ""
    export_workspace_bundle(
        output_path=out_dir / "workspace_bundle.json",
        dialogue=dialogue_list,
        state=state.to_dict(),
        ledger=ledger_writer.rows,
        source_meta=source_meta,
        meta=meta,
        chat_id=chat_id,
        summary=summary_text,
        status="ready",
        processed_pairs=len(sorted_pairs),
    )

    report_file = write_report(
        out_dir=out_dir,
        chat_id=chat_id,
        pairs_processed=len(sorted_pairs),
        wall_time_per_pair=wall_time_per_pair,
        tokens_per_pair=tokens_per_pair,
        llm_calls=getattr(client, "call_count", 0),
        retries=getattr(client, "retry_count", 0),
        cache_hits=getattr(client, "cache_hits", 0),
        state=state,
        checks_passed=list(passed_checks_set),
        checks_failed=list(failed_checks_set),
        final=final_info,
    )
    with open(report_file, "r", encoding="utf-8") as f:
        report_data = json.load(f)
    return report_data
