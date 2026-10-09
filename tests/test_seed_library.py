"""Tests for scripts.seed_library (Tier 1).

Covers copying the 10 processed chats into the local library,
projecting their workspace bundles without LLM calls, and verifying
that FastAPI TestClient serves all 10 chats.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from scripts.seed_library import PROCESSED_CHATS, seed_library
from server.app import create_app
from server.library import Library


@pytest.fixture
def workspace_schema() -> dict:
    schema_path = Path(__file__).resolve().parent.parent / "engine" / "schemas" / "workspace_bundle.schema.json"
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.tier1
def test_seed_library_creates_10_chats(tmp_path: Path) -> None:
    lib_path = tmp_path / "library"
    seeded_ids = seed_library(library_dir=lib_path)

    assert len(seeded_ids) == 10
    assert set(seeded_ids) == set(PROCESSED_CHATS)

    lib = Library(lib_path)
    chats = lib.list_chats()
    assert len(chats) == 10

    # Ensure every chat has dialogue, meta, and bundle
    for cid in seeded_ids:
        cdir = lib.chat_dir(cid)
        assert (cdir / "dialogue.json").is_file()
        assert (cdir / "meta.json").is_file()
        assert (cdir / "workspace_bundle.json").is_file()


@pytest.mark.tier1
def test_seeded_bundles_match_schema(tmp_path: Path, workspace_schema: dict) -> None:
    lib_path = tmp_path / "library"
    seed_library(library_dir=lib_path)
    lib = Library(lib_path)

    validator = Draft202012Validator(workspace_schema)

    for cid in PROCESSED_CHATS:
        bundle_path = lib.chat_dir(cid) / "workspace_bundle.json"
        with bundle_path.open("r", encoding="utf-8") as f:
            bundle = json.load(f)

        errors = list(validator.iter_errors(bundle))
        assert not errors, f"Validation errors in seeded chat {cid}: {[e.message for e in errors]}"
        assert bundle["status"] == "ready"
        assert "platform" in bundle["source"]


@pytest.mark.tier1
def test_server_api_serves_all_10_seeded_chats(tmp_path: Path) -> None:
    lib_path = tmp_path / "library"
    seed_library(library_dir=lib_path)

    lib = Library(lib_path)
    app = create_app(library=lib)
    client = TestClient(app)

    # 1. GET /api/chats returns all 10
    res = client.get("/api/chats")
    assert res.status_code == 200
    chats = res.json()
    assert len(chats) == 10

    ids = {c["id"] for c in chats}
    assert ids == set(PROCESSED_CHATS)

    # 2. GET /api/chats/{id} returns bundle for each
    for cid in PROCESSED_CHATS:
        res_bundle = client.get(f"/api/chats/{cid}")
        assert res_bundle.status_code == 200
        bundle = res_bundle.json()
        assert bundle["id"] == cid
        assert bundle["totalPairs"] > 0
        assert len(bundle["nodes"]) > 0


@pytest.mark.tier1
def test_seed_library_clean_and_idempotent(tmp_path: Path) -> None:
    lib_path = tmp_path / "library"
    seed_library(library_dir=lib_path)

    # Re-run with clean=True
    seeded_again = seed_library(library_dir=lib_path, clean=True)
    assert len(seeded_again) == 10

    lib = Library(lib_path)
    assert len(lib.list_chats()) == 10
