"""engine/brainmap.py — where each chat lives in the Brain, what it sits next to, how chats connect.

Implements docs/design-system/foundations/BRAIN_REGIONS_SPEC.md (track B1), baseline layer:
  fingerprint (title + full dialogue + engine extraction) → TF-IDF cosine similarity →
  near-duplicates → two-level average-linkage clustering (regions inside areas, cuts calibrated from
  the data's own similarity percentiles) → keyword names (class-based TF-IDF) → evidence-only links
  (continued · reused · similar) → flat cortex map layout (two hemisphere discs) → brain_map.json.

Pure Python, zero LLM calls, deterministic. Embeddings (MODEL_EMBED) plug in later behind `similarity`.
Task type never moves a chat (spec §2).
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

SIMILARITY_METHOD = "tfidf-v1"
MASS_PER_PAIR_ESTIMATE = 93  # median measured mass per exchange (BRAIN_NEURON_SPEC §11.1); used only when no ledger exists
NEAR_DUPLICATE = 0.90
SHINGLE = 8
MAX_LINKS_PER_CHAT = 3

STOP = set("""a about above after again against all also am an and any are as at be because been before being below
between both but by can could did do does doing down during each even few for from further get got had has have having
he her here hers him his how i if in into is it its itself just let like make me more most much must my no nor not now
of off on once one only or other our out over own please same she should so some such than that the their them then there
these they this those through to too under until up us use used using very want was we well were what when where which
while who whom why will with would yes you your yours ok okay thanks thank also need based give new way ai user
here's let's i'm it's don't can't you're that's there's we're i've i'll would've could""".split())
# Conversation glue words: frequent in every chat, so they join unrelated chats (study §9.2).
GENERIC = set("""step thing things right real really good great sure know think see look looks made just still actually
feel go going done work working first next two three part section version check help create add update clear keep
around exactly maybe something""".split())
CONTINUATION = re.compile(r"\b(continu\w*|part\s*\d+|phase\s*\d+|follow[- ]?up|revisit\w*)\b", re.I)


# ---------------------------------------------------------------- text

def tokens(text: str) -> list[str]:
    out = []
    for w in re.findall(r"[a-z][a-z0-9+#'-]{2,}", text.lower()):
        w = w.strip("'-")
        if len(w) < 3 or w in STOP or w in GENERIC:
            continue
        if w.endswith("ies") and len(w) > 5:
            w = w[:-3] + "y"
        elif w.endswith("s") and not w.endswith("ss") and len(w) > 4:
            w = w[:-1]
        out.append(w)
    return out


def _read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def _yaml_field(text: str, key: str) -> str:
    m = re.search(rf"^{key}:\s*\"?([^\"\n]*)\"?", text, re.M)
    return m.group(1).strip() if m else ""


def read_chat(chat_dir: Path, engine_dir: Path | None = None) -> dict | None:
    """Collect the empirical fields of one chat (spec §3). Returns None when there is no dialogue."""
    dialogue = _read_json(chat_dir / "dialogue.json")
    if not isinstance(dialogue, list) or not dialogue:
        return None
    title, task_type = "", ""
    meta = _read_json(chat_dir / "meta.json")
    if isinstance(meta, dict):
        title, task_type = meta.get("title") or "", meta.get("taskType") or meta.get("category") or ""
    if (chat_dir / "meta.yaml").exists():
        text = (chat_dir / "meta.yaml").read_text()
        title = title or _yaml_field(text, "title")
        task_type = task_type or _yaml_field(text, "task_type")
    source = _read_json(chat_dir / "source_meta.json")
    if not title and isinstance(source, dict):
        title = source.get("title") or ""
    title = title or chat_dir.name

    engine_dir = engine_dir if engine_dir and engine_dir.exists() else chat_dir
    engine_parts: list[str] = []
    state = _read_json(engine_dir / "state.json")
    if isinstance(state, dict):
        for key in ("outcomes", "requirements", "intentions"):
            items = state.get(key) or []
            for item in items.values() if isinstance(items, dict) else items:
                if isinstance(item, dict) and item.get("text"):
                    engine_parts.append(str(item["text"]))
    export = _read_json(engine_dir / "full_export.json")
    if isinstance(export, dict) and export.get("dialogue_summary"):
        engine_parts.append(str(export["dialogue_summary"]))

    mass = None
    ledger = engine_dir / "ledger.jsonl"
    if ledger.exists():
        mass = 0.0
        for line in ledger.read_text().splitlines():
            if line.strip():
                mass += float(json.loads(line).get("score", 0))

    turns = [t for t in dialogue if isinstance(t, dict) and t.get("text")]
    stamps = sorted(str(t.get("ts")) for t in turns if t.get("ts"))
    pairs = max([int(t.get("pair", 0)) for t in turns] + [0])
    text = " ".join([title] + [str(t["text"]) for t in turns] + engine_parts)
    return {
        "id": chat_dir.name,
        "title": title,
        "taskType": task_type,
        "pairs": pairs,
        "mass": mass if mass is not None else pairs * MASS_PER_PAIR_ESTIMATE,
        "massSource": "ledger" if mass is not None else "estimate",
        "since": stamps[0] if stamps else "",
        "until": stamps[-1] if stamps else "",
        "text": text,
        "hash": hashlib.sha256(text.encode()).hexdigest()[:16],
    }


# ---------------------------------------------------------------- similarity

def tfidf(token_lists: list[list[str]]) -> list[dict[str, float]]:
    n = len(token_lists)
    counts = [Counter(t) for t in token_lists]
    df = Counter(w for c in counts for w in c)
    vecs = []
    for c in counts:
        v = {w: (1 + math.log(f)) * math.log((1 + n) / (1 + df[w])) for w, f in c.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs.append({w: x / norm for w, x in v.items() if x > 0})
    return vecs


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(x * b.get(w, 0.0) for w, x in a.items())


def similarity(chats: list[dict]) -> tuple[list[list[float]], list[dict[str, float]], list[list[str]]]:
    toks = [tokens(c["text"]) for c in chats]
    vecs = tfidf(toks)
    n = len(chats)
    S = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            S[i][j] = S[j][i] = cosine(vecs[i], vecs[j])
    return S, vecs, toks


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    v = sorted(values)
    k = (len(v) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


# ---------------------------------------------------------------- clustering

def average_linkage(S: list[list[float]], groups: list[list[int]], cut: float) -> list[list[int]]:
    """Merge groups while the best average similarity between two groups is >= cut (Lance–Williams update)."""
    groups = [sorted(g) for g in groups]
    m = len(groups)
    sim = {}
    for a in range(m):
        for b in range(a + 1, m):
            sim[(a, b)] = sum(S[i][j] for i in groups[a] for j in groups[b]) / (len(groups[a]) * len(groups[b]))
    alive = set(range(m))
    while len(alive) > 1:
        best, pair = -1.0, None
        for key, s in sim.items():
            if s > best or (s == best and pair is not None and key < pair):
                best, pair = s, key
        if pair is None or best < cut:
            break
        a, b = pair
        na, nb = len(groups[a]), len(groups[b])
        groups[a] = sorted(groups[a] + groups[b])
        alive.discard(b)
        for k in alive:
            if k == a:
                continue
            ka, kb = (min(a, k), max(a, k)), (min(b, k), max(b, k))
            sim[ka] = (na * sim[ka] + nb * sim.pop(kb)) / (na + nb)
        sim = {key: s for key, s in sim.items() if b not in key}
    return sorted((groups[g] for g in alive), key=lambda g: (-len(g), g[0]))


def keywords(members: list[int], toks: list[list[str]], all_groups: list[list[int]], top: int = 6) -> list[str]:
    """Class-based TF-IDF (BERTopic): words frequent inside the group and rare across groups."""
    group_tf = [Counter(w for i in g for w in toks[i]) for g in all_groups]
    avg = sum(sum(c.values()) for c in group_tf) / max(1, len(group_tf))
    total = Counter()
    for c in group_tf:
        total.update(c)
    tf = Counter(w for i in members for w in toks[i])
    size = sum(tf.values()) or 1
    score = {w: (v / size) * math.log(1 + avg / total[w]) for w, v in tf.items()}
    return [w for w, _ in sorted(score.items(), key=lambda x: (-x[1], x[0]))[:top]]


# ---------------------------------------------------------------- links

def _shingles(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9']+", text.lower())
    return {" ".join(words[i:i + SHINGLE]) for i in range(max(0, len(words) - SHINGLE + 1))}


def _gap_hours(a: dict, b: dict) -> float | None:
    from datetime import datetime
    try:
        first, second = sorted([a, b], key=lambda c: c["since"])
        end = datetime.fromisoformat(first["until"].replace("Z", "+00:00"))
        start = datetime.fromisoformat(second["since"].replace("Z", "+00:00"))
        return round((start - end).total_seconds() / 3600, 1)
    except (ValueError, KeyError, TypeError):
        return None


def _title_words(title: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", CONTINUATION.sub(" ", title.lower())) if w not in STOP and len(w) > 2}


def shared_keywords(a: dict[str, float], b: dict[str, float], top: int = 5) -> list[str]:
    common = sorted(((a[w] * b[w], w) for w in a.keys() & b.keys()), reverse=True)
    return [w for _, w in common[:top]]


def find_links(chats, S, vecs, region_cut: float, similar_cut: float) -> list[dict]:
    n = len(chats)
    shingles = [_shingles(c["text"]) for c in chats]
    top3 = [set(sorted((j for j in range(n) if j != i), key=lambda j: (-S[i][j], j))[:3]) for i in range(n)]
    links = []
    for i in range(n):
        for j in range(i + 1, n):
            s = S[i][j]
            evidence = {"keywords": shared_keywords(vecs[i], vecs[j])}
            kind = None
            ti, tj = _title_words(chats[i]["title"]), _title_words(chats[j]["title"])
            same_title = bool(ti) and ti == tj
            # A continuation marker ("part 2", "continuation") counts only when the titles share their wording.
            marker = bool(CONTINUATION.search(chats[i]["title"]) or CONTINUATION.search(chats[j]["title"]))
            overlap = len(ti & tj) / max(1, len(ti | tj))
            if s >= NEAR_DUPLICATE or (s >= region_cut and (same_title or (marker and overlap >= 0.5))):
                kind = "continued"
                evidence["reason"] = "near-identical text" if s >= NEAR_DUPLICATE else ("same title" if same_title else "continuation in title")
            else:
                inter = shingles[i] & shingles[j]
                union = len(shingles[i] | shingles[j]) or 1
                if len(inter) >= 3 and len(inter) / union >= 0.02:
                    kind = "reused"
                    evidence["sharedPassages"] = len(inter)
                    evidence["passages"] = sorted(inter)[:2]
                elif j in top3[i] and i in top3[j] and s >= similar_cut:
                    kind = "similar"
            if kind:
                gap = _gap_hours(chats[i], chats[j])
                if gap is not None:
                    evidence["gapHours"] = gap
                links.append({"a": chats[i]["id"], "b": chats[j]["id"], "type": kind, "score": round(s, 3), "evidence": evidence})
    rank = {"continued": 0, "reused": 1, "similar": 2}
    links.sort(key=lambda l: (rank[l["type"]], -l["score"], l["a"], l["b"]))
    return links


# ---------------------------------------------------------------- layout (flat cortex map → folded surface)

DISC_CENTRE = 1.1  # left hemisphere disc centred at u = -1.1, right at u = +1.1, radius 1


def _golden(i: int, n: int, radius: float) -> tuple[float, float]:
    if n <= 1:
        return 0.0, 0.0
    r = radius * math.sqrt((i + 0.5) / n)
    a = i * 2.399963229728653
    return r * math.cos(a), r * math.sin(a)


def _into_disc(u: float, v: float) -> tuple[float, float]:
    side = 1 if u >= 0 else -1
    a, b = u - side * DISC_CENTRE, v
    d = math.hypot(a, b)
    if d > 0.92:
        a, b = a / d * 0.92, b / d * 0.92
    return side * DISC_CENTRE + a, b


def to_cortex(u: float, v: float) -> tuple[int, list[float]]:
    """Flat-map point → (hemisphere side, unit direction on the lateral cortex used by brainPoint)."""
    side = 1 if u >= 0 else -1
    a, b = u - side * DISC_CENTRE, v
    x, y = a * 0.9, b * 0.72 - 0.05
    # Stay on the lateral cortex: never the base, never under the cerebellum (same mask as the Brain's lattice).
    # Normalising below can only shrink |x| and |y| (the norm is >= 1), so the clamps hold after it.
    y = max(y, -0.42 if x > 0.12 else -0.78)
    z = math.sqrt(max(0.2, 1 - x * x - y * y))
    n = math.sqrt(x * x + y * y + z * z)
    return side, [round(x / n, 5), round(y / n, 5), round(z / n, 5)]


def layout_areas(area_sims: list[list[float]], weights: list[float], iterations: int = 400) -> list[tuple[float, float]]:
    """Deterministic force layout of areas on the two-disc flat map: similar areas attract, all repel."""
    n = len(weights)
    pos = []
    for i in range(n):
        side = 1 if i % 2 == 0 else -1
        x, y = _golden(i // 2, (n + 1) // 2, 0.7)
        pos.append([side * DISC_CENTRE + x, y])
    for it in range(iterations):
        step = 0.02 * (1 - it / iterations) + 0.002
        force = [[0.0, 0.0] for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                dx, dy = pos[j][0] - pos[i][0], pos[j][1] - pos[i][1]
                d = math.hypot(dx, dy) or 1e-6
                rep = 0.06 * (math.sqrt(weights[i]) + math.sqrt(weights[j])) / (d * d)
                att = 1.5 * area_sims[i][j] * d
                f = att - rep
                force[i][0] += f * dx / d; force[i][1] += f * dy / d
                force[j][0] -= f * dx / d; force[j][1] -= f * dy / d
        for i in range(n):
            pos[i][0] += step * max(-5, min(5, force[i][0]))
            pos[i][1] += step * max(-5, min(5, force[i][1]))
            pos[i][0], pos[i][1] = _into_disc(pos[i][0], pos[i][1])
    return [(round(p[0], 5), round(p[1], 5)) for p in pos]


# ---------------------------------------------------------------- build

def build_map(chats: list[dict], previous: dict | None = None) -> dict:
    chats = sorted(chats, key=lambda c: (c["since"], c["id"]))
    n = len(chats)
    S, vecs, toks = similarity(chats)
    pair_sims = [S[i][j] for i in range(n) for j in range(i + 1, n)]
    # Cuts are percentiles of this corpus's own pair similarities (spec §5.2, calibrated on 57 corpus chats:
    # p90 reproduces project-level regions, p80 the broad areas). Small libraries use the measured values.
    region_cut = max(0.10, round(percentile(pair_sims, 0.90), 4)) if n >= 12 else 0.13
    area_cut = max(0.06, round(percentile(pair_sims, 0.80), 4)) if n >= 12 else 0.10
    similar_cut = max(0.15, round(percentile(pair_sims, 0.99), 4)) if n >= 12 else 0.25

    # 1. near-duplicates first, 2. regions, 3. areas (continuing the same average-linkage hierarchy)
    groups = average_linkage(S, [[i] for i in range(n)], NEAR_DUPLICATE)
    region_groups = average_linkage(S, groups, region_cut)
    area_groups = average_linkage(S, region_groups, area_cut)

    regions, chat_region = {}, {}
    named = [g for g in region_groups if len(g) >= 2]
    for k, g in enumerate(named):
        rid = f"r{k + 1}"
        cohesion = (sum(S[i][j] for i in g for j in g if i < j) / (len(g) * (len(g) - 1) / 2)) if len(g) > 1 else 1.0
        kw = keywords(g, toks, region_groups)
        regions[rid] = {"name": " · ".join(kw[:3]), "nameSource": "keywords", "keywords": kw,
                        "members": [chats[i]["id"] for i in g], "cohesion": round(cohesion, 3)}
        for i in g:
            chat_region[i] = rid

    areas, chat_area = {}, {}
    for k, g in enumerate(area_groups):
        aid = f"a{k + 1}"
        kw = keywords(g, toks, area_groups)
        member_regions = sorted({chat_region[i] for i in g if i in chat_region}, key=lambda r: int(r[1:]))
        areas[aid] = {"name": " · ".join(kw[:3]), "nameSource": "keywords", "keywords": kw,
                      "regions": member_regions, "members": [chats[i]["id"] for i in g], "solitary": len(g) == 1}
        for i in g:
            chat_area[i] = aid

    # Owner names survive a rebuild when the membership is mostly the same (spec §5.3).
    if previous:
        for table, prev_table in ((regions, previous.get("regions", {})), (areas, previous.get("areas", {}))):
            for item in table.values():
                members = set(item["members"])
                for old in prev_table.values():
                    if old.get("nameSource") == "owner" and len(members & set(old.get("members", []))) * 2 > len(members):
                        item["name"], item["nameSource"] = old["name"], "owner"

    # Layout: areas on the flat map, then regions and chats around their area centre.
    index = {aid: k for k, aid in enumerate(areas)}
    area_list = list(areas)
    area_members = [[i for i in range(n) if chat_area[i] == aid] for aid in area_list]
    area_sims = [[0.0] * len(area_list) for _ in area_list]
    for a in range(len(area_list)):
        for b in range(a + 1, len(area_list)):
            s = sum(S[i][j] for i in area_members[a] for j in area_members[b]) / (len(area_members[a]) * len(area_members[b]))
            area_sims[a][b] = area_sims[b][a] = s
    weights = [sum(chats[i]["mass"] for i in m) for m in area_members]
    centres = layout_areas(area_sims, weights)
    spread = max(1.0, max(weights or [1.0]))

    out_chats = {}
    prev_chats = (previous or {}).get("chats", {})
    for a, aid in enumerate(area_list):
        members = sorted(area_members[a], key=lambda i: (chat_region.get(i, "~"), chats[i]["since"], chats[i]["id"]))
        radius = 0.08 + 0.32 * math.sqrt(weights[a] / spread)
        for k, i in enumerate(members):
            dx, dy = _golden(k, len(members), radius)
            u, v = _into_disc(centres[a][0] + dx, centres[a][1] + dy)
            side, direction = to_cortex(u, v)
            out_chats[chats[i]["id"]] = {"title": chats[i]["title"], "taskType": chats[i]["taskType"],
                                         "area": aid, "region": chat_region.get(i), "flat": [round(u, 4), round(v, 4)],
                                         "side": side, "direction": direction, "mass": round(chats[i]["mass"], 1),
                                         "massSource": chats[i]["massSource"], "fingerprintHash": chats[i]["hash"], "pinned": True}
    # Stability (spec §5.4): chats already placed keep their position; only new chats get new seats.
    for cid, old in prev_chats.items():
        if cid in out_chats and old.get("pinned"):
            out_chats[cid].update({k: old[k] for k in ("flat", "side", "direction") if k in old})

    for aid, item in areas.items():
        pts = [out_chats[chats[i]["id"]]["flat"] for i in area_members[index[aid]]]
        u = sum(p[0] for p in pts) / len(pts); v = sum(p[1] for p in pts) / len(pts)
        item["side"], item["direction"] = to_cortex(u, v)
    for rid, item in regions.items():
        pts = [out_chats[c]["flat"] for c in item["members"]]
        u = sum(p[0] for p in pts) / len(pts); v = sum(p[1] for p in pts) / len(pts)
        item["side"], item["direction"] = to_cortex(u, v)

    links = find_links(chats, S, vecs, region_cut, similar_cut)
    return {
        "version": (previous or {}).get("version", 0) + 1,
        "method": {"similarity": SIMILARITY_METHOD, "fingerprint": "title + full dialogue + engine extraction",
                   "nearDuplicate": NEAR_DUPLICATE, "regionCut": region_cut, "areaCut": area_cut, "similarCut": similar_cut,
                   "chats": n, "pairs": len(pair_sims)},
        "chats": out_chats,
        "areas": areas,
        "regions": regions,
        "links": links,
        "maxLinksPerChatAtOverview": MAX_LINKS_PER_CHAT,
    }


def collect(paths: list[Path], engine_root: Path | None = None) -> list[dict]:
    """Accept chat folders or parents of chat folders (library `chats/`, `data/corpus`)."""
    dirs: list[Path] = []
    for p in paths:
        if (p / "dialogue.json").exists():
            dirs.append(p)
        elif p.is_dir():
            dirs.extend(sorted(d for d in p.iterdir() if (d / "dialogue.json").exists()))
    out = []
    for d in dirs:
        chat = read_chat(d, engine_root / d.name if engine_root else None)
        if chat:
            out.append(chat)
    return out


def main(paths: list[str], output: str | None, engine_root: str | None, previous: str | None) -> int:
    chats = collect([Path(p) for p in paths], Path(engine_root) if engine_root else None)
    prev = json.loads(Path(previous).read_text()) if previous else None
    result = build_map(chats, prev)
    text = json.dumps(result, indent=1, ensure_ascii=False)
    if output:
        Path(output).write_text(text + "\n")
        m = result["method"]
        print(f"brain map v{result['version']}: {m['chats']} chats · {len(result['areas'])} areas · {len(result['regions'])} regions · "
              f"{len(result['links'])} links (cuts: region {m['regionCut']}, area {m['areaCut']}, similar {m['similarCut']}) → {output}")
    else:
        print(text)
    return 0
