"""
Aletheia — Voice Pipeline Routes (Phase 1 Stub)

POST /api/v1/voice/transcribe  — audio → text (Whisper)
POST /api/v1/voice/speak       — text → audio (ElevenLabs)
WS   /api/v1/voice/stream      — full duplex voice session

TODO Phase 1:
  - Wire Whisper (self-hosted on Proxmox) for STT
  - Wire ElevenLabs TTS
  - WebSocket voice session: mic → Whisper → Orchestrator → ElevenLabs → speaker
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/voice", tags=["voice"])


class TranscribeResponse(BaseModel):
    transcript: str
    confidence: float | None = None
    duration_seconds: float | None = None


class SpeakRequest(BaseModel):
    text: str
    voice_id: str | None = None   # Override default voice


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe():
    """
    Phase 1 TODO: Accept audio file upload, run through self-hosted Whisper,
    return transcript.
    """
    raise HTTPException(
        status_code=501,
        detail="Voice pipeline not yet implemented. Phase 1 milestone.",
    )


@router.post("/speak")
async def speak():
    """
    Phase 1 TODO: Accept text, send to ElevenLabs TTS, stream audio back.
    """
    raise HTTPException(
        status_code=501,
        detail="TTS not yet implemented. Phase 1 milestone.",
    )
