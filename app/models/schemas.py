"""
Aletheia — Request / Response Schemas
"""
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
import time


# ── Intent Classification ─────────────────────────────────────────────

class IntentType(str, Enum):
    CONVERSATIONAL   = "conversational"    # General chat / Q&A
    TOOL_USE         = "tool_use"          # Needs a tool call
    AGENT_TASK       = "agent_task"        # Needs a multi-step agent
    MEMORY_RECALL    = "memory_recall"     # Retrieve from Akasha / history
    SMART_HOME       = "smart_home"        # Home Assistant actions
    CALENDAR_EMAIL   = "calendar_email"    # Gmail / GCal
    NEHO_INTEL       = "neho_intel"        # NEHO research / briefing
    STRATSPHERE      = "stratsphere"       # StratSphere queries


class IntentClassification(BaseModel):
    intent: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    requires_tools: bool = False
    tool_hints: list[str] = []
    rationale: str = ""


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
    intent: IntentType
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
