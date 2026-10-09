"""Generate readable one-page Markdown reports for chats.

Used by the owner to judge maps against memory (STANDALONE_V1_PLAN §4 Step S1.7 and §6A).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.projections.workspace import project_chat_directory


def _find_chat_dir(chat_identifier: str | Path, repo_root: Path | None = None) -> Path:
    repo = repo_root or Path(__file__).resolve().parent.parent
    path = Path(chat_identifier)

    # 1. Direct path exists
    if path.exists() and path.is_dir():
        return path

    # 2. In data/chats/<cid>
    cid = path.name
    candidate_chats = repo / "data" / "chats" / cid
    if candidate_chats.exists() and candidate_chats.is_dir():
        return candidate_chats

    # 3. In data/corpus/<cid>
    candidate_corpus = repo / "data" / "corpus" / cid
    if candidate_corpus.exists() and candidate_corpus.is_dir():
        return candidate_corpus

    raise FileNotFoundError(f"Chat directory not found for: '{chat_identifier}'")


def generate_chat_report(chat_identifier: str | Path, repo_root: Path | None = None) -> str:
    """Generate a clean, readable one-page Markdown report for a chat."""
    repo = repo_root or Path(__file__).resolve().parent.parent
    chat_dir = _find_chat_dir(chat_identifier, repo)

    # Load or project workspace bundle (pure in-memory if not already on disk)
    bundle_path = chat_dir / "workspace_bundle.json"
    bundle = None
    if bundle_path.exists():
        try:
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        except Exception:
            bundle = None

    if bundle is None:
        from engine.projections.workspace import load_chat_metadata, project_workspace
        dlg_path = chat_dir / "dialogue.json"
        if not dlg_path.exists():
            dlg_path = repo / "data" / "corpus" / chat_dir.name / "dialogue.json"
        dlg = json.loads(dlg_path.read_text(encoding="utf-8"))
        st = json.loads((chat_dir / "state.json").read_text(encoding="utf-8"))
        ledger_path = chat_dir / "ledger.jsonl"
        ledger = (
            [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if ledger_path.exists()
            else []
        )
        sm, meta, summary = load_chat_metadata(chat_dir)
        bundle = project_workspace(
            dialogue=dlg,
            state=st,
            ledger=ledger,
            source_meta=sm,
            meta=meta,
            chat_id=chat_dir.name,
            summary=summary,
        )

    # Load optional panel_bundle for quantitative facts
    panel_path = chat_dir / "panel_bundle.json"
    panel_bundle = None
    if panel_path.exists():
        try:
            panel_bundle = json.loads(panel_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Extract high-level scalar facts
    cid = bundle.get("id", chat_dir.name)
    title = bundle.get("title", "Untitled Chat")
    category = bundle.get("category", "Uncategorised")
    total_pairs = bundle.get("totalPairs", 0)
    status = bundle.get("status", "ready")
    summary = bundle.get("summary", "No dialogue summary available.")

    # Compute metrics from final snapshot
    snapshots = bundle.get("snapshots", [])
    latest_snap = snapshots[-1] if snapshots else None

    tot_h = 0.0
    tot_a = 0.0
    if latest_snap:
        tot_h = sum(float(m.get("human", 0.0)) for m in latest_snap.get("mass", {}).values())
        tot_a = sum(float(m.get("ai", 0.0)) for m in latest_snap.get("mass", {}).values())
    total_mass = tot_h + tot_a

    h_pct = (tot_h / total_mass * 100.0) if total_mass > 0 else 0.0
    a_pct = (tot_a / total_mass * 100.0) if total_mass > 0 else 0.0

    # Panel bundle facts fallback
    mode = "COPILOT"
    decisions_you = len([a for a in bundle.get("atoms", []) if (a.get("kind") == "requirement" and a.get("origin") == "human") or (a.get("kind") == "resolved" and a.get("resolver") == "human")])
    decisions_ai = len([a for a in bundle.get("atoms", []) if (a.get("kind") == "requirement" and a.get("origin") == "ai") or (a.get("kind") == "resolved" and a.get("resolver") == "ai")])

    if panel_bundle and panel_bundle.get("pairs"):
        last_pair = panel_bundle["pairs"][-1]
        mode = last_pair.get("how", {}).get("mode", mode)
        dec_info = last_pair.get("decisions", {})
        if "you_count" in dec_info and "ai_count" in dec_info:
            decisions_you = dec_info["you_count"]
            decisions_ai = dec_info["ai_count"]

    # Compute node depths and terminal pairs
    nodes = bundle.get("nodes", [])
    root_node = next((n for n in nodes if n.get("root")), None)
    root_id = root_node["id"] if root_node else ""

    parent_map = {n["id"]: n.get("parent") for n in nodes}

    def _get_depth(nid: str) -> int:
        if nid == root_id or parent_map.get(nid) is None:
            return 0 if nid == root_id else 1
        curr = nid
        d = 0
        visited = set()
        while curr and curr not in visited:
            visited.add(curr)
            p = parent_map.get(curr)
            if not p:
                break
            d += 1
            curr = p
        return d

    terminal_counts: dict[str, list[int]] = {}
    for snap in snapshots:
        term = snap.get("terminal")
        p = snap.get("pair", 1)
        if term:
            terminal_counts.setdefault(term, []).append(p)

    lines: list[str] = [
        f"# Chat Report: {title}",
        "",
        f"**Chat ID**: `{cid}` · **Category**: {category} · **Pairs**: {total_pairs} · **Status**: `{status}`",
        "",
        "> " + summary.replace("\n", " "),
        "",
        "---",
        "",
        "## 1. Overall Balance & Interaction Mode",
        f"- **Cumulative Mass**: {total_mass:.1f} points ({tot_h:.1f} You · {tot_a:.1f} AI)",
        f"- **Direction**: **{h_pct:.1f}% You** · **{a_pct:.1f}% AI**",
        f"- **Decisions**: {decisions_you} You · {decisions_ai} AI ({decisions_you + decisions_ai} total)",
        f"- **Interaction Mode**: `{mode}`",
        "",
        "---",
        "",
        "## 2. Outcome Map & Contribution Shares",
        "",
        "| Outcome | Depth | Born | Mass (You / AI / Total) | Share | Terminal In Pairs |",
        "|---|---|---|---|---|---|",
    ]

    for node in nodes:
        nid = node["id"]
        ntitle = node.get("title", "")
        depth = _get_depth(nid)
        born = node.get("born", 1)

        m = latest_snap.get("mass", {}).get(nid, {}) if latest_snap else {}
        nh = float(m.get("human", 0.0))
        na = float(m.get("ai", 0.0))
        ntot = nh + na
        node_share = (ntot / total_mass * 100.0) if total_mass > 0 else 0.0

        terms = terminal_counts.get(nid, [])
        terms_str = f"P{', P'.join(str(x) for x in terms)}" if terms else "—"

        indent = "↳ " if depth > 0 else "★ "
        display_name = f"{indent}{ntitle}" if depth > 0 else f"**{ntitle}** (Root)"

        lines.append(
            f"| {display_name} | {depth} | P{born} | {nh:.1f} / {na:.1f} / **{ntot:.1f}** | {node_share:.1f}% | {terms_str} |"
        )

    # 3. Decisions & Requirements
    atoms = bundle.get("atoms", [])
    user_reqs = [a for a in atoms if a.get("kind") == "requirement" and a.get("origin") == "human"]
    ai_reqs = [a for a in atoms if a.get("kind") == "requirement" and a.get("origin") == "ai"]
    resolved_slots = [a for a in atoms if a.get("kind") == "resolved"]
    open_questions = [a for a in atoms if a.get("kind") == "question"]

    lines.extend([
        "",
        "---",
        "",
        f"## 3. Key Decisions & Atoms ({len(atoms)} total)",
        "",
        f"### User Requirements ({len(user_reqs)})",
    ])
    if user_reqs:
        for a in user_reqs:
            q = f' — *"{a["quote"]}"*' if a.get("quote") else ""
            lines.append(f"- **P{a.get('sourcePair', 1)}**: {a.get('text')}{q}")
    else:
        lines.append("- *(None)*")

    lines.extend([
        "",
        f"### AI Requirements ({len(ai_reqs)})",
    ])
    if ai_reqs:
        for a in ai_reqs:
            q = f' — *"{a["quote"]}"*' if a.get("quote") else ""
            lines.append(f"- **P{a.get('sourcePair', 1)}**: {a.get('text')}{q}")
    else:
        lines.append("- *(None)*")

    lines.extend([
        "",
        f"### Answered Slots & Choice Resolutions ({len(resolved_slots)})",
    ])
    if resolved_slots:
        for a in resolved_slots:
            resolver = "User" if a.get("resolver") == "human" else "AI"
            q = f' (Chose: *"{a["quote"]}"*)' if a.get("quote") else ""
            q_text = f" Question: *{a['question']}* →" if a.get("question") else ""
            lines.append(f"- **P{a.get('sourcePair', 1)}**: {q_text} **{a.get('text')}** [{resolver} decided]{q}")
    else:
        lines.append("- *(None)*")

    lines.extend([
        "",
        f"### Open Questions ({len(open_questions)})",
    ])
    if open_questions:
        for a in open_questions:
            choices = f" (Options: {', '.join(a['choices'])})" if a.get("choices") else ""
            lines.append(f"- **P{a.get('sourcePair', 1)}**: *{a.get('text')}*{choices}")
    else:
        lines.append("- *(None)*")

    # 4. Review & Invariant Health
    flagged = bundle.get("flaggedPairs", [])
    lines.extend([
        "",
        "---",
        "",
        "## 4. Review & Invariant Health",
    ])
    if flagged:
        lines.append(f"- **Flagged Pairs ({len(flagged)})**: {flagged}")
    else:
        lines.append("- **Review Flags**: None (clean run)")

    lines.append(f"- **Validation Status**: Schema validated (`{status}`); {len(nodes)} outcomes, {len(atoms)} atoms, {len(snapshots)} snapshots.")
    lines.append("")

    return "\n".join(lines)
