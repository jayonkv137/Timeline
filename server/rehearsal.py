"""Rehearsal mode playback engine (STANDALONE_V1_PLAN §4 Step S4.R).

Per docs/PROCESSING_UX_SPEC.md v1.1 §7:
Replays pre-recorded chat runs from data/chats through the real job queue at real or
accelerated pace with ZERO spend ($0.00).

Emits the complete event contract:
- queue_changed
- job_progress
- pair_ready (with partial workspace bundles updated on disk incrementally)
- chat_ready
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
from pathlib import Path
from typing import Any

from engine.projections.workspace import export_workspace_bundle, load_chat_metadata
from server.library import Library, atomic_write_json

logger = logging.getLogger("cotrace.rehearsal")

DEFAULT_REPO_ROOT = Path(__file__).resolve().parent.parent


def get_available_rehearsal_fixtures(repo_root: Path | None = None) -> list[dict[str, Any]]:
    """Scan data/chats for recorded fixture runs (excluding frozen fixture_pair1)."""
    root = repo_root or DEFAULT_REPO_ROOT
    chats_dir = root / "data" / "chats"
    if not chats_dir.is_dir():
        return []

    fixtures: list[dict[str, Any]] = []
    for cdir in sorted(chats_dir.iterdir()):
        if not cdir.is_dir() or cdir.name in ("fixture_pair1", ".git"):
            continue

        dialogue_file = cdir / "dialogue.json"
        state_file = cdir / "state.json"
        ledger_file = cdir / "ledger.jsonl"

        if not (dialogue_file.is_file() and state_file.is_file() and ledger_file.is_file()):
            continue

        try:
            dialogue = json.loads(dialogue_file.read_text(encoding="utf-8"))
            pairs = max((t.get("pair", 1) for t in dialogue), default=1)
            source_meta, meta, summary = load_chat_metadata(cdir)
            title = source_meta.get("title") or meta.get("title") or cdir.name
            cat = meta.get("category") or "General"
            fixtures.append({
                "chatId": cdir.name,
                "title": title,
                "totalPairs": pairs,
                "category": cat.title() if isinstance(cat, str) else "General",
                "summary": summary[:120] + "..." if len(summary) > 120 else summary,
            })
        except Exception as exc:
            logger.debug(f"Skipping {cdir.name} during rehearsal scan: {exc}")

    # Sort shortest chats first per PROCESSING_UX_SPEC §4
    fixtures.sort(key=lambda x: (x["totalPairs"], x["chatId"]))
    return fixtures


class RehearsalRunner:
    """Manages zero-spend replay of pre-recorded chats through the background queue."""

    def __init__(
        self,
        library: Library,
        broadcaster: Any = None,
        repo_root: Path | None = None,
    ) -> None:
        self.library = library
        self.broadcaster = broadcaster
        self.repo_root = repo_root or DEFAULT_REPO_ROOT
        self.fixtures_dir = self.repo_root / "data" / "chats"
        self.delay_per_pair: float = 0.5  # default 0.5s per pair

    def list_fixtures(self) -> list[dict[str, Any]]:
        """Return list of all available fixture runs for rehearsal."""
        return get_available_rehearsal_fixtures(self.repo_root)

    def set_delay(self, seconds: float) -> None:
        """Set execution delay per pair in seconds."""
        self.delay_per_pair = max(0.0, float(seconds))

    async def setup_chat(self, chat_id: str) -> dict[str, Any]:
        """Copy fixture artifacts to library chat directory and write initial pair 0 bundle."""
        fixture_path = self.fixtures_dir / chat_id
        if not fixture_path.is_dir():
            raise FileNotFoundError(f"Rehearsal fixture '{chat_id}' not found in {self.fixtures_dir}")

        cdir = self.library.chat_dir(chat_id)
        cdir.mkdir(parents=True, exist_ok=True)
        (cdir / "run").mkdir(parents=True, exist_ok=True)

        # Copy recorded artifacts (read-only from fixture)
        for fname in ("dialogue.json", "state.json", "ledger.jsonl", "snapshots.json", "source_meta.json", "meta.json"):
            src_f = fixture_path / fname
            if src_f.is_file():
                shutil.copy2(src_f, cdir / fname)

        # Ensure meta.json exists
        source_meta, meta, summary = load_chat_metadata(cdir)
        meta_file = cdir / "meta.json"
        if not meta_file.is_file():
            atomic_write_json(meta_file, meta)

        dialogue = json.loads((cdir / "dialogue.json").read_text(encoding="utf-8"))
        state = json.loads((cdir / "state.json").read_text(encoding="utf-8"))
        ledger_lines = (cdir / "ledger.jsonl").read_text(encoding="utf-8").splitlines()
        ledger = [json.loads(l) for l in ledger_lines if l.strip()]

        total_pairs = max((t.get("pair", 1) for t in dialogue), default=1)
        title = source_meta.get("title") or meta.get("title") or chat_id
        category = meta.get("category") or "General"

        # Project initial bundle at processedPairs=0 (PROCESSING_UX_SPEC §3.3:
        # Transcript readable immediately; graph shows "Mapping the first exchange…")
        bundle_out = cdir / "workspace_bundle.json"
        export_workspace_bundle(
            output_path=bundle_out,
            dialogue=dialogue,
            state=state,
            ledger=ledger,
            source_meta=source_meta,
            meta=meta,
            chat_id=chat_id,
            summary=summary,
            status="processing",
            processed_pairs=0,
        )

        return {
            "chatId": chat_id,
            "title": title,
            "totalPairs": total_pairs,
            "category": category,
        }

    async def handle_pair(self, job: dict[str, Any], pair: int) -> None:
        """Handler invoked by JobQueueManager for pair `pair` during rehearsal."""
        chat_id = job["chatId"]
        total_pairs = int(job.get("totalPairs", 1))
        cdir = self.library.chat_dir(chat_id)

        # Pacing delay
        if self.delay_per_pair > 0:
            await asyncio.sleep(self.delay_per_pair)

        # Load current artifacts
        dialogue = json.loads((cdir / "dialogue.json").read_text(encoding="utf-8"))
        state = json.loads((cdir / "state.json").read_text(encoding="utf-8"))
        ledger_lines = (cdir / "ledger.jsonl").read_text(encoding="utf-8").splitlines()
        ledger = [json.loads(l) for l in ledger_lines if l.strip()]
        source_meta, meta, summary = load_chat_metadata(cdir)

        # Incremental projection: status is processing until last pair, then ready
        is_final = (pair >= total_pairs)
        status = "ready" if is_final else "processing"

        export_workspace_bundle(
            output_path=cdir / "workspace_bundle.json",
            dialogue=dialogue,
            state=state,
            ledger=ledger,
            source_meta=source_meta,
            meta=meta,
            chat_id=chat_id,
            summary=summary,
            status=status,
            processed_pairs=pair,
        )

    async def enqueue_rehearsal_batch(
        self,
        chat_ids: list[str] | None = None,
        delay_seconds: float = 0.5,
        queue_manager: Any = None,
    ) -> list[dict[str, Any]]:
        """Setup and enqueue a rehearsal batch into the persistent job queue."""
        if not chat_ids:
            # Default sample batch: 3 shortest clean fixtures
            available = self.list_fixtures()
            chat_ids = [f["chatId"] for f in available[:3]]
            if not chat_ids:
                chat_ids = ["c03_coding_short", "c20_coding_short", "c04_writing_short"]

        self.set_delay(delay_seconds)
        enqueued: list[dict[str, Any]] = []

        # Setup all fixtures first
        chat_metas: list[dict[str, Any]] = []
        for cid in chat_ids:
            meta_info = await self.setup_chat(cid)
            chat_metas.append(meta_info)

        # Enqueue shortest chats first (PROCESSING_UX_SPEC §4)
        chat_metas.sort(key=lambda m: (m["totalPairs"], m["chatId"]))

        for meta_info in chat_metas:
            job = await queue_manager.enqueue_job(
                chat_id=meta_info["chatId"],
                title=meta_info["title"],
                total_pairs=meta_info["totalPairs"],
                mode="rehearsal",
            )
            enqueued.append(job)

        return enqueued
