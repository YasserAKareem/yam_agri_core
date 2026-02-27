#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $0 [staging_host] [ssh_user]

Environment variables:
  DRY_RUN=1                        Print actions only (default: 1)
  SSH_PORT=22                      SSH port for remote apply
  SSH_HOST_OVERRIDE=1.2.3.4        Optional SSH target host/IP override
  CONNECT_TIMEOUT=8                SSH connect timeout in seconds
  WG_INTERFACE=wg0                 WireGuard interface name
  WG_SUBNET=10.88.0.0/24           WireGuard subnet
  WG_SERVER_IP=10.88.0.1/24        Server tunnel address
  WG_LISTEN_PORT=51820             WireGuard UDP port
  WG_ENDPOINT=staging.example.com  Public endpoint for peer configs
  WG_PEERS="devops,10.88.0.2 qa,10.88.0.3"
                                   Space-separated peer definitions: <name>,<ip>
  OUT_DIR=environments/staging/wireguard/generated
  APPLY_REMOTE=0                   Apply generated server config to remote host
USAGE
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  usage
  exit 0
fi

STAGING_HOST="${1:-}"
SSH_USER="${2:-ubuntu}"
DRY_RUN="${DRY_RUN:-1}"
SSH_PORT="${SSH_PORT:-22}"
SSH_HOST_OVERRIDE="${SSH_HOST_OVERRIDE:-}"
CONNECT_TIMEOUT="${CONNECT_TIMEOUT:-8}"
WG_INTERFACE="${WG_INTERFACE:-wg0}"
WG_SUBNET="${WG_SUBNET:-10.88.0.0/24}"
WG_SERVER_IP="${WG_SERVER_IP:-10.88.0.1/24}"
WG_LISTEN_PORT="${WG_LISTEN_PORT:-51820}"
WG_ENDPOINT="${WG_ENDPOINT:-staging.example.com}"
WG_PEERS="${WG_PEERS:-devops,10.88.0.2 qa,10.88.0.3}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAGING_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT_DIR="${OUT_DIR:-$STAGING_DIR/wireguard/generated}"
APPLY_REMOTE="${APPLY_REMOTE:-0}"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "[DRY-RUN] Would generate WireGuard configs in $OUT_DIR"
  echo "[DRY-RUN] Interface=$WG_INTERFACE Subnet=$WG_SUBNET ServerIP=$WG_SERVER_IP Port=$WG_LISTEN_PORT"
  echo "[DRY-RUN] Peers=$WG_PEERS"
  if [[ "$APPLY_REMOTE" == "1" ]]; then
    ssh_connect_host="${SSH_HOST_OVERRIDE:-$STAGING_HOST}"
    echo "[DRY-RUN] Would install /etc/wireguard/${WG_INTERFACE}.conf on ${SSH_USER}@${ssh_connect_host}:${SSH_PORT}"
    if [[ -n "$SSH_HOST_OVERRIDE" ]]; then
      echo "[DRY-RUN] SSH_HOST_OVERRIDE in use (staging_host=$STAGING_HOST connect_host=$ssh_connect_host)"
    fi
  fi
  exit 0
fi

if ! command -v wg >/dev/null 2>&1; then
  echo "[ERROR] wg command not found. Install wireguard-tools first."
  exit 1
fi

mkdir -p "$OUT_DIR"
server_private_key="$(wg genkey)"
server_public_key="$(printf '%s' "$server_private_key" | wg pubkey)"

server_conf="$OUT_DIR/${WG_INTERFACE}.server.conf"
{
  echo "[Interface]"
  echo "Address = ${WG_SERVER_IP}"
  echo "ListenPort = ${WG_LISTEN_PORT}"
  echo "PrivateKey = ${server_private_key}"
  echo
} > "$server_conf"

for peer_def in $WG_PEERS; do
  peer_name="${peer_def%%,*}"
  peer_ip="${peer_def##*,}"
  if [[ -z "$peer_name" || -z "$peer_ip" || "$peer_name" == "$peer_ip" ]]; then
    echo "[ERROR] Invalid peer definition: $peer_def"
    exit 1
  fi

  peer_private_key="$(wg genkey)"
  peer_public_key="$(printf '%s' "$peer_private_key" | wg pubkey)"
  psk="$(wg genpsk)"

  cat >> "$server_conf" <<PEER
[Peer]
PublicKey = ${peer_public_key}
PresharedKey = ${psk}
AllowedIPs = ${peer_ip}/32

PEER

  peer_conf="$OUT_DIR/${peer_name}.peer.conf"
  cat > "$peer_conf" <<PEERCONF
[Interface]
PrivateKey = ${peer_private_key}
Address = ${peer_ip}/32
DNS = ${WG_SERVER_IP%%/*}

[Peer]
PublicKey = ${server_public_key}
PresharedKey = ${psk}
Endpoint = ${WG_ENDPOINT}:${WG_LISTEN_PORT}
AllowedIPs = ${WG_SUBNET},10.42.0.0/16,10.43.0.0/16
PersistentKeepalive = 25
PEERCONF

done

chmod 600 "$OUT_DIR"/*.conf

echo "[OK] WireGuard configs generated in $OUT_DIR"

echo "[INFO] Server public key: $server_public_key"

if [[ "$APPLY_REMOTE" == "1" ]]; then
  if [[ -z "$STAGING_HOST" ]]; then
    echo "[ERROR] staging_host is required when APPLY_REMOTE=1"
    exit 1
  fi

  ssh_connect_host="${SSH_HOST_OVERRIDE:-$STAGING_HOST}"
  ssh_target="${SSH_USER}@${ssh_connect_host}"
  scp -P "$SSH_PORT" -o StrictHostKeyChecking=accept-new -o ConnectTimeout="$CONNECT_TIMEOUT" "$server_conf" "$ssh_target:/tmp/${WG_INTERFACE}.conf"
  ssh -p "$SSH_PORT" -o StrictHostKeyChecking=accept-new -o ConnectTimeout="$CONNECT_TIMEOUT" "$ssh_target" "sudo mkdir -p /etc/wireguard && sudo mv /tmp/${WG_INTERFACE}.conf /etc/wireguard/${WG_INTERFACE}.conf && sudo chmod 600 /etc/wireguard/${WG_INTERFACE}.conf && sudo systemctl enable --now wg-quick@${WG_INTERFACE} && sudo wg show ${WG_INTERFACE}"
  echo "[OK] Applied WireGuard server config on $ssh_target"
fi
