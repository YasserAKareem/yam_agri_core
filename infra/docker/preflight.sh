#!/usr/bin/env bash
set -euo pipefail

echo "Running infra preflight checks..."

MISSING=0

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker not found on PATH." >&2
  MISSING=1
fi

COMPOSE_CMD=""
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD="docker-compose"
else
  echo "ERROR: neither 'docker compose' nor 'docker-compose' available." >&2
  MISSING=1
fi

if [ $MISSING -ne 0 ]; then
  echo "Preflight failed: please install Docker and the Compose plugin." >&2
  exit 2
fi

DOTENV=".env"
if [ ! -f "$DOTENV" ]; then
  echo "WARNING: $DOTENV not found in infra/docker. Create it from ../.env.example or infra/.env.example" >&2
else
  echo "$DOTENV found."
fi

# Try to inspect compose file images (non-destructive)
DOCKER_COMPOSE_FILE="docker-compose.yaml"
if [ ! -f "$DOCKER_COMPOSE_FILE" ] && [ -f "docker-compose.yml" ]; then
  DOCKER_COMPOSE_FILE="docker-compose.yml"
fi

if [ -f "$DOCKER_COMPOSE_FILE" ]; then
  echo "Found compose file: $DOCKER_COMPOSE_FILE"
  echo "Listing images referenced by compose (read-only):"
  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" config --images || true
else
  echo "WARNING: no compose file found in infra/docker. Expected docker-compose.yaml or docker-compose.yml" >&2
fi

echo "Preflight checks complete. Review warnings above before starting the stack."
