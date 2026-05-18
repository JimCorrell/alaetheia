"""
Aletheia — API key generation and verification.
Keys are high-entropy random tokens; SHA-256 is appropriate (not bcrypt).
"""
import hashlib
import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models import ApiKey, User

KEY_PREFIX = "aletheia_"


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def generate_key() -> tuple[str, str]:
    """Return (raw_key, key_hash). Store the hash; show raw once."""
    raw = KEY_PREFIX + secrets.token_hex(32)
    return raw, _hash(raw)


async def verify_key(db: AsyncSession, raw: str) -> User | None:
    """Verify a raw API key and return its User, or None if invalid."""
    if not raw.startswith(KEY_PREFIX):
        return None
    result = await db.execute(
        select(ApiKey)
        .options(selectinload(ApiKey.user))
        .where(ApiKey.key_hash == _hash(raw), ApiKey.is_active == True)  # noqa: E712
    )
    api_key = result.scalar_one_or_none()
    if api_key is None or not api_key.user.is_active:
        return None
    api_key.last_used_at = datetime.now(timezone.utc)
    await db.commit()
    return api_key.user


async def create_key(db: AsyncSession, user_id: uuid.UUID, label: str) -> tuple[str, ApiKey]:
    """Create a new API key for a user. Returns (raw_key, ApiKey record)."""
    raw, key_hash = generate_key()
    api_key = ApiKey(user_id=user_id, key_hash=key_hash, label=label)
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return raw, api_key


async def has_any_user(db: AsyncSession) -> bool:
    result = await db.execute(select(User).limit(1))
    return result.scalar_one_or_none() is not None
