"""COTRACE local filesystem library manager.

Implements the library layout and lifecycle defined in STANDALONE_V1_PLAN §3.4:
$COTRACE_HOME/
  chats/<id>/
    dialogue.json · source_meta.json · meta.json · state.json · ledger.jsonl ·
    snapshots.json · panel_bundle.json · workspace_bundle.json ·
    run/{cache,usage.jsonl,status.json,report.json}
  imports/<importId>/  raw/ · report.json
  trash/<id>/
  jobs.json · settings.json · secrets.json (0600, key only)
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Allowed chat ID characters: alphanumeric, hyphens, and underscores
SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def _validate_id(identifier: str, entity_name: str = "ID") -> str:
    """Validate identifier to prevent path traversal or malformed paths."""
    if not identifier or not SAFE_ID_PATTERN.match(identifier):
        raise ValueError(
            f"Invalid {entity_name} '{identifier}': must contain only letters, digits, hyphens, and underscores."
        )
    return identifier


def atomic_write_text(path: Path | str, content: str, mode: int | None = None) -> None:
    """Write text atomically to disk using a temporary file in the same directory.
    
    Flushes and fsyncs before replacement to prevent partial writes during crashes.
    """
    target = Path(path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=target.parent, delete=False, encoding="utf-8") as tf:
            tf.write(content)
            tf.flush()
            os.fsync(tf.fileno())
            tmp_path = Path(tf.name)

        if mode is not None:
            os.chmod(tmp_path, mode)

        os.replace(tmp_path, target)
        tmp_path = None
    finally:
        if tmp_path is not None and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def atomic_write_json(path: Path | str, data: Any, mode: int | None = None, indent: int = 2) -> None:
    """Serialize and atomically write JSON data to disk."""
    content = json.dumps(data, indent=indent, ensure_ascii=False) + "\n"
    atomic_write_text(path, content, mode=mode)


class Library:
    """Local COTRACE library manager adhering to STANDALONE_V1_PLAN §3.4."""

    def __init__(self, root: str | Path | None = None) -> None:
        if root is not None:
            self.root = Path(root).expanduser().resolve()
        else:
            env_root = os.environ.get("COTRACE_HOME")
            if env_root:
                self.root = Path(env_root).expanduser().resolve()
            else:
                self.root = (Path.home() / "Cotrace").resolve()

        self.chats_dir = self.root / "chats"
        self.imports_dir = self.root / "imports"
        self.trash_dir = self.root / "trash"
        self.jobs_path = self.root / "jobs.json"
        self.settings_path = self.root / "settings.json"
        self.secrets_path = self.root / "secrets.json"

    def ensure_layout(self) -> None:
        """Create standard library directory structure and initial files if missing."""
        self.chats_dir.mkdir(parents=True, exist_ok=True)
        self.imports_dir.mkdir(parents=True, exist_ok=True)
        self.trash_dir.mkdir(parents=True, exist_ok=True)

        if not self.jobs_path.exists():
            atomic_write_json(self.jobs_path, [])
        if not self.settings_path.exists():
            atomic_write_json(self.settings_path, {})

    def chat_dir(self, chat_id: str) -> Path:
        """Return the directory path for an active chat."""
        _validate_id(chat_id, "chat ID")
        return self.chats_dir / chat_id

    def trash_chat_dir(self, chat_id: str) -> Path:
        """Return the directory path for a trashed chat."""
        _validate_id(chat_id, "chat ID")
        return self.trash_dir / chat_id

    def import_dir(self, import_id: str) -> Path:
        """Return the directory path for an import batch."""
        _validate_id(import_id, "import ID")
        return self.imports_dir / import_id

    def chat_exists(self, chat_id: str) -> bool:
        """Return True if an active chat directory exists."""
        try:
            return self.chat_dir(chat_id).is_dir()
        except ValueError:
            return False

    def is_in_trash(self, chat_id: str) -> bool:
        """Return True if a chat exists in the trash directory."""
        try:
            return self.trash_chat_dir(chat_id).is_dir()
        except ValueError:
            return False

    def create_chat(
        self,
        chat_id: str,
        title: str = "Untitled chat",
        category: str = "General",
        source: dict[str, Any] | None = None,
    ) -> Path:
        """Create a new chat directory with initial metadata, dialogue, and run folder."""
        self.ensure_layout()
        _validate_id(chat_id, "chat ID")
        cdir = self.chat_dir(chat_id)

        if cdir.exists():
            raise FileExistsError(f"Chat '{chat_id}' already exists in library")

        cdir.mkdir(parents=True, exist_ok=False)
        (cdir / "run").mkdir(parents=True, exist_ok=True)

        now = datetime.now(timezone.utc).isoformat()
        src = source or {"platform": "live"}

        meta = {
            "id": chat_id,
            "title": title,
            "category": category,
            "createdAt": now,
            "updatedAt": now,
            "source": src,
        }

        atomic_write_json(cdir / "meta.json", meta)
        atomic_write_json(cdir / "dialogue.json", [])
        return cdir

    def get_chat_bundle(self, chat_id: str) -> dict[str, Any]:
        """Load and return the workspace_bundle.json for a chat."""
        cdir = self.chat_dir(chat_id)
        bundle_path = cdir / "workspace_bundle.json"

        if not cdir.is_dir():
            raise FileNotFoundError(f"Chat '{chat_id}' not found in library")

        if not bundle_path.is_file():
            raise FileNotFoundError(
                f"Workspace bundle for chat '{chat_id}' not found at {bundle_path}"
            )

        with bundle_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def list_chats(self, include_trash: bool = False) -> list[dict[str, Any]]:
        """List active chats (and optionally trashed chats) with summarized metadata."""
        if not self.chats_dir.is_dir():
            return []

        entries: list[dict[str, Any]] = []
        directories = [p for p in self.chats_dir.iterdir() if p.is_dir()]

        if include_trash and self.trash_dir.is_dir():
            directories.extend([p for p in self.trash_dir.iterdir() if p.is_dir()])

        for cdir in directories:
            cid = cdir.name
            bundle_file = cdir / "workspace_bundle.json"
            meta_file = cdir / "meta.json"
            source_meta_file = cdir / "source_meta.json"

            title = cid
            category = "General"
            total_pairs = 0
            status = "ready"
            source: dict[str, Any] = {"platform": "archive"}
            updated_at = datetime.fromtimestamp(cdir.stat().st_mtime, tz=timezone.utc).isoformat()
            mass = {"you": 0.0, "ai": 0.0, "total": 0.0}
            share = {"you": 50.0, "ai": 50.0}

            if bundle_file.is_file():
                try:
                    with bundle_file.open("r", encoding="utf-8") as f:
                        bundle = json.load(f)
                    title = bundle.get("title", title)
                    category = bundle.get("category", category)
                    total_pairs = bundle.get("totalPairs", total_pairs)
                    status = bundle.get("status", status)
                    source = bundle.get("source", source)

                    snapshots = bundle.get("snapshots", [])
                    if snapshots:
                        last_snap = snapshots[-1]
                        snap_mass = last_snap.get("mass", {})
                        you_mass = sum(float(item.get("human", 0.0)) for item in snap_mass.values())
                        ai_mass = sum(float(item.get("ai", 0.0)) for item in snap_mass.values())
                        total_mass = you_mass + ai_mass
                        you_pct = round(100.0 * you_mass / total_mass, 1) if total_mass > 0 else 50.0
                        ai_pct = round(100.0 * ai_mass / total_mass, 1) if total_mass > 0 else 50.0
                        mass = {"you": you_mass, "ai": ai_mass, "total": total_mass}
                        share = {"you": you_pct, "ai": ai_pct}

                    updated_at = datetime.fromtimestamp(
                        bundle_file.stat().st_mtime, tz=timezone.utc
                    ).isoformat()
                except Exception:
                    pass
            elif meta_file.is_file():
                try:
                    with meta_file.open("r", encoding="utf-8") as f:
                        meta = json.load(f)
                    title = meta.get("title", title)
                    category = meta.get("category", category)
                    source = meta.get("source", source)
                    updated_at = meta.get("updatedAt", updated_at)
                except Exception:
                    pass
            elif source_meta_file.is_file():
                try:
                    with source_meta_file.open("r", encoding="utf-8") as f:
                        sm = json.load(f)
                    title = sm.get("title", title)
                    category = sm.get("category", category)
                except Exception:
                    pass

            # Dialogue pair count fallback if bundle wasn't present
            if total_pairs == 0 and (cdir / "dialogue.json").is_file():
                try:
                    with (cdir / "dialogue.json").open("r", encoding="utf-8") as f:
                        turns = json.load(f)
                    if isinstance(turns, list) and turns:
                        total_pairs = max((t.get("pair", 0) for t in turns), default=0)
                except Exception:
                    pass

            is_trashed = cdir.parent == self.trash_dir
            entries.append({
                "id": cid,
                "title": title,
                "category": category,
                "totalPairs": total_pairs,
                "status": status,
                "updatedAt": updated_at,
                "mass": mass,
                "share": share,
                "source": source,
                "isTrash": is_trashed,
            })

        entries.sort(key=lambda x: x["updatedAt"], reverse=True)
        return entries

    def update_chat_meta(
        self,
        chat_id: str,
        title: str | None = None,
        category: str | None = None,
    ) -> dict[str, Any]:
        """Update metadata (title, category) for an active chat."""
        cdir = self.chat_dir(chat_id)
        if not cdir.is_dir():
            raise FileNotFoundError(f"Chat '{chat_id}' not found in library")

        now = datetime.now(timezone.utc).isoformat()
        meta_file = cdir / "meta.json"
        meta: dict[str, Any] = {}
        if meta_file.is_file():
            try:
                with meta_file.open("r", encoding="utf-8") as f:
                    meta = json.load(f)
            except Exception:
                meta = {}

        if title is not None:
            meta["title"] = title
        if category is not None:
            meta["category"] = category
        meta["updatedAt"] = now
        meta["id"] = chat_id

        atomic_write_json(meta_file, meta)

        # Keep workspace_bundle.json in sync if it exists
        bundle_file = cdir / "workspace_bundle.json"
        if bundle_file.is_file():
            try:
                with bundle_file.open("r", encoding="utf-8") as f:
                    bundle = json.load(f)
                if title is not None:
                    bundle["title"] = title
                if category is not None:
                    bundle["category"] = category
                atomic_write_json(bundle_file, bundle)
            except Exception:
                pass

        return meta

    def trash_chat(self, chat_id: str) -> Path:
        """Move an active chat to the trash folder."""
        self.ensure_layout()
        _validate_id(chat_id, "chat ID")
        src = self.chat_dir(chat_id)
        dest = self.trash_chat_dir(chat_id)

        if not src.is_dir():
            raise FileNotFoundError(f"Active chat '{chat_id}' not found in {src}")

        if dest.exists():
            shutil.rmtree(dest)

        shutil.move(str(src), str(dest))
        return dest

    def restore_chat(self, chat_id: str) -> Path:
        """Restore a trashed chat back to the active chats folder."""
        self.ensure_layout()
        _validate_id(chat_id, "chat ID")
        src = self.trash_chat_dir(chat_id)
        dest = self.chat_dir(chat_id)

        if not src.is_dir():
            raise FileNotFoundError(f"Chat '{chat_id}' not found in trash {src}")

        if dest.exists():
            raise FileExistsError(
                f"Cannot restore '{chat_id}': active chat with this ID already exists"
            )

        shutil.move(str(src), str(dest))
        return dest

    def list_trash(self) -> list[dict[str, Any]]:
        """List all chats currently in the trash."""
        if not self.trash_dir.is_dir():
            return []
        all_entries = self.list_chats(include_trash=True)
        return [e for e in all_entries if e.get("isTrash")]

    def delete_chat_permanently(self, chat_id: str) -> None:
        """Permanently delete a chat from the trash folder."""
        _validate_id(chat_id, "chat ID")
        tdir = self.trash_chat_dir(chat_id)
        if not tdir.is_dir():
            raise FileNotFoundError(f"Chat '{chat_id}' not found in trash {tdir}")
        shutil.rmtree(tdir)

    # Settings & Secrets & Jobs helpers
    def get_settings(self) -> dict[str, Any]:
        """Read settings.json from library."""
        if not self.settings_path.is_file():
            return {}
        try:
            with self.settings_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def update_settings(self, updates: dict[str, Any]) -> dict[str, Any]:
        """Merge and atomically persist settings.json."""
        self.ensure_layout()
        current = self.get_settings()
        current.update(updates)
        atomic_write_json(self.settings_path, current)
        return current

    def get_secrets(self) -> dict[str, Any]:
        """Read secrets.json from library."""
        if not self.secrets_path.is_file():
            return {}
        try:
            with self.secrets_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def set_secret(self, key: str, value: str) -> None:
        """Store secret in secrets.json with strict 0600 file permissions."""
        self.ensure_layout()
        current = self.get_secrets()
        current[key] = value
        atomic_write_json(self.secrets_path, current, mode=0o600)

    def get_jobs(self) -> list[dict[str, Any]]:
        """Read jobs.json from library."""
        if not self.jobs_path.is_file():
            return []
        try:
            with self.jobs_path.open("r", encoding="utf-8") as f:
                jobs = json.load(f)
                return jobs if isinstance(jobs, list) else []
        except Exception:
            return []

    def save_jobs(self, jobs: list[dict[str, Any]]) -> None:
        """Atomically persist jobs.json."""
        self.ensure_layout()
        atomic_write_json(self.jobs_path, jobs)
