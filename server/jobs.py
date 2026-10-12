"""COTRACE persistent job queue and concurrency manager.
STANDALONE_V1_PLAN §4 Step S4.3 & docs/PROCESSING_UX_SPEC.md v1.1.

Implements:
- Persistent jobs.json in $COTRACE_HOME
- Shortest-first ordering (§4) with priority overrides ("Map next")
- Dynamic worker pool bounded by parallel_jobs setting (1–8)
- Crash / restart recovery: resumes from last completed pair without re-paying (§5)
- Rate-limit exponential backoff (§5)
- Budget cap halting and clean exchange completion (§5)
- Event contract: queue_changed, job_progress, pair_ready, chat_ready, job_error, budget_stop (§6)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

from engine.budget import BudgetStopError
from engine.llm import RateLimitError
from server.library import Library, atomic_write_json

logger = logging.getLogger("cotrace.jobs")


class Job(dict):
    """Job record wrapper providing dot and dictionary access."""

    def __init__(self, data: dict[str, Any]):
        super().__init__(data)
        self.__dict__ = self


class JobQueueManager:
    """Manages persistent background chat processing jobs."""

    def __init__(
        self,
        library: Library,
        broadcaster: Any = None,
        worker_handler: Callable[[dict[str, Any], int], Awaitable[None]] | None = None,
        rehearsal_runner: Any = None,
        pipeline_runner: Any = None,
    ) -> None:
        self.library = library
        self.broadcaster = broadcaster
        self.worker_handler = worker_handler
        self.rehearsal_runner = rehearsal_runner
        self.pipeline_runner = pipeline_runner

        self._lock = asyncio.Lock()
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._is_paused = False
        self._pause_reason: str | None = None

        # Rate limit backoff tracking
        self._backoff_delay = 2.0
        self._backoff_until = 0.0

        # Background scheduler loop
        self._scheduler_task: asyncio.Task | None = None
        self._stopped = False

        # Load and reconcile on startup
        self._reconcile_startup_jobs()

    def _reconcile_startup_jobs(self) -> None:
        """Crash / restart recovery: reset any 'running' jobs to 'queued' (§5).
        Keeps completedPairs so execution resumes without re-paying.
        """
        jobs = self.library.get_jobs()
        changed = False
        for j in jobs:
            if j.get("status") == "running":
                j["status"] = "queued"
                j["updatedAt"] = datetime.now(timezone.utc).isoformat()
                changed = True
        if changed:
            self.library.save_jobs(jobs)

    def set_rehearsal_runner(self, runner: Any) -> None:
        """Register rehearsal runner for zero-spend replay mode (§7)."""
        self.rehearsal_runner = runner

    def set_pipeline_runner(self, runner: Any) -> None:
        """Register pipeline runner for live chat processing (§4 Step S4.4)."""
        self.pipeline_runner = runner

    def start(self) -> None:
        """Start the background queue scheduler if not already running."""
        self._stopped = False
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and (self._scheduler_task is None or self._scheduler_task.done()):
            self._scheduler_task = loop.create_task(self._scheduler_loop())

    async def stop(self) -> None:
        """Stop scheduler and wait for running tasks to halt."""
        self._stopped = True
        if self._scheduler_task and not self._scheduler_task.done():
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

        # Cancel active running tasks
        for t in list(self._running_tasks.values()):
            if not t.done():
                t.cancel()

    def get_jobs(self) -> list[dict[str, Any]]:
        """Return all jobs from jobs.json."""
        return self.library.get_jobs()

    def get_job(self, job_id_or_chat_id: str) -> dict[str, Any] | None:
        """Find a job by job ID or chat ID."""
        jobs = self.get_jobs()
        for j in jobs:
            if j.get("id") == job_id_or_chat_id or j.get("chatId") == job_id_or_chat_id:
                return j
        return None

    def get_queue_status(self) -> dict[str, Any]:
        """Return queue summary for UI pill and status."""
        jobs = self.get_jobs()
        running = [j for j in jobs if j.get("status") == "running"]
        waiting = [j for j in jobs if j.get("status") == "queued"]
        completed = [j for j in jobs if j.get("status") == "completed"]
        failed = [j for j in jobs if j.get("status") in ("failed", "canceled")]

        settings = self.library.get_effective_settings()
        limit = max(1, min(8, int(settings.get("parallel_jobs", 2))))

        return {
            "isPaused": self._is_paused,
            "pauseReason": self._pause_reason,
            "parallelLimit": limit,
            "runningCount": len(running),
            "waitingCount": len(waiting),
            "completedCount": len(completed),
            "failedCount": len(failed),
            "runningChats": [j.get("chatId") for j in running],
            "waitingChats": [j.get("chatId") for j in waiting],
            "isBackoff": time.time() < self._backoff_until,
            "backoffRemaining": max(0.0, round(self._backoff_until - time.time(), 1)),
        }

    async def enqueue_job(
        self,
        chat_id: str,
        title: str,
        total_pairs: int,
        conv_id: str | None = None,
        import_id: str | None = None,
        priority: int = 0,
        mode: str = "live",
        completed_pairs: int = 0,
    ) -> dict[str, Any]:
        """Enqueue a chat for mapping."""
        async with self._lock:
            jobs = self.library.get_jobs()
            existing = next((j for j in jobs if j.get("chatId") == chat_id), None)

            now = datetime.now(timezone.utc).isoformat()

            # If completed_pairs not specified, check if existing state.json has progress
            if completed_pairs == 0:
                cdir = self.library.chat_dir(chat_id)
                state_file = cdir / "state.json"
                if state_file.is_file():
                    try:
                        sdata = json.loads(state_file.read_text(encoding="utf-8"))
                        completed_pairs = int(sdata.get("run", {}).get("last_completed_pair", 0))
                    except Exception:
                        completed_pairs = 0

            if existing:
                # If already active, return existing
                if existing.get("status") in ("queued", "running", "paused"):
                    return existing
                # If completed or failed, re-queue
                existing["status"] = "completed" if completed_pairs >= total_pairs else "queued"
                existing["mode"] = mode
                existing["priority"] = priority
                existing["completedPairs"] = completed_pairs
                existing["totalPairs"] = total_pairs
                existing["timingLog"] = []
                existing["updatedAt"] = now
                existing["error"] = None
                self.library.save_jobs(jobs)
                self._broadcast_queue_changed()
                self.start()
                return existing

            job_id = f"job_{chat_id}"
            new_job: dict[str, Any] = {
                "id": job_id,
                "chatId": chat_id,
                "convId": conv_id or chat_id,
                "importId": import_id,
                "title": title,
                "mode": mode,
                "status": "completed" if completed_pairs >= total_pairs else "queued",
                "totalPairs": int(total_pairs),
                "completedPairs": int(completed_pairs),
                "priority": int(priority),
                "createdAt": now,
                "startedAt": None,
                "updatedAt": now,
                "completedAt": None,
                "error": None,
                "errorKind": None,
                "timingLog": [],
            }
            jobs.append(new_job)
            self.library.save_jobs(jobs)

        self._broadcast_queue_changed()
        self.start()
        return new_job

    async def enqueue_import_batch(
        self,
        import_id: str,
        conversation_ids: list[str],
    ) -> list[dict[str, Any]]:
        """Promotes selected conversations from an import batch (if needed) and enqueues them."""
        from engine.importer import promote_conversation

        rep = self.library.get_import_report(import_id)
        import_dir = self.library.import_dir(import_id)
        raw_dir = import_dir / "raw"

        # Load raw conversations list
        from engine.importer import find_export_file
        primary_file, fmt = find_export_file(raw_dir)
        if fmt == "gemini_takeout_html":
            from engine.importer import parse_gemini_takeout_html
            raw_convs_data = parse_gemini_takeout_html(primary_file)
        else:
            with open(primary_file, "r", encoding="utf-8") as f:
                raw_convs_data = json.load(f)
            if isinstance(raw_convs_data, dict):
                if "conversations" in raw_convs_data and isinstance(raw_convs_data["conversations"], list):
                    raw_convs_data = raw_convs_data["conversations"]
                else:
                    raw_convs_data = [raw_convs_data]

        convs_by_id = {}
        for c in raw_convs_data:
            uuid_str = c.get("uuid", "")
            raw_id = c.get("id") or c.get("name") or uuid_str
            if uuid_str:
                convs_by_id[uuid_str] = c
                convs_by_id[f"claude_{uuid_str}"] = c
            if raw_id:
                convs_by_id[str(raw_id)] = c
                convs_by_id[f"chatgpt_{raw_id}"] = c
                convs_by_id[f"gemini_{raw_id}"] = c
                convs_by_id[f"claude_{raw_id}"] = c

        rep_convs = {c["convId"]: c for c in rep.get("conversations", [])}
        enqueued: list[dict[str, Any]] = []

        for cid in conversation_ids:
            row_meta = rep_convs.get(cid)
            if not row_meta:
                continue

            chat_id = cid
            cdir = self.library.chat_dir(chat_id)

            # S4.6: Re-upload deduplication — skip identical conversations with same content
            if row_meta.get("isDuplicate") and not row_meta.get("isIncremental"):
                logger.info(f"Skipping identical duplicate {cid} — already present in library.")
                continue

            # Promote conversation to active library if not already promoted
            clean_cid = cid
            for prefix in ("claude_", "chatgpt_", "gemini_"):
                if clean_cid.startswith(prefix):
                    clean_cid = clean_cid[len(prefix):]
                    break

            if not cdir.is_dir():
                raw_conv = convs_by_id.get(cid) or convs_by_id.get(clean_cid)
                if raw_conv:
                    promote_conversation(
                        conv_data=raw_conv,
                        dest_dir=cdir,
                        chat_id=chat_id,
                        category="General",
                    )
            elif row_meta.get("isIncremental"):
                # Incremental extension: update dialogue.json & metadata with appended turns
                raw_conv = convs_by_id.get(cid) or convs_by_id.get(clean_cid)
                if raw_conv:
                    promote_conversation(
                        conv_data=raw_conv,
                        dest_dir=cdir,
                        chat_id=chat_id,
                        category="General",
                    )

            # Ensure initial pair 0 workspace_bundle.json exists so chat is readable immediately (§3.3)
            bundle_file = cdir / "workspace_bundle.json"
            if not bundle_file.is_file():
                dialogue_path = cdir / "dialogue.json"
                if dialogue_path.is_file():
                    from engine.projections.workspace import export_workspace_bundle, load_chat_metadata
                    dialogue_data = json.loads(dialogue_path.read_text(encoding="utf-8"))
                    source_meta, meta, summary = load_chat_metadata(cdir)
                    export_workspace_bundle(
                        output_path=bundle_file,
                        dialogue=dialogue_data,
                        state={"outcomes": [], "requirements": [], "slots": [], "operations_log": [], "actions": []},
                        ledger=[],
                        source_meta=source_meta,
                        meta=meta,
                        chat_id=chat_id,
                        summary=summary,
                        status="processing",
                        processed_pairs=0,
                    )

            total_pairs = row_meta.get("pairs", 0)
            completed_pairs = 0
            if row_meta.get("isIncremental"):
                completed_pairs = int(row_meta.get("existingPairs", 0))

            title = row_meta.get("rawTitle") or row_meta.get("title") or chat_id

            job = await self.enqueue_job(
                chat_id=chat_id,
                title=title,
                total_pairs=total_pairs,
                conv_id=cid,
                import_id=import_id,
                priority=0,
                completed_pairs=completed_pairs,
            )
            enqueued.append(job)

        return enqueued

    async def map_next(self, job_id_or_chat_id: str) -> dict[str, Any]:
        """Move chat to front of queue ('Map next' per §4)."""
        async with self._lock:
            jobs = self.library.get_jobs()
            target = next((j for j in jobs if j.get("id") == job_id_or_chat_id or j.get("chatId") == job_id_or_chat_id), None)
            if not target:
                raise FileNotFoundError(f"Job '{job_id_or_chat_id}' not found")

            # Priority bump
            max_priority = max((j.get("priority", 0) for j in jobs), default=0)
            target["priority"] = max_priority + 10
            target["updatedAt"] = datetime.now(timezone.utc).isoformat()
            if target.get("status") in ("paused", "failed"):
                target["status"] = "queued"

            self.library.save_jobs(jobs)

        self._broadcast_queue_changed()
        self.start()
        return target

    async def cancel_job(self, job_id_or_chat_id: str) -> dict[str, Any]:
        """Stop / cancel mapping for a chat (§3.2, §5). Mapped exchanges are kept."""
        target: dict[str, Any] | None = None
        task_to_cancel: asyncio.Task | None = None

        async with self._lock:
            jobs = self.library.get_jobs()
            target = next((j for j in jobs if j.get("id") == job_id_or_chat_id or j.get("chatId") == job_id_or_chat_id), None)
            if not target:
                raise FileNotFoundError(f"Job '{job_id_or_chat_id}' not found")

            cid = target.get("chatId")
            target["status"] = "canceled"
            target["updatedAt"] = datetime.now(timezone.utc).isoformat()
            self.library.save_jobs(jobs)

            if cid in self._running_tasks:
                task_to_cancel = self._running_tasks.pop(cid)

        if task_to_cancel and not task_to_cancel.done():
            task_to_cancel.cancel()

        self._broadcast_queue_changed()
        return target

    def pause_all(self, reason: str = "user_paused") -> None:
        """Pause queue processing (§3.2)."""
        self._is_paused = True
        self._pause_reason = reason
        self._broadcast_queue_changed()

    def resume_all(self) -> None:
        """Resume queue processing."""
        self._is_paused = False
        self._pause_reason = None
        self._broadcast_queue_changed()
        self.start()

    def record_rate_limit(self, chat_id: str | None = None) -> None:
        """Apply exponential backoff on HTTP 429 (§5)."""
        now = time.time()
        self._backoff_delay = min(60.0, self._backoff_delay * 2.0 if self._backoff_delay >= 2.0 else 2.0)
        self._backoff_until = now + self._backoff_delay
        logger.warning(f"Rate limit backoff active for {self._backoff_delay}s")

        if self.broadcaster:
            self.broadcaster.broadcast(
                "job_error",
                {"chatId": chat_id, "kind": "rate_limit", "backoffSeconds": self._backoff_delay},
            )
        self._broadcast_queue_changed()

    def reset_rate_limit(self) -> None:
        """Reset backoff delay after successful model call."""
        self._backoff_delay = 2.0

    def record_budget_stop(self, spent: float, cap: float) -> None:
        """Pause queue due to budget cap (§5)."""
        self.pause_all(reason="budget_reached")
        if self.broadcaster:
            self.broadcaster.broadcast("budget_stop", {"spent": spent, "cap": cap})

    def _broadcast_queue_changed(self) -> None:
        if self.broadcaster:
            status = self.get_queue_status()
            self.broadcaster.broadcast("queue_changed", status)

    def _select_next_job(self, jobs: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Select next job adhering to §4 ordering:
        1. priority descending (Map next, live replies)
        2. (totalPairs - completedPairs) ascending (shortest chats first!)
        3. createdAt ascending (FIFO)
        """
        candidates = [j for j in jobs if j.get("status") == "queued"]
        if not candidates:
            return None

        def sort_key(j: dict[str, Any]) -> tuple[int, int, str]:
            priority = int(j.get("priority", 0))
            remaining = max(0, int(j.get("totalPairs", 0)) - int(j.get("completedPairs", 0)))
            created = str(j.get("createdAt", ""))
            return (-priority, remaining, created)

        candidates.sort(key=sort_key)
        return candidates[0]

    async def _scheduler_loop(self) -> None:
        """Background worker dispatcher running parallel jobs up to setting (1–8)."""
        while not self._stopped:
            # Clean up finished tasks
            for cid in list(self._running_tasks.keys()):
                if self._running_tasks[cid].done():
                    self._running_tasks.pop(cid, None)

            # Check pause & backoff
            if self._is_paused or time.time() < self._backoff_until:
                await asyncio.sleep(0.4)
                continue

            settings = self.library.get_effective_settings()
            parallel_limit = max(1, min(8, int(settings.get("parallel_jobs", 2))))

            if len(self._running_tasks) >= parallel_limit:
                await asyncio.sleep(0.3)
                continue

            # Pick next candidate
            async with self._lock:
                jobs = self.library.get_jobs()
                next_job = self._select_next_job(jobs)

                if next_job is None:
                    # Nothing queued
                    if len(self._running_tasks) == 0:
                        break  # idle
                    await asyncio.sleep(0.5)
                    continue

                chat_id = next_job["chatId"]
                next_job["status"] = "running"
                next_job["startedAt"] = next_job.get("startedAt") or datetime.now(timezone.utc).isoformat()
                next_job["updatedAt"] = datetime.now(timezone.utc).isoformat()
                self.library.save_jobs(jobs)

            self._broadcast_queue_changed()

            # Spawn worker task for this chat
            task = asyncio.create_task(self._run_chat_worker(next_job))
            self._running_tasks[chat_id] = task

        self._scheduler_task = None

    async def _run_chat_worker(self, job: dict[str, Any]) -> None:
        """Executes a single chat job pair-by-pair sequentially."""
        chat_id = job["chatId"]
        total_pairs = int(job.get("totalPairs", 0))
        start_pair = int(job.get("completedPairs", 0)) + 1

        try:
            for pair in range(start_pair, total_pairs + 1):
                # Check cancellation or pause
                if self._stopped or job.get("status") == "canceled":
                    break

                t0 = time.time()

                # Execute pair using registered handler, rehearsal runner, pipeline runner, or default
                if self.worker_handler is not None:
                    await self.worker_handler(job, pair)
                elif job.get("mode") == "rehearsal" and self.rehearsal_runner is not None:
                    await self.rehearsal_runner.handle_pair(job, pair)
                elif self.pipeline_runner is not None:
                    await self.pipeline_runner.handle_pair(job, pair)
                else:
                    await self._default_pair_handler(job, pair)

                duration_ms = int((time.time() - t0) * 1000)

                # Record pair completion
                async with self._lock:
                    jobs = self.library.get_jobs()
                    j = next((item for item in jobs if item.get("id") == job["id"]), None)
                    if j:
                        j["completedPairs"] = pair
                        j["updatedAt"] = datetime.now(timezone.utc).isoformat()
                        j.setdefault("timingLog", []).append({"pair": pair, "durationMs": duration_ms})
                        self.library.save_jobs(jobs)

                # Emit progress & pair_ready (§6)
                if self.broadcaster:
                    self.broadcaster.broadcast(
                        "job_progress",
                        {"chatId": chat_id, "pair": pair, "of": total_pairs},
                    )
                    self.broadcaster.broadcast(
                        "pair_ready",
                        {"chatId": chat_id, "pair": pair},
                    )

            # Mark complete if all pairs done
            async with self._lock:
                jobs = self.library.get_jobs()
                j = next((item for item in jobs if item.get("id") == job["id"]), None)
                if j and j.get("status") == "running" and j.get("completedPairs", 0) >= total_pairs:
                    j["status"] = "completed"
                    j["completedAt"] = datetime.now(timezone.utc).isoformat()
                    j["updatedAt"] = datetime.now(timezone.utc).isoformat()
                    self.library.save_jobs(jobs)

            if self.broadcaster:
                self.broadcaster.broadcast("chat_ready", {"chatId": chat_id})
            self._broadcast_queue_changed()

        except asyncio.CancelledError:
            logger.info(f"Worker for {chat_id} canceled.")
        except RateLimitError:
            logger.warning(f"Worker rate-limited on {chat_id}, re-queuing.")
            async with self._lock:
                jobs = self.library.get_jobs()
                j = next((item for item in jobs if item.get("id") == job["id"]), None)
                if j and j.get("status") == "running":
                    j["status"] = "queued"
                    j["updatedAt"] = datetime.now(timezone.utc).isoformat()
                    self.library.save_jobs(jobs)
            self._broadcast_queue_changed()
        except BudgetStopError:
            logger.warning(f"Worker budget stop on {chat_id}, re-queuing.")
            async with self._lock:
                jobs = self.library.get_jobs()
                j = next((item for item in jobs if item.get("id") == job["id"]), None)
                if j and j.get("status") == "running":
                    j["status"] = "queued"
                    j["updatedAt"] = datetime.now(timezone.utc).isoformat()
                    self.library.save_jobs(jobs)
            self._broadcast_queue_changed()
        except Exception as exc:
            logger.exception(f"Worker error processing {chat_id}: {exc}")
            async with self._lock:
                jobs = self.library.get_jobs()
                j = next((item for item in jobs if item.get("id") == job["id"]), None)
                if j:
                    j["status"] = "failed"
                    j["error"] = str(exc)
                    j["errorKind"] = "crash"
                    j["updatedAt"] = datetime.now(timezone.utc).isoformat()
                    self.library.save_jobs(jobs)

            if self.broadcaster:
                self.broadcaster.broadcast(
                    "job_error",
                    {"chatId": chat_id, "kind": "crash", "error": str(exc)},
                )
            self._broadcast_queue_changed()

    async def _default_pair_handler(self, job: dict[str, Any], pair: int) -> None:
        """Default pair execution hook placeholder for S4.4 pipeline."""
        # Simulated or minimal step execution
        await asyncio.sleep(0.01)
