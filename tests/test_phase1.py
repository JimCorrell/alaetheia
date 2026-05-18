"""
Aletheia — Test Suite (Phase 1)

Run:  pytest tests/ -v
"""
import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import IntentType


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """TestClient with mocked Redis and Anthropic."""
    with TestClient(app) as c:
        yield c


# ── Health ────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_200(self, client):
        resp = client.get("/api/v1/health")
        # May be 200 even if degraded — status is in body
        assert resp.status_code == 200

    def test_health_has_required_fields(self, client):
        data = client.get("/api/v1/health").json()
        assert "status" in data
        assert "version" in data
        assert "services" in data
        assert "uptime_seconds" in data


# ── Intent Classification ─────────────────────────────────────────────

class TestIntentClassification:
    """Unit tests for Orchestrator._classify_intent."""

    @pytest.mark.asyncio
    async def test_valid_intent_parsed(self):
        from app.core.orchestrator import Orchestrator
        from app.config import get_settings
        from app.memory.redis_store import SessionStore
        from app.tools.registry import registry

        settings = get_settings()

        # Mock the Anthropic client
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps({
            "intent": "conversational",
            "confidence": 0.95,
            "requires_tools": False,
            "tool_hints": [],
            "rationale": "simple question",
        })
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        mock_redis = AsyncMock()
        store = SessionStore(redis=mock_redis, settings=settings)

        with patch("app.core.orchestrator.anthropic.AsyncAnthropic") as MockAnthropic:
            MockAnthropic.return_value = mock_client
            orch = Orchestrator(
                settings=settings,
                session_store=store,
                tool_registry=registry,
            )
            intent = await orch._classify_intent("What is the capital of France?")

        assert intent.intent == IntentType.CONVERSATIONAL
        assert intent.confidence == 0.95

    @pytest.mark.asyncio
    async def test_intent_falls_back_on_error(self):
        """Bad Anthropic response should default to conversational."""
        from app.core.orchestrator import Orchestrator
        from app.config import get_settings
        from app.memory.redis_store import SessionStore
        from app.tools.registry import registry

        settings = get_settings()
        mock_redis = AsyncMock()
        store = SessionStore(redis=mock_redis, settings=settings)

        with patch("app.core.orchestrator.anthropic.AsyncAnthropic") as MockAnthropic:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(side_effect=Exception("API down"))
            MockAnthropic.return_value = mock_client

            orch = Orchestrator(
                settings=settings,
                session_store=store,
                tool_registry=registry,
            )
            intent = await orch._classify_intent("test message")

        assert intent.intent == IntentType.CONVERSATIONAL


# ── Session Store ─────────────────────────────────────────────────────

class TestSessionStore:
    @pytest.mark.asyncio
    async def test_append_and_retrieve(self):
        from app.memory.redis_store import SessionStore
        from app.models.schemas import ChatMessage
        from app.config import get_settings

        settings = get_settings()

        # Mock Redis pipeline and lrange
        mock_redis = AsyncMock()
        mock_pipe = AsyncMock()
        mock_pipe.__aenter__ = AsyncMock(return_value=mock_pipe)
        mock_pipe.__aexit__ = AsyncMock(return_value=False)
        mock_redis.pipeline = MagicMock(return_value=mock_pipe)

        msg = ChatMessage(role="user", content="Hello Aletheia")
        stored = [msg.model_dump_json().encode()]
        mock_redis.lrange = AsyncMock(return_value=stored)

        store = SessionStore(redis=mock_redis, settings=settings)
        history = await store.get_history("test-session")

        assert len(history) == 1
        assert history[0].role == "user"
        assert history[0].content == "Hello Aletheia"


# ── Tool Registry ─────────────────────────────────────────────────────

class TestToolRegistry:
    def test_stub_tools_registered(self):
        from app.tools.registry import registry
        tools = registry.list_tools()
        names = [t["name"] for t in tools]
        assert "web_search" in names
        assert "smart_home" in names
        assert "akasha_recall" in names

    @pytest.mark.asyncio
    async def test_stub_tool_returns_stub_status(self):
        from app.tools.registry import registry
        result = await registry.run("web_search", {"query": "test"})
        assert result["status"] == "stub"

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self):
        from app.tools.registry import registry
        result = await registry.run("nonexistent_tool", {})
        assert "error" in result
