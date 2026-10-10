"""Evidence linking (docs/EVIDENCE_SPEC.md): anchoring rules, truth fixes T1–T5 and invariant W7.

Tier 1: exact, no network. Runs on every processed chat in data/chats.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.evidence import EvidenceIndex, anchor, audit, norm_map, parse_action
from engine.projections.workspace import project_workspace

pytestmark = pytest.mark.tier1

CHATS = Path(__file__).resolve().parent.parent / "data" / "chats"
CHAT_DIRS = sorted(d for d in CHATS.glob("c*") if (d / "state.json").exists() and (d / "dialogue.json").exists())


def _load(d: Path):
    state = json.loads((d / "state.json").read_text(encoding="utf-8"))
    dialogue = json.loads((d / "dialogue.json").read_text(encoding="utf-8"))
    ledger = [json.loads(x) for x in (d / "ledger.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    return state, dialogue, ledger


# --- anchoring rules (spec §4) ---------------------------------------------------------------------------

def test_exact_unique():
    r = anchor("warm off-white", "Keep it, but change the background to warm off-white, please.")
    assert r["match"] == "exact" and r["fragments"][0]["exact"] == "warm off-white"
    f = r["fragments"][0]
    assert f["prefix"].endswith("background to ") and f["suffix"].startswith(", please")


def test_repeated_phrase_uses_reading_order():
    text = "Use blue. Later: use blue for links."
    first = anchor("use blue", text.lower(), after=0)
    second = anchor("use blue", text.lower(), after=first["fragments"][0]["end"])
    assert first["occurrences"] == 2 and second["fragments"][0]["start"] > first["fragments"][0]["start"]


def test_normalised_markdown_quotes_and_whitespace():
    text = "We should **keep** the “warm”   tone."
    r = anchor('keep the "warm" tone', text)
    assert r["match"] == "normalized"
    f = r["fragments"][0]
    assert text[f["start"]:f["end"]] == "keep** the “warm”   tone"


def test_multipart_joined_with_ellipsis_and_wrapping_quotes():
    text = "First part here. Something in between. Second part there."
    r = anchor("First part here... Second part there", text)
    assert r["match"] == "multipart" and [f["exact"] for f in r["fragments"]] == ["First part here", "Second part there"]
    assert anchor('"Something in between."', text)["match"] == "normalized"


def test_not_found_is_never_faked():
    r = anchor("[script content]", "Here's the streamlined version: Scene one…")
    assert r == {"match": "message", "fragments": [], "occurrences": 0}
    assert anchor("", "anything")["match"] == "missing"


def test_norm_map_points_back_to_raw_text():
    raw = "A  **bold**\n\nline"
    n, idx = norm_map(raw)
    assert n == "a bold line" and len(idx) == len(n) and raw[idx[2]] == "b"


# --- whole-corpus measurements (spec §4 table) -------------------------------------------------------------

def test_corpus_anchoring_rates():
    total: dict[str, int] = {}
    for d in CHAT_DIRS:
        state, dialogue, _ = _load(d)
        for k, v in audit(EvidenceIndex(d.name, dialogue, state["actions"])).items():
            total[k] = total.get(k, 0) + v
    n = sum(total.values())
    unanchored = total.get("message", 0) + total.get("missing", 0)
    assert n >= 600, "corpus shrank unexpectedly"
    assert (n - unanchored) / n >= 0.98, f"anchoring fell below 98%: {total}"


# --- truth fixes + invariant W7 (spec §2, §4) --------------------------------------------------------------

@pytest.mark.parametrize("chat_dir", CHAT_DIRS, ids=lambda d: d.name)
def test_w7_every_evidence_is_true(chat_dir: Path):
    state, dialogue, ledger = _load(chat_dir)
    bundle = project_workspace(dialogue, state, ledger, chat_id=chat_dir.name)
    text = {(t["pair"], "human" if t["speaker"] == "user" else "ai"): t["text"] for t in dialogue}
    reqs = {(r["outcome_id"], r["req_id"]): r for r in state["requirements"]}
    slots = {(s["outcome_id"], s["slot_id"]): s for s in state["slots"]}
    resolved_into = {(s["outcome_id"], s["resolved_into"]) for s in state["slots"] if s.get("status") == "resolved" and s.get("resolved_into")}
    for atom in bundle["atoms"]:
        oid, local = atom["id"].split(":", 1)
        for e in atom["evidence"]:
            parsed = parse_action(e["actionId"])
            if e["match"] == "missing":
                assert not e["fragments"]
                continue
            # speaker and exchange come from the action id, never inferred
            assert parsed and e["speaker"] == parsed[0] and e["pair"] == parsed[1], (atom["id"], e)
            msg = text[(e["pair"], e["speaker"])]
            for f in e["fragments"]:
                assert 0 <= f["start"] < f["end"] <= len(msg) and msg[f["start"]:f["end"]] == f["exact"], (atom["id"], e["id"])
            if e["match"] == "exact":
                assert len(e["fragments"]) == 1
            if e["match"] in ("message",):
                assert not e["fragments"]
        roles = [e["role"] for e in atom["evidence"]]
        if atom["kind"] in ("requirement", "resolved"):
            r = reqs[(oid, local)]
            # T1: every creating action is kept
            created = [e["actionId"] for e in atom["evidence"] if e["role"] in ("introduced", "answered")]
            assert set(created) == set(r.get("creation_action_ids") or []) or not r.get("creation_action_ids")
            # T2: revisions are evidence
            assert sorted(e["actionId"] for e in atom["evidence"] if e["role"] == "revised") == sorted(set(r.get("revise_action_ids") or []))
            # T4: "resolved" only when the engine resolved a question into this requirement
            assert (atom["kind"] == "resolved") == ((oid, local) in resolved_into)
            # T3: never an invented speaker
            if not r.get("creation_action_ids"):
                assert atom["origin"] is None or atom["kind"] == "resolved"
        else:
            s = slots[(oid, local)]
            assert roles[0] == "asked"
            assert atom["state"] == {"resolved": "answered", "abandoned": "dropped"}.get(s["status"], "open")
            assert ("answered" in roles) == (s["status"] == "resolved")


def test_t4_answered_questions_match_engine():
    resolved = answered = 0
    for d in CHAT_DIRS:
        state, dialogue, ledger = _load(d)
        bundle = project_workspace(dialogue, state, ledger, chat_id=d.name)
        resolved += sum(1 for a in bundle["atoms"] if a["kind"] == "resolved")
        answered += sum(1 for s in state["slots"] if s.get("status") == "resolved" and s.get("resolved_into"))
    assert resolved == answered
