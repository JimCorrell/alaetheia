"""
Aletheia — Auth endpoints.

POST /auth/setup        — first-run: create owner user + initial key (no auth required)
POST /auth/keys         — create a new key for the current user
GET  /auth/keys         — list current user's keys (hashes never returned)
DELETE /auth/keys/{id}  — revoke a key
"""
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.auth.dependencies import CurrentUser
from app.auth.models import ApiKey
from app.auth.service import create_key, has_any_user
from app.auth.models import User
from app.dependencies import DbDep
from sqlalchemy import select, update

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Schemas ───────────────────────────────────────────────────────────

class SetupRequest(BaseModel):
    name: str


class SetupResponse(BaseModel):
    user_id: str
    api_key: str
    message: str


class CreateKeyRequest(BaseModel):
    label: str


class KeyResponse(BaseModel):
    id: str
    label: str
    created_at: str
    last_used_at: str | None


class CreateKeyResponse(BaseModel):
    api_key: str
    key: KeyResponse


# ── Routes ────────────────────────────────────────────────────────────

@router.post("/setup", response_model=SetupResponse)
async def setup(body: SetupRequest, db: DbDep) -> Any:
    """
    First-run setup. Creates the owner user and initial API key.
    Fails with 409 if any user already exists.
    """
    if await has_any_user(db):
        raise HTTPException(status_code=409, detail="Setup already complete. Use /auth/keys to create additional keys.")

    user = User(name=body.name)
    db.add(user)
    await db.flush()

    raw, api_key = await create_key(db, user.id, label="initial")
    await db.commit()

    return SetupResponse(
        user_id=str(user.id),
        api_key=raw,
        message="Store this key — it will not be shown again.",
    )


@router.post("/keys", response_model=CreateKeyResponse)
async def create_api_key(body: CreateKeyRequest, current_user: CurrentUser, db: DbDep) -> Any:
    """Create a new API key for the authenticated user."""
    raw, api_key = await create_key(db, current_user.id, label=body.label)
    return CreateKeyResponse(
        api_key=raw,
        key=KeyResponse(
            id=str(api_key.id),
            label=api_key.label,
            created_at=api_key.created_at.isoformat(),
            last_used_at=api_key.last_used_at.isoformat() if api_key.last_used_at else None,
        ),
    )


@router.get("/keys", response_model=list[KeyResponse])
async def list_keys(current_user: CurrentUser, db: DbDep) -> Any:
    """List all active API keys for the authenticated user."""
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.user_id == current_user.id, ApiKey.is_active == True)  # noqa: E712
        .order_by(ApiKey.created_at)
    )
    keys = result.scalars().all()
    return [
        KeyResponse(
            id=str(k.id),
            label=k.label,
            created_at=k.created_at.isoformat(),
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
        )
        for k in keys
    ]


@router.delete("/keys/{key_id}", status_code=204)
async def revoke_key(key_id: uuid.UUID, current_user: CurrentUser, db: DbDep) -> None:
    """Revoke an API key. Only the owning user can revoke their own keys."""
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.user_id == current_user.id,
            ApiKey.is_active == True,  # noqa: E712
        )
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status_code=404, detail="Key not found")
    api_key.is_active = False
    await db.commit()
