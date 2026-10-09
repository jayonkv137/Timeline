"""Test workspace_bundle.schema.json validity and coverage of prototype chats.

Step S1.1 of Track S: validating that workspace_bundle.schema.json complies with
Draft 2020-12, validates all 10 chats in web/src/workspace/data.generated.json
(with new status and source fields defaulted), and enforces strict rejection on
malformed inputs.
"""
import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

pytestmark = pytest.mark.tier1

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "engine" / "schemas" / "workspace_bundle.schema.json"
DATA_GENERATED_PATH = REPO_ROOT / "web" / "src" / "workspace" / "data.generated.json"
FIXTURE_DIR = REPO_ROOT / "data" / "chats" / "fixture_pair1"


@pytest.fixture(scope="module")
def schema():
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def validator(schema):
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.fixture(scope="module")
def sample_chats():
    with open(DATA_GENERATED_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["chats"]


def test_schema_syntax_draft202012(schema):
    """The workspace bundle schema itself must be a valid JSON Schema Draft 2020-12."""
    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["title"] == "WorkspaceBundle"


def test_validate_all_generated_chats(validator, sample_chats):
    """All 10 prototype chats must validate when new fields are defaulted."""
    assert len(sample_chats) == 10
    for chat in sample_chats:
        chat_copy = copy.deepcopy(chat)
        chat_copy.setdefault("status", "ready")
        chat_copy.setdefault("source", {"platform": "archive"})
        validator.validate(chat_copy)


def test_missing_required_field_fails(validator, sample_chats):
    """Omitting top-level required fields must trigger a ValidationError."""
    chat = copy.deepcopy(sample_chats[0])
    chat.setdefault("status", "ready")
    chat.setdefault("source", {"platform": "archive"})

    del chat["id"]
    with pytest.raises(ValidationError):
        validator.validate(chat)


def test_missing_status_or_source_fails(validator, sample_chats):
    """Omitting status or source without default must fail validation."""
    chat = copy.deepcopy(sample_chats[0])
    # chat has no status or source initially
    with pytest.raises(ValidationError):
        validator.validate(chat)


def test_invalid_status_enum_fails(validator, sample_chats):
    """An unknown status value must fail validation."""
    chat = copy.deepcopy(sample_chats[0])
    chat["status"] = "in_progress"  # Invalid: must be ready, processing, needs_review, or error
    chat["source"] = {"platform": "archive"}
    with pytest.raises(ValidationError):
        validator.validate(chat)


def test_extra_property_rejected(validator, sample_chats):
    """additionalProperties: false must reject unknown root keys."""
    chat = copy.deepcopy(sample_chats[0])
    chat["status"] = "ready"
    chat["source"] = {"platform": "archive"}
    chat["unknown_custom_field"] = True
    with pytest.raises(ValidationError):
        validator.validate(chat)


def test_malformed_node_fails(validator, sample_chats):
    """A node missing required fields or having wrong speaker must fail."""
    chat = copy.deepcopy(sample_chats[0])
    chat["status"] = "ready"
    chat["source"] = {"platform": "archive"}
    chat["nodes"][0]["sourceSpeaker"] = "alien"
    with pytest.raises(ValidationError):
        validator.validate(chat)


def test_malformed_atom_fails(validator, sample_chats):
    """An atom with an invalid kind must fail."""
    chat = copy.deepcopy(sample_chats[0])
    chat["status"] = "ready"
    chat["source"] = {"platform": "archive"}
    chat["atoms"][0]["kind"] = "unsupported_kind"
    with pytest.raises(ValidationError):
        validator.validate(chat)


def test_malformed_snapshot_mass_fails(validator, sample_chats):
    """Snapshots must enforce human, ai, and delta values."""
    chat = copy.deepcopy(sample_chats[0])
    chat["status"] = "ready"
    chat["source"] = {"platform": "archive"}
    first_node_id = chat["nodes"][0]["id"]
    chat["snapshots"][0]["mass"][first_node_id] = {"human": 10, "ai": 20}  # missing delta
    with pytest.raises(ValidationError):
        validator.validate(chat)


def test_ag_plus_sacred_fixture_numbers():
    """AG+ rule check: fixture numbers remain strictly invariant:
    Δ_you=87.0, Δ_AI=314.0 (21.7% / 78.3%), 4 You · 10 AI, COPILOT.
    """
    with open(FIXTURE_DIR / "panel_bundle.json", encoding="utf-8") as f:
        panel_bundle = json.load(f)

    pair1 = panel_bundle["pairs"][0]
    direction = pair1["direction"]
    assert direction["you_pct"] == 21.7
    assert direction["ai_pct"] == 78.3

    timeline = pair1["timeline"]
    assert timeline["delta_you"] == 87.0
    assert timeline["delta_ai"] == 314.0

    decisions = pair1["decisions"]
    assert decisions["you_count"] == 4
    assert decisions["ai_count"] == 10

    how = pair1["how"]
    assert how["mode"] == "COPILOT"
