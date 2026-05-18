"""
Aletheia — Redis Session Store
Manages conversation history per session_id.
TTL-backed, FIFO-trimmed, serialised as JSON.
"""
import json
import time
from typing import Any

import redis.asyncio as aioredis

from app.config import Settings
from app.models.schemas import ChatMessage


HISTORY_KEY = "aletheia:history:{session_id}"
META_KEY    = "aletheia:meta:{session_id}"


class SessionStore:
    """
    Per-session conversation memory backed by Redis lists.
    Each session stores up to `max_turns` (user+assistant pairs).
    """

    def __init__(self, redis: aioredis.Redis, settings: Settings):
        self.redis    = redis
        self.ttl      = settings.session_ttl_seconds
        self.max_turns = settings.max_history_turns

    def _hkey(self, session_id: str) -> str:
        return HISTORY_KEY.format(session_id=session_id)

    def _mkey(self, session_id: str) -> str:
        return META_KEY.format(session_id=session_id)

    async def append(self, session_id: str, message: ChatMessage) -> None:
        """Append a message to the session history, trim if over limit."""
        key = self._hkey(session_id)
        pipe = self.redis.pipeline()
        pipe.rpush(key, message.model_dump_json())
        # Keep at most max_turns * 2 entries (user + assistant per turn)
        pipe.ltrim(key, -(self.max_turns * 2), -1)
        pipe.expire(key, self.ttl)
        await pipe.execute()

    async def get_history(self, session_id: str) -> list[ChatMessage]:
        """Return ordered conversation history for a session."""
        key = self._hkey(session_id)
        raw = await self.redis.lrange(key, 0, -1)
        messages = []
        for item in raw:
            try:
                data = json.loads(item)
                messages.append(ChatMessage(**data))
            except Exception:
                continue
        return messages

    async def get_anthropic_messages(
        self,
        session_id: str,
    ) -> list[dict[str, Any]]:
        """
        Return history formatted for the Anthropic messages API.
        Anthropic requires alternating user/assistant turns.
        """
        history = await self.get_history(session_id)
        return [
            {"role": msg.role, "content": msg.content}
            for msg in history
        ]

    async def set_meta(self, session_id: str, key: str, value: Any) -> None:
        """Store arbitrary session metadata (e.g. user preferences, context)."""
        mkey = self._mkey(session_id)
        await self.redis.hset(mkey, key, json.dumps(value))
        await self.redis.expire(mkey, self.ttl)

    async def get_meta(self, session_id: str, key: str) -> Any | None:
        mkey = self._mkey(session_id)
        raw = await self.redis.hget(mkey, key)
        if raw is None:
            return None
        return json.loads(raw)

    async def clear_session(self, session_id: str) -> None:
        """Delete all data for a session."""
        await self.redis.delete(
            self._hkey(session_id),
            self._mkey(session_id),
        )

    async def session_exists(self, session_id: str) -> bool:
        return bool(await self.redis.exists(self._hkey(session_id)))

    async def touch(self, session_id: str) -> None:
        """Reset TTL on active session."""
        pipe = self.redis.pipeline()
        pipe.expire(self._hkey(session_id), self.ttl)
        pipe.expire(self._mkey(session_id), self.ttl)
        await pipe.execute()
