"""
Aletheia — Health Check Routes
GET /api/v1/health — returns status of all dependencies
"""
import time
import logging

from fastapi import APIRouter

from app.dependencies import RedisDep, SettingsDep
from app.models.schemas import HealthResponse, HealthStatus, ServiceHealth

router = APIRouter(prefix="/health", tags=["health"])
log = logging.getLogger(__name__)

_start_time = time.monotonic()


@router.get("", response_model=HealthResponse)
async def health(
    redis: RedisDep,
    settings: SettingsDep,
) -> HealthResponse:
    services: list[ServiceHealth] = []
    overall = HealthStatus.OK

    # ── Redis ─────────────────────────────────────────────────────────
    try:
        await redis.ping()
        services.append(ServiceHealth(name="redis", status=HealthStatus.OK))
    except Exception as exc:
        log.warning("Redis health check failed: %s", exc)
        services.append(
            ServiceHealth(name="redis", status=HealthStatus.DOWN, detail=str(exc))
        )
        overall = HealthStatus.DEGRADED

    # ── Anthropic API key ─────────────────────────────────────────────
    if settings.anthropic_api_key:
        services.append(ServiceHealth(name="anthropic", status=HealthStatus.OK))
    else:
        services.append(
            ServiceHealth(
                name="anthropic",
                status=HealthStatus.DOWN,
                detail="ANTHROPIC_API_KEY not set",
            )
        )
        overall = HealthStatus.DEGRADED

    # ── Voice (ElevenLabs) ────────────────────────────────────────────
    if settings.elevenlabs_api_key:
        services.append(ServiceHealth(name="elevenlabs", status=HealthStatus.OK))
    else:
        services.append(
            ServiceHealth(
                name="elevenlabs",
                status=HealthStatus.DEGRADED,
                detail="Not configured — voice disabled",
            )
        )

    return HealthResponse(
        status=overall,
        version=settings.app_version,
        services=services,
        uptime_seconds=round(time.monotonic() - _start_time, 1),
    )
