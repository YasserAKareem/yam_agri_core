# Phase 8 Kickoff Plan (2026-02-27)

## 1) Goal

Start Phase 8 (Staging on k3s) execution against WBS 8.1-8.5 and prepare a repeatable path to M8:

- staging infrastructure deployed in `yam-agri-staging`,
- secrets managed via Kubernetes Secret generation workflow,
- dev data restored to staging,
- AT-01 through AT-10 executed on staging.

## 2) Entry gate confirmation

- Phase 7 completion commit: `16245c2` (`feat(phase7): deliver evidence pack generator and AT-09 acceptance`).
- Dev acceptance checks currently available through `yam_agri_core.yam_agri_core.health.checks.run_at01_automated_check` ... `run_at10_automated_check`.

## 3) WBS execution board

| WBS | Task | Status | Execution in this kickoff |
|-----|------|--------|---------------------------|
| 8.1 | k3s single-node setup | In progress | Added modular `manifests/` layout with namespace + PVC baseline. |
| 8.1.1 | Provision server and install k3s | In progress | Added `scripts/provision_k3s.sh` with dry-run + execution path. |
| 8.1.2 | Storage class + PVC | In progress | Added `manifests/pvc.yaml` with sites + MariaDB PVCs. |
| 8.2 | WireGuard VPN | Pending (ops) | Explicit gate in plan/runbooks: apply/deploy only via VPN path. |
| 8.2.1 | WireGuard config + peers | In progress | Added `scripts/setup_wireguard.sh` to generate/apply peer configs. |
| 8.2.2 | Restrict k3s API to VPN subnet | In progress | Added `scripts/restrict_k3s_api.sh` for remote firewall enforcement. |
| 8.3 | Kubernetes manifests / Helm | In progress | Replaced single-file staging draft with modular manifests + kustomization. |
| 8.3.1 | Chart/services parity | In progress | Added MariaDB, Redis x3, backend/frontend, workers, websocket, gateway stubs. |
| 8.3.2 | Secrets in k3s Secrets only | In progress | Added `.env.example`, preflight, and `generate-secrets.sh`; ignored generated secret file. |
| 8.4 | Data migration dev -> staging | In progress | Added `scripts/migrate_dev_to_staging.sh` with backup-only/full modes. |
| 8.4.1 | bench backup/restore | In progress | Automated in migration script and executed in backup-only evidence mode. |
| 8.4.2 | fixture import | In progress | `MODE=full` path includes post-restore `bench migrate` fixture sync. |
| 8.5 | Run all 10 AT on staging | In progress | Added `phase8_acceptance.sh` runner for AT-01..AT-10. |
| 8.5.1 | AT-01..AT-05 | In progress | Included in runner. |
| 8.5.2 | AT-06..AT-10 | In progress | Included in runner. |

## 4) Immediate execution sequence (operator)

1. `cd environments/staging`
2. `cp .env.example .env` and fill strong credentials.
3. `./scripts/preflight.sh .env`
4. `./scripts/generate-secrets.sh .env manifests/secrets.generated.yaml`
5. `DRY_RUN=1 ./scripts/provision_k3s.sh <staging_host> <ssh_user>`
6. `DRY_RUN=1 WG_ENDPOINT=<public_host_or_ip> ./scripts/setup_wireguard.sh <staging_host> <ssh_user>`
7. `DRY_RUN=1 VPN_SUBNET=10.88.0.0/24 ./scripts/restrict_k3s_api.sh <staging_host> <ssh_user>`
8. `./scripts/apply_manifests.sh`
9. `MODE=backup-only ./scripts/migrate_dev_to_staging.sh`
10. `MODE=full STAGING_TARGET=<user@host> STAGING_SITE=<staging_site> ./scripts/migrate_dev_to_staging.sh`
11. `./scripts/phase8_acceptance.sh <site_name>`

## 5) Known gaps to close in next execution slice

- Replace placeholder gateway image tags with pinned release images and set replicas from `0` to `1`.
- Validate k3s ingress TLS secret wiring (`yam-staging-tls`) and certificate source.
- Execute and evidence full 8.4 restore path on staging host (backup-only evidence is already captured).
- Capture AT-01..AT-10 staging evidence under `artifacts/phase8/` and update WBS milestone scripts.

## 6) Definition of done for Phase 8

- All WBS 8.1-8.5 tasks marked complete with run evidence.
- `run_at01` through `run_at10` pass on staging site.
- M8 exit criterion satisfied: all 10 acceptance tests pass on k3s staging.
