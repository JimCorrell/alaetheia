"""
Aletheia — Auth FastAPI dependencies.
"""
from typing import Annotated

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.models import User
from app.auth.service import verify_key
from app.dependencies import DbDep

_bearer = HTTPBearer()


async def get_current_user(
    db: DbDep,
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
) -> User:
    user = await verify_key(db, credentials.credentials)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired API key")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
