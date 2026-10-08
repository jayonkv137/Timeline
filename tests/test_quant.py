"""Tier 1 tests for Stage 4 Quantification (engine/quant.py).

Deterministic mathematical verification with zero network access and zero LLM calls.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from engine.quant import (
    compute_direction,
    DirectionFact,
    compute_decisions,
    DecisionsFact,
    RequirementFact,
    compute_mode,
    ModeFact,
    ModeSignals,
    ModeSplit,
    compute_timeline,
    compute_r_sum,
    TimelineFact,
    TimelineDrawer,
    DrawerRequirement,
    DrawerSlot,
    compute_goal_view,
    GoalFact,
    GoalDefaultNode,
    GoalTreeNode,
)
import jsonschema

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.tier1
def test_direction_on_frozen_fixture():
    """Verify compute_direction reproduces exact canonical fixture values @ P1."""
    fixture_ledger_path = REPO_ROOT / "data/chats/fixture_pair1/ledger.jsonl"
    assert fixture_ledger_path.exists()

    rows = []
    with open(fixture_ledger_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    assert len(rows) == 157

    facts = compute_direction(rows)
    assert len(facts) == 1

    p1 = facts[0]
    assert p1.t == 1
    assert p1.delta_you == 87.0
    assert p1.delta_ai == 314.0
    assert p1.c_you == 87.0
    assert p1.c_ai == 314.0
    assert p1.you_pct == 21.7
    assert p1.ai_pct == 78.3
    assert round(p1.you_pct + p1.ai_pct, 1) == 100.0


@pytest.mark.tier1
def test_direction_multi_pair_cumulative_accumulation():
    """Verify multi-pair cumulative sums C(t) accumulate monotonically across turns."""
    synth_rows = [
        {"pair_added": 1, "speaker": "U", "score": 10.0},
        {"pair_added": 1, "speaker": "A", "score": 30.0},
        {"pair_added": 2, "speaker": "U", "score": 15.0},
        {"pair_added": 2, "speaker": "A", "score": 25.0},
        {"pair_added": 3, "speaker": "U", "score": 5.0},
        {"pair_added": 3, "speaker": "A", "score": 15.0},
    ]

    facts = compute_direction(synth_rows)
    assert len(facts) == 3

    # Pair 1: U=10, A=30 -> C_U=10, C_A=30 -> 25.0% / 75.0%
    assert facts[0].delta_you == 10.0
    assert facts[0].delta_ai == 30.0
    assert facts[0].c_you == 10.0
    assert facts[0].c_ai == 30.0
    assert facts[0].you_pct == 25.0
    assert facts[0].ai_pct == 75.0

    # Pair 2: U=15, A=25 -> C_U=25, C_A=55 -> 31.25% -> 31.2% / 68.8%
    assert facts[1].delta_you == 15.0
    assert facts[1].delta_ai == 25.0
    assert facts[1].c_you == 25.0
    assert facts[1].c_ai == 55.0
    assert facts[1].you_pct == 31.2
    assert facts[1].ai_pct == 68.8

    # Pair 3: U=5, A=15 -> C_U=30, C_A=70 -> 30.0% / 70.0%
    assert facts[2].delta_you == 5.0
    assert facts[2].delta_ai == 15.0
    assert facts[2].c_you == 30.0
    assert facts[2].c_ai == 70.0
    assert facts[2].you_pct == 30.0
    assert facts[2].ai_pct == 70.0


@pytest.mark.tier1
def test_direction_empty_or_zero_mass():
    """Verify empty turns or zero total mass produce safe 0.0% / 0.0% splits."""
    facts = compute_direction([], max_pair=2)
    assert len(facts) == 2
    for f in facts:
        assert f.delta_you == 0.0
        assert f.delta_ai == 0.0
        assert f.c_you == 0.0
        assert f.c_ai == 0.0
        assert f.you_pct == 0.0
        assert f.ai_pct == 0.0


@pytest.mark.tier1
def test_decisions_on_frozen_fixture():
    """Verify compute_decisions matches Stage 4 Pair 1 Results.md table exactly."""
    fixture_dir = REPO_ROOT / "data/chats/fixture_pair1"
    with open(fixture_dir / "ledger.jsonl", "r", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    with open(fixture_dir / "state.json", "r", encoding="utf-8") as f:
        state = json.load(f)

    fallback_example = (
        "Final production scene generations must use the Style "
        "Anchor plus a texture crop plus a color swatch as triple-references"
    )

    facts = compute_decisions(
        ledger_rows=rows,
        state_requirements=state.get("requirements", []),
        fallback_latest_ai_example=fallback_example,
    )
    assert len(facts) == 1
    p1 = facts[0]

    # Decisions counter: 4 you · 10 AI over 14 requirements
    assert p1.you_count == 4
    assert p1.ai_count == 10
    assert len(p1.requirements) == 14
    assert p1.latest_ai_example == fallback_example

    # Expected canonical table from Stage 4 Pair 1 Results.md
    expected_table = {
        ("outcome 1", "req 1"): ("U", 14.0, 6.0, "grey"),
        ("outcome 1", "req 2"): ("U", 15.0, 23.0, "grey"),  # tie-break: earliest U(1,5) -> U
        ("outcome 1", "req 3"): ("A", 12.0, 37.0, "grey"),  # corrected: 37.0, not 42
        ("outcome 1", "req 4"): ("A", 3.0, 16.0, "grey"),
        ("outcome 2", "req 1"): ("U", 10.0, 33.0, "grey"),
        ("outcome 3", "req 1"): ("A", 5.0, 55.0, "grey"),
        ("outcome 3", "req 2"): ("A", 5.0, 33.0, "grey"),
        ("outcome 4", "req 1"): ("A", 2.0, 10.0, "grey"),
        ("outcome 4", "req 2"): ("A", 3.0, 26.0, "grey"),
        ("outcome 5", "req 1"): ("A", 1.0, 18.0, "grey"),
        ("outcome 5", "req 2"): ("A", 0.0, 10.0, "orange"),  # only orange chip
        ("outcome 6", "req 1"): ("U", 12.0, 14.0, "grey"),
        ("outcome 6", "req 2"): ("A", 3.0, 18.0, "grey"),
        ("outcome 6", "req 3"): ("A", 2.0, 15.0, "grey"),
    }

    for key, (exp_creator, exp_m_you, exp_m_ai, exp_chip) in expected_table.items():
        assert key in p1.requirements, f"Missing requirement {key}"
        rf = p1.requirements[key]
        assert rf.creator == exp_creator, f"{key} creator: {rf.creator} != {exp_creator}"
        assert rf.mass_you == exp_m_you, f"{key} mass_you: {rf.mass_you} != {exp_m_you}"
        assert rf.mass_ai == exp_m_ai, f"{key} mass_ai: {rf.mass_ai} != {exp_m_ai}"
        assert rf.chip == exp_chip, f"{key} chip: {rf.chip} != {exp_chip}"


@pytest.mark.tier1
def test_decisions_creator_tie_break_rules():
    """Verify earliest creation action tie-break: pair order, then U before A, then sequence."""
    from engine.quant import action_sort_key

    # Within same pair: U(1,5) precedes A(1,2)
    assert action_sort_key("U(1,5)") < action_sort_key("A(1,2)")
    # Pair ordering wins: A(1,9) precedes U(2,1)
    assert action_sort_key("A(1,9)") < action_sort_key("U(2,1)")
    # Sequence order within same speaker: U(1,1) precedes U(1,2)
    assert action_sort_key("U(1,1)") < action_sort_key("U(1,2)")
    assert action_sort_key("A(1,10)") < action_sort_key("A(1,11)")


@pytest.mark.tier1
def test_decisions_chip_colors_classification():
    """Verify chip color assignments: blue for AI mass 0, orange for user mass 0, grey for straddling."""
    synth_rows = [
        # Req 1: user-only -> blue
        {"pair_added": 1, "speaker": "U", "score": 5.0, "outcome_id": "o1", "req_id": "r1", "kind": "creation", "action_id": "U(1,1)"},
        {"pair_added": 1, "speaker": "U", "score": 3.0, "outcome_id": "o1", "req_id": "r1", "kind": "labeled", "action_id": "U(1,2)"},
        # Req 2: AI-only -> orange
        {"pair_added": 1, "speaker": "A", "score": 5.0, "outcome_id": "o1", "req_id": "r2", "kind": "creation", "action_id": "A(1,1)"},
        # Req 3: straddling -> grey
        {"pair_added": 1, "speaker": "U", "score": 5.0, "outcome_id": "o1", "req_id": "r3", "kind": "creation", "action_id": "U(1,3)"},
        {"pair_added": 1, "speaker": "A", "score": 2.0, "outcome_id": "o1", "req_id": "r3", "kind": "labeled", "action_id": "A(1,2)"},
    ]

    facts = compute_decisions(synth_rows)
    assert len(facts) == 1
    reqs = facts[0].requirements

    assert reqs[("o1", "r1")].chip == "blue"
    assert reqs[("o1", "r2")].chip == "orange"
    assert reqs[("o1", "r3")].chip == "grey"


@pytest.mark.tier1
def test_truncate_clause():
    """Verify truncate_clause truncates at clause boundaries without rewording."""
    from engine.quant import truncate_clause

    short = "Simple requirement text"
    assert truncate_clause(short) == "Simple requirement text"

    long_with_comma = (
        "The decomposition must cover exactly 8 specified layers, including color, linework, texture, "
        "form, lighting, composition, mood, and cultural lineage across both source files"
    )
    res = truncate_clause(long_with_comma, max_chars=65)
    assert len(res) <= 65
    assert not res.endswith(",")
    assert res == "The decomposition must cover exactly 8 specified layers"

    res80 = truncate_clause(long_with_comma, max_chars=80)
    assert len(res80) <= 80
    assert res80 == "The decomposition must cover exactly 8 specified layers, including color"


@pytest.mark.tier1
def test_mode_on_frozen_fixture():
    """Verify compute_mode reproduces exact canonical fixture HOW values @ P1."""
    fixture_dir = REPO_ROOT / "data/chats/fixture_pair1"
    with open(fixture_dir / "ledger.jsonl", "r", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    with open(fixture_dir / "state.json", "r", encoding="utf-8") as f:
        state = json.load(f)

    facts = compute_mode(
        ledger_rows=rows,
        state_requirements=state.get("requirements", []),
    )
    assert len(facts) == 1
    p1 = facts[0]

    # Mode classification: COPILOT
    assert p1.t == 1
    assert p1.mode == "COPILOT"
    assert p1.inherited_mode == "COPILOT"

    # Signals: w_you=4, w_ai=10, h_you=47.0, h_ai=239.0, substantive_user=True
    assert p1.signals.w_you == 4
    assert p1.signals.w_ai == 10
    assert p1.signals.h_you == 47.0
    assert p1.signals.h_ai == 239.0
    assert p1.signals.substantive_user is True

    # Running mode split: 100.0% COPILOT
    assert p1.split.centaur_pct == 0.0
    assert p1.split.copilot_pct == 100.0
    assert p1.split.autopilot_pct == 0.0


@pytest.mark.tier1
def test_mode_all_classification_branches():
    """Verify all four classification branches of Pipeline Spec §10.5."""
    # Branch 1: w_you >= w_ai and h_ai <= h_you -> CENTAUR
    rows_centaur = [
        {"pair_added": 1, "speaker": "U", "score": 5.0, "outcome_id": "o1", "req_id": "r1", "kind": "creation", "action_id": "U(1,1)"},
        {"pair_added": 1, "speaker": "U", "score": 5.0, "outcome_id": "o1", "req_id": "r2", "kind": "creation", "action_id": "U(1,2)"},
        {"pair_added": 1, "speaker": "A", "score": 5.0, "outcome_id": "o1", "req_id": "r3", "kind": "creation", "action_id": "A(1,1)"},
        {"pair_added": 1, "speaker": "U", "score": 10.0, "outcome_id": "o1", "req_id": "r1", "kind": "labeled", "role": "SHAPER"},
        {"pair_added": 1, "speaker": "A", "score": 5.0, "outcome_id": "o1", "req_id": "r1", "kind": "labeled", "role": "EXECUTOR"},
    ]
    fact1 = compute_mode(rows_centaur)[0]
    assert fact1.signals.w_you == 2
    assert fact1.signals.w_ai == 1
    assert fact1.signals.h_you == 10.0
    assert fact1.signals.h_ai == 5.0
    assert fact1.mode == "CENTAUR"

    # Branch 2: w_you >= w_ai and h_ai > h_you -> COPILOT
    rows_copilot_1 = [
        {"pair_added": 1, "speaker": "U", "score": 5.0, "outcome_id": "o1", "req_id": "r1", "kind": "creation", "action_id": "U(1,1)"},
        {"pair_added": 1, "speaker": "U", "score": 5.0, "outcome_id": "o1", "req_id": "r2", "kind": "creation", "action_id": "U(1,2)"},
        {"pair_added": 1, "speaker": "A", "score": 5.0, "outcome_id": "o1", "req_id": "r3", "kind": "creation", "action_id": "A(1,1)"},
        {"pair_added": 1, "speaker": "U", "score": 5.0, "outcome_id": "o1", "req_id": "r1", "kind": "labeled", "role": "SHAPER"},
        {"pair_added": 1, "speaker": "A", "score": 15.0, "outcome_id": "o1", "req_id": "r1", "kind": "labeled", "role": "EXECUTOR"},
    ]
    fact2 = compute_mode(rows_copilot_1)[0]
    assert fact2.signals.w_you == 2
    assert fact2.signals.w_ai == 1
    assert fact2.signals.h_you == 5.0
    assert fact2.signals.h_ai == 15.0
    assert fact2.mode == "COPILOT"

    # Branch 3: w_ai > w_you and not substantive_user -> AUTOPILOT
    rows_autopilot = [
        {"pair_added": 1, "speaker": "A", "score": 5.0, "outcome_id": "o1", "req_id": "r1", "kind": "creation", "action_id": "A(1,1)"},
        {"pair_added": 1, "speaker": "A", "score": 5.0, "outcome_id": "o1", "req_id": "r2", "kind": "creation", "action_id": "A(1,2)"},
        {"pair_added": 1, "speaker": "U", "score": 1.0, "outcome_id": "o1", "req_id": "r1", "kind": "labeled", "role": "OTHER"},  # score < 2, not SHAPER
        {"pair_added": 1, "speaker": "A", "score": 10.0, "outcome_id": "o1", "req_id": "r1", "kind": "labeled", "role": "EXECUTOR"},
    ]
    fact3 = compute_mode(rows_autopilot)[0]
    assert fact3.signals.w_you == 0
    assert fact3.signals.w_ai == 2
    assert fact3.signals.substantive_user is False
    assert fact3.mode == "AUTOPILOT"

    # Branch 4: w_ai > w_you and substantive_user -> COPILOT
    rows_copilot_2 = [
        {"pair_added": 1, "speaker": "A", "score": 5.0, "outcome_id": "o1", "req_id": "r1", "kind": "creation", "action_id": "A(1,1)"},
        {"pair_added": 1, "speaker": "A", "score": 5.0, "outcome_id": "o1", "req_id": "r2", "kind": "creation", "action_id": "A(1,2)"},
        {"pair_added": 1, "speaker": "U", "score": 2.0, "outcome_id": "o1", "req_id": "r1", "kind": "labeled", "role": "SHAPER"},  # substantive
        {"pair_added": 1, "speaker": "A", "score": 10.0, "outcome_id": "o1", "req_id": "r1", "kind": "labeled", "role": "EXECUTOR"},
    ]
    fact4 = compute_mode(rows_copilot_2)[0]
    assert fact4.signals.w_you == 0
    assert fact4.signals.w_ai == 2
    assert fact4.signals.substantive_user is True
    assert fact4.mode == "COPILOT"


@pytest.mark.tier1
def test_mode_quiet_pair_and_running_split():
    """Verify quiet pair inherits previous mode and is excluded from running split calculation."""
    synth_rows = [
        # Pair 1: Centaur (U creates r1, delta=10)
        {"pair_added": 1, "speaker": "U", "score": 5.0, "outcome_id": "o1", "req_id": "r1", "kind": "creation", "action_id": "U(1,1)"},
        {"pair_added": 1, "speaker": "U", "score": 5.0, "outcome_id": "o1", "req_id": "r1", "kind": "labeled", "role": "SHAPER"},
        # Pair 2: Quiet (no rows, delta=0)
        # Pair 3: Autopilot (A creates r2, r3, user silent)
        {"pair_added": 3, "speaker": "A", "score": 5.0, "outcome_id": "o1", "req_id": "r2", "kind": "creation", "action_id": "A(3,1)"},
        {"pair_added": 3, "speaker": "A", "score": 5.0, "outcome_id": "o1", "req_id": "r3", "kind": "creation", "action_id": "A(3,2)"},
        {"pair_added": 3, "speaker": "A", "score": 5.0, "outcome_id": "o1", "req_id": "r2", "kind": "labeled", "role": "EXECUTOR"},
    ]

    facts = compute_mode(synth_rows, max_pair=3)
    assert len(facts) == 3

    # Pair 1: CENTAUR -> split: 100% CENTAUR
    assert facts[0].mode == "CENTAUR"
    assert facts[0].split.centaur_pct == 100.0
    assert facts[0].split.copilot_pct == 0.0
    assert facts[0].split.autopilot_pct == 0.0

    # Pair 2: QUIET -> inherits CENTAUR, split unchanged (100% CENTAUR)
    assert facts[1].mode == "QUIET"
    assert facts[1].inherited_mode == "CENTAUR"
    assert facts[1].split.centaur_pct == 100.0
    assert facts[1].split.copilot_pct == 0.0
    assert facts[1].split.autopilot_pct == 0.0

    # Pair 3: AUTOPILOT -> 2 non-quiet pairs: 1 CENTAUR, 1 AUTOPILOT -> 50% / 50%
    assert facts[2].mode == "AUTOPILOT"
    assert facts[2].inherited_mode == "AUTOPILOT"
    assert facts[2].split.centaur_pct == 50.0
    assert facts[2].split.copilot_pct == 0.0
    assert facts[2].split.autopilot_pct == 50.0


@pytest.mark.tier1
def test_timeline_on_frozen_fixture():
    """Verify compute_timeline matches frozen fixture panel_bundle.json timeline exactly."""
    fixture_dir = REPO_ROOT / "data/chats/fixture_pair1"
    with open(fixture_dir / "ledger.jsonl", "r", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    with open(fixture_dir / "state.json", "r", encoding="utf-8") as f:
        state = json.load(f)
    with open(fixture_dir / "panel_bundle.json", "r", encoding="utf-8") as f:
        bundle = json.load(f)

    facts = compute_timeline(
        ledger_rows=rows,
        state_requirements=state.get("requirements", []),
        state_slots=state.get("slots", []),
        operations_log=state.get("operations_log", []),
        summary_by_pair={1: "adding Style DNA framework"},
    )
    assert len(facts) == 1
    p1 = facts[0]

    # Verify collapsed timeline row
    exp_tl = bundle["pairs"][0]["timeline"]
    assert p1.pair == exp_tl["pair"]
    assert p1.delta_you == exp_tl["delta_you"]
    assert p1.delta_ai == exp_tl["delta_ai"]
    assert p1.summary == exp_tl["summary"]

    # Verify drawer requirements (all 14 items)
    exp_reqs = exp_tl["drawer"]["requirements"]
    assert len(p1.drawer.requirements) == len(exp_reqs) == 14

    for actual, expected in zip(p1.drawer.requirements, exp_reqs):
        assert actual.outcome_id == expected["outcome_id"]
        assert actual.req_id == expected["req_id"]
        assert actual.label == expected["label"]
        assert actual.op == expected["op"]
        assert actual.delta_you == expected["delta_you"]
        assert actual.delta_ai == expected["delta_ai"]
        assert actual.chip == expected["chip"]

    # Verify drawer slots (all 5 items)
    exp_slots = exp_tl["drawer"]["slots"]
    assert len(p1.drawer.slots) == len(exp_slots) == 5

    for actual, expected in zip(p1.drawer.slots, exp_slots):
        assert actual.slot_id == expected["slot_id"]
        assert actual.origin == expected["origin"]
        assert actual.status == expected["status"]
        assert actual.resolved_into == expected["resolved_into"]


@pytest.mark.tier1
def test_r_sum_template_rules():
    """Verify R-SUM deterministic template rules per PANEL_SPEC §4.5."""
    # 1. Requirement op present: verb + label/description (<= 5 words)
    r1 = DrawerRequirement(outcome_id="o1", req_id="r1", label="R1", op="create", delta_you=10.0, delta_ai=5.0, chip="grey")
    assert compute_r_sum([r1], []) == "adding R1"

    r2 = DrawerRequirement(outcome_id="o1", req_id="r2", label="R2", op="revise", delta_you=2.0, delta_ai=20.0, chip="grey")
    # r2 has higher delta (22 > 15), so it wins
    assert compute_r_sum([r1, r2], []) == "revising R2"

    # With requirement text
    req_texts = {("o1", "r2"): "Database migration pipeline script setup"}
    res = compute_r_sum([r1, r2], [], req_texts=req_texts)
    assert len(res.split()) <= 5
    assert res.startswith("revising")

    # 2. Slot ops only: 1 slot -> "raising an open question"
    s1 = DrawerSlot(slot_id="s1", origin="AI", status="open")
    assert compute_r_sum([], [s1]) == "raising an open question"

    # Multiple slots -> "parking N questions"
    s2 = DrawerSlot(slot_id="s2", origin="user", status="open")
    s3 = DrawerSlot(slot_id="s3", origin="AI", status="open")
    assert compute_r_sum([], [s1, s2, s3]) == "parking 3 questions"

    # 3. Empty -> "execution only"
    assert compute_r_sum([], []) == "execution only"


@pytest.mark.tier1
def test_timeline_multi_pair_drawer_scoping_and_chips():
    """Verify per-turn scoping (bars show only mass added that turn) and chip progression."""
    synth_rows = [
        # Pair 1: U creates r1 (U=10, A=0 -> blue chip)
        {"pair_added": 1, "speaker": "U", "score": 10.0, "outcome_id": "o1", "req_id": "r1", "kind": "creation", "action_id": "U(1,1)"},
        # Pair 2: A contributes to r1 (U=0, A=15 in turn 2 -> turn deltas are U=0, A=15; cumulative is U=10, A=15 -> grey chip)
        #         A creates r2 (U=0, A=5 -> orange chip)
        {"pair_added": 2, "speaker": "A", "score": 15.0, "outcome_id": "o1", "req_id": "r1", "kind": "labeled", "action_id": "A(2,1)"},
        {"pair_added": 2, "speaker": "A", "score": 5.0, "outcome_id": "o1", "req_id": "r2", "kind": "creation", "action_id": "A(2,2)"},
    ]

    facts = compute_timeline(synth_rows, max_pair=2)
    assert len(facts) == 2

    # Pair 1
    p1 = facts[0]
    assert p1.delta_you == 10.0
    assert p1.delta_ai == 0.0
    assert len(p1.drawer.requirements) == 1
    r1_p1 = p1.drawer.requirements[0]
    assert r1_p1.label == "R1"
    assert r1_p1.delta_you == 10.0
    assert r1_p1.delta_ai == 0.0
    assert r1_p1.chip == "blue"  # A mass is 0

    # Pair 2
    p2 = facts[1]
    assert p2.delta_you == 0.0
    assert p2.delta_ai == 20.0
    assert len(p2.drawer.requirements) == 2

    # R1 in pair 2: per-turn delta is U=0.0, A=15.0 (per-turn scoping!)
    r1_p2 = [r for r in p2.drawer.requirements if r.req_id == "r1"][0]
    assert r1_p2.delta_you == 0.0
    assert r1_p2.delta_ai == 15.0
    assert r1_p2.chip == "grey"  # cumulative U=10, A=15 -> straddling

    # R2 in pair 2: A-only creation
    r2_p2 = [r for r in p2.drawer.requirements if r.req_id == "r2"][0]
    assert r2_p2.delta_you == 0.0
    assert r2_p2.delta_ai == 5.0
    assert r2_p2.chip == "orange"  # U mass is 0


@pytest.mark.tier1
def test_goal_view_on_frozen_fixture():
    """Verify compute_goal_view reproduces exact canonical fixture values @ P1."""
    fixture_state_path = REPO_ROOT / "data/chats/fixture_pair1/state.json"
    fixture_bundle_path = REPO_ROOT / "data/chats/fixture_pair1/panel_bundle.json"
    assert fixture_state_path.exists()
    assert fixture_bundle_path.exists()

    with open(fixture_state_path, "r", encoding="utf-8") as f:
        state = json.load(f)
    with open(fixture_bundle_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    expected_goal = bundle["pairs"][0]["goal"]
    goal_fact = compute_goal_view(state["outcomes"])
    actual_goal = goal_fact.to_dict()

    assert actual_goal == expected_goal

    # Check against panel_bundle schema for goal
    schema_path = REPO_ROOT / "engine/schemas/panel_bundle.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        full_schema = json.load(f)
    goal_schema = full_schema["properties"]["pairs"]["items"]["properties"]["goal"]
    jsonschema.validate(instance=actual_goal, schema=goal_schema)


@pytest.mark.tier1
def test_goal_view_depth_cases():
    """Verify thread-collapse rules for d=0, d=1, d=2, d=3, d=4 per Panel Spec §1."""
    # Synthetic tree with 5 levels:
    # o1 (root, d=0) -> o2 (d=1) -> o3 (d=2) -> o4 (d=3) -> o5 (d=4)
    outcomes = [
        {"id": "o1", "text": "Root Goal", "parent": None, "children": ["o2"]},
        {"id": "o2", "text": "Sub Goal 1", "parent": "o1", "children": ["o3"]},
        {"id": "o3", "text": "Sub Goal 2", "parent": "o2", "children": ["o4"]},
        {"id": "o4", "text": "Sub Goal 3", "parent": "o3", "children": ["o5"]},
        {"id": "o5", "text": "Sub Goal 4", "parent": "o4", "children": []},
    ]

    schema_path = REPO_ROOT / "engine/schemas/panel_bundle.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        full_schema = json.load(f)
    goal_schema = full_schema["properties"]["pairs"]["items"]["properties"]["goal"]

    # Case d = 0 (root is current)
    g0 = compute_goal_view(outcomes, current_outcome_id="o1")
    d0_dict = g0.to_dict()
    jsonschema.validate(instance=d0_dict, schema=goal_schema)
    assert len(g0.default_view) == 1
    assert g0.default_view[0].outcome_id == "o1"
    assert g0.default_view[0].depth == 0
    assert g0.default_view[0].is_current is True

    # Case d = 1 (child is current)
    g1 = compute_goal_view(outcomes, current_outcome_id="o2")
    d1_dict = g1.to_dict()
    jsonschema.validate(instance=d1_dict, schema=goal_schema)
    assert len(g1.default_view) == 2
    assert [n.outcome_id for n in g1.default_view] == ["o1", "o2"]
    assert [n.depth for n in g1.default_view] == [0, 1]
    assert [n.is_current for n in g1.default_view] == [False, True]

    # Case d = 2 (grandchild is current)
    g2 = compute_goal_view(outcomes, current_outcome_id="o3")
    d2_dict = g2.to_dict()
    jsonschema.validate(instance=d2_dict, schema=goal_schema)
    assert len(g2.default_view) == 3
    assert [n.outcome_id for n in g2.default_view] == ["o1", "o2", "o3"]
    assert [n.depth for n in g2.default_view] == [0, 1, 2]
    assert [n.is_current for n in g2.default_view] == [False, False, True]

    # Case d = 3 (great-grandchild is current) -> chip triggers (gap 2 - 0 - 1 = 1 more)
    g3 = compute_goal_view(outcomes, current_outcome_id="o4")
    d3_dict = g3.to_dict()
    jsonschema.validate(instance=d3_dict, schema=goal_schema)
    assert len(g3.default_view) == 3
    assert [n.outcome_id for n in g3.default_view] == ["o1", "o3", "o4"]
    assert [n.depth for n in g3.default_view] == [0, 2, 3]
    assert [n.is_current for n in g3.default_view] == [False, False, True]
    # Check hidden gap
    gap3 = g3.default_view[1].depth - g3.default_view[0].depth - 1
    assert gap3 == 1  # "⌄ 1 more", never "0 more"

    # Case d = 4 (deepest child is current) -> chip triggers (gap 3 - 0 - 1 = 2 more)
    g4 = compute_goal_view(outcomes, current_outcome_id="o5")
    d4_dict = g4.to_dict()
    jsonschema.validate(instance=d4_dict, schema=goal_schema)
    assert len(g4.default_view) == 3
    assert [n.outcome_id for n in g4.default_view] == ["o1", "o4", "o5"]
    assert [n.depth for n in g4.default_view] == [0, 3, 4]
    assert [n.is_current for n in g4.default_view] == [False, False, True]
    gap4 = g4.default_view[1].depth - g4.default_view[0].depth - 1
    assert gap4 == 2  # "⌄ 2 more"


@pytest.mark.tier1
def test_goal_view_edge_cases():
    """Verify empty outcomes and tree structural details."""
    # Empty outcomes
    empty_fact = compute_goal_view([])
    assert empty_fact.default_view == []
    assert empty_fact.full_tree == []
    assert empty_fact.to_dict() == {"default_view": [], "full_tree": []}

    # Branching tree: children lists correctly populated
    branching = [
        {"id": "root", "text": "Main", "parent": None},
        {"id": "b1", "text": "Branch 1", "parent": "root"},
        {"id": "b2", "text": "Branch 2", "parent": "root"},
        {"id": "leaf", "text": "Leaf", "parent": "b2"},
    ]
    fact = compute_goal_view(branching, current_outcome_id="leaf")
    assert len(fact.full_tree) == 4
    root_node = fact.full_tree[0]
    assert root_node.children == ["b1", "b2"]
    assert root_node.depth == 0

    leaf_node = [n for n in fact.full_tree if n.outcome_id == "leaf"][0]
    assert leaf_node.depth == 2
    assert leaf_node.children == []

    # default view for leaf (d=2): root, b2, leaf
    assert [n.outcome_id for n in fact.default_view] == ["root", "b2", "leaf"]
    assert [n.depth for n in fact.default_view] == [0, 1, 2]



