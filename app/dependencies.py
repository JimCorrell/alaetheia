"""
Aletheia — FastAPI Dependencies
Injected via Depends() across route handlers.
"""
from typing import Annotated, AsyncGenerator

import redis.asyncio as aioredis
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings


# ── Settings ─────────────────────────────────────────────────────────

SettingsDep = Annotated[Settings, Depends(get_settings)]


# ── Redis ─────────────────────────────────────────────────────────────

async def get_redis(request: Request) -> aioredis.Redis:
    pool: aioredis.ConnectionPool = request.app.state.redis_pool
    return aioredis.Redis(connection_pool=pool)


RedisDep = Annotated[aioredis.Redis, Depends(get_redis)]


# ── Database ──────────────────────────────────────────────────────────

async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    async with request.app.state.db_session_factory() as session:
        yield session


DbDep = Annotated[AsyncSession, Depends(get_db)]
