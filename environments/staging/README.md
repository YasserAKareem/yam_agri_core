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
- `scripts/provision_k3s.sh`: remote k3s installation/provisioning helper (8.1.1).
- `scripts/check_staging_access.sh`: validates VPN/DNS/SSH access to staging host.
- `scripts/unblock_staging_access.sh`: resolves common workstation blockers (missing wg tools/session, DNS fallback, hosts mapping).
- `scripts/setup_wireguard.sh`: WireGuard config generation/apply helper (8.2.1).
- `scripts/restrict_k3s_api.sh`: firewall rule helper to limit k3s API to VPN subnet (8.2.2).
- `scripts/preflight.sh`: validates local tooling and `.env` readiness.
- `scripts/generate-secrets.sh`: generates `manifests/secrets.generated.yaml` from `.env`.
- `scripts/apply_manifests.sh`: applies manifests in required WBS order.
- `scripts/migrate_dev_to_staging.sh`: backup/restore workflow and fixture-sync path (8.4).
- `scripts/phase8_acceptance.sh`: runs AT-01..AT-10 using bench execute commands.
- `*.sh` wrappers in this directory proxy to `scripts/*.sh` so commands work both with and without the `scripts/` prefix.

## Quickstart (operator)

1. Copy template and set values:

```bash
cd environments/staging
cp .env.example .env
# edit .env with strong passwords and staging host values
```

2. Validate staging host reachability:

```bash
./check_staging_access.sh <staging_host> <ssh_user>
```

2a. If WireGuard/DNS is currently blocked on your workstation, run unblock flow:

```bash
# example: bring up WG, set DNS fallback via host IP, then run access gate
WG_AUTO_UP=1 WG_CONFIG=<peer-config-or-name> \
STAGING_HOST_IP=<staging_vpn_ip_or_reachable_ip> UPDATE_HOSTS=1 \
./unblock_staging_access.sh <staging_host> <ssh_user>
```

3. Provision staging server and secure VPN/API path:

```bash
# 8.1.1: k3s install (dry-run first)
DRY_RUN=1 ./provision_k3s.sh <staging_host> <ssh_user>

# 8.2.1: WireGuard config generation (dry-run first)
DRY_RUN=1 WG_ENDPOINT=<public_host_or_ip> ./setup_wireguard.sh <staging_host> <ssh_user>

# 8.2.2: Restrict k3s API to VPN subnet (dry-run first)
DRY_RUN=1 VPN_SUBNET=10.88.0.0/24 ./restrict_k3s_api.sh <staging_host> <ssh_user>
```

4. Run preflight and generate secrets:

```bash
./preflight.sh .env
./generate-secrets.sh .env manifests/secrets.generated.yaml
```

5. Apply manifests on staging server (via WireGuard VPN):

```bash
# offline render validation
DRY_RUN_MODE=render ./apply_manifests.sh

# real apply on staging host
./apply_manifests.sh
```

6. Run dev -> staging migration (backup-only rehearsal then full):

```bash
# backup-only evidence run
MODE=backup-only ./migrate_dev_to_staging.sh

# full restore run (requires staging SSH)
MODE=full STAGING_TARGET=<user@host> STAGING_SITE=<staging_site> ./migrate_dev_to_staging.sh
```

7. Execute acceptance bundle on staging bench node:

```bash
./phase8_acceptance.sh localhost
```

## Notes

- The legacy `k3s-manifest.yaml` is retained for historical reference only.
- `gateways.yaml` starts with `replicas: 0` by default; enable after publishing/pinning images.
