#!/usr/bin/env bash
set -e

COMPOSE_FILE="docker-compose.yaml"
ENV_FILE=".env"

# Load environment variables from .env if present
if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1090
  set -a; source "$ENV_FILE"; set +a
fi

function up() {
  docker compose -f $COMPOSE_FILE up -d
}

function down() {
  docker compose -f $COMPOSE_FILE down
}

function logs() {
  docker compose -f $COMPOSE_FILE logs -f
}

function shell() {
  docker compose -f $COMPOSE_FILE exec frappe bash
}

function init() {
  echo "Initializing site and installing apps..."
  docker compose -f $COMPOSE_FILE exec frappe bench new-site $FRAPPE_SITE --mariadb-root-password $MYSQL_ROOT_PASSWORD --admin-password $ADMIN_PASSWORD
  docker compose -f $COMPOSE_FILE exec frappe bench install-app erpnext agriculture
}

function reset() {
  echo "Resetting volumes and rebuilding stack..."
  docker compose -f $COMPOSE_FILE down -v
  docker compose -f $COMPOSE_FILE up -d --build
}

case "$1" in
  up) up ;;
  down) down ;;
  logs) logs ;;
  shell) shell ;;
  init) init ;;
  reset) reset ;;
  *) echo "Usage: $0 {up|down|logs|shell|init|reset}" ;;
esac
