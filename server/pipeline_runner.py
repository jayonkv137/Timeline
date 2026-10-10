"""Pipeline per chat execution engine (STANDALONE_V1_PLAN §4 Step S4.4).

Per docs/PROCESSING_UX_SPEC.md v1.1 §5 & §6:
Executes extraction pipeline for promoted chats using configured LLM client,
caching wrapper, usage meter, and runtime checks.

Sync LLM and CPU work runs in worker threads (asyncio.to_thread) so the FastAPI
server and SSE broadcast never block.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from engine.artifacts import LedgerWriter, write_json_artifact
from engine.budget import BudgetGuard, BudgetStopError, get_usage_summary
from engine.checks import InvariantViolationError, is_state_valid, run_pair_checks, write_report, write_status
from engine.config import Config
from engine.llm import LLMClient, RateLimitError
from engine.llm_cache import CachingLLMClient
from engine.pipeline import process_pair
from engine.projections.panel import export_panel_projections
from engine.projections.workspace import export_workspace_bundle, load_chat_metadata
from engine.state import State
from server.library import Library

logger = logging.getLogger("cotrace.pipeline_runner")


def build_config_from_settings(settings: dict[str, Any], api_key: str) -> Config:
    """Build immutable engine Config dataclass from library settings."""
    model_main = settings.get("model_main") or "gemini-2.5-flash"
    return Config(
        llm_api_key=api_key,
        llm_base_url=settings.get("provider_url") or "https://generativelanguage.googleapis.com/v1beta/openai/",
        model_fast=settings.get("model_fast") or model_main,
        model_main=model_main,
        model_step2=settings.get("model_step2") or model_main,
        model_step3=settings.get("model_step3") or model_main,
        step3_batch_size=int(settings.get("step3_batch_size", 4)),
        reasoning_effort=settings.get("reasoning_effort", "none"),
    )


class PipelineRunner:
    """Orchestrates live extraction pipeline runs for promoted chats."""

    def __init__(
        self,
        library: Library,
        broadcaster: Any = None,
        job_queue: Any = None,
        custom_client: Any = None,
    ) -> None:
        self.library = library
        self.broadcaster = broadcaster
        self.job_queue = job_queue
        self.custom_client = custom_client

    def set_job_queue(self, queue: Any) -> None:
        self.job_queue = queue

    async def handle_pair(self, job: dict[str, Any], pair: int) -> None:
        """Execute extraction pipeline for single pair (called by JobQueueManager worker)."""
        chat_id = job["chatId"]
        cdir = self.library.chat_dir(chat_id)
        if not cdir.is_dir():
            raise FileNotFoundError(f"Chat directory '{chat_id}' not found in library")

        settings = self.library.get_effective_settings()
        api_key = self.library.get_api_key()

        # Auth guard: if no API key configured and no mock client injected, stop before any spend (§5)
        if not api_key and self.custom_client is None:
            err_msg = "No API key configured. Check your key in Settings."
            if self.broadcaster:
                self.broadcaster.broadcast(
                    "job_error",
                    {"chatId": chat_id, "kind": "auth", "error": err_msg},
                )
            raise ValueError(err_msg)

        cfg = build_config_from_settings(settings, api_key)
        summary = get_usage_summary(library_root=self.library.root, settings=settings)
        monthly_cap = float(summary.get("monthly_budget", 50.0))
        current_spent = float(summary.get("spent_this_month", 0.0))
        budget_guard = BudgetGuard(
            cap=monthly_cap,
            current_spent=current_spent,
            chat_id=chat_id,
        )

        # Offload sync model and processing work to thread pool
        try:
            await asyncio.to_thread(
                self._execute_pair_sync,
                cdir,
                chat_id,
                pair,
                cfg,
                budget_guard,
            )
        except RateLimitError:
            logger.warning(f"Rate limit encountered while processing {chat_id} pair {pair}")
            if self.job_queue:
                self.job_queue.record_rate_limit(chat_id)
            raise
        except BudgetStopError as b_err:
            logger.warning(f"Budget cap reached while processing {chat_id}: {b_err}")
            if self.job_queue:
                self.job_queue.record_budget_stop(spent=budget_guard.current_spent, cap=budget_guard.cap)
            raise
        except InvariantViolationError as inv_err:
            logger.warning(f"Invariant check flagged on {chat_id} pair {pair}: {inv_err}")
            if self.broadcaster:
                self.broadcaster.broadcast(
                    "pair_flagged",
                    {"chatId": chat_id, "pair": pair, "reason": str(inv_err)},
                )
            # In product mode (S-D9), keep going if state is valid
        except Exception as exc:
            logger.exception(f"Pipeline error on {chat_id} pair {pair}: {exc}")
            if self.broadcaster:
                self.broadcaster.broadcast(
                    "job_error",
                    {"chatId": chat_id, "kind": "crash", "error": str(exc)},
                )
            raise

    def _execute_pair_sync(
        self,
        cdir: Path,
        chat_id: str,
        pair: int,
        config: Config,
        budget_guard: BudgetGuard,
    ) -> None:
        """Synchronous pair execution executed in thread worker."""
        dialogue_path = cdir / "dialogue.json"
        if not dialogue_path.is_file():
            raise FileNotFoundError(f"dialogue.json missing in {cdir}")

        with dialogue_path.open("r", encoding="utf-8") as f:
            dialogue_list = json.load(f)

        # Find turns for this pair
        u_text = ""
        a_text = ""
        for t in dialogue_list:
            if t.get("pair") == pair:
                if t.get("speaker") == "user":
                    u_text = t.get("text", "")
                elif t.get("speaker") == "ai":
                    a_text = t.get("text", "")

        total_pairs = max((t.get("pair", 1) for t in dialogue_list), default=1)

        # State loading or initialization
        state_file = cdir / "state.json"
        if state_file.is_file() and pair > 1:
            state = State.load(cdir)
        else:
            state = State()

        # Build client
        if self.custom_client is not None:
            client = self.custom_client
            if hasattr(client, "set_out_dir"):
                client.set_out_dir(cdir)
        else:
            base_client = LLMClient(config=config, out_dir=cdir, budget_guard=budget_guard)
            client = CachingLLMClient(
                inner_client=base_client,
                mode="record",
                cassettes_dir=self.library.root / "cache",
                out_dir=cdir,
            )

        run_dir = cdir / "run"
        run_dir.mkdir(parents=True, exist_ok=True)
        ledger_writer = LedgerWriter(cdir / "ledger.jsonl")

        # Execute extraction steps 1a -> 1b -> 1c -> 2 -> 3
        new_actions, l2_res = process_pair(
            client=client,
            config=config,
            state=state,
            pair_number=pair,
            user_text=u_text,
            ai_text=a_text,
            ledger_writer=ledger_writer,
        )

        state.run["last_completed_pair"] = pair

        # Save state.json and run/pipeline_state.json
        write_json_artifact(state_file, state.to_dict(), "state")
        with (run_dir / "pipeline_state.json").open("w", encoding="utf-8") as f:
            json.dump(state.run, f, indent=2, ensure_ascii=False)
            f.write("\n")

        # Projections: panel_bundle.json & snapshots.json
        export_panel_projections(
            target_dir=cdir,
            ledger_rows=ledger_writer.rows,
            state_dict=state.to_dict(),
            max_pair=pair,
        )

        # Runtime checks (§11.4 & TEST_STRATEGY §6)
        chk_res = run_pair_checks(
            state=state,
            ledger_rows=ledger_writer.rows,
            dialogue=dialogue_list,
            prev_ledger_rows=None,
            current_pair=pair,
        )
        healthy = len(chk_res.violations) == 0
        write_status(
            cdir,
            healthy=healthy,
            pair_number=pair,
            violations=chk_res.violations,
        )

        flagged_list = list(state.run.get("flagged_pairs", []))
        if not healthy:
            flagged_record = {
                "pair": pair,
                "invariant": chk_res.failed[0] if chk_res.failed else "invariant_violation",
                "detail": "; ".join(chk_res.violations),
            }
            flagged_list.append(flagged_record)
            state.run["flagged_pairs"] = flagged_list

            if self.broadcaster:
                self.broadcaster.broadcast(
                    "pair_flagged",
                    {"chatId": chat_id, "pair": pair, "reason": "; ".join(chk_res.violations)},
                )

            # In product mode (S-D9): if state is corrupt, halt and raise
            if not is_state_valid(state):
                logger.error(f"State corrupted on {chat_id} pair {pair}: {chk_res.violations}")
                raise InvariantViolationError(chk_res.violations, chk_res.failed)

        # Incremental workspace bundle projection
        source_meta, meta, file_summary = load_chat_metadata(cdir)
        summary_text = state.run.get("dialogue_summary") or file_summary or ""
        is_final = (pair >= total_pairs)

        if flagged_list:
            status = "needs_review"
        elif is_final:
            status = "ready"
        else:
            status = "processing"

        export_workspace_bundle(
            output_path=cdir / "workspace_bundle.json",
            dialogue=dialogue_list,
            state=state.to_dict(),
            ledger=ledger_writer.rows,
            source_meta=source_meta,
            meta=meta,
            chat_id=chat_id,
            summary=summary_text,
            status=status,
            processed_pairs=pair,
            flagged_pairs=flagged_list if flagged_list else None,
        )

        # Final report on completion
        if is_final:
            write_report(
                out_dir=cdir,
                chat_id=chat_id,
                pairs_processed=total_pairs,
                wall_time_per_pair=[],
                tokens_per_pair=[],
                llm_calls=getattr(client, "call_count", 0),
                retries=getattr(client, "retry_count", 0),
                cache_hits=getattr(client, "cache_hits", 0),
                state=state,
                checks_passed=list(chk_res.passed),
                checks_failed=list(chk_res.failed),
            )
