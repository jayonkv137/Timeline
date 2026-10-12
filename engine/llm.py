"""LLM call layer.

One entry point: `LLMClient.call_json(...)` — sends a single-user-message
chat completion, logs the FULL prompt and FULL response to
`<out>/run/llm_monitor.txt`, retries transient failures with exponential
backoff, and parses the response to JSON (strip code fences → json.loads →
json_repair fallback). A response that still fails to parse after repair is a
hard error (LLMParseError), never a warning.

Built on the OpenAI SDK with configurable base_url per the owner-approved
provider amendment (SPEC_QUESTIONS.md Q1) — not the Anthropic SDK named in
PHASE2_BRIEF S1.
"""
import datetime
import json
import time
from pathlib import Path

import json_repair
from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError

MAX_ATTEMPTS = 4
BACKOFF_BASE_SECONDS = 2.0  # 2, 4, 8 between the 4 attempts

_TRANSIENT_EXCEPTIONS = (APIConnectionError, APITimeoutError, RateLimitError)


class LLMError(Exception):
    """A call failed after all retry attempts."""


class LLMParseError(Exception):
    """The response text could not be parsed to JSON even after repair."""


def strip_code_fences(text):
    """Remove a single wrapping ``` / ```json fence if present."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    # drop opening fence line (``` or ```json etc.)
    lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def parse_json_response(text):
    """fence-strip → json.loads → json_repair → LLMParseError."""
    cleaned = strip_code_fences(text)
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        pass
    try:
        repaired = json_repair.loads(cleaned)
    except Exception as exc:
        raise LLMParseError(f"unparseable LLM response even after repair: {exc}\n"
                            f"--- response text ---\n{text}") from exc
    # json_repair can silently coerce garbage to '' or None — treat as failure
    if repaired is None or repaired == "" or repaired == []:
        raise LLMParseError("LLM response repaired to an empty value\n"
                            f"--- response text ---\n{text}")
    return repaired


import re
from typing import Any
from engine.models import compute_token_cost


class UsageMeter:
    """Tracks token consumption and USD costs, logging to run/usage.jsonl.
    
    Adheres to STANDALONE_V1_PLAN §4 (Step S3.1):
    {"timestamp": ..., "step": ..., "pair": ..., "model": ..., "tokens": {...}, "cost": {...}, "mode": ...}
    """

    def __init__(self, usage_path: Path | str | None = None, budget_guard: Any = None):
        self.usage_path = Path(usage_path).resolve() if usage_path else None
        self.budget_guard = budget_guard
        self.records: list[dict[str, Any]] = []
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0
        self.total_cost: float = 0.0

    def set_path(self, usage_path: Path | str) -> None:
        self.usage_path = Path(usage_path).resolve()

    def record(
        self,
        step: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        is_replay: bool = False,
        mode: str = "live",
        chat_id: str | None = None,
    ) -> dict[str, Any]:
        prompt_tokens = max(0, int(prompt_tokens))
        completion_tokens = max(0, int(completion_tokens))
        total_tokens = prompt_tokens + completion_tokens

        pair_num = None
        match = re.search(r"pair(\d+)", step)
        if match:
            pair_num = int(match.group(1))

        step_name = step.split(":")[0] if ":" in step else step

        cost = compute_token_cost(
            model_name=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            is_replay=is_replay,
        )

        entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "chat_id": chat_id,
            "step": step_name,
            "call": step,
            "pair": pair_num,
            "model": model,
            "tokens": {
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "total": total_tokens,
            },
            "cost": cost,
            "mode": mode,
        }

        self.records.append(entry)
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_cost += cost["total"]

        if self.usage_path:
            self.usage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.usage_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        if self.budget_guard is not None:
            self.budget_guard.check_or_record(cost["total"])

        return entry

    def summary(self) -> dict[str, Any]:
        return {
            "calls": len(self.records),
            "tokens": {
                "prompt": self.total_prompt_tokens,
                "completion": self.total_completion_tokens,
                "total": self.total_prompt_tokens + self.total_completion_tokens,
            },
            "cost": round(self.total_cost, 6),
        }


class LLMClient:
    def __init__(self, config, out_dir, budget_guard: Any = None):
        """`out_dir` is the run's output folder (`<out>`); the monitor file is
        `<out>/run/llm_monitor.txt`, appended from the first call.
        """
        if not config.llm_api_key:
            raise LLMError("LLM_API_KEY is not set (check .env at repo root)")
        self._client = OpenAI(api_key=config.llm_api_key, base_url=config.llm_base_url)
        self.out_dir = Path(out_dir)
        self.monitor_path = self.out_dir / "run" / "llm_monitor.txt"
        self.monitor_path.parent.mkdir(parents=True, exist_ok=True)
        self.usage_path = self.out_dir / "run" / "usage.jsonl"
        self.budget_guard = budget_guard
        self.usage_meter = UsageMeter(self.usage_path, budget_guard=budget_guard)
        self.reasoning_effort = getattr(config, "reasoning_effort", "none")
        self.call_count = 0
        self.retry_count = 0
        self.total_tokens = 0
        self.cache_hits = 0

    def set_budget_guard(self, budget_guard: Any) -> None:
        self.budget_guard = budget_guard
        self.usage_meter.budget_guard = budget_guard

    def set_out_dir(self, out_dir: Path | str) -> None:
        self.out_dir = Path(out_dir)
        self.monitor_path = self.out_dir / "run" / "llm_monitor.txt"
        self.usage_path = self.out_dir / "run" / "usage.jsonl"
        self.usage_meter.set_path(self.usage_path)

    def call_json(self, step, model, prompt):
        """One LLM call → parsed JSON object. `step` is a label for the
        monitor log (e.g. "1a", "2:outcome 3", "3:o1/req2:batch0").
        """
        last_exc = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            started = time.monotonic()
            kwargs: dict[str, Any] = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
            }
            if self.reasoning_effort and self.reasoning_effort != "default":
                kwargs["reasoning_effort"] = self.reasoning_effort

            try:
                try:
                    response = self._client.chat.completions.create(**kwargs)
                except TypeError:
                    if "reasoning_effort" in kwargs:
                        kwargs.pop("reasoning_effort", None)
                        response = self._client.chat.completions.create(**kwargs)
                    else:
                        raise
                except APIStatusError as a_exc:
                    if "reasoning_effort" in str(a_exc).lower() and "reasoning_effort" in kwargs:
                        kwargs.pop("reasoning_effort", None)
                        response = self._client.chat.completions.create(**kwargs)
                    else:
                        raise
                text = response.choices[0].message.content or ""
                elapsed = time.monotonic() - started
                usage = getattr(response, "usage", None)
                prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
                completion_tokens = getattr(usage, "completion_tokens", 0) or 0
                if usage is None and text:
                    prompt_tokens = max(1, len(prompt) // 4)
                    completion_tokens = max(1, len(text) // 4)
                if usage is not None:
                    self.total_tokens += getattr(usage, "total_tokens", 0) or 0
                else:
                    self.total_tokens += prompt_tokens + completion_tokens

                self.usage_meter.record(
                    step=step,
                    model=model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    is_replay=False,
                    mode="live",
                )
                self._log(step, model, attempt, prompt, text, elapsed, usage, error=None)
                return parse_json_response(text)
            except _TRANSIENT_EXCEPTIONS as exc:
                self.retry_count += 1
                elapsed = time.monotonic() - started
                self._log(step, model, attempt, prompt, "", elapsed, None, error=repr(exc))
                last_exc = exc
            except APIStatusError as exc:
                elapsed = time.monotonic() - started
                self._log(step, model, attempt, prompt, "", elapsed, None, error=repr(exc))
                if exc.status_code >= 500:
                    self.retry_count += 1
                    last_exc = exc  # server-side: retry
                else:
                    raise LLMError(f"non-retryable API error on step {step}: {exc}") from exc
            if attempt < MAX_ATTEMPTS:
                time.sleep(BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)))
        raise LLMError(f"step {step}: all {MAX_ATTEMPTS} attempts failed; last: {last_exc}") from last_exc

    def _log(self, step, model, attempt, prompt, response_text, elapsed, usage, error):
        self.call_count += 1
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        usage_line = ""
        if usage is not None:
            usage_line = (f"tokens: prompt={getattr(usage, 'prompt_tokens', '?')} "
                          f"completion={getattr(usage, 'completion_tokens', '?')} "
                          f"total={getattr(usage, 'total_tokens', '?')}\n")
        entry = (
            f"{'=' * 78}\n"
            f"CALL #{self.call_count} · step {step} · model {model} · attempt {attempt}\n"
            f"time: {ts} · elapsed: {elapsed:.2f}s\n"
            f"{usage_line}"
            + (f"ERROR: {error}\n" if error else "")
            + f"{'-' * 30} PROMPT {'-' * 30}\n"
            f"{prompt}\n"
            f"{'-' * 29} RESPONSE {'-' * 29}\n"
            f"{response_text}\n"
        )
        with open(self.monitor_path, "a") as f:
            f.write(entry)


import asyncio
from typing import AsyncGenerator
from openai import AsyncOpenAI


async def stream_chat_turn(
    messages: list[dict[str, str]],
    api_key: str,
    base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/",
    model: str = "gemini-3.6-flash",
    temperature: float = 0.7,
) -> AsyncGenerator[str, None]:
    """Asynchronously stream chat completion tokens from OpenAI-compatible endpoint.
    
    Yields string chunks as they arrive from the model.
    Supports mock/test bypass for fast deterministic unit tests.
    """
    if not api_key:
        raise LLMError("No API key configured for live chat.")

    # Mock or test mode bypass for unit tests without external network dependencies
    if (
        api_key.lower().startswith(("mock", "test", "fake"))
        or "mock" in (base_url or "").lower()
        or "fake" in (base_url or "").lower()
    ):
        mock_tokens = [
            "Hello! ",
            "I am ",
            "ready to help ",
            "you explore ",
            "and develop ",
            "this topic.",
        ]
        for token in mock_tokens:
            await asyncio.sleep(0.01)
            yield token
        return

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=temperature,
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as exc:
        raise LLMError(f"Error streaming chat completion: {exc}") from exc

