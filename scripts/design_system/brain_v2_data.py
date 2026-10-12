"""Data for the simple brain (docs/design-system/foundations/BRAIN_V2_SPEC.md). Zero LLM, deterministic.

Universal layer: 8 life-wide domains, the same for every person and always in the same lobe (like brain anatomy),
adapted from OpenAI "How People Use ChatGPT" topics and Anthropic Economic Index O*NET groups.
Personal layer: the person's own regions from engine/brainmap.py (BRAIN_REGIONS_SPEC).
Per chat: who led (human share of measured mass), size (mass), outcomes (the chat's own graph), decisions.

Writes web/src/brain-v2/brain_v2.generated.json.
"""
from __future__ import annotations

import json
import math
import sys
import tempfile
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from engine.brainmap import build_map, collect, tokens  # noqa: E402
from engine.projections.workspace import project_chat_directory  # noqa: E402

# Lobe anchors in the Brain's direction space: x = back(+)/front(-), y = up, z = lateral surface.
# Placement follows the brain's own functional map as a metaphor: vision at the back, language low at the side,
# planning at the front.
DOMAINS = [
    ("work", "Work & career", (-0.74, 0.34, 0.58),
     "job career internship interview company business client application cover resume cv salary team manager strategy presentation employer hiring role"),
    ("research", "Research & ideas", (-0.22, 0.74, 0.63),
     "research paper papers literature source sources theory evidence analysis analyse academic study framework concept society topic topics reading role contribution pattern patterns requirement requirements analogy analogies explain"),
    ("tech", "Technology & code", (0.30, 0.70, 0.65),
     "code coding program programming software website web app bug debug api database python javascript typescript react css html deploy server github function component engine schema pipeline frontend backend script figma svg interface implementation repository"),
    ("creative", "Creative & media", (0.82, 0.12, 0.56),
     "image video film photo photograph art artistic character animation shot scene music illustration midjourney render cinematic storyboard kling seedance runway footage camera lighting colour color"),
    ("health", "Health & personal", (0.50, -0.36, 0.79),
     "health sleep fitness diet symptom doctor therapy relationship dating friend family feeling feelings bumble wedding birthday personal"),
    ("learning", "Learning & education", (0.20, -0.52, 0.83),
     "learn learning lesson course study vocabulary grammar practice exam tutor flashcard quiz language session teach teaching preposition word"),
    ("writing", "Writing & communication", (-0.50, -0.46, 0.73),
     "write writing email letter message text edit correction proofread translate translation bio post essay wording phrasing tone draft reply"),
    ("life", "Life & admin", (-0.86, -0.06, 0.50),
     "rent apartment room flat visa bank tax insurance contract bill bills schufa permit travel booking budget move moving landlord registration residence extension"),
]
OTHER = ("other", "Other", (0.0, 0.05, 1.0))
LEX = {key: set(tokens(words)) | set(words.split()) for key, _, _, words in DOMAINS}


def classify(chat: dict) -> tuple[str, float]:
    """Zero-cost keyword baseline: title words count 3x, message words by density. Returns (domain, margin)."""
    title = tokens(chat["title"])
    body = tokens(" ".join(chat["text"].split()[:4000]))
    score = Counter()
    for key, lex in LEX.items():
        score[key] = 3 * sum(w in lex for w in title) + sum(w in lex for w in body) / max(1, len(body)) * 400
    (best, s1), (_, s2) = score.most_common(2)
    if s1 <= 0.5:
        return "other", 0.0
    return best, round((s1 - s2) / s1, 2)


def _norm(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return [c / n for c in v]


def _tangent(d):
    up = (0.0, 1.0, 0.0) if abs(d[1]) < 0.95 else (1.0, 0.0, 0.0)
    dot = sum(a * b for a, b in zip(up, d))
    u = _norm([up[i] - dot * d[i] for i in range(3)])
    w = [d[1] * u[2] - d[2] * u[1], d[2] * u[0] - d[0] * u[2], d[0] * u[1] - d[1] * u[0]]
    return u, w


def _lateral(v):
    x, y, z = _norm(v)
    y = max(y, -0.42 if x > 0.12 else -0.80)
    z = max(z, 0.2)
    return [round(c, 5) for c in _norm([x, y, z])]


def _offset(anchor, dx, dy):
    u, w = _tangent(anchor)
    return _lateral([anchor[i] + w[i] * dx + u[i] * dy for i in range(3)])


def main(out_path: Path) -> None:
    chats = collect([REPO / "data" / "corpus"], REPO / "data" / "chats")
    bmap = build_map(chats)
    by_id = {c["id"]: c for c in chats}

    own = {c["id"]: classify(c) for c in chats}
    domain, source = {}, {}
    for region in bmap["regions"].values():
        votes = Counter(own[cid][0] for cid in region["members"])
        top, count = votes.most_common(1)[0]
        for cid in region["members"]:
            domain[cid], source[cid] = (top, "region vote") if count * 2 > len(region["members"]) else (own[cid][0], "own text")
    for cid in by_id:
        domain.setdefault(cid, own[cid][0])
        source.setdefault(cid, "own text")

    # Processed chats: outcomes, per-outcome mass, decisions (requirement creators), from the engine projection.
    processed = {}
    with tempfile.TemporaryDirectory() as tmp:
        for d in sorted((REPO / "data" / "chats").iterdir()):
            if d.name not in by_id or not (d / "state.json").exists() or not (d / "ledger.jsonl").exists():
                continue
            bundle = project_chat_directory(d, Path(tmp) / f"{d.name}.json")
            final = bundle["snapshots"][-1]["mass"] if bundle["snapshots"] else {}
            outcomes = [{"id": n["id"], "title": n["title"], "parent": n.get("parent"), "root": bool(n.get("root")),
                         "x": n.get("x", 0), "y": n.get("y", 0),
                         "human": round(final.get(n["id"], {}).get("human", 0), 1), "ai": round(final.get(n["id"], {}).get("ai", 0), 1)}
                        for n in bundle["nodes"]]
            reqs = [a for a in bundle["atoms"] if a.get("kind") == "requirement"]
            human = sum(o["human"] for o in outcomes)
            ai = sum(o["ai"] for o in outcomes)
            processed[d.name] = {"human": round(human, 1), "ai": round(ai, 1), "outcomes": outcomes,
                                 "decisions": {"human": sum(a.get("origin") == "human" for a in reqs), "ai": sum(a.get("origin") == "ai" for a in reqs)}}

    # Placement: domain lobe → the person's regions around the lobe centre → chats around their region centre.
    anchors = {key: _norm(a) for key, _, a, _ in DOMAINS}
    anchors["other"] = _norm(OTHER[2])
    out_chats = {}
    for key in list(anchors):
        members = [cid for cid in by_id if domain[cid] == key]
        groups: dict[str, list[str]] = {}
        for cid in members:
            groups.setdefault(bmap["chats"][cid]["region"] or f"solo:{cid}", []).append(cid)
        mass_of = lambda cid: (processed[cid]["human"] + processed[cid]["ai"]) if cid in processed else by_id[cid]["pairs"] * 93
        ordered = sorted(groups.items(), key=lambda kv: (-sum(mass_of(c) for c in kv[1]), kv[0]))
        for k, (gid, cids) in enumerate(ordered):
            side = 1 if k % 2 == 0 else -1
            r, a = 0.13 * math.sqrt(k // 2), (k // 2) * 2.399963
            centre = _offset(anchors[key], r * math.cos(a), r * math.sin(a)) if k > 1 else anchors[key]
            for i, cid in enumerate(sorted(cids, key=lambda c: (-mass_of(c), c))):
                rr, aa = 0.045 * math.sqrt(i), i * 2.399963
                p = processed.get(cid)
                out_chats[cid] = {
                    "title": by_id[cid]["title"], "domain": key, "domainSource": source[cid], "domainMargin": own[cid][1],
                    "region": None if gid.startswith("solo:") else gid, "area": bmap["chats"][cid]["area"],
                    "side": side, "direction": _offset(centre, rr * math.cos(aa), rr * math.sin(aa)),
                    "mapped": p is not None, "pairs": by_id[cid]["pairs"],
                    "human": p["human"] if p else None, "ai": p["ai"] if p else None,
                    "share": round(p["human"] / (p["human"] + p["ai"]), 4) if p and (p["human"] + p["ai"]) else None,
                    "outcomes": p["outcomes"] if p else [], "decisions": p["decisions"] if p else None,
                }

    mapped = [c for c in out_chats.values() if c["mapped"]]
    you, ai = sum(c["human"] for c in mapped), sum(c["ai"] for c in mapped)
    data = {
        "domains": [{"id": k, "name": n, "direction": anchors[k]} for k, n, _, _ in DOMAINS] + [{"id": "other", "name": "Other", "direction": anchors["other"]}],
        "regions": {rid: {"name": r["name"], "keywords": r["keywords"], "members": r["members"]} for rid, r in bmap["regions"].items()},
        "chats": out_chats,
        "links": bmap["links"],
        "balance": {"human": round(you, 1), "ai": round(ai, 1), "mappedChats": len(mapped), "chats": len(out_chats)},
        "method": {"domains": "keyword baseline (zero cost) + region vote; owner corrections win", "regions": bmap["method"]},
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    counts = Counter(c["domain"] for c in out_chats.values())
    print(f"{len(out_chats)} chats ({len(mapped)} mapped) · balance you {you:.0f} / AI {ai:.0f} · domains {dict(counts)} → {out_path}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "web" / "src" / "brain-v2" / "brain_v2.generated.json")
