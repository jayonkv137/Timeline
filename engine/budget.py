"""COTRACE Budget Guard and Usage Monitoring.

Adheres to STANDALONE_V1_PLAN §4 (Step S3.4):
- Jobs refuse to start if estimated cost exceeds remaining monthly budget (BudgetExceededError).
- Running jobs stop at budget cap and emit budget_stop {spent, cap} (BudgetStopError).
- get_usage_summary() aggregates spend this month, per chat, per step, and per model.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any, Callable


class BudgetExceededError(Exception):
    """Refuse to start: estimated cost exceeds remaining monthly budget."""


class BudgetStopError(BudgetExceededError):
    """Mid-flight stop: running execution reached or exceeded the budget cap."""


def get_current_year_month() -> str:
    """Return UTC YYYY-MM string."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m")


def load_usage_entries(paths: list[Path]) -> list[dict[str, Any]]:
    """Load usage records from multiple JSONL files, de-duplicating identical records."""
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, int]] = set()

    for p in paths:
        if not p.is_file():
            continue
        try:
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        ts = str(entry.get("timestamp", ""))
                        call = str(entry.get("call", entry.get("step", "")))
                        model = str(entry.get("model", ""))
                        tokens_total = int(entry.get("tokens", {}).get("total", 0))
                        dedup_key = (ts, call, model, tokens_total)
                        if dedup_key in seen:
                            continue
                        seen.add(dedup_key)
                        records.append(entry)
                    except (json.JSONDecodeError, ValueError):
                        continue
        except OSError:
            continue

    return records


def get_usage_summary(
    library_root: Path | str | None = None,
    year_month: str | None = None,
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Aggregate token usage and USD costs for the specified month.
    
    Returns:
    {
        "month": "YYYY-MM",
        "spent_this_month": float,
        "monthly_budget": float,
        "remaining_budget": float,
        "by_chat": {chat_id: cost},
        "by_step": {step_name: cost},
        "by_model": {model_name: cost},
        "recent_calls": [...],
        "total_calls": int,
    }
    """
    if year_month is None:
        year_month = get_current_year_month()

    candidate_files: list[Path] = []

    if library_root is not None:
        lib_path = Path(library_root).expanduser().resolve()
        candidate_files.append(lib_path / "usage.jsonl")
        chats_dir = lib_path / "chats"
        if chats_dir.is_dir():
            for c_dir in chats_dir.iterdir():
                if c_dir.is_dir():
                    candidate_files.append(c_dir / "run" / "usage.jsonl")
    else:
        # Default fallback: check COTRACE_HOME or local repo runs
        candidate_files.append(Path("run/usage.jsonl").resolve())

    # Filter out non-existent files and load records
    all_records = load_usage_entries([f for f in candidate_files if f.is_file()])

    monthly_records = [
        r for r in all_records
        if str(r.get("timestamp", "")).startswith(year_month)
    ]

    spent_this_month = 0.0
    by_chat: dict[str, float] = {}
    by_step: dict[str, float] = {}
    by_model: dict[str, float] = {}

    for r in monthly_records:
        cost_dict = r.get("cost", {})
        cost_val = float(cost_dict.get("total", 0.0))
        spent_this_month += cost_val

        chat_id = str(r.get("chat_id") or "unassigned")
        by_chat[chat_id] = round(by_chat.get(chat_id, 0.0) + cost_val, 6)

        step_name = str(r.get("step") or "other")
        by_step[step_name] = round(by_step.get(step_name, 0.0) + cost_val, 6)

        model_name = str(r.get("model") or "unknown")
        by_model[model_name] = round(by_model.get(model_name, 0.0) + cost_val, 6)

    spent_this_month = round(spent_this_month, 6)

    # Budget cap from settings
    monthly_budget = 20.0
    if settings is not None and "monthly_budget" in settings:
        try:
            monthly_budget = float(settings["monthly_budget"])
        except (ValueError, TypeError):
            pass
    elif library_root is not None:
        settings_file = Path(library_root) / "settings.json"
        if settings_file.is_file():
            try:
                with open(settings_file, "r", encoding="utf-8") as sf:
                    s_data = json.load(sf)
                    monthly_budget = float(s_data.get("monthly_budget", 20.0))
            except Exception:
                pass

    remaining_budget = max(0.0, round(monthly_budget - spent_this_month, 6))

    # Sort recent calls by timestamp descending
    sorted_calls = sorted(
        monthly_records,
        key=lambda x: str(x.get("timestamp", "")),
        reverse=True,
    )[:50]

    return {
        "month": year_month,
        "spent_this_month": spent_this_month,
        "monthly_budget": monthly_budget,
        "remaining_budget": remaining_budget,
        "by_chat": by_chat,
        "by_step": by_step,
        "by_model": by_model,
        "recent_calls": sorted_calls,
        "total_calls": len(monthly_records),
    }


def check_budget_before_start(
    estimated_cost: float,
    library_root: Path | str | None = None,
    settings: dict[str, Any] | None = None,
) -> None:
    """Pre-flight check: refuse to start a job if estimate exceeds remaining budget."""
    summary = get_usage_summary(library_root=library_root, settings=settings)
    remaining = summary["remaining_budget"]
    cap = summary["monthly_budget"]
    spent = summary["spent_this_month"]
    est = float(estimated_cost)

    if round(spent + est, 6) > cap or remaining < est:
        raise BudgetExceededError(
            f"Job estimated at ${est:.4f} exceeds remaining budget of ${remaining:.4f} "
            f"(spent ${spent:.4f} of ${cap:.2f} monthly budget)"
        )


class BudgetGuard:
    """Runtime budget guard: stops execution mid-flight when budget cap is reached."""

    def __init__(
        self,
        cap: float,
        current_spent: float = 0.0,
        on_budget_stop: Callable[[float, float], None] | None = None,
        chat_id: str | None = None,
    ) -> None:
        self.cap = round(float(cap), 6)
        self.current_spent = round(float(current_spent), 6)
        self.on_budget_stop = on_budget_stop
        self.chat_id = chat_id
        self.stopped = False

    def check_or_record(self, cost: float) -> None:
        """Add cost and immediately raise BudgetStopError if cumulative spent reaches or exceeds cap."""
        self.current_spent = round(self.current_spent + float(cost), 6)
        if self.current_spent >= self.cap:
            self.stopped = True
            if self.on_budget_stop:
                try:
                    self.on_budget_stop(self.current_spent, self.cap)
                except Exception:
                    pass
            raise BudgetStopError(
                f"Budget cap reached: spent ${self.current_spent:.4f} >= cap ${self.cap:.2f}"
            )
