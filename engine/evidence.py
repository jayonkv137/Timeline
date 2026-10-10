"""Evidence linking (docs/EVIDENCE_SPEC.md).

Turns the engine's action quotes into exact, verifiable places in the transcript, and lists every source that
supports a requirement or a question: where it was introduced, revised, carried out, asked and answered.

Two rules hold everywhere:
  * Nothing is invented. A quote that cannot be found says so (`match: "message"`); an action that is missing
    says so (`match: "missing"`). No fuzzy match is ever reported as exact.
  * Anchors use the W3C Web Annotation selectors (TextQuoteSelector exact/prefix/suffix + TextPositionSelector
    start/end on the raw message text), so the same record anchors in our transcript and, later, in a host page.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

_ACTION_RE = re.compile(r"^([UA])\((\d+),(\d+)\)$")
_REPLACE = {"’": "'", "‘": "'", "“": '"', "”": '"', "—": "-", "–": "-", " ": " "}
_SKIP = set("*_`#>")
CONTEXT = 32  # characters of prefix / suffix kept around each fragment
MATCHES = ("exact", "normalized", "multipart", "message", "missing")


def parse_action(action_id: str | None) -> tuple[str, int, int] | None:
    """'U(3,2)' -> ('human', 3, 2). None when the id is not an engine action id."""
    m = _ACTION_RE.match(str(action_id or ""))
    if not m:
        return None
    return ("human" if m.group(1) == "U" else "ai", int(m.group(2)), int(m.group(3)))


def norm_map(text: str) -> tuple[str, list[int]]:
    """Normalise for matching and keep, for every normalised character, the index of its raw character.

    Curly quotes and dashes are straightened, markdown symbols dropped, whitespace collapsed, case folded.
    The same function exists in TypeScript (web/src/workspace/evidence.ts) and must stay identical.
    """
    out: list[str] = []
    idx: list[int] = []
    prev_space = False
    for i, ch in enumerate(text):
        ch = _REPLACE.get(ch, ch)
        if ch in _SKIP:
            continue
        if ch.isspace():
            if prev_space or not out:
                continue
            ch = " "
            prev_space = True
        else:
            prev_space = False
        for low in ch.lower():
            out.append(low)
            idx.append(i)
    while out and out[-1] == " ":
        out.pop()
        idx.pop()
    return "".join(out), idx


def text_hash(text: str) -> str:
    """Stable fingerprint of a message's normalised text (detects later edits)."""
    return "sha256:" + hashlib.sha256(norm_map(text)[0].encode("utf-8")).hexdigest()[:16]


def _fragment(text: str, start: int, end: int) -> dict[str, Any]:
    return {
        "exact": text[start:end],
        "prefix": text[max(0, start - CONTEXT):start],
        "suffix": text[end:end + CONTEXT],
        "start": start,
        "end": end,
    }


def _split_quote(quote: str) -> list[str]:
    parts = [p.strip(" .,;:\"'") for p in re.split(r"\.\.\.|…", quote)]
    return [p for p in parts if len(p) >= 4]


def anchor(quote: str | None, text: str, after: int = 0, normed: tuple[str, list[int]] | None = None) -> dict[str, Any]:
    """Locate `quote` in `text` (one message). `after` = where the previous action of this message ended, used to
    pick the right occurrence when a phrase repeats (actions are numbered in reading order).

    Returns {"match", "fragments", "occurrences"}; fragments carry raw-text offsets.
    """
    q = (quote or "").strip()
    if not q:
        return {"match": "missing", "fragments": [], "occurrences": 0}
    # 1. exact substring
    hits = [m.start() for m in re.finditer(re.escape(q), text)]
    if hits:
        start = next((h for h in hits if h >= after), hits[0])
        return {"match": "exact", "fragments": [_fragment(text, start, start + len(q))], "occurrences": len(hits)}
    nt, idx = normed or norm_map(text)
    # Quotation marks the model wrapped around a quote are not part of the message.
    nq = norm_map(q.strip("\"'\u201c\u201d\u2018\u2019 "))[0]
    # 2. exact after formatting normalisation
    if nq:
        nhits = [m.start() for m in re.finditer(re.escape(nq), nt)]
        if nhits:
            na = next((h for h in nhits if idx[h] >= after), nhits[0])
            start, end = idx[na], idx[na + len(nq) - 1] + 1
            return {"match": "normalized", "fragments": [_fragment(text, start, end)], "occurrences": len(nhits)}
    # 3. several verbatim passages joined with "..." by the model, found in reading order
    parts = _split_quote(q)
    if parts and ("..." in q or "…" in q):
        frags, pos = [], 0
        for part in parts:
            np_ = norm_map(part)[0]
            k = nt.find(np_, pos)
            if k < 0:
                k = nt.find(np_)  # the model sometimes joins passages out of reading order; each is still verbatim
            if k < 0:
                break
            frags.append(_fragment(text, idx[k], idx[k + len(np_) - 1] + 1))
            pos = k + len(np_)
        if len(frags) == len(parts):
            return {"match": "multipart", "fragments": sorted(frags, key=lambda f: f["start"]), "occurrences": 1}
    # 4. not in its message: open the message, highlight nothing
    return {"match": "message", "fragments": [], "occurrences": 0}


class EvidenceIndex:
    """Anchors every action of one chat once, then builds evidence lists for atoms."""

    def __init__(self, chat_id: str, dialogue: list[dict[str, Any]], actions: list[dict[str, Any]]):
        self.chat_id = chat_id
        self.text: dict[tuple[int, str], str] = {}
        for t in dialogue:
            sp = "human" if t.get("speaker") in ("user", "human") else "ai"
            self.text[(int(t.get("pair", 0)), sp)] = t.get("text") or ""
        self.actions = {a["id"]: a for a in actions if isinstance(a, dict) and "id" in a}
        self.normed = {k: norm_map(v) for k, v in self.text.items()}
        self.hashes = {k: "sha256:" + hashlib.sha256(v[0].encode("utf-8")).hexdigest()[:16] for k, v in self.normed.items()}
        self.anchors: dict[str, dict[str, Any]] = {}
        # Anchor in reading order per message so repeated phrases resolve to the right occurrence.
        ordered = sorted((parse_action(aid), aid) for aid in self.actions if parse_action(aid))
        last_end: dict[tuple[int, str], int] = {}
        for (speaker, pair, _seq), aid in ordered:
            key = (pair, speaker)
            text = self.text.get(key)
            if text is None:
                self.anchors[aid] = {"match": "missing", "fragments": [], "occurrences": 0, "note": "message not in transcript"}
                continue
            res = anchor(self.actions[aid].get("evidence_quote"), text, last_end.get(key, 0), self.normed[key])
            if res["fragments"]:
                last_end[key] = res["fragments"][-1]["end"]
            elif res["match"] == "message":
                res["note"] = self._found_elsewhere(self.actions[aid].get("evidence_quote") or "", key)
            self.anchors[aid] = res

    def _found_elsewhere(self, quote: str, own: tuple[int, str]) -> str | None:
        nq = norm_map(quote)[0][:60]
        if len(nq) < 8:
            return None
        for (pair, speaker), (nt, _idx) in sorted(self.normed.items()):
            if (pair, speaker) != own and nq in nt:
                who = "you" if speaker == "human" else "the AI"
                return f"quote found in exchange {pair} ({who})"
        return None

    def item(self, role: str, action_id: str | None) -> dict[str, Any]:
        """One evidence record. Speaker and exchange always come from the action id, never from a guess."""
        parsed = parse_action(action_id)
        if not parsed or action_id not in self.actions:
            return {"id": f"{action_id or 'none'}:{role}", "role": role, "actionId": action_id if parsed else None,
                    "pair": parsed[1] if parsed else None, "speaker": parsed[0] if parsed else None,
                    "messageId": None, "textHash": None, "match": "missing", "fragments": [], "note": "source not linked"}
        speaker, pair, _ = parsed
        res = self.anchors.get(action_id) or {"match": "missing", "fragments": []}
        text = self.text.get((pair, speaker), "")
        return {
            "id": f"{action_id}:{role}",
            "role": role,
            "actionId": action_id,
            "pair": pair,
            "speaker": speaker,
            "messageId": f"{self.chat_id}:{pair}:{'user' if speaker == 'human' else 'ai'}",
            "textHash": self.hashes.get((pair, speaker)) if text else None,
            "match": res["match"],
            "fragments": res["fragments"],
            "occurrences": res.get("occurrences", 0),
            "note": res.get("note"),
        }

    def items(self, role: str, action_ids: list[str] | None) -> list[dict[str, Any]]:
        seen, out = set(), []
        for aid in action_ids or []:
            if aid in seen:
                continue
            seen.add(aid)
            out.append(self.item(role, aid))
        return out


def _order(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(items, key=lambda e: (e["pair"] or 0, parse_action(e["actionId"])[2] if parse_action(e["actionId"]) else 0))


def requirement_evidence(ev: EvidenceIndex, req: dict[str, Any], question: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Introduced → revised → carried out; an answer to a question is preceded by where the question was asked."""
    out: list[dict[str, Any]] = []
    if question is not None:
        out += _order(ev.items("asked", question.get("creation_action_ids")))
        out += _order(ev.items("answered", req.get("creation_action_ids")))
    else:
        out += _order(ev.items("introduced", req.get("creation_action_ids")))
    out += _order(ev.items("revised", req.get("revise_action_ids")))
    out += _order(ev.items("carried-out", req.get("implementation_action_ids")))
    if not req.get("creation_action_ids"):
        out.insert(0, ev.item("answered" if question is not None else "introduced", None))
    return out


def question_evidence(ev: EvidenceIndex, slot: dict[str, Any], answer: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Asked, and, when the engine resolved it, where it was answered."""
    out = _order(ev.items("asked", slot.get("creation_action_ids")))
    if not slot.get("creation_action_ids"):
        out.insert(0, ev.item("asked", None))
    if answer is not None:
        out += _order(ev.items("answered", answer.get("creation_action_ids")))
    return out


def audit(ev: EvidenceIndex) -> dict[str, int]:
    """Counts of anchor outcomes for this chat (scripts/evidence_audit.py, invariant W7)."""
    counts: dict[str, int] = {}
    for res in ev.anchors.values():
        key = res["match"] + (" (repeated phrase)" if res.get("occurrences", 0) > 1 else "")
        counts[key] = counts.get(key, 0) + 1
    return counts
