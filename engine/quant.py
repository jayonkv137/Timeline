"""Stage 4 — Quantification Layer (pure arithmetic, no LLM).

Pipeline Spec §10:
- §10.2: Eq. 1 I(a->r), Eq. 2 M(p,r), Eq. 3 M(p,rho,r)
- §10.4: Increments and snapshots:
    Δ(t, p) = sum of scores where pair_added = t and speaker = p
    C(t, p) = sum of Δ(t', p) for t' <= t
- §10.5: Direction split & Decisions:
    you% = C(t, you) / (C(t, you) + C(t, AI)) * 100
    ai%  = C(t, AI) / (C(t, you) + C(t, AI)) * 100
    Creator = speaker of the earliest creation action (sorted by pair, U before A, sequence)
    Decisions = counts of distinct requirements by creator (keyed on (outcome_id, req_id))
    Chip = blue if M(AI, r) == 0, orange if M(you, r) == 0, grey otherwise

Rounding Policy:
- All intermediate calculations (turn deltas, cumulative odometers, requirement masses)
  retain full IEEE 754 floating-point precision throughout. No intermediate values are rounded.
- Direction percentages are rounded once, at the final presentation/export boundary, to 1
  decimal place using Python's round(pct, 1).
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable

ACTION_ID_RE = re.compile(r"^([UA])\((\d+),(\d+)\)$")


def action_sort_key(action_id: str) -> tuple[int, int, int]:
    """Sort key for action IDs: (pair_number, 0 if U else 1, sequence_number).

    User actions precede AI actions within the same pair exchange.
    """
    m = ACTION_ID_RE.match(str(action_id).strip())
    if m:
        spk = 0 if m.group(1) == "U" else 1
        return (int(m.group(2)), spk, int(m.group(3)))
    return (999999, 999999, 999999)


def truncate_clause(text: str, max_chars: int = 140) -> str:
    """Truncate text at a clause boundary without rewording (Panel Spec §3)."""
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_chars:
        return text.rstrip(".")

    boundaries = [". ", "; ", " — ", " - ", ", "]
    candidates = []
    for b in boundaries:
        idx = text[:max_chars].rfind(b)
        if idx >= 30:
            candidates.append(idx)

    if candidates:
        cut = max(candidates)
        return text[:cut].strip().rstrip(".,;-")

    words = text[:max_chars].split()
    if len(words) > 1:
        return " ".join(words[:-1]).strip().rstrip(".,;-")
    return text[:max_chars].strip()


@dataclass(frozen=True)
class DirectionFact:
    t: int
    delta_you: float
    delta_ai: float
    c_you: float
    c_ai: float
    you_pct: float
    ai_pct: float


@dataclass(frozen=True)
class RequirementFact:
    outcome_id: str
    req_id: str
    creator: str            # "U" or "A"
    created_at_pair: int
    mass_you: float
    mass_ai: float
    chip: str               # "blue" | "grey" | "orange"
    text: str = ""


@dataclass(frozen=True)
class DecisionsFact:
    t: int
    you_count: int
    ai_count: int
    latest_ai_example: str | None
    requirements: dict[tuple[str, str], RequirementFact]


@dataclass(frozen=True)
class ModeSignals:
    w_you: int
    w_ai: int
    h_you: float
    h_ai: float
    substantive_user: bool


@dataclass(frozen=True)
class ModeSplit:
    centaur_pct: float
    copilot_pct: float
    autopilot_pct: float


@dataclass(frozen=True)
class ModeFact:
    t: int
    mode: str               # "CENTAUR" | "COPILOT" | "AUTOPILOT" | "QUIET"
    signals: ModeSignals
    split: ModeSplit
    inherited_mode: str | None = None


@dataclass(frozen=True)
class DrawerRequirement:
    outcome_id: str
    req_id: str
    label: str              # "R1", "R2", ...
    op: str                 # "create" | "revise" | "delete"
    delta_you: float
    delta_ai: float
    chip: str               # "blue" | "grey" | "orange"


@dataclass(frozen=True)
class DrawerSlot:
    slot_id: str
    origin: str             # "user" | "AI"
    status: str             # "open" | "resolved" | "abandoned"
    resolved_into: str | None = None
    outcome_id: str | None = None


@dataclass(frozen=True)
class TimelineDrawer:
    requirements: list[DrawerRequirement]
    slots: list[DrawerSlot]


@dataclass(frozen=True)
class TimelineFact:
    pair: int
    delta_you: float
    delta_ai: float
    summary: str
    drawer: TimelineDrawer


@dataclass(frozen=True)
class GoalDefaultNode:
    outcome_id: str
    text: str
    depth: int
    is_current: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome_id": self.outcome_id,
            "text": self.text,
            "depth": self.depth,
            "is_current": self.is_current,
        }


@dataclass(frozen=True)
class GoalTreeNode:
    outcome_id: str
    text: str
    depth: int
    parent: str | None
    children: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome_id": self.outcome_id,
            "text": self.text,
            "depth": self.depth,
            "parent": self.parent,
            "children": list(self.children),
        }


@dataclass(frozen=True)
class GoalFact:
    default_view: list[GoalDefaultNode]
    full_tree: list[GoalTreeNode]

    def to_dict(self) -> dict[str, Any]:
        return {
            "default_view": [n.to_dict() for n in self.default_view],
            "full_tree": [n.to_dict() for n in self.full_tree],
        }



def compute_direction(
    ledger_rows: Iterable[dict[str, Any]],
    max_pair: int | None = None,
) -> list[DirectionFact]:
    """Compute per-pair deltas, cumulative totals, and direction split percentages.

    Follows Pipeline Spec §10.4 and §10.5.
    Pure arithmetic over ledger rows.
    """
    rows = list(ledger_rows)
    pairs_in_rows = [int(r["pair_added"]) for r in rows if "pair_added" in r]
    total_pairs = max_pair if max_pair is not None else (max(pairs_in_rows) if pairs_in_rows else 1)

    deltas_you: dict[int, float] = {t: 0.0 for t in range(1, total_pairs + 1)}
    deltas_ai: dict[int, float] = {t: 0.0 for t in range(1, total_pairs + 1)}

    for r in rows:
        t = int(r.get("pair_added", 1))
        spk = r.get("speaker")
        score = float(r.get("score", 0.0))
        if t in deltas_you:
            if spk == "U":
                deltas_you[t] += score
            elif spk == "A":
                deltas_ai[t] += score

    facts: list[DirectionFact] = []
    c_you = 0.0
    c_ai = 0.0

    for t in range(1, total_pairs + 1):
        d_you = deltas_you[t]
        d_ai = deltas_ai[t]
        c_you += d_you
        c_ai += d_ai
        tot = c_you + c_ai

        if tot > 0:
            you_pct = round((c_you / tot) * 100.0, 1)
            ai_pct = round((c_ai / tot) * 100.0, 1)
        else:
            you_pct = 0.0
            ai_pct = 0.0

        facts.append(
            DirectionFact(
                t=t,
                delta_you=d_you,
                delta_ai=d_ai,
                c_you=c_you,
                c_ai=c_ai,
                you_pct=you_pct,
                ai_pct=ai_pct,
            )
        )

    return facts


def _extract_requirements_meta(
    rows: list[dict[str, Any]],
    state_requirements: Iterable[dict[str, Any]] | None = None,
) -> tuple[
    dict[tuple[str, str], dict[str, Any]],
    dict[tuple[str, str], list[tuple[str, str]]],
    dict[tuple[str, str], str],
]:
    """Harvest requirements metadata, creation actions, and creator attribution."""
    req_meta: dict[tuple[str, str], dict[str, Any]] = {}
    if state_requirements:
        for r in state_requirements:
            key = (str(r["outcome_id"]), str(r["req_id"]))
            req_meta[key] = {
                "text": str(r.get("text", "")),
                "created_at_pair": int(r.get("created_at_pair", 1)),
                "creation_action_ids": list(r.get("creation_action_ids", [])),
            }

    creation_actions: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    for r in rows:
        key = (str(r["outcome_id"]), str(r["req_id"]))
        if r.get("kind") == "creation":
            creation_actions[key].append((str(r["action_id"]), str(r["speaker"])))
            if key not in req_meta:
                req_meta[key] = {
                    "text": "",
                    "created_at_pair": int(r.get("pair_added", 1)),
                    "creation_action_ids": [],
                }
            else:
                pair_added = int(r.get("pair_added", 1))
                if pair_added < req_meta[key]["created_at_pair"]:
                    req_meta[key]["created_at_pair"] = pair_added

    for key, meta in req_meta.items():
        if key not in creation_actions and meta.get("creation_action_ids"):
            for aid in meta["creation_action_ids"]:
                spk = "U" if str(aid).startswith("U") else "A"
                creation_actions[key].append((str(aid), spk))

    creators: dict[tuple[str, str], str] = {}
    for key, actions in creation_actions.items():
        sorted_acts = sorted(actions, key=lambda x: action_sort_key(x[0]))
        creators[key] = sorted_acts[0][1] if sorted_acts else "U"

    for key in req_meta:
        if key not in creators:
            creators[key] = "U"

    return req_meta, creation_actions, creators


def compute_decisions(
    ledger_rows: Iterable[dict[str, Any]],
    state_requirements: Iterable[dict[str, Any]] | None = None,
    max_pair: int | None = None,
    fallback_latest_ai_example: str | None = None,
) -> list[DecisionsFact]:
    """Compute per-pair decisions and per-requirement masses/chips.

    Pipeline Spec §10.2, §10.5, Panel Spec §3:
    - Keyed on (outcome_id, req_id), never req_id alone.
    - Creator determined from earliest creation action (sorted by pair, U before A, sequence).
    - Mass computed cumulatively up to pair t: M(p, r) = sum_{a in A_p} I(a -> r).
    - Chip: blue if M(AI, r) == 0, orange if M(you, r) == 0, grey otherwise.
    - Decisions counters: requirements with created_at_pair <= t, grouped by creator.
    - Latest AI example: text of highest-pair AI-created requirement, truncated at clause boundary.
    """
    rows = list(ledger_rows)
    pairs_in_rows = [int(r["pair_added"]) for r in rows if "pair_added" in r]
    total_pairs = max_pair if max_pair is not None else (max(pairs_in_rows) if pairs_in_rows else 1)

    req_meta, creation_actions, creators = _extract_requirements_meta(rows, state_requirements)

    facts: list[DecisionsFact] = []

    # Compute per-pair facts
    for t in range(1, total_pairs + 1):
        active_req_keys = [k for k, meta in req_meta.items() if meta["created_at_pair"] <= t]

        req_facts: dict[tuple[str, str], RequirementFact] = {}
        mass_you: dict[tuple[str, str], float] = defaultdict(float)
        mass_ai: dict[tuple[str, str], float] = defaultdict(float)

        for r in rows:
            if int(r.get("pair_added", 1)) <= t:
                key = (str(r["outcome_id"]), str(r["req_id"]))
                if key in active_req_keys:
                    score = float(r.get("score", 0.0))
                    if r.get("speaker") == "U":
                        mass_you[key] += score
                    elif r.get("speaker") == "A":
                        mass_ai[key] += score

        you_count = 0
        ai_count = 0
        ai_candidates: list[tuple[int, tuple[int, int, int], str, str]] = []

        for key in sorted(active_req_keys):
            c = creators.get(key, "U")
            m_you = mass_you[key]
            m_ai = mass_ai[key]

            if m_ai == 0.0:
                chip = "blue"
            elif m_you == 0.0:
                chip = "orange"
            else:
                chip = "grey"

            meta = req_meta[key]
            text = meta.get("text", "")
            if c == "U":
                you_count += 1
            else:
                ai_count += 1
                acts = creation_actions.get(key, [])
                earliest_act_key = min([action_sort_key(a[0]) for a in acts]) if acts else (999, 999, 999)
                ai_candidates.append((meta["created_at_pair"], earliest_act_key, key[0], key[1]))

            req_facts[key] = RequirementFact(
                outcome_id=key[0],
                req_id=key[1],
                creator=c,
                created_at_pair=meta["created_at_pair"],
                mass_you=m_you,
                mass_ai=m_ai,
                chip=chip,
                text=text,
            )

        latest_ai_example = None
        if ai_candidates:
            ai_candidates.sort(reverse=True)
            chosen_key = (ai_candidates[0][2], ai_candidates[0][3])
            chosen_text = req_meta[chosen_key].get("text", "")
            if chosen_text and chosen_text != "(not captured in fixture)":
                latest_ai_example = truncate_clause(chosen_text)
            elif fallback_latest_ai_example:
                latest_ai_example = fallback_latest_ai_example

        facts.append(
            DecisionsFact(
                t=t,
                you_count=you_count,
                ai_count=ai_count,
                latest_ai_example=latest_ai_example,
                requirements=req_facts,
            )
        )

    return facts


def compute_mode(
    ledger_rows: Iterable[dict[str, Any]],
    state_requirements: Iterable[dict[str, Any]] | None = None,
    max_pair: int | None = None,
    ops_per_pair: dict[int, list[dict[str, Any]]] | None = None,
) -> list[ModeFact]:
    """Compute per-pair HOW usage mode classification and running mode distribution.

    Pipeline Spec §10.5, Panel Spec §5, panel_bundle.schema.json:
    - Signals per pair:
      - w_you / w_ai: # requirements created at pair t grouped by creator.
      - h_you / h_ai: non-creation mass added at pair t (sum of scores for kind != "creation").
      - substantive_user: true if any user action is SHAPER or user non-creation row score >= 2.0.
    - Quiet pair: no ops and total mass added Δ < 2.0.
    - Classification:
      quiet -> QUIET (inheriting previous mode for the narrative sentence)
      w_you >= w_ai and h_ai <= h_you -> CENTAUR
      w_you >= w_ai and h_ai > h_you -> COPILOT
      w_ai > w_you and not substantive_user -> AUTOPILOT
      w_ai > w_you and substantive_user -> COPILOT
    - Running split: % of non-quiet pairs per mode up to pair t (rounded to 1 decimal place).
    """
    rows = list(ledger_rows)
    pairs_in_rows = [int(r["pair_added"]) for r in rows if "pair_added" in r]
    total_pairs = max_pair if max_pair is not None else (max(pairs_in_rows) if pairs_in_rows else 1)

    req_meta, creation_actions, creators = _extract_requirements_meta(rows, state_requirements)

    facts: list[ModeFact] = []
    non_quiet_history: list[str] = []
    last_non_quiet_mode: str | None = None

    for t in range(1, total_pairs + 1):
        w_you = sum(
            1 for k, meta in req_meta.items()
            if meta["created_at_pair"] == t and creators.get(k) == "U"
        )
        w_ai = sum(
            1 for k, meta in req_meta.items()
            if meta["created_at_pair"] == t and creators.get(k) == "A"
        )

        delta_you = 0.0
        delta_ai = 0.0
        h_you = 0.0
        h_ai = 0.0
        has_user_shaper = False
        has_user_non_creat_ge2 = False

        for r in rows:
            if int(r.get("pair_added", 1)) == t:
                score = float(r.get("score", 0.0))
                spk = r.get("speaker")
                kind = r.get("kind")
                role = r.get("role")

                if spk == "U":
                    delta_you += score
                    if kind != "creation":
                        h_you += score
                    if role == "SHAPER":
                        has_user_shaper = True
                    if kind != "creation" and score >= 2.0:
                        has_user_non_creat_ge2 = True
                elif spk == "A":
                    delta_ai += score
                    if kind != "creation":
                        h_ai += score

        substantive_user = has_user_shaper or has_user_non_creat_ge2

        delta_total = delta_you + delta_ai
        if ops_per_pair is not None:
            has_ops = len(ops_per_pair.get(t, [])) > 0
            is_quiet = (not has_ops) and (delta_total < 2.0)
        else:
            is_quiet = (w_you == 0 and w_ai == 0) and (delta_total < 2.0)

        if is_quiet:
            mode = "QUIET"
            inherited_mode = last_non_quiet_mode
        else:
            if w_you >= w_ai:
                if h_ai <= h_you:
                    mode = "CENTAUR"
                else:
                    mode = "COPILOT"
            else:  # w_ai > w_you
                if not substantive_user:
                    mode = "AUTOPILOT"
                else:
                    mode = "COPILOT"
            last_non_quiet_mode = mode
            non_quiet_history.append(mode)
            inherited_mode = mode

        if non_quiet_history:
            nq_len = len(non_quiet_history)
            centaur_pct = round((non_quiet_history.count("CENTAUR") / nq_len) * 100.0, 1)
            copilot_pct = round((non_quiet_history.count("COPILOT") / nq_len) * 100.0, 1)
            autopilot_pct = round((non_quiet_history.count("AUTOPILOT") / nq_len) * 100.0, 1)
        else:
            centaur_pct = 0.0
            copilot_pct = 0.0
            autopilot_pct = 0.0

        signals = ModeSignals(
            w_you=w_you,
            w_ai=w_ai,
            h_you=round(h_you, 1),
            h_ai=round(h_ai, 1),
            substantive_user=substantive_user,
        )
        split = ModeSplit(
            centaur_pct=centaur_pct,
            copilot_pct=copilot_pct,
            autopilot_pct=autopilot_pct,
        )

        facts.append(
            ModeFact(
                t=t,
                mode=mode,
                signals=signals,
                split=split,
                inherited_mode=inherited_mode,
            )
        )

    return facts


def compute_r_sum(
    req_drawer_rows: list[DrawerRequirement],
    slot_drawer_rows: list[DrawerSlot],
    fallback_summary: str | None = None,
    outcome_texts: dict[str, str] | None = None,
    req_texts: dict[tuple[str, str], str] | None = None,
) -> str:
    """Generate <= 5-word summary line following PANEL_SPEC §4.5."""
    if fallback_summary:
        return fallback_summary

    if req_drawer_rows:
        best_req = max(
            req_drawer_rows,
            key=lambda r: (r.delta_you + r.delta_ai, r.delta_ai, r.delta_you),
        )
        verb_map = {
            "create": "adding",
            "revise": "revising",
            "resolve": "settling",
            "delete": "dropping",
        }
        verb = verb_map.get(best_req.op, "adding")

        text = ""
        if req_texts:
            text = req_texts.get((best_req.outcome_id, best_req.req_id), "").strip()
        if not text and outcome_texts:
            text = outcome_texts.get(best_req.outcome_id, "").strip()

        if text and text != "(not captured in fixture)":
            words = text.split()
            short_desc = " ".join(words[:4]).rstrip(".,;:-& ")
            summary = f"{verb} {short_desc}"
        else:
            summary = f"{verb} {best_req.label}"

        words = summary.split()
        if len(words) > 5:
            return " ".join(words[:5])
        return summary

    elif slot_drawer_rows:
        if len(slot_drawer_rows) == 1:
            return "raising an open question"
        else:
            return f"parking {len(slot_drawer_rows)} questions"

    else:
        return "execution only"


def compute_timeline(
    ledger_rows: Iterable[dict[str, Any]],
    state_requirements: Iterable[dict[str, Any]] | None = None,
    state_slots: Iterable[dict[str, Any]] | None = None,
    operations_log: Iterable[dict[str, Any]] | None = None,
    max_pair: int | None = None,
    summary_by_pair: dict[int, str] | None = None,
    outcome_texts: dict[str, str] | None = None,
) -> list[TimelineFact]:
    """Compute per-pair timeline drawer facts and R-SUM summary lines.

    Panel Spec §4, Pipeline Spec §10.4 & §10.5, panel_bundle.schema.json:
    - Per-pair deltas: Δ(t, you) and Δ(t, AI).
    - Requirements drawer rows:
      - Filtered to requirements active/created/revised in this exchange.
      - Stable R-label in creation order across outcomes (R1, R2...).
      - Op: "create" | "revise" | "delete".
      - Per-turn delta: Δ(t, you, r) and Δ(t, AI, r).
      - Chip: blue (cum AI mass == 0), orange (cum you mass == 0), grey (straddling).
    - Slots drawer rows:
      - Captured from operations_log / state_slots at this pair.
    - Summary line: deterministic R-SUM template (<= 5 words).
    """
    rows = list(ledger_rows)
    pairs_in_rows = [int(r["pair_added"]) for r in rows if "pair_added" in r]
    total_pairs = max_pair if max_pair is not None else (max(pairs_in_rows) if pairs_in_rows else 1)

    req_meta, creation_actions, creators = _extract_requirements_meta(rows, state_requirements)

    # 1. Assign stable R-labels across chat in creation order: (created_at_pair, outcome_id, req_id)
    sorted_req_keys = sorted(
        req_meta.keys(),
        key=lambda k: (req_meta[k]["created_at_pair"], k[0], k[1]),
    )
    r_labels: dict[tuple[str, str], str] = {
        k: f"R{i + 1}" for i, k in enumerate(sorted_req_keys)
    }

    # 2. Index operations_log by pair if provided
    ops_by_pair: dict[int, list[dict[str, Any]]] = defaultdict(list)
    if operations_log:
        for op in operations_log:
            ops_by_pair[int(op.get("pair", 1))].append(op)

    # 3. Index slots if provided
    slots_by_outcome_and_id: dict[tuple[str, str], dict[str, Any]] = {}
    slots_list: list[dict[str, Any]] = []
    if state_slots:
        for s in state_slots:
            oid = str(s.get("outcome_id", ""))
            sid = str(s.get("slot_id", ""))
            slots_by_outcome_and_id[(oid, sid)] = s
            slots_list.append(s)

    req_texts: dict[tuple[str, str], str] = {
        k: meta.get("text", "") for k, meta in req_meta.items()
    }

    facts: list[TimelineFact] = []

    for t in range(1, total_pairs + 1):
        turn_rows = [r for r in rows if int(r.get("pair_added", 1)) == t]
        delta_you = sum(float(r.get("score", 0.0)) for r in turn_rows if r.get("speaker") == "U")
        delta_ai = sum(float(r.get("score", 0.0)) for r in turn_rows if r.get("speaker") == "A")

        pair_ops = ops_by_pair.get(t, [])
        req_ops_for_pair: dict[tuple[str, str], str] = {}
        for op in pair_ops:
            if op.get("target_type") == "requirement":
                oid = str(op.get("outcome_id", ""))
                rid = str(op.get("target_id", ""))
                req_ops_for_pair[(oid, rid)] = str(op.get("op", "create"))

        touched_keys: set[tuple[str, str]] = set(req_ops_for_pair.keys())
        for r in turn_rows:
            k = (str(r["outcome_id"]), str(r["req_id"]))
            touched_keys.add(k)
        for k, meta in req_meta.items():
            if meta["created_at_pair"] == t:
                touched_keys.add(k)

        drawer_reqs: list[DrawerRequirement] = []
        for k in sorted(touched_keys, key=lambda x: (int(r_labels.get(x, "R999")[1:]), x[0], x[1])):
            oid, rid = k
            label = r_labels.get(k, "R1")

            if k in req_ops_for_pair:
                op = req_ops_for_pair[k]
            elif req_meta.get(k, {}).get("created_at_pair", 1) == t:
                op = "create"
            else:
                op = "revise"

            req_turn_rows = [r for r in turn_rows if str(r.get("outcome_id")) == oid and str(r.get("req_id")) == rid]
            d_you = sum(float(r.get("score", 0.0)) for r in req_turn_rows if r.get("speaker") == "U")
            d_ai = sum(float(r.get("score", 0.0)) for r in req_turn_rows if r.get("speaker") == "A")

            cum_rows = [r for r in rows if int(r.get("pair_added", 1)) <= t and str(r.get("outcome_id")) == oid and str(r.get("req_id")) == rid]
            cum_you = sum(float(r.get("score", 0.0)) for r in cum_rows if r.get("speaker") == "U")
            cum_ai = sum(float(r.get("score", 0.0)) for r in cum_rows if r.get("speaker") == "A")

            if cum_ai == 0.0:
                chip = "blue"
            elif cum_you == 0.0:
                chip = "orange"
            else:
                chip = "grey"

            drawer_reqs.append(
                DrawerRequirement(
                    outcome_id=oid,
                    req_id=rid,
                    label=label,
                    op=op,
                    delta_you=float(round(d_you, 1)),
                    delta_ai=float(round(d_ai, 1)),
                    chip=chip,
                )
            )

        drawer_slots: list[DrawerSlot] = []
        slot_ops = [op for op in pair_ops if op.get("target_type") == "slot" or op.get("op") in ("open_slot", "resolve_slot", "abandon_slot")]
        if slot_ops:
            for op in slot_ops:
                sid = str(op.get("target_id", ""))
                oid = str(op.get("outcome_id", ""))
                slot_data = slots_by_outcome_and_id.get((oid, sid))
                if not slot_data:
                    for s in slots_list:
                        if str(s.get("slot_id")) == sid:
                            slot_data = s
                            break
                origin = slot_data.get("origin", "AI") if slot_data else "AI"
                status = slot_data.get("status", "open") if slot_data else "open"
                resolved_into = slot_data.get("resolved_into") if slot_data else None
                drawer_slots.append(
                    DrawerSlot(
                        slot_id=sid,
                        origin=origin,
                        status=status,
                        resolved_into=resolved_into,
                        outcome_id=oid if oid else None,
                    )
                )
        elif t == 1 and slots_list and not operations_log:
            for s in slots_list:
                drawer_slots.append(
                    DrawerSlot(
                        slot_id=str(s.get("slot_id", "")),
                        origin=str(s.get("origin", "AI")),
                        status=str(s.get("status", "open")),
                        resolved_into=s.get("resolved_into"),
                        outcome_id=str(s.get("outcome_id")) if "outcome_id" in s else None,
                    )
                )

        fallback = summary_by_pair.get(t) if summary_by_pair else None
        summary = compute_r_sum(
            req_drawer_rows=drawer_reqs,
            slot_drawer_rows=drawer_slots,
            fallback_summary=fallback,
            outcome_texts=outcome_texts,
            req_texts=req_texts,
        )

        facts.append(
            TimelineFact(
                pair=t,
                delta_you=float(round(delta_you, 1)),
                delta_ai=float(round(delta_ai, 1)),
                summary=summary,
                drawer=TimelineDrawer(
                    requirements=drawer_reqs,
                    slots=drawer_slots,
                ),
            )
        )

    return facts


def compute_goal_view(
    outcomes: Iterable[dict[str, Any]],
    current_outcome_id: str | None = None,
) -> GoalFact:
    """Compute the goal tree (full_tree) and collapsed view (default_view).

    Follows Panel Spec §1 and panel_bundle.schema.json:
    - full_tree: Complete outcome hierarchy with calculated tree depth, parent pointer,
      and children IDs.
    - default_view: Thread-collapse view based on current goal depth d below root:
        - d = 0: 1 line: [main goal] (is_current=True)
        - d = 1: 2 lines: [main goal] · [current]
        - d = 2: 3 lines: [main goal] · [previous] · [current]
        - d >= 3: 3 lines: [main goal] · [previous] · [current]
          (the depth jump from 0 to d-1 triggers the UI expander chip '⌄ d-2 more').
    """
    raw_list = list(outcomes)
    if not raw_list:
        return GoalFact(default_view=[], full_tree=[])

    outcome_list: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    child_map: dict[str, list[str]] = defaultdict(list)

    for o in raw_list:
        oid = str(o.get("id") or o.get("outcome_id") or "")
        if not oid:
            continue
        text = str(o.get("text") or o.get("outcome") or "")
        raw_parent = o.get("parent") if "parent" in o else o.get("parent_outcome_id")
        parent = str(raw_parent) if raw_parent not in (None, "", "null") else None
        raw_children = o.get("children") if "children" in o else o.get("child_outcome_ids")
        children = [str(c) for c in raw_children] if raw_children else []

        item = {
            "outcome_id": oid,
            "text": text,
            "parent": parent,
            "children": children,
            "is_current": bool(o.get("is_current", False)),
        }
        outcome_list.append(item)
        by_id[oid] = item

    if not outcome_list:
        return GoalFact(default_view=[], full_tree=[])

    # Populate children map from parents if children not explicitly given
    for item in outcome_list:
        p = item["parent"]
        if p and p in by_id:
            child_map[p].append(item["outcome_id"])

    # Determine root: first outcome with parent is None, else first outcome in list
    roots = [item for item in outcome_list if item["parent"] is None]
    root = roots[0] if roots else outcome_list[0]
    root_id = root["outcome_id"]

    # Compute depth for all outcomes
    depths: dict[str, int] = {}

    def get_depth(node_id: str, visited: set[str] | None = None) -> int:
        if node_id in depths:
            return depths[node_id]
        if visited is None:
            visited = set()
        if node_id in visited or node_id not in by_id:
            return 0
        visited.add(node_id)
        p = by_id[node_id]["parent"]
        if p is None or p not in by_id:
            d = 0
        else:
            d = get_depth(p, visited) + 1
        depths[node_id] = d
        return d

    for item in outcome_list:
        get_depth(item["outcome_id"])

    # Build full_tree (preserving input order)
    full_tree: list[GoalTreeNode] = []
    for item in outcome_list:
        oid = item["outcome_id"]
        children = item["children"] if item["children"] else child_map.get(oid, [])
        full_tree.append(
            GoalTreeNode(
                outcome_id=oid,
                text=item["text"],
                depth=depths.get(oid, 0),
                parent=item["parent"],
                children=children,
            )
        )

    # Determine current outcome ID
    curr_id = root_id
    if current_outcome_id and current_outcome_id in by_id:
        curr_id = current_outcome_id
    else:
        # Check if an outcome had is_current: True
        explicit_current = next((item["outcome_id"] for item in outcome_list if item["is_current"]), None)
        if explicit_current:
            curr_id = explicit_current

    # Trace ancestral path from root to current node
    path: list[str] = [curr_id]
    curr = curr_id
    visited_path = {curr_id}
    while True:
        p = by_id[curr]["parent"]
        if p is None or p not in by_id or p in visited_path:
            break
        path.append(p)
        visited_path.add(p)
        curr = p
    path.reverse()  # [root, ..., previous, current]

    # Current goal depth below root of this path
    d = depths.get(curr_id, len(path) - 1)

    # Thread-collapse default_view per Panel Spec §1
    if d == 0 or len(path) == 1:
        default_view = [
            GoalDefaultNode(
                outcome_id=curr_id,
                text=by_id[curr_id]["text"],
                depth=0,
                is_current=True,
            )
        ]
    elif d == 1 or len(path) == 2:
        default_view = [
            GoalDefaultNode(
                outcome_id=path[0],
                text=by_id[path[0]]["text"],
                depth=0,
                is_current=False,
            ),
            GoalDefaultNode(
                outcome_id=curr_id,
                text=by_id[curr_id]["text"],
                depth=1,
                is_current=True,
            ),
        ]
    elif d == 2 or len(path) == 3:
        default_view = [
            GoalDefaultNode(
                outcome_id=path[0],
                text=by_id[path[0]]["text"],
                depth=0,
                is_current=False,
            ),
            GoalDefaultNode(
                outcome_id=path[1],
                text=by_id[path[1]]["text"],
                depth=1,
                is_current=False,
            ),
            GoalDefaultNode(
                outcome_id=curr_id,
                text=by_id[curr_id]["text"],
                depth=2,
                is_current=True,
            ),
        ]
    else:  # d >= 3
        default_view = [
            GoalDefaultNode(
                outcome_id=path[0],
                text=by_id[path[0]]["text"],
                depth=0,
                is_current=False,
            ),
            GoalDefaultNode(
                outcome_id=path[-2],
                text=by_id[path[-2]]["text"],
                depth=depths.get(path[-2], d - 1),
                is_current=False,
            ),
            GoalDefaultNode(
                outcome_id=curr_id,
                text=by_id[curr_id]["text"],
                depth=d,
                is_current=True,
            ),
        ]

    return GoalFact(default_view=default_view, full_tree=full_tree)


def build_analysis_dict(
    ledger_rows: Iterable[dict[str, Any]],
    state_dict: dict[str, Any] | Any | None = None,
    max_pair: int | None = None,
) -> dict[str, Any]:
    """Assemble an analysis dictionary from Stage 4 quantification for runtime invariants.

    Provides the exact structure expected by inv_11 through inv_16 and inv_19:
    - pairs: list of per-pair metrics:
        pair, delta_you, delta_ai, c_you, c_ai, h_you, h_ai, you_pct, ai_pct, mode
    - creator_counts: {'you': count, 'ai': count}
    - total_requirements: int
    """
    rows = list(ledger_rows)
    if hasattr(state_dict, "to_dict"):
        state_reqs = state_dict.to_dict().get("requirements", [])
    elif isinstance(state_dict, dict):
        state_reqs = state_dict.get("requirements", [])
    elif hasattr(state_dict, "requirements"):
        state_reqs = getattr(state_dict, "requirements", [])
    else:
        state_reqs = []

    dir_facts = compute_direction(rows, max_pair=max_pair)
    dec_facts = compute_decisions(rows, state_requirements=state_reqs, max_pair=max_pair)
    mode_facts = compute_mode(rows, state_requirements=state_reqs, max_pair=max_pair)

    pairs_data: list[dict[str, Any]] = []
    total = len(dir_facts)
    for i in range(total):
        d = dir_facts[i]
        m = mode_facts[i]
        pairs_data.append({
            "pair": d.t,
            "delta_you": d.delta_you,
            "delta_ai": d.delta_ai,
            "c_you": d.c_you,
            "c_ai": d.c_ai,
            "h_you": m.signals.h_you,
            "h_ai": m.signals.h_ai,
            "you_pct": d.you_pct,
            "ai_pct": d.ai_pct,
            "mode": m.mode,
        })

    latest_dec = dec_facts[-1] if dec_facts else None
    creator_counts = {
        "you": latest_dec.you_count if latest_dec else 0,
        "ai": latest_dec.ai_count if latest_dec else 0,
    }
    total_requirements = len(latest_dec.requirements) if latest_dec else 0

    return {
        "pairs": pairs_data,
        "creator_counts": creator_counts,
        "total_requirements": total_requirements,
    }


