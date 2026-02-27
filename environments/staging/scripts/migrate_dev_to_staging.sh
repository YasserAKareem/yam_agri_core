#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $0

Environment variables:
  MODE=backup-only|full             Execution mode (default: backup-only)
  DEV_CONTAINER=docker-backend-1    Dev backend container name
  DEV_BENCH=/home/frappe/frappe-bench
  DEV_SITE=localhost
  ARTIFACT_ROOT=artifacts/evidence/phase8/migration

  STAGING_TARGET=user@host          Required for MODE=full
  STAGING_BENCH=/home/frappe/frappe-bench
  STAGING_SITE=yam-staging.vpn.internal
  RUN_FIXTURE_SYNC=1                Run bench migrate after restore
USAGE
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  usage
  exit 0
fi

MODE="${MODE:-backup-only}"
DEV_CONTAINER="${DEV_CONTAINER:-docker-backend-1}"
DEV_BENCH="${DEV_BENCH:-/home/frappe/frappe-bench}"
DEV_SITE="${DEV_SITE:-localhost}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAGING_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$STAGING_DIR/../.." && pwd)"
ARTIFACT_ROOT="${ARTIFACT_ROOT:-$REPO_ROOT/artifacts/evidence/phase8/migration}"
STAGING_TARGET="${STAGING_TARGET:-}"
STAGING_BENCH="${STAGING_BENCH:-/home/frappe/frappe-bench}"
STAGING_SITE="${STAGING_SITE:-yam-staging.vpn.internal}"
RUN_FIXTURE_SYNC="${RUN_FIXTURE_SYNC:-1}"

if [[ "$MODE" != "backup-only" && "$MODE" != "full" ]]; then
  echo "[ERROR] Unsupported MODE=$MODE"
  usage
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "[ERROR] docker is required"
  exit 1
fi

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
out_dir="$ARTIFACT_ROOT/$timestamp"
mkdir -p "$out_dir"

echo "[INFO] Creating dev backup for site=$DEV_SITE in container=$DEV_CONTAINER"
docker exec "$DEV_CONTAINER" bash -lc "cd '$DEV_BENCH' && bench --site '$DEV_SITE' backup --with-files"

declare -A patterns
patterns[database]="*-${DEV_SITE}-database.sql.gz"
patterns[site_config]="*-${DEV_SITE}-site_config_backup.json"
patterns[private_files]="*-${DEV_SITE}-private-files.tar"
patterns[public_files]="*-${DEV_SITE}-files.tar"

declare -A picked
for key in "${!patterns[@]}"; do
  pattern="${patterns[$key]}"
  path="$(docker exec "$DEV_CONTAINER" bash -lc "cd '$DEV_BENCH' && ls -1t sites/'$DEV_SITE'/private/backups/${pattern} 2>/dev/null | head -n1" | tr -d '\r')"
  if [[ -n "$path" ]]; then
    picked[$key]="$path"
    docker cp "$DEV_CONTAINER:$DEV_BENCH/$path" "$out_dir/"
  fi
done

manifest_path="$out_dir/manifest.json"
python3 - <<'PY' "$manifest_path" "$MODE" "$DEV_SITE" "$DEV_CONTAINER" "$timestamp" \
  "${picked[database]:-}" "${picked[site_config]:-}" "${picked[private_files]:-}" "${picked[public_files]:-}"
import json
import os
import sys
manifest_path, mode, dev_site, dev_container, timestamp, db_file, site_cfg, private_files, public_files = sys.argv[1:]
payload = {
    "mode": mode,
    "timestamp": timestamp,
    "dev": {
        "site": dev_site,
        "container": dev_container,
    },
    "files": {
        "database": os.path.basename(db_file) if db_file else "",
        "site_config": os.path.basename(site_cfg) if site_cfg else "",
        "private_files": os.path.basename(private_files) if private_files else "",
        "public_files": os.path.basename(public_files) if public_files else "",
    },
}
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=True, indent=2)
print(manifest_path)
PY

if [[ "$MODE" == "backup-only" ]]; then
  echo "[OK] Backup-only mode complete"
  echo "[OK] Backup artifacts: $out_dir"
  exit 0
fi

if [[ -z "$STAGING_TARGET" ]]; then
  echo "[ERROR] STAGING_TARGET is required for MODE=full"
  exit 1
fi

if [[ -z "${picked[database]:-}" ]]; then
  echo "[ERROR] Database backup file not found; cannot continue"
  exit 1
fi

remote_dir="/tmp/yam-phase8-restore-$timestamp"
ssh "$STAGING_TARGET" "mkdir -p '$remote_dir'"
scp "$out_dir"/* "$STAGING_TARGET:$remote_dir/"

db_file="$(basename "${picked[database]}")"
private_files="$(basename "${picked[private_files]:-}")"
public_files="$(basename "${picked[public_files]:-}")"

restore_cmd="cd '$STAGING_BENCH' && bench --site '$STAGING_SITE' restore '$remote_dir/$db_file' --force"
if [[ -n "$private_files" ]]; then
  restore_cmd+=" --with-private-files '$remote_dir/$private_files'"
fi
if [[ -n "$public_files" ]]; then
  restore_cmd+=" --with-public-files '$remote_dir/$public_files'"
fi

ssh "$STAGING_TARGET" "$restore_cmd"

if [[ "$RUN_FIXTURE_SYNC" == "1" ]]; then
  ssh "$STAGING_TARGET" "cd '$STAGING_BENCH' && bench --site '$STAGING_SITE' migrate"
fi

echo "[OK] Full migration workflow completed for staging site=$STAGING_SITE"
