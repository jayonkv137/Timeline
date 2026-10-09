"""Model catalog and pricing layer adhering to STANDALONE_V1_PLAN §4 (Step S3.1).

Loads engine/models.yaml using a zero-dependency YAML parser. Computes exact token
costs per call and supports replay mode ($0.00 cost with preserved token counts).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

MODELS_YAML_PATH = Path(__file__).resolve().parent / "models.yaml"

DEFAULT_PRICING: dict[str, float] = {
    "input_cost_per_m": 0.100,
    "output_cost_per_m": 0.400,
}


def parse_simple_yaml(text: str) -> dict[str, Any]:
    """Parse hierarchical key-value YAML without external dependencies.
    
    Supports comments (#), root sections, and 2-space or 4-space indented dictionaries.
    """
    data: dict[str, Any] = {}
    current_section: str | None = None
    current_key: str | None = None

    for raw_line in text.splitlines():
        # Strip comments
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip())
        content = line.strip()

        if ":" not in content:
            continue

        key, val = [part.strip() for part in content.split(":", 1)]

        if indent == 0:
            if val:
                data[key] = _cast_value(val)
            else:
                data[key] = {}
                current_section = key
                current_key = None
        elif indent == 2:
            if current_section:
                if val:
                    data[current_section][key] = _cast_value(val)
                else:
                    data[current_section][key] = {}
                    current_key = key
            else:
                data[key] = _cast_value(val)
        elif indent >= 4 and current_section and current_key:
            data[current_section][current_key][key] = _cast_value(val)

    return data


def _cast_value(val_str: str) -> Any:
    """Cast string value to float, int, bool, or stripped string."""
    clean = val_str.strip().strip("'\"")
    if not clean:
        return ""
    if clean.lower() == "true":
        return True
    if clean.lower() == "false":
        return False
    try:
        if "." in clean or "e" in clean.lower():
            return float(clean)
        return int(clean)
    except ValueError:
        return clean


_CACHED_PRICE_TABLE: dict[str, dict[str, float]] | None = None


def load_price_table(path: Path | str | None = None, force_reload: bool = False) -> dict[str, dict[str, float]]:
    """Load model pricing catalog from engine/models.yaml."""
    global _CACHED_PRICE_TABLE
    if _CACHED_PRICE_TABLE is not None and not force_reload and path is None:
        return _CACHED_PRICE_TABLE

    yaml_path = Path(path).resolve() if path is not None else MODELS_YAML_PATH
    if not yaml_path.is_file():
        return {"default": DEFAULT_PRICING}

    content = yaml_path.read_text(encoding="utf-8")
    raw = parse_simple_yaml(content)
    models = raw.get("models", raw)

    table: dict[str, dict[str, float]] = {}
    for name, fields in models.items():
        if isinstance(fields, dict):
            table[name.strip()] = {
                "input_cost_per_m": float(fields.get("input_cost_per_m", DEFAULT_PRICING["input_cost_per_m"])),
                "output_cost_per_m": float(fields.get("output_cost_per_m", DEFAULT_PRICING["output_cost_per_m"])),
            }

    if "default" not in table:
        table["default"] = DEFAULT_PRICING

    if path is None:
        _CACHED_PRICE_TABLE = table
    return table


def get_model_price(model_name: str, table: dict[str, dict[str, float]] | None = None) -> tuple[float, float]:
    """Return (input_cost_per_m, output_cost_per_m) for the given model."""
    catalog = table if table is not None else load_price_table()
    name = (model_name or "").strip()

    if name in catalog:
        entry = catalog[name]
        return entry["input_cost_per_m"], entry["output_cost_per_m"]

    # Case-insensitive lookup
    lower_map = {k.lower(): v for k, v in catalog.items()}
    if name.lower() in lower_map:
        entry = lower_map[name.lower()]
        return entry["input_cost_per_m"], entry["output_cost_per_m"]

    # Prefix match (e.g. "gemini-3.5-flash-latest" -> "gemini-3.5-flash")
    for key, entry in catalog.items():
        if key != "default" and name.lower().startswith(key.lower()):
            return entry["input_cost_per_m"], entry["output_cost_per_m"]

    default_entry = catalog.get("default", DEFAULT_PRICING)
    return default_entry["input_cost_per_m"], default_entry["output_cost_per_m"]


def compute_token_cost(
    model_name: str,
    prompt_tokens: int,
    completion_tokens: int,
    is_replay: bool = False,
    table: dict[str, dict[str, float]] | None = None,
) -> dict[str, float]:
    """Compute prompt, completion, and total cost in USD.
    
    If is_replay is True, cost is strictly $0.00.
    """
    if is_replay:
        return {"prompt": 0.0, "completion": 0.0, "total": 0.0}

    in_price, out_price = get_model_price(model_name, table=table)
    prompt_cost = round((max(0, prompt_tokens) / 1_000_000.0) * in_price, 7)
    completion_cost = round((max(0, completion_tokens) / 1_000_000.0) * out_price, 7)
    total_cost = round(prompt_cost + completion_cost, 7)

    return {
        "prompt": prompt_cost,
        "completion": completion_cost,
        "total": total_cost,
    }
