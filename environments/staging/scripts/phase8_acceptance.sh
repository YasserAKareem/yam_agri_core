#!/usr/bin/env bash
set -euo pipefail

SITE_NAME="${1:-localhost}"
REPORT_DIR="${2:-artifacts/phase8}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT_FILE="$REPORT_DIR/acceptance_$TIMESTAMP.jsonl"

mkdir -p "$REPORT_DIR"

methods=(
  "yam_agri_core.yam_agri_core.health.checks.run_at01_automated_check"
  "yam_agri_core.yam_agri_core.health.checks.run_at02_automated_check"
  "yam_agri_core.yam_agri_core.health.checks.run_at03_automated_check"
  "yam_agri_core.yam_agri_core.health.checks.run_at04_automated_check"
  "yam_agri_core.yam_agri_core.health.checks.run_at05_automated_check"
  "yam_agri_core.yam_agri_core.health.checks.run_at06_automated_check"
  "yam_agri_core.yam_agri_core.health.checks.run_at07_automated_check"
  "yam_agri_core.yam_agri_core.health.checks.run_at08_automated_check"
  "yam_agri_core.yam_agri_core.health.checks.run_at09_automated_check"
  "yam_agri_core.yam_agri_core.health.checks.run_at10_automated_check"
)

pass_count=0
fail_count=0
blocked_count=0
error_count=0

echo "[INFO] Running Phase 8 acceptance checks on site: $SITE_NAME"
echo "[INFO] Report file: $REPORT_FILE"

for method in "${methods[@]}"; do
  echo "[RUN] $method"
  output=""
  rc=0
  if ! output="$(bench --site "$SITE_NAME" execute "$method" 2>&1)"; then
    rc=$?
  fi

  status="error"
  if [[ $rc -eq 0 ]]; then
    status="$(python3 - <<'PY' "$output"
import json
import re
import sys
text = sys.argv[1]
status = "error"
for line in reversed(text.splitlines()):
    line = line.strip()
    if not line:
        continue
    if not line.startswith("{"):
        continue
    try:
        payload = json.loads(line)
    except Exception:
        continue
    status = str(payload.get("status") or "error").strip().lower() or "error"
    break
print(status)
PY
)"
  fi

  case "$status" in
    pass)
      pass_count=$((pass_count + 1))
      ;;
    fail)
      fail_count=$((fail_count + 1))
      ;;
    blocked)
      blocked_count=$((blocked_count + 1))
      ;;
    *)
      error_count=$((error_count + 1))
      ;;
  esac

  python3 - <<'PY' "$method" "$status" "$output" >> "$REPORT_FILE"
import json
import sys
method, status, output = sys.argv[1], sys.argv[2], sys.argv[3]
print(json.dumps({"method": method, "status": status, "raw": output}, ensure_ascii=True))
PY

  echo "[RESULT] $method => $status"
done

echo "[SUMMARY] pass=$pass_count fail=$fail_count blocked=$blocked_count error=$error_count"

if [[ $fail_count -gt 0 || $blocked_count -gt 0 || $error_count -gt 0 ]]; then
  echo "[FAIL] Phase 8 acceptance bundle did not pass"
  exit 1
fi

echo "[OK] All 10 acceptance checks passed"
