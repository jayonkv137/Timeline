"""Tests for Settings API and write-only secrets management (STANDALONE_V1_PLAN §4 Step S3.3).

Verifies:
- Settings API endpoints (GET /api/settings, PATCH /api/settings, POST /api/settings/test-connection).
- Mode 0600 file permissions on secrets.json.
- Security invariant: API key is write-only and NEVER appears in any API response,
  bundle, log, or public settings file (verified via full recursive canary grep).
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from server.app import create_app
from server.library import Library, atomic_write_json


@pytest.fixture
def library(tmp_path: Path) -> Library:
    lib = Library(tmp_path)
    lib.ensure_layout()
    return lib


@pytest.fixture
def client(library: Library) -> TestClient:
    app = create_app(library=library)
    return TestClient(app)


@pytest.mark.tier1
def test_default_settings(client: TestClient) -> None:
    """GET /api/settings returns default public configuration without sensitive credentials."""
    res = client.get("/api/settings")
    assert res.status_code == 200
    data = res.json()

    assert data["provider_url"] == "https://generativelanguage.googleapis.com/v1beta/openai/"
    assert data["model_fast"] == "gemini-3.1-flash-lite"
    assert data["model_main"] == "gemini-3.5-flash"
    assert data["model_step2"] == "gemini-3.5-flash"
    assert data["model_step3"] == "gemini-3.5-flash"
    assert data["chat_model"] == "gemini-3.5-flash"
    assert data["monthly_budget"] == 20.0
    assert data["parallel_jobs"] == 2
    assert "has_api_key" in data
    assert "key_preview" in data

    # Raw key keys must never exist
    assert "api_key" not in data
    assert "llm_api_key" not in data


@pytest.mark.tier1
def test_patch_settings_and_write_only_key(client: TestClient, library: Library) -> None:
    """PATCH /api/settings updates settings and stores write-only key in secrets.json."""
    canary_key = "sk-live-canary-secret-token-1234"
    patch_payload = {
        "monthly_budget": 50.0,
        "model_fast": "gemini-3.5-flash-lite",
        "parallel_jobs": 4,
        "api_key": canary_key,
    }

    res = client.patch("/api/settings", json=patch_payload)
    assert res.status_code == 200
    data = res.json()

    assert data["monthly_budget"] == 50.0
    assert data["model_fast"] == "gemini-3.5-flash-lite"
    assert data["parallel_jobs"] == 4
    assert data["has_api_key"] is True
    assert data["key_preview"] == "...1234"

    # Response must NEVER contain the raw canary key
    res_text = res.text
    assert canary_key not in res_text

    # secrets.json must store the key
    assert library.secrets_path.is_file()
    with open(library.secrets_path, "r", encoding="utf-8") as f:
        secrets_data = json.load(f)
    assert secrets_data.get("llm_api_key") == canary_key

    # settings.json must NOT contain the key
    assert library.settings_path.is_file()
    with open(library.settings_path, "r", encoding="utf-8") as f:
        settings_data = json.load(f)
    assert "api_key" not in settings_data
    assert "llm_api_key" not in settings_data
    assert canary_key not in json.dumps(settings_data)


@pytest.mark.tier1
def test_secrets_file_mode_0600(client: TestClient, library: Library) -> None:
    """secrets.json must have strict 0600 file permissions (read/write owner only)."""
    client.patch("/api/settings", json={"api_key": "sk-secret-test-permissions-key-0000"})
    assert library.secrets_path.is_file()

    file_stat = os.stat(library.secrets_path)
    file_mode = stat.S_IMODE(file_stat.st_mode)

    # 0o600: -rw-------
    assert file_mode == 0o600, f"Expected file mode 0600, got {oct(file_mode)}"


@pytest.mark.tier1
def test_key_never_appears_in_any_api_response_or_bundle_grep(
    client: TestClient, library: Library
) -> None:
    """Security audit: The raw API key must NEVER appear in any API response or bundle file."""
    canary_token = "sk-super-secret-canary-token-never-leak-998877"

    # Set key
    client.patch("/api/settings", json={"api_key": canary_token})

    # Create dummy chat and bundle
    library.create_chat("c_sec", title="Security Test Chat", category="Security")
    atomic_write_json(
        library.chat_dir("c_sec") / "workspace_bundle.json",
        {"id": "c_sec", "title": "Security Test Chat", "totalPairs": 1},
    )

    # Query all public API endpoints
    responses = [
        client.get("/api/settings"),
        client.get("/api/chats"),
        client.get("/api/chats/c_sec"),
        client.get("/api/health"),
        client.patch("/api/chats/c_sec", json={"title": "Updated Sec Title"}),
        client.post("/api/settings/test-connection", json={"api_key": canary_token}),
    ]

    for resp in responses:
        assert canary_token not in resp.text, f"Canary leaked in response: {resp.text}"

    # Search all files in library root EXCEPT secrets.json
    for root, dirs, files in os.walk(library.root):
        for fname in files:
            p = Path(root) / fname
            if p == library.secrets_path:
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            assert canary_token not in text, f"Canary leaked in file {p}"


@pytest.mark.tier1
def test_connection_health_check_endpoint(client: TestClient, library: Library) -> None:
    """POST /api/settings/test-connection verifies connection handling."""
    # 1. No key configured
    res_no_key = client.post("/api/settings/test-connection", json={})
    assert res_no_key.status_code == 200
    assert res_no_key.json()["ok"] is False
    assert "No API key" in res_no_key.json()["error"]

    # 2. Mock mode with test key
    res_mock = client.post(
        "/api/settings/test-connection",
        json={"api_key": "mock-test-key-12345", "provider_url": "https://fake.url/v1"},
    )
    assert res_mock.status_code == 200
    assert res_mock.json()["ok"] is True
    assert "successful" in res_mock.json()["message"]
