# Aletheia — Dockerfile
# Multi-stage: builder → runtime
# Target: Ubuntu 24.04 on Proxmox VM

ARG PYTHON_VERSION=3.12

# ── Stage 1: Builder ──────────────────────────────────────────────────
FROM python:${PYTHON_VERSION}-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Runtime ─────────────────────────────────────────────────
FROM python:${PYTHON_VERSION}-slim AS runtime

WORKDIR /app

# Runtime deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application
COPY app/ ./app/

# Non-root user for security
RUN useradd -m -u 1000 aletheia && chown -R aletheia:aletheia /app
USER aletheia

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Prod: gunicorn with uvicorn workers
# Dev: uvicorn with --reload (override in compose)
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "2", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
