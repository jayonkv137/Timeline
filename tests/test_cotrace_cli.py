"""Tests for the root ./cotrace CLI and static workspace serving (Tier 1).

Covers serving web/dist-workspace from FastAPI at /, static asset mounting,
API precedence over static files, and ./cotrace command dispatch.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from importlib.machinery import SourceFileLoader

REPO_ROOT = Path(__file__).resolve().parent.parent

# Dynamically import extensionless executable script
_loader = SourceFileLoader("cotrace_script", str(REPO_ROOT / "cotrace"))
_spec = importlib.util.spec_from_loader("cotrace_script", _loader)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore
_loader.exec_module(_mod)
is_dist_stale = _mod.is_dist_stale

from server.app import create_app
from server.library import Library


@pytest.mark.tier1
def test_fastapi_serves_dist_workspace_at_root(tmp_path: Path) -> None:
    # Set up custom mock dist directory
    dist_dir = tmp_path / "mock_dist"
    dist_dir.mkdir()
    (dist_dir / "assets").mkdir()

    (dist_dir / "workspace.html").write_text("<!doctype html><html><head><title>Mock Workspace</title></head><body>Hello</body></html>")
    (dist_dir / "assets" / "app.js").write_text("console.log('test');")

    lib = Library(tmp_path / "lib")
    app = create_app(library=lib, dist_dir=dist_dir)
    client = TestClient(app)

    # 1. GET / serves workspace.html
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "Mock Workspace" in res_root.text

    # 2. GET /workspace.html also serves it
    res_ws = client.get("/workspace.html")
    assert res_ws.status_code == 200
    assert "Mock Workspace" in res_ws.text

    # 3. GET /assets/app.js serves asset
    res_asset = client.get("/assets/app.js")
    assert res_asset.status_code == 200
    assert "console.log('test')" in res_asset.text

    # 4. API endpoints take precedence and are not shadowed
    res_api = client.get("/api/health")
    assert res_api.status_code == 200
    assert res_api.json()["status"] == "ok"


@pytest.mark.tier1
def test_fastapi_serves_actual_compiled_dist_workspace() -> None:
    # Tests against the real repo dist-workspace
    app = create_app()
    client = TestClient(app)

    res = client.get("/")
    assert res.status_code == 200
    assert "<title>COTRACE · Workspace</title>" in res.text

    res_health = client.get("/api/health")
    assert res_health.status_code == 200


@pytest.mark.tier1
def test_cotrace_cli_help() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    cmd = [sys.executable, str(repo_root / "cotrace"), "--help"]
    proc = subprocess.run(cmd, capture_output=True, text=True)

    assert proc.returncode == 0
    assert "COTRACE Standalone Application Runner" in proc.stdout
    assert "start" in proc.stdout
    assert "dev" in proc.stdout
    assert "seed" in proc.stdout


@pytest.mark.tier1
def test_is_dist_stale_helper() -> None:
    # When dist-workspace exists, is_dist_stale should return a boolean without throwing
    stale = is_dist_stale()
    assert isinstance(stale, bool)
