"""
Aletheia — Configuration
All settings loaded from environment / .env file.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_ignore_empty=True,
    )

    # ── App ──────────────────────────────────────────────────────
    app_name: str = "Aletheia"
    app_version: str = "0.1.0"
    debug: bool = False
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # ── Anthropic ────────────────────────────────────────────────
    anthropic_api_key: str
    # Fast model for intent classification
    claude_haiku_model: str = "claude-haiku-4-5-20251001"
    # Main reasoning model
    claude_sonnet_model: str = "claude-sonnet-4-6"
    # Max tokens for responses
    max_response_tokens: int = 2048

    # ── Redis ────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    # Session TTL: 24 hours
    session_ttl_seconds: int = 86_400
    # Max conversation turns kept in Redis
    max_history_turns: int = 20

    # ── Voice (Phase 1 — stubbed, activated later) ────────────────
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel
    whisper_model_path: str = "/opt/whisper/models/base.en"

    # —— Tavily —————————————————————————————————————————————————————
    tavily_api_key: str = ""

    # ── Memory / Akasha ──────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://aletheia:aletheia@localhost:5432/aletheia"
    pgvector_collection: str = "akasha_memory"

    # ── Aletheia Identity ────────────────────────────────────────
    system_prompt: str = (
        "You are Aletheia, a highly capable personal AI assistant and orchestrator. "
        "You are direct, intelligent, and precise. You have access to tools and agents "
        "and coordinate them to accomplish tasks. You speak in first person and maintain "
        "continuity across conversations. When you are uncertain, you say so. "
        "Your responses are concise unless depth is explicitly requested."
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
