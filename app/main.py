"""
Aletheia — FastAPI Application Entry Point
Run locally:   uvicorn app.main:app --reload --port 8000
Deploy on VM:  gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 2
"""
import logging
import sys
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import app.auth.models  # noqa: F401 — registers models with Base before create_all
from app.api.router import api_router
from app.config import get_settings
from app.db import Base, make_engine, make_session_factory

# ── Logging ───────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("aletheia")


# ── Lifespan (startup / shutdown) ─────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    log.info("Starting Aletheia v%s", settings.app_version)

    # Redis connection pool — shared across all requests
    app.state.redis_pool = aioredis.ConnectionPool.from_url(
        settings.redis_url,
        db=settings.redis_db,
        decode_responses=True,
        max_connections=20,
    )
    log.info("Redis pool created → %s", settings.redis_url)

    # Postgres — create tables if they don't exist, then share session factory
    engine = make_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.state.db_session_factory = make_session_factory(engine)
    log.info("Database ready → %s", settings.database_url.split("@")[-1])

    yield  # ← application runs here

    log.info("Shutting down Aletheia…")
    await app.state.redis_pool.aclose()
    await engine.dispose()


# ── App Factory ───────────────────────────────────────────────────────

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Aletheia",
        description=(
            "Voice-first AI orchestrator. "
            "FastAPI + Claude API + Redis + pgvector."
        ),
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS — allow iPhone PWA and local dev
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(api_router, prefix="/api/v1")

    # Root
    @app.get("/", include_in_schema=False)
    async def root():
        return JSONResponse({
            "name": "Aletheia",
            "version": settings.app_version,
            "status": "online",
            "docs": "/docs",
        })

    return app


app = create_app()
