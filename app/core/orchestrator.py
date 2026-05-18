"""
Aletheia — Core Orchestrator
Agentic tool-use loop: user message → Claude Sonnet → [tool calls] → response.
"""
import json
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

        await self.session.append(session_id, ChatMessage(role="user", content=user_message))
        messages = await self.session.get_anthropic_messages(session_id)
        system   = self._build_system_prompt(context or {})
        tools    = self.tools.to_anthropic_tools()

        tool_calls_made: list[dict] = []
        response_text = ""
        tokens = 0

        while True:
            resp = await self.client.messages.create(
                model=self.settings.claude_sonnet_model,
                max_tokens=self.settings.max_response_tokens,
                system=system,
                messages=messages,
                **({"tools": tools} if tools else {}),
            )
            tokens += resp.usage.input_tokens + resp.usage.output_tokens
            messages.append({"role": "assistant", "content": resp.content})

            if resp.stop_reason == "tool_use":
                tool_results = []
                for block in resp.content:
                    if block.type == "tool_use":
                        log.info("Tool call: %s %s", block.name, block.input)
                        try:
                            result = await self.tools.run(block.name, block.input)
                        except Exception as exc:
                            result = {"error": str(exc)}
                        tool_calls_made.append({"name": block.name, "input": block.input, "result": result})
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })
                messages.append({"role": "user", "content": tool_results})
                continue

            # end_turn or no tools — extract text and exit loop
            response_text = next(
                (b.text for b in resp.content if hasattr(b, "text")), ""
            )
            break

        await self.session.append(session_id, ChatMessage(role="assistant", content=response_text))

        return ChatResponse(
            session_id=session_id,
            message=response_text,
            tool_calls=tool_calls_made,
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
        await self.session.append(session_id, ChatMessage(role="user", content=user_message))
        messages = await self.session.get_anthropic_messages(session_id)
        system   = self._build_system_prompt(context or {})
        tools    = self.tools.to_anthropic_tools()

        full_response: list[str] = []

        while True:
            async with self.client.messages.stream(
                model=self.settings.claude_sonnet_model,
                max_tokens=self.settings.max_response_tokens,
                system=system,
                messages=messages,
                **({"tools": tools} if tools else {}),
            ) as stream:
                async for chunk in stream.text_stream:
                    full_response.append(chunk)
                    yield chunk
                final = await stream.get_final_message()

            messages.append({"role": "assistant", "content": final.content})

            if final.stop_reason == "tool_use":
                tool_results = []
                for block in final.content:
                    if block.type == "tool_use":
                        log.info("Tool call (stream): %s %s", block.name, block.input)
                        try:
                            result = await self.tools.run(block.name, block.input)
                        except Exception as exc:
                            result = {"error": str(exc)}
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })
                messages.append({"role": "user", "content": tool_results})
                full_response = []
                continue

            break

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
