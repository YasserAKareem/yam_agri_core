#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

REPORT_FILE="phase01_acceptance_report.json"
START_TS="$(date +%s)"

SITE_NAME_VALUE="${SITE_NAME:-localhost}"
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  set -a; source .env; set +a
  SITE_NAME_VALUE="${SITE_NAME:-$SITE_NAME_VALUE}"
fi

HTTP_URL="${PHASE01_URL:-http://localhost:${HTTP_PUBLISH_PORT:-8000}/login}"

PASS_STACK_UP=false
PASS_LOGIN=false
PASS_RESTART=false
PASS_SITE_INIT=false
PASS_APP_INSTALL=false
PASS_BUILD=false

function wait_for_login() {
  local timeout="${1:-180}"
  local elapsed=0
  while [[ "$elapsed" -lt "$timeout" ]]; do
    if curl -fsS "$HTTP_URL" | grep -qi "login"; then
      return 0
    fi
    sleep 3
    elapsed=$((elapsed + 3))
  done
  return 1
}

function set_pass() {
  local var_name="$1"
  eval "$var_name=true"
}

echo "[Phase 0/1] Running preflight..."
bash preflight.sh

echo "[Phase 0/1] Bringing stack up..."
bash run.sh up

if wait_for_login 300; then
  set_pass PASS_LOGIN
fi

UP_ELAPSED=$(( $(date +%s) - START_TS ))
if [[ "$UP_ELAPSED" -le 300 ]]; then
  set_pass PASS_STACK_UP
fi

echo "[Phase 0/1] Validating site and app installation..."
if bash run.sh bench --site "$SITE_NAME_VALUE" list-apps >/tmp/phase01_apps.txt 2>/tmp/phase01_apps.err; then
  set_pass PASS_SITE_INIT
else
  echo "Site not ready, attempting init..."
  if bash run.sh init; then
    set_pass PASS_SITE_INIT
    bash run.sh bench --site "$SITE_NAME_VALUE" list-apps >/tmp/phase01_apps.txt 2>/tmp/phase01_apps.err || true
  fi
fi

if grep -q "erpnext" /tmp/phase01_apps.txt && grep -q "yam_agri_core" /tmp/phase01_apps.txt; then
  set_pass PASS_APP_INSTALL
fi

echo "[Phase 1] Running bench build smoke..."
if bash run.sh bench build >/tmp/phase01_build.txt 2>/tmp/phase01_build.err; then
  set_pass PASS_BUILD
fi

echo "[Phase 0] Restart verification..."
bash run.sh down
bash run.sh up
if wait_for_login 240; then
  set_pass PASS_RESTART
fi

END_TS="$(date +%s)"
TOTAL_ELAPSED=$(( END_TS - START_TS ))

OVERALL=true
for flag in PASS_STACK_UP PASS_LOGIN PASS_RESTART PASS_SITE_INIT PASS_APP_INSTALL PASS_BUILD; do
  if [[ "${!flag}" != "true" ]]; then
    OVERALL=false
  fi
done

cat > "$REPORT_FILE" <<JSON
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "site": "${SITE_NAME_VALUE}",
  "url": "${HTTP_URL}",
  "elapsed_seconds": ${TOTAL_ELAPSED},
  "checks": {
    "stack_up_under_5_min": ${PASS_STACK_UP},
    "login_works": ${PASS_LOGIN},
    "restart_works": ${PASS_RESTART},
    "site_creation_or_exists": ${PASS_SITE_INIT},
    "app_install_check": ${PASS_APP_INSTALL},
    "bench_build_smoke": ${PASS_BUILD}
  },
  "overall_pass": ${OVERALL}
}
JSON

echo "Report written: $SCRIPT_DIR/$REPORT_FILE"
cat "$REPORT_FILE"

if [[ "$OVERALL" != "true" ]]; then
  echo "Phase 0/1 acceptance failed. See $REPORT_FILE and /tmp/phase01_*.err"
  exit 1
fi

echo "Phase 0/1 acceptance passed."
