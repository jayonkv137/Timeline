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

    return router


def create_app(library: Library | None = None) -> FastAPI:
    """Application factory for the COTRACE server."""
    app = FastAPI(title="COTRACE Local Server", version="1.0.0")

    # Injected library or default
    app_lib = library or Library()
    app_lib.ensure_layout()
    app.state.library = app_lib
    app.state.broadcaster = SSEBroadcaster()

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

    return app


# Default singleton app instance
app = create_app()
