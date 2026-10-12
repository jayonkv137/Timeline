"""Tests for engine/brainmap.py — BRAIN_REGIONS_SPEC (track B1.1). All tier1: local files, no network, no LLM."""
import copy
import json
from pathlib import Path

import pytest

from engine import brainmap as bm

REPO = Path(__file__).resolve().parents[1]


def _chat(tmp: Path, cid: str, title: str, messages: list[str], ts: str = "2026-01-01T10:00:00Z", task: str = "research") -> Path:
    d = tmp / cid
    d.mkdir(parents=True)
    turns = []
    for k, text in enumerate(messages):
        turns.append({"pair": k // 2 + 1, "speaker": "user" if k % 2 == 0 else "ai", "text": text, "attachments": [], "ts": ts})
    (d / "dialogue.json").write_text(json.dumps(turns))
    (d / "meta.json").write_text(json.dumps({"title": title, "taskType": task}))
    return d


FILM = "storyboard the short film scene: camera dolly shot, character lighting, colour grade, frame composition, film cut"
GERMAN = "German grammar practice: accusative prepositions, vocabulary flashcards, sentence drills, articles der die das"
GARDEN = "tomato seedlings: compost, watering schedule, greenhouse soil, harvest timing, pruning the vines"


def _small_library(tmp: Path) -> list[dict]:
    _chat(tmp, "film1", "Short film storyboard", [FILM, "camera dolly shot plan and character lighting for the film scene", FILM], "2026-01-01T10:00:00Z")
    _chat(tmp, "film2", "Short film colour grade", [FILM + " colour grade", "film frame composition and colour grade notes", FILM], "2026-01-02T10:00:00Z")
    _chat(tmp, "film2b", "Short film colour grade", [FILM + " colour grade", "film frame composition and colour grade notes", FILM], "2026-01-02T12:00:00Z")
    _chat(tmp, "german1", "German accusative drills", [GERMAN, "accusative preposition drills with der die das articles", GERMAN], "2026-01-03T10:00:00Z", "learning")
    _chat(tmp, "german2", "German vocabulary flashcards", [GERMAN + " flashcards", "vocabulary flashcards for german articles", GERMAN], "2026-01-04T10:00:00Z", "planning")
    _chat(tmp, "garden", "Tomato garden", [GARDEN, "pruning and compost for tomato vines", GARDEN], "2026-01-05T10:00:00Z")
    return bm.collect([tmp])


@pytest.fixture(scope="module")
def corpus_map():
    chats = bm.collect([REPO / "data" / "corpus"], REPO / "data" / "chats")
    return chats, bm.build_map(chats)


@pytest.mark.tier1
def test_near_duplicates_are_continued_and_share_a_region(tmp_path):
    m = bm.build_map(_small_library(tmp_path))
    link = next(l for l in m["links"] if {l["a"], l["b"]} == {"film2", "film2b"})
    assert link["type"] == "continued" and link["score"] >= bm.NEAR_DUPLICATE
    assert m["chats"]["film2"]["region"] is not None
    assert m["chats"]["film2"]["region"] == m["chats"]["film2b"]["region"]


@pytest.mark.tier1
def test_unrelated_chat_stays_solitary(tmp_path):
    m = bm.build_map(_small_library(tmp_path))
    assert m["chats"]["garden"]["region"] is None
    assert m["areas"][m["chats"]["garden"]["area"]]["solitary"] is True


@pytest.mark.tier1
def test_task_type_never_moves_a_chat(tmp_path):
    chats = _small_library(tmp_path)
    before = bm.build_map(chats)
    relabelled = copy.deepcopy(chats)
    for c in relabelled:
        c["taskType"] = "coding"
    after = bm.build_map(relabelled)
    for cid in before["chats"]:
        for key in ("area", "region", "side", "direction"):
            assert before["chats"][cid][key] == after["chats"][cid][key]


@pytest.mark.tier1
def test_existing_chats_stay_pinned_when_a_chat_is_added(tmp_path):
    chats = _small_library(tmp_path)
    first = bm.build_map(chats[:-1])
    second = bm.build_map(chats, previous=first)
    assert second["version"] == first["version"] + 1
    for cid, placed in first["chats"].items():
        assert second["chats"][cid]["direction"] == placed["direction"]
        assert second["chats"][cid]["side"] == placed["side"]


@pytest.mark.tier1
def test_owner_region_names_survive_a_rebuild(tmp_path):
    chats = _small_library(tmp_path)
    first = bm.build_map(chats)
    rid = first["chats"]["german1"]["region"]
    first["regions"][rid].update(name="German lessons", nameSource="owner")
    second = bm.build_map(chats, previous=first)
    renamed = second["regions"][second["chats"]["german1"]["region"]]
    assert renamed["name"] == "German lessons" and renamed["nameSource"] == "owner"


@pytest.mark.tier1
def test_build_is_deterministic(tmp_path):
    chats = _small_library(tmp_path)
    assert json.dumps(bm.build_map(chats), sort_keys=True) == json.dumps(bm.build_map(chats), sort_keys=True)


@pytest.mark.tier1
def test_every_link_carries_its_evidence(corpus_map):
    _, m = corpus_map
    assert m["links"]
    for link in m["links"]:
        assert link["type"] in {"continued", "reused", "similar"}
        assert 0 <= link["score"] <= 1.0001
        ev = link["evidence"]
        assert ev.get("keywords") or ev.get("passages") or ev.get("reason")
        if link["type"] == "continued":
            assert ev.get("reason")
        if link["type"] == "reused":
            assert ev.get("sharedPassages", 0) >= 3


@pytest.mark.tier1
def test_directions_lie_on_the_lateral_cortex(corpus_map):
    _, m = corpus_map
    for placed in list(m["chats"].values()) + list(m["areas"].values()):
        x, y, z = placed["direction"]
        assert abs(x * x + y * y + z * z - 1) < 1e-3
        assert z > -0.1 and y > -0.84 and not (y < -0.48 and x > 0.12)
        assert placed["side"] in (-1, 1)


@pytest.mark.tier1
def test_corpus_reproduces_the_study_regions(corpus_map):
    """BRAIN_REGIONS_SPEC §9.2: topics cut across the owner's task types."""
    _, m = corpus_map
    region = lambda cid: m["chats"][cid]["region"]
    german = ["c37_learning_medium", "c41_planning_medium", "c42_planning_medium", "c43_learning_medium", "c48_learning_long"]
    rooms = ["c22_writing_long", "c38_planning_medium", "c40_planning_medium"]
    paperwork = ["c26_planning_medium", "c50_planning_long"]
    film = ["c12_creative_medium", "c19_creative_long", "c25_creative_long", "c32_creative_long", "c33_creative_medium"]
    for group in (german, rooms, paperwork, film):
        assert region(group[0]) is not None and len({region(c) for c in group}) == 1, group
    assert len({region(german[0]), region(rooms[0]), region(paperwork[0]), region(film[0])}) == 4
    # Room hunting and German paperwork are two regions of one area: life in Bremen.
    area = lambda cid: m["chats"][cid]["area"]
    assert len({area(c) for c in rooms + paperwork}) == 1


@pytest.mark.tier1
def test_corpus_near_duplicate_pairs_are_continued(corpus_map):
    _, m = corpus_map
    continued = {frozenset((l["a"], l["b"])) for l in m["links"] if l["type"] == "continued"}
    for pair in [("c06_planning_long", "c55_creative_long"), ("c18_research_long", "c53_research_long"),
                 ("c34_planning_long", "c54_planning_long"), ("c36_coding_long", "c52_coding_long")]:
        assert frozenset(pair) in continued, pair


@pytest.mark.tier1
def test_cli_writes_a_map(tmp_path, capsys):
    from engine.__main__ import main
    _small_library(tmp_path / "lib")
    out = tmp_path / "brain_map.json"
    assert main(["brainmap", str(tmp_path / "lib"), "-o", str(out)]) == 0
    data = json.loads(out.read_text())
    assert set(data) >= {"version", "method", "chats", "areas", "regions", "links"}
    assert "brain map v1" in capsys.readouterr().out
