#!/usr/bin/env bash
set -euo pipefail

# Load .env if present
ENV_FILE="$(dirname "$0")/.env"
if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

FRAPPE_SERVICE="${FRAPPE_SERVICE:-backend}"

# detect docker compose command
if command -v docker >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
  else
    echo "Neither 'docker compose' nor 'docker-compose' found." >&2
    exit 1
  fi
else
  echo "Docker not found. Install Docker Desktop / Docker Engine." >&2
  exit 1
fi

if [ "$#" -eq 0 ]; then
  echo "Usage: $0 <bench-args...>"
  echo "Examples:"
  echo "  $0 --site site1.local reload-doc yam_agri_core"
  echo "  $0 --site site1.local execute 'frappe.enqueue'"
  exit 1
fi

exec $COMPOSE_CMD exec -T "$FRAPPE_SERVICE" bench "$@"
