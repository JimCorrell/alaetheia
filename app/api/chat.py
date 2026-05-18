"""
Aletheia — Chat API Routes
POST /api/v1/chat          — single-turn request/response
POST /api/v1/chat/stream   — SSE streaming response
DELETE /api/v1/chat/{session_id} — clear session history
GET  /api/v1/chat/{session_id}/history — inspect history
"""
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.auth.dependencies import CurrentUser
from app.core.orchestrator import Orchestrator
from app.dependencies import RedisDep, SettingsDep
from app.memory.redis_store import SessionStore
from app.models.schemas import ChatRequest, ChatResponse, ChatMessage
from app.tools.registry import registry

router = APIRouter(prefix="/chat", tags=["chat"])
log = logging.getLogger(__name__)


def _get_orchestrator(redis, settings) -> Orchestrator:
    store = SessionStore(redis=redis, settings=settings)
    return Orchestrator(
        settings=settings,
        session_store=store,
        tool_registry=registry,
    )


def _scoped_session_id(user_id, session_id: str) -> str:
    """Prefix session_id with user_id to isolate sessions across users."""
    return f"{user_id}:{session_id}"


# ── POST /chat ────────────────────────────────────────────────────────

@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    current_user: CurrentUser,
    redis: RedisDep,
    settings: SettingsDep,
) -> ChatResponse:
    orchestrator = _get_orchestrator(redis, settings)
    try:
        return await orchestrator.chat(
            session_id=_scoped_session_id(current_user.id, body.session_id),
            user_message=body.message,
            context=body.context,
        )
    except Exception as exc:
        log.exception("Chat error session=%s", body.session_id)
        raise HTTPException(status_code=500, detail=str(exc))


# ── POST /chat/stream ─────────────────────────────────────────────────

@router.post("/stream")
async def chat_stream(
    body: ChatRequest,
    current_user: CurrentUser,
    redis: RedisDep,
    settings: SettingsDep,
) -> StreamingResponse:
    orchestrator = _get_orchestrator(redis, settings)
    scoped_id = _scoped_session_id(current_user.id, body.session_id)

    async def event_generator():
        try:
            async for chunk in orchestrator.stream(
                session_id=scoped_id,
                user_message=body.message,
                context=body.context,
            ):
                safe = chunk.replace("\n", "\\n")
                yield f"data: {safe}\n\n"
        except Exception as exc:
            log.exception("Stream error session=%s", body.session_id)
            yield f"data: [ERROR] {exc}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── GET /chat/{session_id}/history ────────────────────────────────────

@router.get("/{session_id}/history", response_model=list[ChatMessage])
async def get_history(
    session_id: str,
    current_user: CurrentUser,
    redis: RedisDep,
    settings: SettingsDep,
) -> list[ChatMessage]:
    store = SessionStore(redis=redis, settings=settings)
    return await store.get_history(_scoped_session_id(current_user.id, session_id))


# ── DELETE /chat/{session_id} ─────────────────────────────────────────

@router.delete("/{session_id}", status_code=204)
async def clear_session(
    session_id: str,
    current_user: CurrentUser,
    redis: RedisDep,
    settings: SettingsDep,
) -> None:
    store = SessionStore(redis=redis, settings=settings)
    await store.clear_session(_scoped_session_id(current_user.id, session_id))
