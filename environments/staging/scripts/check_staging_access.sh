#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $0 [staging_host] [ssh_user]

Environment variables:
  SSH_PORT=22
  CONNECT_TIMEOUT=8
USAGE
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  usage
  exit 0
fi

STAGING_HOST="${1:-yam-staging.vpn.internal}"
SSH_USER="${2:-ubuntu}"
SSH_PORT="${SSH_PORT:-22}"
CONNECT_TIMEOUT="${CONNECT_TIMEOUT:-8}"

echo "[INFO] Checking staging access prerequisites"
echo "[INFO] host=$STAGING_HOST ssh_user=$SSH_USER ssh_port=$SSH_PORT"

if command -v wg >/dev/null 2>&1; then
  if wg show >/dev/null 2>&1; then
    echo "[OK] WireGuard appears active"
  else
    echo "[WARN] WireGuard installed but no active interface"
  fi
else
  echo "[WARN] WireGuard tools are not installed (wg missing)"
fi

if getent hosts "$STAGING_HOST" >/dev/null 2>&1; then
  echo "[OK] DNS resolved: $(getent hosts "$STAGING_HOST" | head -n1)"
else
  echo "[ERROR] Cannot resolve staging host: $STAGING_HOST"
  exit 2
fi

if ssh -p "$SSH_PORT" -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout="$CONNECT_TIMEOUT" "$SSH_USER@$STAGING_HOST" "echo connected" >/dev/null 2>&1; then
  echo "[OK] SSH connectivity and auth succeeded"
else
  echo "[ERROR] SSH connectivity/auth failed for $SSH_USER@$STAGING_HOST"
  exit 3
fi

echo "[OK] Staging access check passed"
