"""
Aletheia — Tool Registry
Each tool that provides an input_schema is surfaced to Claude via the
Anthropic tool-use API. Tools without a schema are registered but not
passed to the model (useful for internal stubs not yet ready).
"""
import logging
from typing import Any, Callable, Coroutine

log = logging.getLogger(__name__)

ToolFn = Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]


class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        fn: ToolFn,
        input_schema: dict | None = None,
    ):
        self.name         = name
        self.description  = description
        self.input_schema = input_schema
        self.fn           = fn

    def to_anthropic(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    async def run(self, args: dict[str, Any]) -> dict[str, Any]:
        log.info("Tool.run name=%s args=%s", self.name, args)
        return await self.fn(args)


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(
        self,
        name: str,
        description: str,
        input_schema: dict | None = None,
    ):
        """Decorator to register a tool function."""
        def decorator(fn: ToolFn):
            self._tools[name] = Tool(
                name=name,
                description=description,
                fn=fn,
                input_schema=input_schema,
            )
            log.debug("Registered tool: %s", name)
            return fn
        return decorator

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def to_anthropic_tools(self) -> list[dict]:
        """Return tool definitions for tools that have a schema (ready for Claude)."""
        return [t.to_anthropic() for t in self._tools.values() if t.input_schema]

    def list_tools(self) -> list[dict[str, str]]:
        return [
            {"name": t.name, "description": t.description}
            for t in self._tools.values()
        ]

    async def run(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        tool = self.get(name)
        if tool is None:
            return {"error": f"Tool '{name}' not found"}
        return await tool.run(args)


# ── Global registry instance ──────────────────────────────────────────

registry = ToolRegistry()


# ── Live tools ────────────────────────────────────────────────────────

from app.tools.weather import get_weather, TOOL_SCHEMA as _weather_schema  # noqa: E402

@registry.register(
    name="get_weather",
    description="Get current weather conditions for any location.",
    input_schema=_weather_schema,
)
async def _get_weather(args: dict) -> dict:
    return await get_weather(args)


# ── Stub tools (no schema — not surfaced to Claude until implemented) ─

@registry.register(
    name="web_search",
    description="Search the web for current information. Args: {query: str}",
)
async def _web_search(args: dict) -> dict:
    return {"status": "stub", "message": "Web search coming in Phase 2."}


@registry.register(
    name="smart_home",
    description="Control Home Assistant devices. Args: {action: str, entity_id: str}",
)
async def _smart_home(args: dict) -> dict:
    return {"status": "stub", "message": "Smart home integration coming in Phase 2."}


@registry.register(
    name="calendar",
    description="Read or write Google Calendar. Args: {action: str, ...}",
)
async def _calendar(args: dict) -> dict:
    return {"status": "stub", "message": "Calendar integration coming in Phase 2."}


@registry.register(
    name="email",
    description="Read or send Gmail. Args: {action: str, ...}",
)
async def _email(args: dict) -> dict:
    return {"status": "stub", "message": "Email integration coming in Phase 2."}


@registry.register(
    name="akasha_recall",
    description="Query the Akasha knowledge base. Args: {query: str, top_k: int}",
)
async def _akasha_recall(args: dict) -> dict:
    return {"status": "stub", "message": "Akasha recall coming in Phase 2."}
