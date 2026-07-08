"""Engine configuration, env-driven.

Loads from process env first, then from the repo-root `.env` file (process env
wins). Provider scheme is the OpenAI-compatible one per the owner-approved
amendment (BUILDLOG 2026-07-08, SPEC_QUESTIONS.md Q1): `LLM_API_KEY` +
`LLM_BASE_URL`, Gemini model defaults.

Model routing per PHASE2_BRIEF S1:
- MODEL_FAST  — Step 1a
- MODEL_MAIN  — Steps 1b / 1c / 2 / 3
- MODEL_STEP2 / MODEL_STEP3 — optional per-step overrides, falling back to
  MODEL_MAIN when unset/empty.
"""
import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path):
    """Minimal .env reader (KEY=VALUE lines, # comments). No new dependency —
    the allowlist (Build Playbook §5) has no dotenv package.
    """
    values = {}
    if not path.exists():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _env(dotenv, key, default=""):
    value = os.environ.get(key)
    if value is None or value == "":
        value = dotenv.get(key, "")
    return value if value != "" else default


@dataclass(frozen=True)
class Config:
    llm_api_key: str
    llm_base_url: str
    model_fast: str      # Step 1a
    model_main: str      # Steps 1b / 1c, and fallback for 2 / 3
    model_step2: str     # Step 2 (defaults to model_main)
    model_step3: str     # Step 3 (defaults to model_main)
    step3_batch_size: int


def load_config(env_file=None):
    dotenv = _load_dotenv(Path(env_file) if env_file else REPO_ROOT / ".env")
    model_main = _env(dotenv, "MODEL_MAIN", "gemini-3.5-flash")
    return Config(
        llm_api_key=_env(dotenv, "LLM_API_KEY"),
        llm_base_url=_env(
            dotenv, "LLM_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta/openai/",
        ),
        model_fast=_env(dotenv, "MODEL_FAST", "gemini-3.1-flash-lite"),
        model_main=model_main,
        model_step2=_env(dotenv, "MODEL_STEP2", model_main),
        model_step3=_env(dotenv, "MODEL_STEP3", model_main),
        step3_batch_size=int(_env(dotenv, "STEP3_BATCH_SIZE", "3")),
    )
