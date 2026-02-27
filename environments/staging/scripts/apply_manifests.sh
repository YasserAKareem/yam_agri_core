#!/usr/bin/env bash
set -euo pipefail

DRY_RUN_MODE="${DRY_RUN_MODE:-none}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

files=(
  "manifests/namespace.yaml"
  "manifests/pvc.yaml"
  "manifests/configmap.yaml"
  "manifests/secrets.generated.yaml"
  "manifests/mariadb.yaml"
  "manifests/redis.yaml"
  "manifests/frappe.yaml"
  "manifests/nginx.yaml"
  "manifests/gateways.yaml"
  "manifests/ingress.yaml"
)

for rel in "${files[@]}"; do
  abs="$ROOT_DIR/$rel"
  if [[ ! -f "$abs" ]]; then
    echo "[ERROR] Missing required manifest: $rel"
    exit 1
  fi

done

for rel in "${files[@]}"; do
  abs="$ROOT_DIR/$rel"
  echo "[APPLY] $rel"
  if [[ "$DRY_RUN_MODE" == "client" ]]; then
    kubectl apply --dry-run=client -f "$abs"
  else
    kubectl apply -f "$abs"
  fi
done

echo "[OK] Applied manifests in Phase 8 documented order"
