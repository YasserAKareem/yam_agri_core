#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-.env}"
OUT_FILE="${2:-manifests/secrets.generated.yaml}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[ERROR] Missing env file: $ENV_FILE"
  exit 1
fi

if ! command -v kubectl >/dev/null 2>&1; then
  echo "[ERROR] kubectl is required"
  exit 1
fi

# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a

: "${K8S_NAMESPACE:?K8S_NAMESPACE is required}"
: "${DB_ROOT_PASSWORD:?DB_ROOT_PASSWORD is required}"
: "${DB_PASSWORD:?DB_PASSWORD is required}"
: "${ADMIN_PASSWORD:?ADMIN_PASSWORD is required}"

mkdir -p "$(dirname "$OUT_FILE")"

kubectl -n "$K8S_NAMESPACE" create secret generic yam-agri-staging-secrets \
  --from-literal=db-root-password="$DB_ROOT_PASSWORD" \
  --from-literal=db-password="$DB_PASSWORD" \
  --from-literal=admin-password="$ADMIN_PASSWORD" \
  --dry-run=client -o yaml > "$OUT_FILE"

chmod 600 "$OUT_FILE"

echo "[OK] Generated $OUT_FILE"
