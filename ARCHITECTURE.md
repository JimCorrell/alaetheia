# Aletheia — Architecture & Ecosystem

## Overview

Personal AI orchestrator. Voice-first, self-hosted, multi-tenant scaffolded
(single user initially). Runs on Proxmox. Accessible from home, mobile, and browser.

---

## Ecosystem map

```
┌─────────────────────────────────────────────────────────┐
│  Clients                                                │
│                                                         │
│  iOS app    Browser    Home Assistant    CLI/curl        │
│     │           │            │              │           │
└─────┼───────────┼────────────┼──────────────┼───────────┘
      │           │            │              │
      │     Cloudflare    local network       │
      │      Tunnel            │              │
      │           │            │              │
┌─────▼───────────▼────────────▼──────────────▼───────────┐
│  Proxmox — always-on                                    │
│                                                         │
│  Caddy (reverse proxy + SSL)                            │
│      │                                                  │
│      ├── Aletheia API (FastAPI)                         │
│      │       ├── Redis          (session memory)        │
│      │       ├── Postgres       (Akasha + users)        │
│      │       └── Whisper        (STT service)           │
│      │                                                  │
│      ├── Gitea                  (source control)        │
│      ├── Woodpecker CI          (pipelines)             │
│      └── Gitea Registry         (Docker images)         │
│                                                         │
│  Home Assistant (already running)                       │
│      └── conversation agent → Aletheia API              │
└─────────────────────────────────────────────────────────┘
```

---

## Networking

Two layers, both permanent:

| Layer | Tool | Purpose |
|---|---|---|
| Private mesh | **Tailscale** | Trusted devices (phone, laptop, Proxmox nodes) — primary access layer. Devices connect as if on the same LAN regardless of location. |
| Public access | **Cloudflare Tunnel** | Web UI, OAuth callbacks, anything needing a real URL. Outbound-only connection from Proxmox — no open firewall ports. |

---

## Clients

| Client | Transport | Auth |
|---|---|---|
| iOS app | HTTPS via Tailscale | API key stored in Keychain, silent on every request |
| Browser | HTTPS via Cloudflare Tunnel | JWT session (login once) |
| Home Assistant | Local network / Tailscale | API key in HA config, set once |
| CLI / curl | HTTPS via Tailscale | API key in env var |

---

## Services

### Always-on (Proxmox)

| Service | Role |
|---|---|
| Aletheia API | FastAPI — core orchestrator |
| Redis | Session memory (conversation history) |
| Postgres + pgvector | User accounts, API keys, Akasha long-term memory |
| Whisper | Standalone HTTP STT service |
| Caddy | Reverse proxy + automatic SSL |
| Gitea | Self-hosted source control |
| Woodpecker CI | Build and deploy pipelines |
| Gitea Registry | Docker image storage |
| Home Assistant | Home automation + voice pipeline (wake word → Whisper → Aletheia → TTS) |

### On-demand (Proxmox)

- Test / staging VMs spun up by Woodpecker CI pipelines

---

## Auth

**Machine clients** (iOS, HA, CLI): API key as Bearer token, SHA-256 hashed in Postgres.
**Browser**: JWT session (added when web UI is built).
**All routes use `get_current_user(request)`** — a single FastAPI dependency. The implementation is swappable without touching routes.

Key format: `aletheia_<64 hex chars>` (256 bits of entropy). Generated once, shown once, store it.

Setup flow:
1. First deploy: `POST /api/v1/auth/setup` creates the owner user + first key (only works when no users exist)
2. Store that key
3. Create per-client keys via `POST /api/v1/auth/keys`
4. Put each key in the relevant client (HA config, iOS Keychain, shell profile)

Sessions are scoped to users: the Redis key includes `user_id`, so sessions from different users are isolated even if they use the same `session_id` string.

---

## CI/CD

| Stage | Tool |
|---|---|
| Source control | Gitea (self-hosted on Proxmox) |
| CI pipelines | Woodpecker CI |
| Container registry | Gitea built-in registry |
| Deploy | Woodpecker pipeline → SSH → `docker compose pull && up -d` |

Pipeline on push to `main`:
1. Run tests (`pytest`)
2. Build Docker image
3. Push to Gitea registry
4. SSH to Proxmox, pull image, restart service

---

## Voice pipeline (home)

Home Assistant owns the voice pipeline. Aletheia registers as the conversation agent.

```
Wake word (openWakeWord)
    → Whisper STT (HA add-on or Aletheia Whisper service)
    → Aletheia API  (conversation agent endpoint)
    → ElevenLabs TTS
    → Speaker
```

No custom WebSocket layer needed for home voice — HA handles it.

---

## Roadmap

### Done
- [x] FastAPI scaffold with lifespan Redis pool
- [x] Claude Sonnet integration (chat + streaming)
- [x] Redis session memory with TTL and history trimming
- [x] Text I/O endpoints: POST /chat, /chat/stream, GET /history, DELETE /session
- [x] Health check endpoint with dependency liveness
- [x] Agentic tool-use loop (chat + stream)
- [x] Weather tool (Open-Meteo, no API key)

### Phase 1 — Auth, Tools, Voice
- [ ] API key auth (Postgres-backed, per-client keys)
- [ ] Web search tool (Tavily)
- [ ] Whisper as standalone HTTP service on Proxmox
- [ ] HA conversation agent endpoint
- [ ] ElevenLabs TTS integration
- [ ] iOS app

### Phase 2 — Memory, CI/CD, Infrastructure
- [ ] Akasha long-term memory (pgvector)
- [ ] Gitea + Woodpecker CI setup
- [ ] Caddy + Cloudflare Tunnel
- [ ] Smart home tools (Home Assistant REST API)
- [ ] Calendar & email (Gmail / GCal)

### Phase 3 — Agents
- [ ] NEHO research briefing agent
- [ ] StratSphere league management agent
- [ ] Multi-step planning agent
