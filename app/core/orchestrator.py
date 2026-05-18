"""
Aletheia — Core Orchestrator
Single-stage pipeline: user message → Claude Sonnet → response.
Intent classification and tool routing will be added when tools are wired.
"""
import logging
import time
from typing import Any, AsyncIterator

import anthropic

from app.config import Settings
from app.memory.redis_store import SessionStore
from app.models.schemas import ChatMessage, ChatResponse
from app.tools.registry import ToolRegistry

log = logging.getLogger(__name__)


class Orchestrator:
    def __init__(
        self,
        settings: Settings,
        session_store: SessionStore,
        tool_registry: ToolRegistry,
    ):
        self.settings = settings
        self.session  = session_store
        self.tools    = tool_registry
        self.client   = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def chat(
        self,
        session_id: str,
        user_message: str,
        context: dict[str, Any] | None = None,
    ) -> ChatResponse:
        t0 = time.monotonic()

        user_msg = ChatMessage(role="user", content=user_message)
        await self.session.append(session_id, user_msg)

        history = await self.session.get_anthropic_messages(session_id)
        system  = self._build_system_prompt(context or {})

        resp = await self.client.messages.create(
            model=self.settings.claude_sonnet_model,
            max_tokens=self.settings.max_response_tokens,
            system=system,
            messages=history,
        )

        response_text = resp.content[0].text
        tokens = resp.usage.input_tokens + resp.usage.output_tokens

        await self.session.append(
            session_id, ChatMessage(role="assistant", content=response_text)
        )

        return ChatResponse(
            session_id=session_id,
            message=response_text,
            tool_calls=[],
            latency_ms=round((time.monotonic() - t0) * 1000, 1),
            model_used=self.settings.claude_sonnet_model,
            tokens_used=tokens,
        )

    async def stream(
        self,
        session_id: str,
        user_message: str,
        context: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        user_msg = ChatMessage(role="user", content=user_message)
        await self.session.append(session_id, user_msg)

        history = await self.session.get_anthropic_messages(session_id)
        full_response = []

        async with self.client.messages.stream(
            model=self.settings.claude_sonnet_model,
            max_tokens=self.settings.max_response_tokens,
            system=self._build_system_prompt(context or {}),
            messages=history,
        ) as stream:
            async for chunk in stream.text_stream:
                full_response.append(chunk)
                yield chunk

        await self.session.append(
            session_id,
            ChatMessage(role="assistant", content="".join(full_response)),
        )

    def _build_system_prompt(self, context: dict[str, Any]) -> str:
        parts = [self.settings.system_prompt]
        if context:
            ctx_lines = "\n".join(f"  {k}: {v}" for k, v in context.items())
            parts.append(f"\nClient context:\n{ctx_lines}")
        return "\n".join(parts)
