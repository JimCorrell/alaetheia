"""
Aletheia — Tool Registry
Phase 1: registry scaffold + stub tools.
Phase 2: real implementations wired here.

Each tool is a callable that accepts a dict of arguments
and returns a dict result. Tools are registered by name
and invoked by the orchestrator's tool dispatch loop.
"""
import logging
from typing import Any, Callable, Coroutine

log = logging.getLogger(__name__)

ToolFn = Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]


class Tool:
    def __init__(self, name: str, description: str, fn: ToolFn):
        self.name        = name
        self.description = description
        self.fn          = fn

    async def run(self, args: dict[str, Any]) -> dict[str, Any]:
        log.info("Tool.run name=%s args=%s", self.name, args)
        return await self.fn(args)


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, name: str, description: str):
        """Decorator to register a tool function."""
        def decorator(fn: ToolFn):
            self._tools[name] = Tool(name=name, description=description, fn=fn)
            log.debug("Registered tool: %s", name)
            return fn
        return decorator

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

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


# ── Stub tools (Phase 1) — replace with real implementations in Phase 2 ──

@registry.register(
    name="web_search",
    description="Search the web for current information. Args: {query: str}",
)
async def _web_search(args: dict) -> dict:
    """Phase 2: Tavily API integration."""
    return {"status": "stub", "message": "Web search coming in Phase 2."}


@registry.register(
    name="smart_home",
    description="Control Home Assistant devices. Args: {action: str, entity_id: str}",
)
async def _smart_home(args: dict) -> dict:
    """Phase 2: Home Assistant REST/WebSocket."""
    return {"status": "stub", "message": "Smart home integration coming in Phase 2."}


@registry.register(
    name="calendar",
    description="Read or write Google Calendar. Args: {action: str, ...}",
)
async def _calendar(args: dict) -> dict:
    """Phase 2: Google Calendar API via MCP."""
    return {"status": "stub", "message": "Calendar integration coming in Phase 2."}


@registry.register(
    name="email",
    description="Read or send Gmail. Args: {action: str, ...}",
)
async def _email(args: dict) -> dict:
    """Phase 2: Gmail MCP integration."""
    return {"status": "stub", "message": "Email integration coming in Phase 2."}


@registry.register(
    name="akasha_recall",
    description="Query the Akasha knowledge base. Args: {query: str, top_k: int}",
)
async def _akasha_recall(args: dict) -> dict:
    """Phase 2: pgvector semantic search against Akasha."""
    return {"status": "stub", "message": "Akasha recall coming in Phase 2."}
