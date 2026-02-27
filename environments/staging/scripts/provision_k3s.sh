#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $0 <staging_host> [ssh_user]

Environment variables:
  DRY_RUN=1                  Print remote commands only (default: 1)
  SSH_PORT=22                SSH port
  K3S_VERSION=v1.30.6+k3s1   k3s version to install
  EXPORT_KUBECONFIG=0        Export kubeconfig to local file when set to 1
  KUBECONFIG_OUT=...         Local kubeconfig output path
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
K3S_VERSION="${K3S_VERSION:-v1.30.6+k3s1}"
DRY_RUN="${DRY_RUN:-1}"
EXPORT_KUBECONFIG="${EXPORT_KUBECONFIG:-0}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAGING_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$STAGING_DIR/../.." && pwd)"
KUBECONFIG_OUT="${KUBECONFIG_OUT:-$REPO_ROOT/artifacts/evidence/phase8/kubeconfig_staging.yaml}"
SSH_TARGET="${SSH_USER}@${STAGING_HOST}"

REMOTE_SCRIPT="$(cat <<SCRIPT
set -euo pipefail
if ! command -v curl >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y curl
fi
if ! command -v k3s >/dev/null 2>&1; then
  curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION='${K3S_VERSION}' INSTALL_K3S_EXEC='server --write-kubeconfig-mode 644' sh -
fi
sudo systemctl enable --now k3s
sudo kubectl get nodes -o wide
SCRIPT
)"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "[DRY-RUN] Would provision k3s on ${SSH_TARGET}:${SSH_PORT}"
  echo "[DRY-RUN] Remote script:"
  echo "${REMOTE_SCRIPT}"
  exit 0
fi

ssh -p "$SSH_PORT" -o BatchMode=yes -o StrictHostKeyChecking=accept-new "$SSH_TARGET" "bash -s" <<<"$REMOTE_SCRIPT"

if [[ "$EXPORT_KUBECONFIG" == "1" ]]; then
  mkdir -p "$(dirname "$KUBECONFIG_OUT")"
  ssh -p "$SSH_PORT" -o BatchMode=yes -o StrictHostKeyChecking=accept-new "$SSH_TARGET" "sudo cat /etc/rancher/k3s/k3s.yaml" > "$KUBECONFIG_OUT"
  chmod 600 "$KUBECONFIG_OUT"
  echo "[OK] Wrote kubeconfig to $KUBECONFIG_OUT"
fi

echo "[OK] k3s provisioning step completed on $SSH_TARGET"
