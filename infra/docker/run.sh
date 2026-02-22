#!/usr/bin/env bash
set -e

# Default compose filename (prefer .yaml but fallback to .yml)
DOCKER_COMPOSE_FILE="docker-compose.yaml"
# Backwards-compatible fallback: some checkouts use .yml
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
  if [ -f "docker-compose.yml" ]; then
    DOCKER_COMPOSE_FILE="docker-compose.yml"
  fi
fi
DOTENV_CONFIG_FILE=".env"
BACKUP_DIR="./backups"
# Archive of pre-pulled images for offline delivery (Yemen use-case)
OFFLINE_IMAGES_ARCHIVE="${OFFLINE_IMAGES_ARCHIVE:-./offline-images.tar}"

# Load environment variables from .env if present
if [ -f "$DOTENV_CONFIG_FILE" ]; then
  # shellcheck disable=SC1090
  set -a; source "$DOTENV_CONFIG_FILE"; set +a
fi

# Canonicalize site/env names: accept either FRAPPE_SITE or SITE_NAME
if [ -z "$FRAPPE_SITE" ] && [ -n "$SITE_NAME" ]; then
  FRAPPE_SITE="$SITE_NAME"
fi
if [ -z "$SITE_NAME" ] && [ -n "$FRAPPE_SITE" ]; then
  SITE_NAME="$FRAPPE_SITE"
fi

# Default service name; allow override via env (FRAPPE_SERVICE)
FRAPPE_SERVICE="${FRAPPE_SERVICE:-backend}"

# Detect whether host has 'docker compose' (v2) or legacy 'docker-compose'
COMPOSE_CMD=""
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD="docker-compose"
else
  echo "Error: neither 'docker compose' nor 'docker-compose' found on PATH. Install Docker Desktop or the Compose plugin." >&2
  exit 1
fi

if [ ! -f "$DOTENV_CONFIG_FILE" ]; then
  echo "WARNING: $DOTENV_CONFIG_FILE not found. Create it from .env.example." >&2
fi

function start_services() {
  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" up -d
}

function stop_services() {
  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" down
}

function stream_service_logs() {
  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" logs -f
}

function open_frappe_shell() {
  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" exec "$FRAPPE_SERVICE" bash
}

function run_bench_command() {
  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" exec -T "$FRAPPE_SERVICE" bench "$@"
}

function initialize_frappe_site() {
  echo "Initializing site and installing apps..."

  # Configure bench to use the docker-compose services (mirrors frappe_docker configurator)
  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" exec "$FRAPPE_SERVICE" \
    bench set-config -g db_host db
  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" exec "$FRAPPE_SERVICE" \
    bench set-config -gp db_port 3306
  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" exec "$FRAPPE_SERVICE" \
    bench set-config -g redis_cache "redis://redis-cache:6379"
  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" exec "$FRAPPE_SERVICE" \
    bench set-config -g redis_queue "redis://redis-queue:6379"
  # Backward compatibility key used by some configs
  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" exec "$FRAPPE_SERVICE" \
    bench set-config -g redis_socketio "redis://redis-queue:6379"
  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" exec "$FRAPPE_SERVICE" \
    bench set-config -gp socketio_port 9000

  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" exec "$FRAPPE_SERVICE" bench new-site "$FRAPPE_SITE" \
    --mariadb-root-password "${DB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" \
    --db-root-username "${DB_ROOT_USER:-root}" \
    --admin-password "$ADMIN_PASSWORD"

  # Make the site resolvable on localhost without host file edits
  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" exec "$FRAPPE_SERVICE" \
    bench set-config -g default_site "$FRAPPE_SITE"

  # Install apps onto the newly created site
  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" exec "$FRAPPE_SERVICE" \
    bench --site "$FRAPPE_SITE" install-app erpnext

  # Install optional apps if they exist in this image
  if [ -n "$INSTALL_APPS" ]; then
    IFS=',' read -r -a apps_to_install <<<"$INSTALL_APPS"
    for app in "${apps_to_install[@]}"; do
      app_trimmed="$(echo "$app" | xargs)"
      if [ -z "$app_trimmed" ] || [ "$app_trimmed" = "erpnext" ]; then
        continue
      fi
      if $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" exec -T "$FRAPPE_SERVICE" bash -lc "test -d apps/$app_trimmed"; then
        $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" exec "$FRAPPE_SERVICE" \
          bench --site "$FRAPPE_SITE" install-app "$app_trimmed"
      else
        echo "NOTE: app '$app_trimmed' not found in image (apps/$app_trimmed). Skipping."
      fi
    done
  fi
}

function reset_and_rebuild() {
  echo "Resetting volumes and rebuilding stack..."
  docker compose -f "$DOCKER_COMPOSE_FILE" down -v
  docker compose -f "$DOCKER_COMPOSE_FILE" up -d --build
}

# ── Yemen-resilient helpers ────────────────────────────────────────────────

# Pull all required images while internet is available, then save to a tar
# archive so the stack can be started at a remote site with no internet.
# Usage: bash run.sh prefetch
function prefetch_images() {
  echo "Pulling all images defined in $DOCKER_COMPOSE_FILE ..."
  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" pull
  echo "Saving images to $OFFLINE_IMAGES_ARCHIVE (this may take a few minutes)..."
  # Extract image names into an array and save them all in one archive
  mapfile -t images < <($COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" config --images)
  docker save "${images[@]}" -o "$OFFLINE_IMAGES_ARCHIVE"
  echo "Done. Transfer $OFFLINE_IMAGES_ARCHIVE to the target machine."
}

# Load images from the pre-saved archive, then start normally.
# Run this on a machine with NO internet access (field site, offline laptop).
# Usage: bash run.sh offline-init
function offline_init() {
  if [ ! -f "$OFFLINE_IMAGES_ARCHIVE" ]; then
    echo "ERROR: offline image archive not found at $OFFLINE_IMAGES_ARCHIVE"
    echo "Run 'bash run.sh prefetch' on a machine with internet, copy the .tar here, then retry."
    exit 1
  fi
  echo "Loading images from $OFFLINE_IMAGES_ARCHIVE ..."
  docker load -i "$OFFLINE_IMAGES_ARCHIVE"
  echo "Starting services (no pull) ..."
  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" up -d --no-build
  echo "Services started. Now run: bash run.sh init"
}

# Back up the Frappe site database and files into ./backups/
# Safe to run while the stack is up. Creates a timestamped subdirectory.
# Usage: bash run.sh backup
function backup_site() {
  mkdir -p "$BACKUP_DIR"
  TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
  DEST="$BACKUP_DIR/$TIMESTAMP"
  mkdir -p "$DEST"
  echo "Backing up site database ..."
  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" exec "$FRAPPE_SERVICE" \
    bench --site "$FRAPPE_SITE" backup --with-files
  echo "Copying backup files to $DEST ..."
  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" cp \
    "$FRAPPE_SERVICE:/home/frappe/frappe-bench/sites/$FRAPPE_SITE/private/backups/." \
    "$DEST/"
  echo "Backup complete: $DEST"
  ls -lh "$DEST"
}

# Restore from the most recent backup (or specify a directory as $2).
# Usage: bash run.sh restore [optional: path/to/backup/dir]
function restore_site() {
  RESTORE_DIR="${2:-$(ls -dt "$BACKUP_DIR"/*/  2>/dev/null | head -1)}"
  if [ -z "$RESTORE_DIR" ] || [ ! -d "$RESTORE_DIR" ]; then
    echo "ERROR: no backup directory found. Usage: bash run.sh restore [backup-dir]"
    exit 1
  fi
  echo "Restoring from $RESTORE_DIR ..."
  # Copy backup files into the container
  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" cp \
    "$RESTORE_DIR/." \
    "$FRAPPE_SERVICE:/home/frappe/frappe-bench/sites/$FRAPPE_SITE/private/backups/"
  # Identify the SQL file and restore
  SQL_FILE=$(ls "$RESTORE_DIR"/*.sql.gz 2>/dev/null | head -1)
  if [ -z "$SQL_FILE" ]; then
    echo "ERROR: no .sql.gz file found in $RESTORE_DIR"
    exit 1
  fi
  SQL_BASENAME=$(basename "$SQL_FILE")
  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" exec "$FRAPPE_SERVICE" \
    bench --site "$FRAPPE_SITE" restore \
    "/home/frappe/frappe-bench/sites/$FRAPPE_SITE/private/backups/$SQL_BASENAME"
  echo "Restore complete."
}

# Print running container health status — useful after a power cut.
# Usage: bash run.sh status
function show_status() {
  echo "=== Container status ==="
  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" ps
  echo ""
  echo "=== Recent logs (last 20 lines per service) ==="
  $COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" logs --tail=20
}

case "$1" in
  up)           start_services ;;
  down)         stop_services ;;
  logs)         stream_service_logs ;;
  shell)        open_frappe_shell ;;
  init)         initialize_frappe_site ;;
  reset)        reset_and_rebuild ;;
  prefetch)     prefetch_images ;;
  offline-init) offline_init ;;
  backup)       backup_site ;;
  restore)      restore_site "$@" ;;
  bench)        shift; run_bench_command "$@" ;;
  status)       show_status ;;
  *)
    echo "Usage: $0 {up|down|logs|shell|bench|init|reset|prefetch|offline-init|backup|restore|status}"
    echo ""
    echo "  Standard:"
    echo "    up            Start the Docker Compose stack"
    echo "    down          Stop the stack"
    echo "    logs          Stream logs from all services"
    echo "    shell         Open a bash shell inside the frappe container"
    echo "    bench         Run bench commands (e.g., bench migrate)"
    echo "    init          Create Frappe site and install apps (run after 'up')"
    echo "    reset         Wipe all volumes and rebuild from scratch"
    echo ""
    echo "  Yemen offline / resilience:"
    echo "    prefetch      Pull + save all images to an archive (run with internet)"
    echo "    offline-init  Load images from archive + start (no internet needed)"
    echo "    backup        Backup Frappe site database and files to ./backups/"
    echo "    restore       Restore from the latest backup (or: restore <path>)"
    echo "    status        Show container health + recent logs (post-power-cut check)"
    ;;
esac
