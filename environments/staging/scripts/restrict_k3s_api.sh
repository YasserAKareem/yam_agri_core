#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $0 <staging_host> [ssh_user]

Environment variables:
  DRY_RUN=1                 Print remote commands only (default: 1)
  SSH_PORT=22               SSH port
  VPN_SUBNET=10.88.0.0/24   Allowed VPN subnet for k3s API (6443/tcp)
  SSH_ALLOW=0.0.0.0/0       Allowed source for SSH (set to VPN subnet if desired)
USAGE
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

STAGING_HOST="$1"
SSH_USER="${2:-ubuntu}"
SSH_PORT="${SSH_PORT:-22}"
DRY_RUN="${DRY_RUN:-1}"
VPN_SUBNET="${VPN_SUBNET:-10.88.0.0/24}"
SSH_ALLOW="${SSH_ALLOW:-0.0.0.0/0}"
SSH_TARGET="${SSH_USER}@${STAGING_HOST}"

REMOTE_SCRIPT="$(cat <<SCRIPT
set -euo pipefail
if ! command -v ufw >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y ufw
fi
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from ${SSH_ALLOW} to any port ${SSH_PORT} proto tcp
sudo ufw allow from ${VPN_SUBNET} to any port 6443 proto tcp
sudo ufw deny 6443/tcp
sudo ufw --force enable
sudo ufw status verbose
SCRIPT
)"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "[DRY-RUN] Would apply k3s API firewall restriction on $SSH_TARGET"
  echo "$REMOTE_SCRIPT"
  exit 0
fi

ssh -p "$SSH_PORT" -o BatchMode=yes -o StrictHostKeyChecking=accept-new "$SSH_TARGET" "bash -s" <<<"$REMOTE_SCRIPT"

echo "[OK] k3s API restriction applied on $SSH_TARGET"
