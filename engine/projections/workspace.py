"""Workspace bundle projection layer.

Transforms engine artifacts (dialogue, state, ledger, source_meta, meta) into
the normalized workspace_bundle.json contract consumed by the UI.
Adheres strictly to STANDALONE_V1_PLAN §3.1 and web/src/workspace/types.ts.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from engine.artifacts import write_json_artifact


def _pair_of(action_or_turn_id: str | None) -> int:
    """Extract pair index from action id or turn id string (e.g. 'U(3,1)' -> 3)."""
    if not action_or_turn_id:
        return 1
    m = re.search(r"\((\d+),", str(action_or_turn_id))
    return int(m.group(1)) if m else 1


def _speaker_party(action_id: str | None) -> str:
    """Return 'human' if action begins with 'U', else 'ai'."""
    s = str(action_id or "")
    return "human" if s.startswith("U") else "ai"


def _seq_of(action_id: str | None) -> int:
    """Extract action sequence index within a pair (e.g. 'A(1,5)' -> 5)."""
    m = re.search(r",(\d+)\)", str(action_id or ""))
    return int(m.group(1)) if m else 0


def compute_outcome_layout(nodes: list[dict[str, Any]], root_id: str) -> dict[str, tuple[float, float]]:
    """Compute deterministic layout coordinates for outcomes.

    - Root outcome is placed at (0.0, 0.0).
    - Child outcomes are placed on concentric rings by tree depth (radius = 160.0 * depth).
    - Angular positions are distributed evenly by birth order, with a deterministic phase
      jitter seeded by outcome id hash so repeated runs give byte-identical results.
    """
    parent_map = {n["id"]: n.get("parent") for n in nodes}
    depth_map: dict[str, int] = {}

    def get_depth(nid: str) -> int:
        if nid == root_id or parent_map.get(nid) is None:
            return 0 if nid == root_id else 1
        if nid in depth_map:
            return depth_map[nid]
        p = parent_map.get(nid)
        d = 1 + get_depth(p) if p else 1
        depth_map[nid] = d
        return d

    nodes_by_depth: dict[int, list[dict[str, Any]]] = {}
    for n in nodes:
        if n["id"] == root_id:
            continue
        d = get_depth(n["id"])
        nodes_by_depth.setdefault(d, []).append(n)

    coords: dict[str, tuple[float, float]] = {root_id: (0.0, 0.0)}

    for d, d_nodes in sorted(nodes_by_depth.items()):
        # Sort by birth order, tie-breaking by outcome id
        d_nodes.sort(key=lambda item: (item.get("born", 1), item["id"]))
        k_count = len(d_nodes)
        ring_radius = 160.0 * d

        for i, node in enumerate(d_nodes):
            nid = node["id"]
            h = int(hashlib.sha256(nid.encode("utf-8")).hexdigest()[:6], 16)
            seed_jitter = ((h % 1000) / 1000.0 - 0.5) * (0.2 * (2.0 * math.pi / max(k_count, 1)))
            angle = (2.0 * math.pi * i / max(k_count, 1)) + seed_jitter
            x = round(ring_radius * math.cos(angle), 1)
            y = round(ring_radius * math.sin(angle), 1)
            coords[nid] = (x, y)

    return coords


def project_workspace(
    dialogue: list[dict[str, Any]],
    state: dict[str, Any] | Any,
    ledger: list[dict[str, Any]],
    source_meta: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
    chat_id: str | None = None,
    summary: str | None = None,
    status: str = "ready",
    source: dict[str, Any] | None = None,
    processed_pairs: int | None = None,
    flagged_pairs: list[Any] | None = None,
) -> dict[str, Any]:
    """Pure, deterministic projection from engine artifacts into a workspace bundle."""
    source_meta = source_meta or {}
    meta = meta or {}

    # 1. Resolve State containers
    outcomes = state.outcomes if hasattr(state, "outcomes") else state.get("outcomes", [])
    requirements = state.requirements if hasattr(state, "requirements") else state.get("requirements", [])
    slots = state.slots if hasattr(state, "slots") else state.get("slots", [])
    operations_log = state.operations_log if hasattr(state, "operations_log") else state.get("operations_log", [])
    actions_list = state.actions if hasattr(state, "actions") else state.get("actions", [])
    actions_by_id = {x["id"]: x for x in actions_list if isinstance(x, dict) and "id" in x}

    # 2. Total pairs count
    total_pairs = max((t.get("pair", 1) for t in dialogue), default=0)

    # 3. Identify Root outcome
    root_outcome = next((o for o in outcomes if o.get("parent") is None), None)
    if root_outcome is None and outcomes:
        root_outcome = outcomes[0]
    root_id = root_outcome["id"] if root_outcome else ""
    root_title = root_outcome.get("text", "") if root_outcome else ""

    # 4. Build Nodes with birth tracking and deterministic coordinates
    preliminary_nodes: list[dict[str, Any]] = []
    for o in outcomes:
        oid = o["id"]
        is_root = (oid == root_id)
        related_rows = [r for r in ledger if r.get("outcome_id") == oid]
        op_pairs = [x["pair"] for x in operations_log if x.get("outcome_id") == oid and "pair" in x]
        birth_candidates = [r["pair_added"] for r in related_rows if "pair_added" in r] + op_pairs + [_pair_of(o.get("turn_id"))]
        birth = min(birth_candidates) if birth_candidates else 1
        born = 1 if is_root else birth

        related_birth_actions = [r["action_id"] for r in related_rows if r.get("pair_added") == birth and "action_id" in r]
        first_aid = related_birth_actions[0] if related_birth_actions else o.get("turn_id", "U")
        source_speaker = _speaker_party(first_aid)

        preliminary_nodes.append({
            "id": oid,
            "title": o.get("text", ""),
            "parent": o.get("parent"),
            "related": list(o.get("related", [])),
            "born": born,
            "root": is_root,
            "sourcePair": born,
            "sourceSpeaker": source_speaker,
        })

    layout_coords = compute_outcome_layout(preliminary_nodes, root_id)
    final_nodes: list[dict[str, Any]] = []
    for n in preliminary_nodes:
        x, y = layout_coords.get(n["id"], (0.0, 0.0))
        final_nodes.append({
            "id": n["id"],
            "title": n["title"],
            "parent": n["parent"],
            "related": n["related"],
            "born": n["born"],
            "x": x,
            "y": y,
            "root": n["root"],
            "sourcePair": n["sourcePair"],
            "sourceSpeaker": n["sourceSpeaker"],
        })

    # 5. Build Atoms (requirements + slots)
    atoms: list[dict[str, Any]] = []
    for r in requirements:
        creation_ids = r.get("creation_action_ids") or ["U(1,1)"]
        origin_aid = creation_ids[0]
        born = r.get("created_at_pair", _pair_of(origin_aid))

        # Check for resolving ancestor slot
        ancestors = [
            s for s in slots
            if s.get("outcome_id") == r.get("outcome_id") and s.get("slot_id") in r.get("related_to", [])
        ]
        slot = ancestors[0] if ancestors else None
        slot_creation_aid = (slot.get("creation_action_ids") or ["A(1,1)"])[0] if slot else origin_aid

        deleted_candidates = [
            x["pair"] for x in operations_log
            if x.get("outcome_id") == r.get("outcome_id")
            and x.get("target_id") == r.get("req_id")
            and x.get("target_type") == "requirement"
            and x.get("op") == "delete"
            and "pair" in x
        ]
        end_pair = min(deleted_candidates) if deleted_candidates else (total_pairs + 1)

        atoms.append({
            "id": f"{r['outcome_id']}:{r['req_id']}",
            "nodeId": r["outcome_id"],
            "kind": "resolved" if slot else "requirement",
            "text": r.get("text", ""),
            "question": slot.get("text") if slot else None,
            "origin": _speaker_party(slot_creation_aid),
            "resolver": _speaker_party(origin_aid),
            "born": born,
            "end": end_pair,
            "sourcePair": _pair_of(origin_aid),
            "sourceSpeaker": _speaker_party(origin_aid),
            "quote": actions_by_id.get(origin_aid, {}).get("evidence_quote", ""),
            "choices": list(slot.get("choices", [])) if slot else [],
        })

    for s in slots:
        aid = (s.get("creation_action_ids") or ["A(1,1)"])[0]
        end_candidates = [
            x["pair"] for x in operations_log
            if x.get("outcome_id") == s.get("outcome_id")
            and x.get("target_id") == s.get("slot_id")
            and x.get("target_type") == "slot"
            and x.get("op") in ("resolve", "abandon")
            and "pair" in x
        ]
        end_pair = min(end_candidates) if end_candidates else (total_pairs + 1)

        atoms.append({
            "id": f"{s['outcome_id']}:{s['slot_id']}",
            "nodeId": s["outcome_id"],
            "kind": "question",
            "text": s.get("text", ""),
            "question": None,
            "origin": _speaker_party(aid),
            "resolver": None,
            "born": _pair_of(aid),
            "end": end_pair,
            "sourcePair": _pair_of(aid),
            "sourceSpeaker": _speaker_party(aid),
            "quote": actions_by_id.get(aid, {}).get("evidence_quote", ""),
            "choices": list(s.get("choices", [])),
        })

    # 6. Build Snapshots
    node_ids = [n["id"] for n in final_nodes]
    snapshots: list[dict[str, Any]] = []
    for p in range(1, total_pairs + 1):
        mass = {nid: {"human": 0.0, "ai": 0.0, "delta": 0.0} for nid in node_ids}
        for r in ledger:
            pa = r.get("pair_added", 1)
            oid = r.get("outcome_id")
            if pa <= p and oid in mass:
                score = float(r.get("score", 0.0))
                speaker = r.get("speaker", "U")
                if speaker == "U":
                    mass[oid]["human"] += score
                else:
                    mass[oid]["ai"] += score
                if pa == p:
                    mass[oid]["delta"] += score

        # Clean integer-like floats to ints for tidy output
        for m_val in mass.values():
            if m_val["human"].is_integer():
                m_val["human"] = int(m_val["human"])
            if m_val["ai"].is_integer():
                m_val["ai"] = int(m_val["ai"])
            if m_val["delta"].is_integer():
                m_val["delta"] = int(m_val["delta"])

        # Determine terminal outcome at pair p
        ai_rows = [r for r in ledger if r.get("pair_added") == p and r.get("speaker") == "A"]
        ai_rows.sort(key=lambda r: _seq_of(r.get("action_id")))
        terminal = ai_rows[-1]["outcome_id"] if ai_rows else root_id

        snapshots.append({
            "pair": p,
            "mass": mass,
            "terminal": terminal,
        })

    # 7. Metadata Resolution
    # ID
    cid = chat_id or source_meta.get("chat_id") or source_meta.get("id") or "chat"

    # Title
    resolved_title = source_meta.get("title") or source_meta.get("source_title")
    if not resolved_title:
        user_msgs = [t.get("text", "") for t in dialogue if t.get("speaker") == "user"]
        resolved_title = user_msgs[0][:42] if user_msgs else "Untitled Conversation"

    # Category
    resolved_cat = meta.get("category") or meta.get("task_type") or "Uncategorised"
    if isinstance(resolved_cat, str):
        resolved_cat = resolved_cat.title()

    # Summary
    if summary is not None:
        resolved_summary = str(summary)
    elif source_meta.get("summary"):
        resolved_summary = str(source_meta["summary"])
    elif source_meta.get("dialogue_summary"):
        resolved_summary = str(source_meta["dialogue_summary"])
    else:
        run_state = state.get("run", {}) if isinstance(state, dict) else getattr(state, "run", {})
        resolved_summary = run_state.get("dialogue_summary", "") if isinstance(run_state, dict) else ""

    # Source
    if source is not None:
        final_source = dict(source)
    else:
        platform = source_meta.get("source_kind") or source_meta.get("platform") or "archive"
        final_source = {"platform": platform}
        if "imported_at" in source_meta:
            final_source["importedAt"] = source_meta["imported_at"]
        if "source_link" in source_meta:
            final_source["conversationId"] = source_meta["source_link"]
        elif "chat_id" in source_meta:
            final_source["conversationId"] = source_meta["chat_id"]

    bundle: dict[str, Any] = {
        "id": cid,
        "title": resolved_title,
        "rootTitle": root_title,
        "category": resolved_cat,
        "totalPairs": total_pairs,
        "dialogue": [
            {
                "pair": t["pair"],
                "speaker": t["speaker"],
                "text": t["text"],
                "attachments": list(t.get("attachments", [])),
                "ts": t["ts"],
            }
            for t in dialogue
        ],
        "nodes": final_nodes,
        "atoms": atoms,
        "snapshots": snapshots,
        "summary": resolved_summary,
        "status": status,
        "source": final_source,
    }

    if processed_pairs is not None:
        bundle["processedPairs"] = processed_pairs
    if flagged_pairs is not None:
        bundle["flaggedPairs"] = flagged_pairs

    return bundle


def export_workspace_bundle(
    output_path: str | Path,
    dialogue: list[dict[str, Any]],
    state: dict[str, Any] | Any,
    ledger: list[dict[str, Any]],
    source_meta: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
    chat_id: str | None = None,
    summary: str | None = None,
    status: str = "ready",
    source: dict[str, Any] | None = None,
    processed_pairs: int | None = None,
    flagged_pairs: list[Any] | None = None,
) -> dict[str, Any]:
    """Project and write a validated workspace_bundle.json artifact."""
    bundle = project_workspace(
        dialogue=dialogue,
        state=state,
        ledger=ledger,
        source_meta=source_meta,
        meta=meta,
        chat_id=chat_id,
        summary=summary,
        status=status,
        source=source,
        processed_pairs=processed_pairs,
        flagged_pairs=flagged_pairs,
    )
    write_json_artifact(output_path, bundle, "workspace_bundle")
    return bundle


def load_chat_metadata(chat_dir: str | Path) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Resolve source_meta, meta, and summary from chat directory or fallback corpus."""
    chat_path = Path(chat_dir)
    cid = chat_path.name
    repo_root = Path(__file__).resolve().parent.parent.parent

    source_meta: dict[str, Any] = {}
    meta: dict[str, Any] = {}
    summary: str = ""

    # 1. source_meta
    for sm_path in [
        chat_path / "source_meta.json",
        repo_root / "data" / "corpus" / cid / "source_meta.json",
    ]:
        if sm_path.exists():
            try:
                source_meta = json.loads(sm_path.read_text(encoding="utf-8"))
                break
            except Exception:
                pass

    # 2. meta (JSON or YAML)
    for m_path in [
        chat_path / "meta.json",
        repo_root / "data" / "corpus" / cid / "meta.json",
    ]:
        if m_path.exists():
            try:
                meta = json.loads(m_path.read_text(encoding="utf-8"))
                break
            except Exception:
                pass
    if not meta:
        for my_path in [
            chat_path / "meta.yaml",
            repo_root / "data" / "corpus" / cid / "meta.yaml",
        ]:
            if my_path.exists():
                try:
                    for line in my_path.read_text(encoding="utf-8").splitlines():
                        line = line.strip()
                        if line.startswith("task_type:"):
                            meta["category"] = line.split(":", 1)[1].strip()
                        elif line.startswith("title:") and not source_meta.get("title"):
                            t = line.split(":", 1)[1].strip().strip('"').strip("'")
                            if t:
                                source_meta["title"] = t
                    break
                except Exception:
                    pass

    # 3. summary
    for s_path in [
        chat_path / "full_export.json",
        repo_root / "design_pack" / "sample_data" / f"{cid}.json",
    ]:
        if s_path.exists():
            try:
                d = json.loads(s_path.read_text(encoding="utf-8"))
                s = d.get("dialogue_summary")
                if s:
                    summary = s
                    break
            except Exception:
                pass

    return source_meta, meta, summary


def project_chat_directory(
    chat_dir: str | Path,
    output_path: str | Path | None = None,
    status: str = "ready",
    processed_pairs: int | None = None,
    flagged_pairs: list[Any] | None = None,
) -> dict[str, Any]:
    """Project an entire chat directory into a validated workspace_bundle.json artifact."""
    chat_path = Path(chat_dir)
    cid = chat_path.name
    repo_root = Path(__file__).resolve().parent.parent.parent

    # Find dialogue
    dialogue_path = chat_path / "dialogue.json"
    if not dialogue_path.exists():
        dialogue_path = repo_root / "data" / "corpus" / cid / "dialogue.json"
    if not dialogue_path.exists():
        raise FileNotFoundError(f"dialogue.json not found in {chat_dir}")
    dialogue = json.loads(dialogue_path.read_text(encoding="utf-8"))

    # Find state
    state_path = chat_path / "state.json"
    if not state_path.exists():
        raise FileNotFoundError(f"state.json not found in {chat_dir}")
    state = json.loads(state_path.read_text(encoding="utf-8"))

    # Find ledger
    ledger_path = chat_path / "ledger.jsonl"
    ledger: list[dict[str, Any]] = []
    if ledger_path.exists():
        ledger = [
            json.loads(line)
            for line in ledger_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    source_meta, meta, summary = load_chat_metadata(chat_path)

    out_file = Path(output_path) if output_path else (chat_path / "workspace_bundle.json")
    return export_workspace_bundle(
        output_path=out_file,
        dialogue=dialogue,
        state=state,
        ledger=ledger,
        source_meta=source_meta,
        meta=meta,
        chat_id=cid,
        summary=summary,
        status=status,
        processed_pairs=processed_pairs,
        flagged_pairs=flagged_pairs,
    )

