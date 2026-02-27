#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[ERROR] Missing env file: $ENV_FILE"
  echo "        Copy .env.example to .env and fill required values."
  exit 1
fi

for cmd in kubectl awk sed grep; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "[ERROR] Missing required command: $cmd"
    exit 1
  fi
done

# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a

required_vars=(
  K8S_NAMESPACE
  SITE_NAME
  INGRESS_HOST
  INSTALL_APPS
  DB_NAME
  DB_USER
  DB_ROOT_PASSWORD
  DB_PASSWORD
  ADMIN_PASSWORD
)

for var_name in "${required_vars[@]}"; do
  value="${!var_name:-}"
  if [[ -z "$value" ]]; then
    echo "[ERROR] $var_name is empty"
    exit 1
  fi
  if [[ "$value" == REPLACE_* || "$value" == *CHANGE_ME* ]]; then
    echo "[ERROR] $var_name still has placeholder value"
    exit 1
  fi
done

if git ls-files --error-unmatch environments/staging/manifests/secrets.generated.yaml >/dev/null 2>&1; then
  echo "[ERROR] secrets.generated.yaml is tracked by git; this must remain untracked"
  exit 1
fi

echo "[OK] Phase 8 preflight passed for $ENV_FILE"
