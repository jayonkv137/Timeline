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


class LLMClient:
    def __init__(self, config, out_dir):
        """`out_dir` is the run's output folder (`<out>`); the monitor file is
        `<out>/run/llm_monitor.txt`, appended from the first call.
        """
        if not config.llm_api_key:
            raise LLMError("LLM_API_KEY is not set (check .env at repo root)")
        self._client = OpenAI(api_key=config.llm_api_key, base_url=config.llm_base_url)
        self.monitor_path = Path(out_dir) / "run" / "llm_monitor.txt"
        self.monitor_path.parent.mkdir(parents=True, exist_ok=True)
        self.call_count = 0

    def call_json(self, step, model, prompt):
        """One LLM call → parsed JSON object. `step` is a label for the
        monitor log (e.g. "1a", "2:outcome 3", "3:o1/req2:batch0").
        """
        last_exc = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            started = time.monotonic()
            try:
                response = self._client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                text = response.choices[0].message.content or ""
                elapsed = time.monotonic() - started
                usage = getattr(response, "usage", None)
                self._log(step, model, attempt, prompt, text, elapsed, usage, error=None)
                return parse_json_response(text)
            except _TRANSIENT_EXCEPTIONS as exc:
                elapsed = time.monotonic() - started
                self._log(step, model, attempt, prompt, "", elapsed, None, error=repr(exc))
                last_exc = exc
            except APIStatusError as exc:
                elapsed = time.monotonic() - started
                self._log(step, model, attempt, prompt, "", elapsed, None, error=repr(exc))
                if exc.status_code >= 500:
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
