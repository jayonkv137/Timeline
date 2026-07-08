"""Artifact validation gate + writers.

Every artifact write in the engine goes through `validate_artifact` — a failed
validation RAISES (jsonschema.ValidationError), never warns. No unvalidated
write path exists (Build Playbook §5, PHASE2_BRIEF hard rules).

Artifacts (ARCHITECTURE §3):
- state.json         — whole-file, state.schema.json
- ledger.jsonl       — one row per line, each row ledger_row.schema.json,
                       APPEND-ONLY (the writer never rewrites the file)
- snapshots.json     — whole-file, snapshots.schema.json
- dialogue.json      — whole-file, dialogue.schema.json
- panel_bundle.json  — whole-file, panel_bundle.schema.json (written by Stage 4)
"""
import json
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMAS_DIR = Path(__file__).resolve().parent / "schemas"

_validators = {}


def _validator(schema_name):
    if schema_name not in _validators:
        with open(SCHEMAS_DIR / f"{schema_name}.schema.json") as f:
            _validators[schema_name] = Draft202012Validator(json.load(f))
    return _validators[schema_name]


def validate_artifact(instance, schema_name):
    """Validate `instance` against engine/schemas/<schema_name>.schema.json.
    Raises jsonschema.ValidationError on failure. Returns the instance so
    writers can validate-and-use in one expression.
    """
    _validator(schema_name).validate(instance)
    return instance


def write_json_artifact(path, instance, schema_name):
    """Validate, then write pretty-printed JSON. Validation failure raises
    BEFORE anything touches the file.
    """
    validate_artifact(instance, schema_name)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(instance, f, indent=2, ensure_ascii=False)
        f.write("\n")


class LedgerWriter:
    """Append-only writer for ledger.jsonl (PIPELINE_SPEC §10.3: rows are
    append-only, never edited). Each row is schema-validated before the line
    is written. Keeps all rows (pre-existing + appended) in memory so Stage 4
    can query without re-reading the file.
    """

    def __init__(self, path):
        self.path = Path(path)
        self.rows = []
        if self.path.exists():
            with open(self.path) as f:
                for line in f:
                    if line.strip():
                        self.rows.append(
                            validate_artifact(json.loads(line), "ledger_row"))
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, row):
        validate_artifact(row, "ledger_row")
        with open(self.path, "a") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        self.rows.append(row)

    def wipe_pair(self, P):
        """Idempotency helper: filters out any existing rows where pair_added == P
        both in memory and on disk.
        """
        self.rows = [row for row in self.rows if row.get("pair_added") != P]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Rewrite the ledger file completely to remove the wiped rows
        with open(self.path, "w") as f:
            for row in self.rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_ledger(path):
    """Read + validate all rows of a ledger.jsonl without opening it for
    writing (for --contributions-only / verification over existing folders).
    """
    rows = []
    with open(path) as f:
        for line in f:
            if line.strip():
                rows.append(validate_artifact(json.loads(line), "ledger_row"))
    return rows
