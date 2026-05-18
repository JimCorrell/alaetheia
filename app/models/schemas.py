"""
Aletheia — Request / Response Schemas
"""
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
import time


# ── Chat ──────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str                   # "user" | "assistant"
    content: str
    timestamp: float = Field(default_factory=time.time)
    metadata: dict[str, Any] = {}


class ChatRequest(BaseModel):
    session_id: str = Field(
        default="default",
        description="Client-generated session ID. Use a UUID per conversation."
    )
    message: str = Field(
        min_length=1,
        max_length=8192,
        description="The user's input message."
    )
    stream: bool = False
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional client context (location, active app, etc.)"
    )


class ChatResponse(BaseModel):
    session_id: str
    message: str
    tool_calls: list[dict[str, Any]] = []
    latency_ms: float
    model_used: str
    tokens_used: int = 0


# ── Health ────────────────────────────────────────────────────────────

class HealthStatus(str, Enum):
    OK      = "ok"
    DEGRADED = "degraded"
    DOWN    = "down"


class ServiceHealth(BaseModel):
    name: str
    status: HealthStatus
    detail: str = ""


class HealthResponse(BaseModel):
    status: HealthStatus
    version: str
    services: list[ServiceHealth]
    uptime_seconds: float
