#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $0 [staging_host] [ssh_user]

Purpose:
  Resolve staging connectivity blockers on operator workstation
  (WireGuard tools/session, DNS fallback, SSH reachability), then
  optionally execute the Phase 8 remote sequence.

Environment variables:
  STAGING_HOST_IP=10.88.0.1        Optional direct IP fallback for staging host
  SSH_HOST_OVERRIDE=1.2.3.4         Optional explicit SSH target host/IP
  WG_AUTO_INSTALL=0                 Install wireguard-tools when missing (apt-based distros)
  WG_AUTO_UP=0                      Bring up WireGuard tunnel before checks
  WG_CONFIG=devops.conf             WireGuard config name/path for WG_AUTO_UP=1
  WG_USE_SUDO=1                     Use sudo for install/wg-quick/hosts operations
  UPDATE_HOSTS=0                    Update /etc/hosts with STAGING_HOST_IP mapping

  RUN_SEQUENCE=0                    Execute remote sequence after access check passes
  SEQUENCE_DRY_RUN=0                DRY_RUN value for remote mutation scripts
  SEQUENCE_APPLY_WG_REMOTE=1        APPLY_REMOTE value for setup_wireguard.sh
  STAGING_SITE=yam-staging.vpn.internal
USAGE
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  usage
  exit 0
fi

STAGING_HOST="${1:-yam-staging.vpn.internal}"
SSH_USER="${2:-ubuntu}"

STAGING_HOST_IP="${STAGING_HOST_IP:-}"
SSH_HOST_OVERRIDE="${SSH_HOST_OVERRIDE:-}"
WG_AUTO_INSTALL="${WG_AUTO_INSTALL:-0}"
WG_AUTO_UP="${WG_AUTO_UP:-0}"
WG_CONFIG="${WG_CONFIG:-}"
WG_USE_SUDO="${WG_USE_SUDO:-1}"
UPDATE_HOSTS="${UPDATE_HOSTS:-0}"

RUN_SEQUENCE="${RUN_SEQUENCE:-0}"
SEQUENCE_DRY_RUN="${SEQUENCE_DRY_RUN:-0}"
SEQUENCE_APPLY_WG_REMOTE="${SEQUENCE_APPLY_WG_REMOTE:-1}"
STAGING_SITE="${STAGING_SITE:-yam-staging.vpn.internal}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAGING_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

run_with_optional_sudo() {
  if [[ "$WG_USE_SUDO" == "1" ]]; then
    sudo "$@"
  else
    "$@"
  fi
}

update_hosts_entry() {
  local host ip tmp_hosts
  host="$1"
  ip="$2"

  if [[ -z "$ip" ]]; then
    echo "[ERROR] UPDATE_HOSTS=1 requires STAGING_HOST_IP"
    exit 1
  fi

  tmp_hosts="$(mktemp)"
  awk -v target_host="$host" '
    BEGIN { FS="[ \t]+" }
    {
      keep = 1
      if ($0 !~ /^[[:space:]]*#/) {
        for (i = 2; i <= NF; i++) {
          if ($i == target_host) {
            keep = 0
            break
          }
        }
      }
      if (keep) print $0
    }
  ' /etc/hosts > "$tmp_hosts"

  printf "%s %s # yam-agri-staging\n" "$ip" "$host" >> "$tmp_hosts"
  run_with_optional_sudo cp "$tmp_hosts" /etc/hosts
  rm -f "$tmp_hosts"
  echo "[OK] Updated /etc/hosts: $host -> $ip"
}

echo "[INFO] Unblocking staging access for host=$STAGING_HOST user=$SSH_USER"

if [[ "$WG_AUTO_INSTALL" == "1" ]] && ! command -v wg >/dev/null 2>&1; then
  if ! command -v apt-get >/dev/null 2>&1; then
    echo "[ERROR] WG_AUTO_INSTALL is supported only on apt-based systems"
    exit 1
  fi
  echo "[INFO] Installing wireguard-tools"
  run_with_optional_sudo apt-get update
  run_with_optional_sudo apt-get install -y wireguard-tools
fi

if [[ "$UPDATE_HOSTS" == "1" ]]; then
  update_hosts_entry "$STAGING_HOST" "$STAGING_HOST_IP"
fi

STAGING_HOST_IP="$STAGING_HOST_IP" \
SSH_HOST_OVERRIDE="$SSH_HOST_OVERRIDE" \
WG_AUTO_UP="$WG_AUTO_UP" \
WG_CONFIG="$WG_CONFIG" \
WG_USE_SUDO="$WG_USE_SUDO" \
"$SCRIPT_DIR/check_staging_access.sh" "$STAGING_HOST" "$SSH_USER"

if [[ "$RUN_SEQUENCE" != "1" ]]; then
  echo "[INFO] Access gate passed. RUN_SEQUENCE=0, stopping before remote mutations."
  echo "[NEXT] From $STAGING_DIR run:"
  echo "       ./provision_k3s.sh $STAGING_HOST $SSH_USER"
  echo "       ./setup_wireguard.sh $STAGING_HOST $SSH_USER"
  echo "       ./restrict_k3s_api.sh $STAGING_HOST $SSH_USER"
  echo "       ./apply_manifests.sh"
  echo "       ./migrate_dev_to_staging.sh"
  echo "       ./phase8_acceptance.sh $STAGING_SITE"
  exit 0
fi

echo "[INFO] Running Phase 8 remote sequence"

SSH_HOST_OVERRIDE="$SSH_HOST_OVERRIDE" \
DRY_RUN="$SEQUENCE_DRY_RUN" \
"$SCRIPT_DIR/provision_k3s.sh" "$STAGING_HOST" "$SSH_USER"

SSH_HOST_OVERRIDE="$SSH_HOST_OVERRIDE" \
DRY_RUN="$SEQUENCE_DRY_RUN" \
APPLY_REMOTE="$SEQUENCE_APPLY_WG_REMOTE" \
"$SCRIPT_DIR/setup_wireguard.sh" "$STAGING_HOST" "$SSH_USER"

SSH_HOST_OVERRIDE="$SSH_HOST_OVERRIDE" \
DRY_RUN="$SEQUENCE_DRY_RUN" \
"$SCRIPT_DIR/restrict_k3s_api.sh" "$STAGING_HOST" "$SSH_USER"

DRY_RUN_MODE="${DRY_RUN_MODE:-apply}" "$SCRIPT_DIR/apply_manifests.sh"
"$SCRIPT_DIR/migrate_dev_to_staging.sh"
"$SCRIPT_DIR/phase8_acceptance.sh" "$STAGING_SITE"

echo "[OK] Phase 8 remote sequence completed"
