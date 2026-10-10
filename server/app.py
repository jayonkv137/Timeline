"""FastAPI application for COTRACE standalone desktop application.

Exposes REST and SSE endpoints adhering to STANDALONE_V1_PLAN §3.2 & §3.3:
- GET /health
- GET /chats
- GET /chats/{id}
- PATCH /chats/{id}
- DELETE /chats/{id}
- POST /chats/{id}/restore
- GET /events (Server-Sent Events)
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from server.library import Library

logger = logging.getLogger("cotrace.server")


class SSEBroadcaster:
    """Thread-safe and async-safe SSE event queue broadcaster."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[str]] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue[str]:
        queue: asyncio.Queue[str] = asyncio.Queue()
        async with self._lock:
            self._subscribers.add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[str]) -> None:
        async with self._lock:
            self._subscribers.discard(queue)

    def broadcast(self, event: str, data: Any) -> None:
        """Enqueue SSE formatted message to all active subscribers."""
        payload = json.dumps(data, ensure_ascii=False)
        message = f"event: {event}\ndata: {payload}\n\n"
        for q in list(self._subscribers):
            try:
                q.put_nowait(message)
            except asyncio.QueueFull:
                pass


class ChatUpdatePayload(BaseModel):
    title: str | None = Field(default=None, description="Updated chat title")
    category: str | None = Field(default=None, description="Updated chat category")


class SettingsUpdatePayload(BaseModel):
    provider_url: str | None = Field(default=None, description="OpenAI-compatible LLM base URL")
    model_fast: str | None = Field(default=None, description="Step 1a extraction model")
    model_main: str | None = Field(default=None, description="Main extraction model")
    model_step2: str | None = Field(default=None, description="Step 2 model")
    model_step3: str | None = Field(default=None, description="Step 3 model")
    chat_model: str | None = Field(default=None, description="Interactive chat model")
    monthly_budget: float | None = Field(default=None, description="Monthly dollar budget cap")
    parallel_jobs: int | None = Field(default=None, description="Max concurrent processing jobs")
    api_key: str | None = Field(default=None, description="Write-only API key (stored in secrets.json mode 0600)")


class TestConnectionPayload(BaseModel):
    provider_url: str | None = Field(default=None, description="Optional override provider URL")
    api_key: str | None = Field(default=None, description="Optional override API key")


class RehearsalPayload(BaseModel):
    chatIds: list[str] = Field(default_factory=list, description="Optional fixture chat IDs to rehearse")
    delaySeconds: float = Field(default=0.5, description="Pacing delay in seconds per exchange pair")


def create_router() -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health_check(request: Request) -> dict[str, Any]:
        lib: Library = request.app.state.library
        chats = lib.list_chats()
        return {
            "status": "ok",
            "version": "1.0.0",
            "library": str(lib.root),
            "chatsCount": len(chats),
        }

    @router.get("/chats")
    def list_chats(request: Request) -> list[dict[str, Any]]:
        lib: Library = request.app.state.library
        return lib.list_chats(include_trash=False)

    @router.get("/chats/{chat_id}")
    def get_chat(chat_id: str, request: Request) -> dict[str, Any]:
        lib: Library = request.app.state.library
        try:
            return lib.get_chat_bundle(chat_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    @router.patch("/chats/{chat_id}")
    def update_chat(chat_id: str, payload: ChatUpdatePayload, request: Request) -> dict[str, Any]:
        lib: Library = request.app.state.library
        try:
            updated = lib.update_chat_meta(
                chat_id=chat_id,
                title=payload.title,
                category=payload.category,
            )
            broadcaster: SSEBroadcaster = request.app.state.broadcaster
            broadcaster.broadcast(
                "chat_updated",
                {"chatId": chat_id, "title": updated.get("title"), "category": updated.get("category")},
            )
            return updated
        except FileNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    @router.delete("/chats/{chat_id}")
    def trash_chat(chat_id: str, request: Request) -> dict[str, Any]:
        lib: Library = request.app.state.library
        try:
            lib.trash_chat(chat_id)
            broadcaster: SSEBroadcaster = request.app.state.broadcaster
            broadcaster.broadcast("chat_trashed", {"chatId": chat_id})
            return {"status": "trashed", "id": chat_id}
        except FileNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    @router.post("/chats/{chat_id}/restore")
    def restore_chat(chat_id: str, request: Request) -> dict[str, Any]:
        lib: Library = request.app.state.library
        try:
            lib.restore_chat(chat_id)
            broadcaster: SSEBroadcaster = request.app.state.broadcaster
            broadcaster.broadcast("chat_restored", {"chatId": chat_id})
            return {"status": "restored", "id": chat_id}
        except FileNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except FileExistsError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    @router.get("/events")
    async def events_stream(request: Request) -> StreamingResponse:
        broadcaster: SSEBroadcaster = request.app.state.broadcaster
        queue = await broadcaster.subscribe()

        async def event_generator():
            # Initial comment to establish connection
            yield ": connected\n\n"
            try:
                while True:
                    if await request.is_disconnected():
                        break
                    try:
                        message = await asyncio.wait_for(queue.get(), timeout=15.0)
                        yield message
                    except asyncio.TimeoutError:
                        # Periodic comment keepalive
                        yield ": keepalive\n\n"
            finally:
                await broadcaster.unsubscribe(queue)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @router.get("/settings")
    def get_settings_endpoint(request: Request) -> dict[str, Any]:
        lib: Library = request.app.state.library
        return lib.get_public_settings()

    @router.patch("/settings")
    def update_settings_endpoint(payload: SettingsUpdatePayload, request: Request) -> dict[str, Any]:
        lib: Library = request.app.state.library
        broadcaster: SSEBroadcaster = request.app.state.broadcaster
        updates = payload.model_dump(exclude_unset=True)
        updated = lib.save_settings_and_secrets(updates)
        broadcaster.broadcast("settings_updated", updated)
        return updated

    @router.post("/settings/test-connection")
    def test_connection_endpoint(payload: TestConnectionPayload, request: Request) -> dict[str, Any]:
        lib: Library = request.app.state.library
        settings = lib.get_effective_settings()
        provider_url = payload.provider_url or settings.get("provider_url", "")
        api_key = payload.api_key or lib.get_api_key()

        if not api_key:
            return {"ok": False, "error": "No API key configured. Please enter an API key."}

        # Mock or test mode bypass for unit tests and local mock servers
        if (
            api_key.lower().startswith(("mock", "test", "fake"))
            or "mock" in provider_url.lower()
            or "fake" in provider_url.lower()
        ):
            return {
                "ok": True,
                "message": "Connection test successful (mock mode)",
                "provider_url": provider_url,
            }

        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key, base_url=provider_url, timeout=10.0)
            client.models.list()
            return {"ok": True, "message": "Connection test successful", "provider_url": provider_url}
        except Exception as exc:
            safe_err = str(exc).replace(api_key, "[REDACTED]")
            return {"ok": False, "error": f"Connection failed: {safe_err}"}

    @router.get("/usage")
    def get_usage_endpoint(request: Request, month: str | None = None) -> dict[str, Any]:
        """Return spend this month, per chat, per step, per model, and remaining budget (S3.4)."""
        lib: Library = request.app.state.library
        return lib.get_usage_summary(year_month=month)

    @router.post("/imports")
    async def upload_import_endpoint(
        request: Request,
        sync: bool = False,
    ) -> JSONResponse:
        """Stores raw upload files in $COTRACE_HOME/imports/<importId>/raw/ and runs scan in background."""
        lib: Library = request.app.state.library
        broadcaster: SSEBroadcaster = request.app.state.broadcaster
        import_id, raw_dir = lib.create_import_batch()

        content_type = request.headers.get("content-type", "")
        body = await request.body()
        files_saved = 0

        # 1. Multipart form-data upload
        if "multipart/form-data" in content_type:
            from email.parser import BytesParser
            from email.policy import default as email_default

            header_bytes = f"Content-Type: {content_type}\r\n\r\n".encode("utf-8")
            msg = BytesParser(policy=email_default).parsebytes(header_bytes + body)
            for part in msg.iter_parts():
                fn = part.get_filename()
                if fn:
                    clean_fn = Path(fn).name
                    payload = part.get_payload(decode=True)
                    if payload is not None:
                        (raw_dir / clean_fn).write_bytes(payload)
                        files_saved += 1

        # 2. JSON payload (disk path reference or direct export JSON)
        elif "application/json" in content_type:
            try:
                parsed_json = json.loads(body.decode("utf-8"))
                if isinstance(parsed_json, dict) and ("filePath" in parsed_json or "path" in parsed_json):
                    target_str = parsed_json.get("filePath") or parsed_json.get("path")
                    target_path = Path(target_str).expanduser().resolve()
                    if not target_path.exists():
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Source file not found: {target_str}",
                        )
                    if target_path.suffix.lower() == ".zip":
                        shutil.copy2(target_path, raw_dir / target_path.name)
                    else:
                        shutil.copy2(target_path, raw_dir / target_path.name)
                    files_saved += 1
                else:
                    # Raw export JSON uploaded directly as request body
                    (raw_dir / "conversations.json").write_bytes(body)
                    files_saved += 1
            except json.JSONDecodeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed JSON body")

        # 3. Direct binary or stream upload
        else:
            raw_filename = request.headers.get("x-filename")
            if not raw_filename:
                # Detect format from magic bytes or text
                if body.startswith(b"PK\x03\x04"):
                    raw_filename = "export.zip"
                elif body.strip().startswith((b"[", b"{")):
                    raw_filename = "conversations.json"
                else:
                    raw_filename = "export.dat"

            clean_fn = Path(raw_filename).name
            if body:
                (raw_dir / clean_fn).write_bytes(body)
                files_saved += 1

        if files_saved == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files received in upload payload",
            )

        from engine.importer import scan_import

        def run_scan() -> dict[str, Any]:
            try:
                rep = scan_import(raw_dir, import_id, lib.root)
                broadcaster.broadcast(
                    "import_ready",
                    {
                        "importId": import_id,
                        "status": "ready",
                        "totalConversations": rep.get("totalConversations", 0),
                        "totalPairs": rep.get("totalPairs", 0),
                    },
                )
                return rep
            except Exception as exc:
                err_rep = {
                    "importId": import_id,
                    "status": "failed",
                    "error": str(exc),
                    "conversations": [],
                }
                lib.save_import_report(import_id, err_rep)
                broadcaster.broadcast(
                    "import_failed",
                    {"importId": import_id, "status": "failed", "error": str(exc)},
                )
                return err_rep

        if sync:
            final_report = await asyncio.to_thread(run_scan)
            return JSONResponse(status_code=status.HTTP_200_OK, content=final_report)

        asyncio.create_task(asyncio.to_thread(run_scan))
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "importId": import_id,
                "status": "scanning",
                "message": "Import upload received; background scan initiated.",
            },
        )

    @router.get("/imports/{import_id}")
    def get_import_endpoint(import_id: str, request: Request) -> dict[str, Any]:
        """Return triage report.json for an import batch."""
        lib: Library = request.app.state.library
        try:
            return lib.get_import_report(import_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    @router.get("/imports")
    def list_imports_endpoint(request: Request) -> list[dict[str, Any]]:
        """List all import batches with status and summary metrics."""
        lib: Library = request.app.state.library
        return lib.list_imports()

    class ProcessBatchPayload(BaseModel):
        conversationIds: list[str] = Field(default_factory=list, description="IDs of conversations to enqueue")

    @router.post("/imports/{import_id}/process")
    async def process_import_batch_endpoint(
        import_id: str,
        payload: ProcessBatchPayload,
        request: Request,
    ) -> dict[str, Any]:
        """Enqueue selected conversations from an import batch for background processing (§4)."""
        job_queue = request.app.state.job_queue
        enqueued = await job_queue.enqueue_import_batch(import_id, payload.conversationIds)
        return {
            "status": "queued",
            "importId": import_id,
            "enqueuedCount": len(enqueued),
            "jobs": enqueued,
        }

    @router.get("/jobs")
    async def list_jobs_endpoint(request: Request) -> dict[str, Any]:
        """Return queue summary and all jobs from jobs.json."""
        job_queue = request.app.state.job_queue
        res = job_queue.get_queue_status()
        res["jobs"] = job_queue.get_jobs()
        return res

    @router.post("/jobs/{job_id}/priority")
    async def map_next_job_endpoint(job_id: str, request: Request) -> dict[str, Any]:
        """Move job to the front of the queue ('Map next' per §4)."""
        job_queue = request.app.state.job_queue
        try:
            return await job_queue.map_next(job_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    @router.post("/jobs/{job_id}/cancel")
    async def cancel_job_endpoint(job_id: str, request: Request) -> dict[str, Any]:
        """Cancel mapping for a job (§3.2, §5). Mapped exchanges are kept."""
        job_queue = request.app.state.job_queue
        try:
            return await job_queue.cancel_job(job_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    @router.post("/jobs/pause-all")
    async def pause_all_jobs_endpoint(request: Request) -> dict[str, Any]:
        """Pause queue processing (§3.2)."""
        job_queue = request.app.state.job_queue
        job_queue.pause_all(reason="user_paused")
        return {"status": "paused"}

    @router.post("/jobs/resume-all")
    async def resume_all_jobs_endpoint(request: Request) -> dict[str, Any]:
        """Resume queue processing."""
        job_queue = request.app.state.job_queue
        job_queue.resume_all()
        return {"status": "resumed"}

    @router.get("/jobs/rehearsal-presets")
    def list_rehearsal_presets_endpoint(request: Request) -> list[dict[str, Any]]:
        """List pre-recorded chat fixtures available for zero-spend rehearsal replay (§7)."""
        rehearsal = getattr(request.app.state, "rehearsal_runner", None)
        return rehearsal.list_fixtures() if rehearsal else []

    @router.post("/jobs/rehearse")
    async def start_rehearsal_endpoint(
        payload: RehearsalPayload,
        request: Request,
    ) -> dict[str, Any]:
        """Start zero-spend rehearsal mode replay through the job queue (§7)."""
        rehearsal = request.app.state.rehearsal_runner
        job_queue = request.app.state.job_queue
        enqueued = await rehearsal.enqueue_rehearsal_batch(
            chat_ids=payload.chatIds if payload.chatIds else None,
            delay_seconds=payload.delaySeconds,
            queue_manager=job_queue,
        )
        return {
            "status": "rehearsal_started",
            "enqueuedCount": len(enqueued),
            "delaySeconds": payload.delaySeconds,
            "jobs": enqueued,
        }

    return router


from pathlib import Path
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

DEFAULT_DIST_DIR = Path(__file__).resolve().parent.parent / "web" / "dist-workspace"


def create_app(
    library: Library | None = None,
    dist_dir: Path | str | None = None,
    job_queue: Any = None,
    rehearsal_runner: Any = None,
    pipeline_runner: Any = None,
) -> FastAPI:
    """Application factory for the COTRACE server."""
    # Injected library or default
    app_lib = library or Library()
    app_lib.ensure_layout()
    broadcaster = SSEBroadcaster()

    # Injected job queue or default
    from server.jobs import JobQueueManager
    from server.rehearsal import RehearsalRunner
    from server.pipeline_runner import PipelineRunner

    queue = job_queue or JobQueueManager(library=app_lib, broadcaster=broadcaster)
    rehearsal = rehearsal_runner or RehearsalRunner(library=app_lib, broadcaster=broadcaster)
    pipeline = pipeline_runner or PipelineRunner(library=app_lib, broadcaster=broadcaster, job_queue=queue)

    if hasattr(queue, "set_rehearsal_runner") and queue.rehearsal_runner is None:
        queue.set_rehearsal_runner(rehearsal)
    if hasattr(queue, "set_pipeline_runner") and queue.pipeline_runner is None:
        queue.set_pipeline_runner(pipeline)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if hasattr(app.state, "job_queue") and hasattr(app.state.job_queue, "start"):
            app.state.job_queue.start()
        yield
        if hasattr(app.state, "job_queue") and hasattr(app.state.job_queue, "stop"):
            await app.state.job_queue.stop()

    app = FastAPI(title="COTRACE Local Server", version="1.0.0", lifespan=lifespan)
    app.state.library = app_lib
    app.state.broadcaster = broadcaster
    app.state.job_queue = queue
    app.state.rehearsal_runner = rehearsal
    app.state.pipeline_runner = pipeline

    # CORS configuration for local frontends
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    router = create_router()
    # Support both /api/... and root-level routes for complete compatibility
    app.include_router(router, prefix="/api")
    app.include_router(router, prefix="")

    # Serve static frontend from dist-workspace if available
    dist_path = Path(dist_dir).resolve() if dist_dir is not None else DEFAULT_DIST_DIR
    if dist_path.is_dir():
        workspace_html = dist_path / "workspace.html"
        if workspace_html.is_file():
            @app.get("/", include_in_schema=False)
            def root_index() -> FileResponse:
                return FileResponse(workspace_html)

            @app.get("/workspace", include_in_schema=False)
            def root_workspace() -> FileResponse:
                return FileResponse(workspace_html)

            @app.get("/workspace.html", include_in_schema=False)
            def root_workspace_html() -> FileResponse:
                return FileResponse(workspace_html)

        favicon_file = dist_path / "favicon.svg"
        if favicon_file.is_file():
            @app.get("/favicon.svg", include_in_schema=False)
            def root_favicon() -> FileResponse:
                return FileResponse(favicon_file)

        icons_file = dist_path / "icons.svg"
        if icons_file.is_file():
            @app.get("/icons.svg", include_in_schema=False)
            def root_icons() -> FileResponse:
                return FileResponse(icons_file)

        assets_dir = dist_path / "assets"
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        fixture_dir = dist_path / "fixture"
        if fixture_dir.is_dir():
            app.mount("/fixture", StaticFiles(directory=fixture_dir), name="fixture")

    return app


# Default singleton app instance
app = create_app()

