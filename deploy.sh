#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
#  Aletheia — Deploy to Proxmox VM
#  Usage: ./deploy.sh [--build] [--restart]
#
#  Prerequisites:
#    - SSH key access to VM (10.69.30.23)
#    - Docker + Docker Compose on VM
#    - .env file on VM at /opt/aletheia/.env
# ─────────────────────────────────────────────────────────────────

set -euo pipefail

VM_HOST="10.69.30.23"
VM_USER="ubuntu"
VM_DIR="/opt/aletheia"
COMPOSE_FILE="docker-compose.yml"
BUILD=false
RESTART=false

# Parse args
for arg in "$@"; do
  case $arg in
    --build)   BUILD=true   ;;
    --restart) RESTART=true ;;
  esac
done

echo "▶ Syncing code to ${VM_USER}@${VM_HOST}:${VM_DIR}"
rsync -avz --exclude='.env' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.git' \
  --exclude='.venv' \
  ./ "${VM_USER}@${VM_HOST}:${VM_DIR}/"

echo "▶ Running on VM…"
ssh "${VM_USER}@${VM_HOST}" bash -s <<REMOTE
  set -euo pipefail
  cd ${VM_DIR}

  if [ "${BUILD}" = "true" ]; then
    echo "  Building Docker image…"
    docker compose build aletheia
  fi

  echo "  Pulling latest images…"
  docker compose pull --ignore-pull-failures redis

  echo "  Starting services…"
  docker compose up -d redis aletheia

  echo "  Waiting for health check…"
  sleep 3
  curl -sf http://localhost:8000/api/v1/health | python3 -m json.tool || echo "  ⚠ Health check failed"

  echo "  Container status:"
  docker compose ps
REMOTE

echo "✓ Deploy complete → http://${VM_HOST}:8000"
echo "  Docs:    http://${VM_HOST}:8000/docs"
echo "  Health:  http://${VM_HOST}:8000/api/v1/health"
