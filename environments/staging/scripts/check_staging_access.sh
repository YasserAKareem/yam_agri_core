#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $0 [staging_host] [ssh_user]

Environment variables:
  SSH_PORT=22
  CONNECT_TIMEOUT=8
  STAGING_HOST_IP=10.88.0.1      Optional direct IP fallback when DNS is unavailable
  SSH_HOST_OVERRIDE=1.2.3.4       Optional SSH target host/IP override
  WG_AUTO_UP=0                    Bring up WireGuard via wg-quick before checks
  WG_CONFIG=devops.conf           WireGuard config name/path for WG_AUTO_UP=1
  WG_USE_SUDO=1                   Use sudo when invoking wg-quick
  PING_CHECK=0                    Run ICMP ping check before SSH test
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
STAGING_HOST_IP="${STAGING_HOST_IP:-}"
SSH_HOST_OVERRIDE="${SSH_HOST_OVERRIDE:-}"
WG_AUTO_UP="${WG_AUTO_UP:-0}"
WG_CONFIG="${WG_CONFIG:-}"
WG_USE_SUDO="${WG_USE_SUDO:-1}"
PING_CHECK="${PING_CHECK:-0}"

echo "[INFO] Checking staging access prerequisites"
echo "[INFO] host=$STAGING_HOST ssh_user=$SSH_USER ssh_port=$SSH_PORT"

if [[ "$WG_AUTO_UP" == "1" ]]; then
  if [[ -z "$WG_CONFIG" ]]; then
    echo "[ERROR] WG_AUTO_UP=1 requires WG_CONFIG to be set"
    exit 4
  fi
  if ! command -v wg >/dev/null 2>&1 || ! command -v wg-quick >/dev/null 2>&1; then
    echo "[ERROR] WireGuard tools missing (wg/wg-quick). Install wireguard-tools first."
    exit 4
  fi
  if [[ -z "$(wg show interfaces 2>/dev/null || true)" ]]; then
    echo "[INFO] Bringing up WireGuard: $WG_CONFIG"
    if [[ "$WG_USE_SUDO" == "1" ]]; then
      sudo wg-quick up "$WG_CONFIG"
    else
      wg-quick up "$WG_CONFIG"
    fi
  fi
fi

if command -v wg >/dev/null 2>&1; then
  wg_interfaces="$(wg show interfaces 2>/dev/null || true)"
  if [[ -n "$wg_interfaces" ]]; then
    echo "[OK] WireGuard active interface(s): $wg_interfaces"
  else
    echo "[WARN] WireGuard installed but no active interface"
  fi
else
  echo "[WARN] WireGuard tools are not installed (wg missing)"
fi

ssh_connect_host="$STAGING_HOST"
if getent hosts "$STAGING_HOST" >/dev/null 2>&1; then
  echo "[OK] DNS resolved: $(getent hosts "$STAGING_HOST" | head -n1)"
elif [[ -n "$STAGING_HOST_IP" ]]; then
  ssh_connect_host="$STAGING_HOST_IP"
  echo "[WARN] DNS unresolved for $STAGING_HOST, using STAGING_HOST_IP=$STAGING_HOST_IP"
elif [[ -n "$SSH_HOST_OVERRIDE" ]]; then
  ssh_connect_host="$SSH_HOST_OVERRIDE"
  echo "[WARN] DNS unresolved for $STAGING_HOST, using SSH_HOST_OVERRIDE=$SSH_HOST_OVERRIDE"
else
  echo "[ERROR] Cannot resolve staging host: $STAGING_HOST"
  exit 2
fi

if [[ -n "$SSH_HOST_OVERRIDE" ]]; then
  ssh_connect_host="$SSH_HOST_OVERRIDE"
fi

if [[ "$PING_CHECK" == "1" ]]; then
  if ping -c 1 -W "$CONNECT_TIMEOUT" "$ssh_connect_host" >/dev/null 2>&1; then
    echo "[OK] Ping succeeded: $ssh_connect_host"
  else
    echo "[WARN] Ping failed: $ssh_connect_host (continuing to SSH check)"
  fi
fi

if ssh -p "$SSH_PORT" -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout="$CONNECT_TIMEOUT" "$SSH_USER@$ssh_connect_host" "echo connected" >/dev/null 2>&1; then
  echo "[OK] SSH connectivity and auth succeeded"
else
  echo "[ERROR] SSH connectivity/auth failed for $SSH_USER@$ssh_connect_host"
  exit 3
fi

echo "[OK] Staging access check passed"
