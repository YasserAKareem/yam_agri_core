# Staging (Phase 8) Kickoff

This directory is the execution baseline for WBS Phase 8 (k3s staging).

## WBS coverage in this kickoff

- 8.1: k3s single-node structure and namespace/persistent storage manifests.
- 8.2: VPN-restricted access runbook steps and explicit preflight gate.
- 8.3: modular Kubernetes manifests and secret-generation workflow (no plaintext secrets in git).
- 8.4: data migration command runbook (backup/restore + fixtures).
- 8.5: acceptance command runner for AT-01 through AT-10.

## Layout

- `config.yaml`: non-secret staging config contract.
- `.env.example`: operator-provided secrets/overrides template.
- `manifests/`: modular k3s manifests.
- `scripts/preflight.sh`: validates local tooling and `.env` readiness.
- `scripts/generate-secrets.sh`: generates `manifests/secrets.generated.yaml` from `.env`.
- `scripts/phase8_acceptance.sh`: runs AT-01..AT-10 using bench execute commands.

## Quickstart (operator)

1. Copy template and set values:

```bash
cd environments/staging
cp .env.example .env
# edit .env with strong passwords and staging host values
```

2. Run preflight and generate secrets:

```bash
./scripts/preflight.sh .env
./scripts/generate-secrets.sh .env manifests/secrets.generated.yaml
```

3. Apply manifests on staging server (via WireGuard VPN):

```bash
kubectl apply -f manifests/namespace.yaml
kubectl apply -f manifests/pvc.yaml
kubectl apply -f manifests/configmap.yaml
kubectl apply -f manifests/secrets.generated.yaml
kubectl apply -f manifests/mariadb.yaml
kubectl apply -f manifests/redis.yaml
kubectl apply -f manifests/frappe.yaml
kubectl apply -f manifests/nginx.yaml
kubectl apply -f manifests/gateways.yaml
kubectl apply -f manifests/ingress.yaml
```

4. Execute acceptance bundle on staging bench node:

```bash
./scripts/phase8_acceptance.sh localhost
```

## Notes

- The legacy `k3s-manifest.yaml` is retained for historical reference only.
- `gateways.yaml` starts with `replicas: 0` by default; enable after publishing/pinning images.
