# ALETHEIA — v0.1.0

Voice-first AI orchestrator. FastAPI + Claude API + Redis + pgvector.

## Quickstart (local dev)

```bash
# 1. Create venv
python3.12 -m venv .venv && source .venv/bin/activate

# 2. Install deps
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env — minimum required: ANTHROPIC_API_KEY

# 4. Start Redis (Docker)
docker compose up -d redis

# 5. Run API
uvicorn app.main:app --reload --port 8000
```

**API is live at http://localhost:8000**
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

## Quick test

```bash
# Health check
curl http://localhost:8000/api/v1/health | python3 -m json.tool

# Chat (text I/O)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "dev-001", "message": "What are you capable of?"}'

# Streaming chat
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"session_id": "dev-001", "message": "Tell me about Aletheia"}'

# View conversation history
curl http://localhost:8000/api/v1/chat/dev-001/history

# Clear session
curl -X DELETE http://localhost:8000/api/v1/chat/dev-001
```

## Deploy to Proxmox VM

```bash
# First deploy (with image build)
./deploy.sh --build

# Subsequent deploys (code sync only)
./deploy.sh
```

## Project structure

```
aletheia/
├── app/
│   ├── main.py              # FastAPI app + lifespan (Redis pool)
│   ├── config.py            # Pydantic settings (all env vars)
│   ├── dependencies.py      # FastAPI Depends() — Redis, settings
│   ├── api/
│   │   ├── router.py        # Assembles all sub-routers
│   │   ├── chat.py          # POST /chat, /chat/stream, history, clear
│   │   ├── health.py        # GET /health — dependency liveness
│   │   └── voice.py         # Voice pipeline (Phase 1 stub)
│   ├── core/
│   │   └── orchestrator.py  # Intent classify (Haiku) → generate (Sonnet)
│   ├── memory/
│   │   └── redis_store.py   # Session history — Redis list per session_id
│   ├── models/
│   │   └── schemas.py       # Pydantic schemas — ChatRequest, ChatResponse, etc.
│   └── tools/
│       └── registry.py      # Tool registry + Phase 1 stubs
├── tests/
│   └── test_phase1.py       # pytest — health, intent, session, tools
├── docker-compose.yml       # Redis + Postgres (phase2 profile) + API
├── Dockerfile               # Multi-stage, non-root, gunicorn prod
├── deploy.sh                # rsync → VM + docker compose up
├── requirements.txt
└── .env.example
```

## Architecture — Phase 1

```
Client (curl / web / iPhone)
        │
        ▼ POST /api/v1/chat
FastAPI (app/main.py)
        │
        ▼
Orchestrator (app/core/orchestrator.py)
   ├── 1. Classify intent → Claude Haiku (~200ms)
   ├── 2. Load history   → Redis SessionStore
   ├── 3. Generate       → Claude Sonnet (~500ms)
   └── 4. Persist        → Redis SessionStore
        │
        ▼
ChatResponse (JSON) | SSE stream
```

## Phase 1 milestones

- [x] FastAPI scaffold
- [x] Claude API integration (Haiku intent + Sonnet response)
- [x] Redis session memory
- [x] Text I/O endpoints (chat + stream)
- [ ] Whisper STT (self-hosted on Proxmox)
- [ ] ElevenLabs TTS
- [ ] WebSocket voice session
- [ ] Weather agent (first real tool)
- [ ] Research agent (web search via Tavily)
- [ ] pgvector Akasha integration

## Running tests

```bash
pytest tests/ -v
```
