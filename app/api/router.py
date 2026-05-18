"""
Aletheia — API Router
Assembles all sub-routers under /api/v1
"""
from fastapi import APIRouter
from app.api import chat, health, voice

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(chat.router)
api_router.include_router(voice.router)
