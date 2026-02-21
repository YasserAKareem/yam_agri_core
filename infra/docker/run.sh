#!/usr/bin/env bash
set -e

DOCKER_COMPOSE_FILE="docker-compose.yaml"
DOTENV_CONFIG_FILE=".env"

# Load environment variables from .env if present
if [ -f "$DOTENV_CONFIG_FILE" ]; then
  # shellcheck disable=SC1090
  set -a; source "$DOTENV_CONFIG_FILE"; set +a
fi

function start_services() {
  docker compose -f "$DOCKER_COMPOSE_FILE" up -d
}

function stop_services() {
  docker compose -f "$DOCKER_COMPOSE_FILE" down
}

function stream_service_logs() {
  docker compose -f "$DOCKER_COMPOSE_FILE" logs -f
}

function open_frappe_shell() {
  docker compose -f "$DOCKER_COMPOSE_FILE" exec frappe bash
}

function initialize_frappe_site() {
  echo "Initializing site and installing apps..."
  docker compose -f "$DOCKER_COMPOSE_FILE" exec frappe bench new-site $FRAPPE_SITE --mariadb-root-password $MYSQL_ROOT_PASSWORD --admin-password $ADMIN_PASSWORD
  docker compose -f "$DOCKER_COMPOSE_FILE" exec frappe bench install-app erpnext agriculture
}

function reset_and_rebuild() {
  echo "Resetting volumes and rebuilding stack..."
  docker compose -f "$DOCKER_COMPOSE_FILE" down -v
  docker compose -f "$DOCKER_COMPOSE_FILE" up -d --build
}

case "$1" in
  up) start_services ;;
  down) stop_services ;;
  logs) stream_service_logs ;;
  shell) open_frappe_shell ;;
  init) initialize_frappe_site ;;
  reset) reset_and_rebuild ;;
  *) echo "Usage: $0 {up|down|logs|shell|init|reset}" ;;
esac
