"""Caching LLM client wrapper (TEST_STRATEGY §1 & E0_BRIEF S6).

Wraps an LLMClient with record and replay modes.
Does not modify engine/llm.py.

Modes (configured via LLM_CACHE_MODE env var or constructor):
  - 'off': Pass through directly to inner LLMClient (default)
  - 'record': Call API, write prompt + response to tests/cassettes/<key>.json
  - 'replay': Serve from cassette file with zero network calls. Cache miss is a hard error.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine.llm import LLMError


class LLMCacheMissError(LLMError):
    """Raised when a cassette is missing in replay mode."""


def compute_cache_key(model: str, prompt: str) -> str:
    """Deterministic SHA-256 hash of model name and exact prompt text."""
    payload = f"{model.strip()}:{prompt}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class CachingLLMClient:
    """Wraps an LLMClient with disk-based record/replay caching."""

    def __init__(
        self,
        inner_client: Any = None,
        mode: str | None = None,
        cassettes_dir: Path | str | None = None,
    ) -> None:
        if mode is None:
            mode = os.environ.get("LLM_CACHE_MODE", "off").lower()
        self.mode = mode.lower()
        if self.mode not in ("off", "record", "replay"):
            raise ValueError(f"unknown LLM cache mode: '{self.mode}'. Expected off, record, or replay.")

        if cassettes_dir is None:
            cassettes_dir = (
                os.environ.get("LLM_CASSETTES_DIR")
                or Path(__file__).resolve().parent.parent / "tests" / "cassettes"
            )
        self.cassettes_dir = Path(cassettes_dir)
        self.cassettes_dir.mkdir(parents=True, exist_ok=True)

        self._inner = inner_client

    def call_json(self, step: str, model: str, prompt: str) -> Any:
        """Call LLM or serve from cassette according to mode."""
        if self.mode == "off":
            if self._inner is None:
                raise LLMError("inner LLMClient is required when cache mode is 'off'")
            return self._inner.call_json(step, model, prompt)

        key = compute_cache_key(model, prompt)
        cassette_path = self.cassettes_dir / f"{key}.json"

        if self.mode == "replay":
            if not cassette_path.exists():
                raise LLMCacheMissError(
                    f"cassette miss in replay mode: key={key} (step='{step}', model='{model}')\n"
                    f"File not found: {cassette_path}"
                )
            with open(cassette_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data["response"]

        if self.mode == "record":
            if self._inner is None:
                raise LLMError("inner LLMClient is required when cache mode is 'record'")
            response = self._inner.call_json(step, model, prompt)
            cassette_data = {
                "key": key,
                "step": step,
                "model": model,
                "prompt": prompt,
                "response": response,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }
            with open(cassette_path, "w", encoding="utf-8") as f:
                json.dump(cassette_data, f, indent=2, ensure_ascii=False)
                f.write("\n")
            return response

        raise ValueError(f"unexpected mode: {self.mode}")


# Alias for flexible importing
LLMCacheClient = CachingLLMClient
