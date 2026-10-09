"""Tests for server.library (Tier 1).

Covers local library layout §3.4, COTRACE_HOME configuration, atomic file writes,
chat creation, listing, trashing, restoring, and settings/secrets management.
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest

from server.library import Library, atomic_write_json, atomic_write_text


@pytest.mark.tier1
def test_library_layout_creation(tmp_path: Path) -> None:
    lib = Library(tmp_path)
    lib.ensure_layout()

    assert lib.chats_dir.is_dir()
    assert lib.imports_dir.is_dir()
    assert lib.trash_dir.is_dir()
    assert lib.jobs_path.is_file()
    assert lib.settings_path.is_file()

    with lib.jobs_path.open() as f:
        assert json.load(f) == []

    with lib.settings_path.open() as f:
        assert json.load(f) == {}


@pytest.mark.tier1
def test_cotrace_home_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    custom_home = tmp_path / "custom_cotrace"
    monkeypatch.setenv("COTRACE_HOME", str(custom_home))

    lib = Library()
    assert lib.root == custom_home.resolve()
    assert lib.chats_dir == custom_home.resolve() / "chats"


@pytest.mark.tier1
def test_atomic_writes(tmp_path: Path) -> None:
    target_txt = tmp_path / "sub" / "file.txt"
    atomic_write_text(target_txt, "hello atomic")
    assert target_txt.read_text(encoding="utf-8") == "hello atomic"

    # Overwrite text
    atomic_write_text(target_txt, "hello updated")
    assert target_txt.read_text(encoding="utf-8") == "hello updated"

    # JSON write
    target_json = tmp_path / "sub" / "data.json"
    atomic_write_json(target_json, {"k": 1, "nested": [1, 2]})
    with target_json.open() as f:
        assert json.load(f) == {"k": 1, "nested": [1, 2]}


@pytest.mark.tier1
def test_atomic_write_mode_permissions(tmp_path: Path) -> None:
    target = tmp_path / "secret.json"
    atomic_write_json(target, {"secret": "val"}, mode=0o600)

    file_mode = stat.S_IMODE(target.stat().st_mode)
    assert file_mode == 0o600


@pytest.mark.tier1
def test_create_chat_and_directory_structure(tmp_path: Path) -> None:
    lib = Library(tmp_path)
    cdir = lib.create_chat(
        chat_id="chat_01",
        title="My First Chat",
        category="Research",
        source={"platform": "live"},
    )

    assert cdir.is_dir()
    assert (cdir / "run").is_dir()
    assert (cdir / "meta.json").is_file()
    assert (cdir / "dialogue.json").is_file()

    with (cdir / "meta.json").open() as f:
        meta = json.load(f)
        assert meta["id"] == "chat_01"
        assert meta["title"] == "My First Chat"
        assert meta["category"] == "Research"
        assert meta["source"]["platform"] == "live"

    with (cdir / "dialogue.json").open() as f:
        assert json.load(f) == []

    assert lib.chat_exists("chat_01") is True
    assert lib.chat_exists("nonexistent") is False


@pytest.mark.tier1
def test_create_duplicate_chat_raises(tmp_path: Path) -> None:
    lib = Library(tmp_path)
    lib.create_chat("chat_dup")

    with pytest.raises(FileExistsError):
        lib.create_chat("chat_dup")


@pytest.mark.tier1
def test_invalid_chat_id_raises(tmp_path: Path) -> None:
    lib = Library(tmp_path)
    with pytest.raises(ValueError):
        lib.create_chat("../evil_escape")

    with pytest.raises(ValueError):
        lib.chat_dir("bad/slash")


@pytest.mark.tier1
def test_list_chats(tmp_path: Path) -> None:
    lib = Library(tmp_path)
    lib.create_chat("chat_a", title="Chat A", category="Coding")
    lib.create_chat("chat_b", title="Chat B", category="Writing")

    # Add a mock workspace_bundle to chat_b
    bundle_b = {
        "id": "chat_b",
        "title": "Chat B Title",
        "category": "Writing",
        "totalPairs": 3,
        "status": "ready",
        "snapshots": [
            {
                "pair": 3,
                "mass": {
                    "out1": {"human": 20.0, "ai": 80.0, "delta": 0.0}
                },
            }
        ],
        "source": {"platform": "archive"},
    }
    atomic_write_json(lib.chat_dir("chat_b") / "workspace_bundle.json", bundle_b)

    chats = lib.list_chats()
    assert len(chats) == 2

    # Verify bundle reading for chat_b
    chat_b_entry = next(c for c in chats if c["id"] == "chat_b")
    assert chat_b_entry["totalPairs"] == 3
    assert chat_b_entry["mass"]["you"] == 20.0
    assert chat_b_entry["mass"]["ai"] == 80.0
    assert chat_b_entry["share"]["you"] == 20.0
    assert chat_b_entry["share"]["ai"] == 80.0
    assert chat_b_entry["status"] == "ready"


@pytest.mark.tier1
def test_update_chat_meta(tmp_path: Path) -> None:
    lib = Library(tmp_path)
    lib.create_chat("chat_edit", title="Initial Title", category="Research")

    updated = lib.update_chat_meta("chat_edit", title="New Title", category="Design")
    assert updated["title"] == "New Title"
    assert updated["category"] == "Design"

    with (lib.chat_dir("chat_edit") / "meta.json").open() as f:
        meta = json.load(f)
        assert meta["title"] == "New Title"
        assert meta["category"] == "Design"

    with pytest.raises(FileNotFoundError):
        lib.update_chat_meta("nonexistent", title="No chat")


@pytest.mark.tier1
def test_trash_and_restore_lifecycle(tmp_path: Path) -> None:
    lib = Library(tmp_path)
    lib.create_chat("chat_lifecycle", title="To Trash")

    assert lib.chat_exists("chat_lifecycle") is True
    assert lib.is_in_trash("chat_lifecycle") is False

    # Trash chat
    trash_path = lib.trash_chat("chat_lifecycle")
    assert trash_path.is_dir()
    assert lib.chat_exists("chat_lifecycle") is False
    assert lib.is_in_trash("chat_lifecycle") is True

    trash_items = lib.list_trash()
    assert len(trash_items) == 1
    assert trash_items[0]["id"] == "chat_lifecycle"
    assert trash_items[0]["isTrash"] is True

    # Restore chat
    restored_path = lib.restore_chat("chat_lifecycle")
    assert restored_path.is_dir()
    assert lib.chat_exists("chat_lifecycle") is True
    assert lib.is_in_trash("chat_lifecycle") is False
    assert len(lib.list_trash()) == 0


@pytest.mark.tier1
def test_restore_collision_fails(tmp_path: Path) -> None:
    lib = Library(tmp_path)
    lib.create_chat("collision_chat", title="Original")
    lib.trash_chat("collision_chat")

    # Create new active chat with same ID
    lib.create_chat("collision_chat", title="Replacement")

    # Restoring should fail with FileExistsError
    with pytest.raises(FileExistsError):
        lib.restore_chat("collision_chat")


@pytest.mark.tier1
def test_trash_and_restore_errors(tmp_path: Path) -> None:
    lib = Library(tmp_path)

    with pytest.raises(FileNotFoundError):
        lib.trash_chat("no_such_chat")

    with pytest.raises(FileNotFoundError):
        lib.restore_chat("no_such_chat")


@pytest.mark.tier1
def test_delete_chat_permanently(tmp_path: Path) -> None:
    lib = Library(tmp_path)
    lib.create_chat("to_delete")
    lib.trash_chat("to_delete")

    lib.delete_chat_permanently("to_delete")
    assert lib.is_in_trash("to_delete") is False
    assert not (lib.trash_dir / "to_delete").exists()

    with pytest.raises(FileNotFoundError):
        lib.delete_chat_permanently("to_delete")


@pytest.mark.tier1
def test_settings_and_secrets(tmp_path: Path) -> None:
    lib = Library(tmp_path)

    # Settings
    assert lib.get_settings() == {}
    lib.update_settings({"theme": "dark", "model": "gemini-1.5-pro"})
    assert lib.get_settings()["theme"] == "dark"

    # Secrets
    assert lib.get_secrets() == {}
    lib.set_secret("TEST_KEY", "val_123")
    assert lib.get_secrets()["TEST_KEY"] == "val_123"

    # Verify 0600 mode on secrets file
    file_mode = stat.S_IMODE(lib.secrets_path.stat().st_mode)
    assert file_mode == 0o600


@pytest.mark.tier1
def test_jobs_persistence(tmp_path: Path) -> None:
    lib = Library(tmp_path)
    assert lib.get_jobs() == []

    jobs_data = [{"jobId": "j1", "type": "import", "status": "running"}]
    lib.save_jobs(jobs_data)
    assert lib.get_jobs() == jobs_data
