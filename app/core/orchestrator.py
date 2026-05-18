"""
Aletheia — Core Orchestrator
Two-stage pipeline:
  1. Intent classification   → Claude Haiku  (fast, cheap)
  2. Response generation     → Claude Sonnet (capable)

Phase 1: text I/O only. Tool dispatch is stubbed — wired in Phase 1/2.
"""
import json
import logging
import time
from typing import Any, AsyncIterator

import anthropic

from app.config import Settings
from app.memory.redis_store import SessionStore
from app.models.schemas import (
    ChatMessage,
    ChatResponse,
    IntentClassification,
    IntentType,
)
from app.tools.registry import ToolRegistry

log = logging.getLogger(__name__)


# ── Intent classification prompt ──────────────────────────────────────

_INTENT_SYSTEM = """
You are an intent classifier for Aletheia, a personal AI assistant.

Classify the user's message into exactly ONE intent from this list:
- conversational   : general chat, questions, explanations, creative tasks
- tool_use         : needs a specific tool (web search, calculator, weather)
- agent_task       : multi-step task requiring planning and multiple tool calls
- memory_recall    : asking about past conversations or stored knowledge (Akasha)
- smart_home       : Home Assistant controls (lights, climate, switches)
- calendar_email   : Gmail read/write, Google Calendar management
- neho_intel       : NEHO research, defense tech news, newsletter tasks
- stratsphere      : StratSphere league management queries

Respond ONLY with valid JSON matching this schema:
{
  "intent": "<intent_type>",
  "confidence": 0.0-1.0,
  "requires_tools": true|false,
  "tool_hints": ["optional", "list", "of", "tool", "names"],
  "rationale": "one sentence explanation"
}
""".strip()


class Orchestrator:
    """
    Main Aletheia orchestrator.
    Owns the Claude client, session store, and tool registry.
    """

    def __init__(
        self,
        settings: Settings,
        session_store: SessionStore,
        tool_registry: ToolRegistry,
    ):
        self.settings       = settings
        self.session        = session_store
        self.tools          = tool_registry
        self.client         = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key
        )

    # ── Public entrypoint ─────────────────────────────────────────────

    async def chat(
        self,
        session_id: str,
        user_message: str,
        context: dict[str, Any] | None = None,
    ) -> ChatResponse:
        t0 = time.monotonic()

        # 1. Classify intent
        intent = await self._classify_intent(user_message)
        log.info(
            "session=%s intent=%s confidence=%.2f",
            session_id, intent.intent, intent.confidence,
        )

        # 2. Persist user turn
        user_msg = ChatMessage(role="user", content=user_message)
        await self.session.append(session_id, user_msg)

        # 3. Route and generate response
        response_text, model_used, tokens = await self._generate(
            session_id=session_id,
            intent=intent,
            context=context or {},
        )

        # 4. Persist assistant turn
        assistant_msg = ChatMessage(role="assistant", content=response_text)
        await self.session.append(session_id, assistant_msg)

        latency_ms = (time.monotonic() - t0) * 1000

        return ChatResponse(
            session_id=session_id,
            message=response_text,
            intent=intent.intent,
            tool_calls=[],          # populated in Phase 1/2 when tools fire
            latency_ms=round(latency_ms, 1),
            model_used=model_used,
            tokens_used=tokens,
        )

    async def stream(
        self,
        session_id: str,
        user_message: str,
        context: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Streaming variant — yields text chunks as they arrive."""
        intent = await self._classify_intent(user_message)

        user_msg = ChatMessage(role="user", content=user_message)
        await self.session.append(session_id, user_msg)

        history = await self.session.get_anthropic_messages(session_id)
        full_response = []

        async with self.client.messages.stream(
            model=self.settings.claude_sonnet_model,
            max_tokens=self.settings.max_response_tokens,
            system=self._build_system_prompt(intent, context or {}),
            messages=history,
        ) as stream:
            async for chunk in stream.text_stream:
                full_response.append(chunk)
                yield chunk

        # Persist completed response
        assistant_msg = ChatMessage(
            role="assistant",
            content="".join(full_response),
        )
        await self.session.append(session_id, assistant_msg)

    # ── Intent Classification ─────────────────────────────────────────

    async def _classify_intent(self, message: str) -> IntentClassification:
        """
        Fast intent classification using Claude Haiku.
        Falls back to 'conversational' on any error.
        """
        try:
            resp = await self.client.messages.create(
                model=self.settings.claude_haiku_model,
                max_tokens=256,
                system=_INTENT_SYSTEM,
                messages=[{"role": "user", "content": message}],
            )
            raw = resp.content[0].text.strip()
            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)
            return IntentClassification(**data)
        except Exception as exc:
            log.warning("Intent classification failed: %s — defaulting to conversational", exc)
            return IntentClassification(
                intent=IntentType.CONVERSATIONAL,
                confidence=0.5,
                rationale="classification error, defaulted",
            )

    # ── Response Generation ───────────────────────────────────────────

    async def _generate(
        self,
        session_id: str,
        intent: IntentClassification,
        context: dict[str, Any],
    ) -> tuple[str, str, int]:
        """
        Generate a response. Returns (text, model_name, token_count).
        Phase 1: pure conversational. Tool dispatch wired in Phase 2.
        """
        history = await self.session.get_anthropic_messages(session_id)
        system  = self._build_system_prompt(intent, context)

        # Route to tool handler if required (Phase 2 expansion point)
        if intent.requires_tools and intent.intent != IntentType.CONVERSATIONAL:
            return await self._dispatch_tool_intent(
                intent=intent,
                history=history,
                system=system,
            )

        # Standard conversational response
        resp = await self.client.messages.create(
            model=self.settings.claude_sonnet_model,
            max_tokens=self.settings.max_response_tokens,
            system=system,
            messages=history,
        )

        text   = resp.content[0].text
        tokens = resp.usage.input_tokens + resp.usage.output_tokens
        return text, self.settings.claude_sonnet_model, tokens

    async def _dispatch_tool_intent(
        self,
        intent: IntentClassification,
        history: list[dict],
        system: str,
    ) -> tuple[str, str, int]:
        """
        Phase 2 expansion point: route to registered tools.
        For now, falls through to a standard response with intent context.
        """
        log.info(
            "Tool intent '%s' (hints=%s) — tool dispatch not yet active",
            intent.intent, intent.tool_hints,
        )
        # Append intent context to system prompt so Claude knows what's coming
        augmented_system = (
            system
            + f"\n\nNote: This request was classified as '{intent.intent}'. "
            "Full tool integration is coming. Respond as helpfully as possible "
            "with your current knowledge."
        )
        resp = await self.client.messages.create(
            model=self.settings.claude_sonnet_model,
            max_tokens=self.settings.max_response_tokens,
            system=augmented_system,
            messages=history,
        )
        text   = resp.content[0].text
        tokens = resp.usage.input_tokens + resp.usage.output_tokens
        return text, self.settings.claude_sonnet_model, tokens

    # ── System Prompt Builder ─────────────────────────────────────────

    def _build_system_prompt(
        self,
        intent: IntentClassification,
        context: dict[str, Any],
    ) -> str:
        parts = [self.settings.system_prompt]

        if context:
            ctx_lines = "\n".join(f"  {k}: {v}" for k, v in context.items())
            parts.append(f"\nClient context:\n{ctx_lines}")

        if intent.intent != IntentType.CONVERSATIONAL:
            parts.append(
                f"\nThis request has been classified as: {intent.intent.value}. "
                f"Respond accordingly."
            )

        return "\n".join(parts)
