"""
Aletheia — FastAPI Dependencies
Injected via Depends() across route handlers.
"""
from typing import Annotated
import redis.asyncio as aioredis
from fastapi import Depends, Request
from app.config import Settings, get_settings


# ── Settings ─────────────────────────────────────────────────────────

SettingsDep = Annotated[Settings, Depends(get_settings)]


# ── Redis ─────────────────────────────────────────────────────────────

async def get_redis(request: Request) -> aioredis.Redis:
    """Return an async Redis client from the shared connection pool."""
    pool: aioredis.ConnectionPool = request.app.state.redis_pool
    return aioredis.Redis(connection_pool=pool)


RedisDep = Annotated[aioredis.Redis, Depends(get_redis)]
