# Phase 8 Execution Log (2026-02-27)

## 1) Scope executed in this run

- Execute Phase 8 next-step sequence:
  1. run `preflight.sh`
  2. run `generate-secrets.sh`
  3. apply staging manifests in documented order
  4. run `phase8_acceptance.sh` and attach report output

## 2) Commands run and outcomes

### 2.1 Preflight and secret generation

Executed from `environments/staging`:

1. `./scripts/preflight.sh .env`
2. `./scripts/generate-secrets.sh .env manifests/secrets.generated.yaml`

Result:

- preflight: `pass`
- secret generation: `pass`

### 2.2 Manifest apply attempt

Attempted apply validation in documented order from this workstation.

Result:

- blocked: no reachable staging k3s API context from this machine.
- kubectl error: connection refused to `https://127.0.0.1:12833`.

Note:

- This confirms apply must be run on the actual staging server via WireGuard VPN (WBS 8.1.1/8.2 path).
- Added helper script for exact order execution: `environments/staging/scripts/apply_manifests.sh`.

### 2.3 Acceptance bundle run

`phase8_acceptance.sh` was executed in a bench-capable container context as a rehearsal run:

- command context: `/tmp/phase8_acceptance.sh localhost /home/frappe/frappe-bench/sites/artifacts/phase8`

Final result:

- `pass=10 fail=0 blocked=0 error=0`
- all AT-01 through AT-10 passed in this run context.

## 3) Evidence artifacts attached

Copied reports to repository evidence folder:

- `artifacts/evidence/phase8/acceptance_20260227T065130Z.jsonl` (final all-pass run)
- earlier failed runs retained for traceability:
  - `artifacts/evidence/phase8/acceptance_20260227T064813Z.jsonl`
  - `artifacts/evidence/phase8/acceptance_20260227T064900Z.jsonl`
  - `artifacts/evidence/phase8/acceptance_20260227T065009Z.jsonl`

## 4) Corrective fix applied during execution

Issue discovered:

- AT-07 automated check was non-deterministic in repeat runs due static ticket IDs and mismatched device reference behavior.

Fix implemented:

- updated `run_at07_automated_check` in `yam_agri_core.yam_agri_core.health.checks` to:
  - use resolved device reference in CSV payload,
  - generate unique ticket numbers per run tag.

## 5) Remaining actions to complete on staging server

1. Connect via WireGuard to staging host.
2. Run `./scripts/preflight.sh .env`.
3. Run `./scripts/generate-secrets.sh .env manifests/secrets.generated.yaml`.
4. Run `./scripts/apply_manifests.sh`.
5. Run `./scripts/phase8_acceptance.sh <staging_site_name>` and archive JSONL in Phase 8 evidence.

## 6) Remaining WBS execution pass (8.1.1, 8.2.x, 8.4)

### 6.1 Added operator scripts

- `environments/staging/scripts/provision_k3s.sh` (WBS 8.1.1)
- `environments/staging/scripts/setup_wireguard.sh` (WBS 8.2.1)
- `environments/staging/scripts/restrict_k3s_api.sh` (WBS 8.2.2)
- `environments/staging/scripts/migrate_dev_to_staging.sh` (WBS 8.4.1/8.4.2)

### 6.2 Commands executed in this pass

1. `DRY_RUN=1 ./scripts/provision_k3s.sh staging.example.internal ubuntu`
2. `DRY_RUN=1 WG_ENDPOINT=staging.example.internal ./scripts/setup_wireguard.sh staging.example.internal ubuntu`
3. `DRY_RUN=1 VPN_SUBNET=10.88.0.0/24 ./scripts/restrict_k3s_api.sh staging.example.internal ubuntu`
4. `MODE=backup-only ARTIFACT_ROOT=artifacts/evidence/phase8/migration ./scripts/migrate_dev_to_staging.sh`

### 6.3 Results

- 8.1.1 remote install path: validated in dry-run (safe execution preview produced).
- 8.2.1 WireGuard config path: validated in dry-run.
- 8.2.2 k3s API restriction path: validated in dry-run.
- 8.4 backup workflow: executed successfully in backup-only mode.

Backup evidence from latest run:

- directory: `artifacts/evidence/phase8/migration/20260227T070325Z/`
- files captured:
  - `20260227_100326-localhost-database.sql.gz`
  - `20260227_100326-localhost-files.tar`
  - `20260227_100326-localhost-private-files.tar`
  - `20260227_100326-localhost-site_config_backup.json`
  - `manifest.json`

### 6.4 Remaining hard blocker for full Phase 8 closure

- Apply + restore still require execution on real staging host reachable via WireGuard (not available from this workstation context).
- Final closure command set remains:
  1. `DRY_RUN=0 ./scripts/provision_k3s.sh <staging_host> <ssh_user>`
  2. `DRY_RUN=0 WG_ENDPOINT=<public_host_or_ip> ./scripts/setup_wireguard.sh <staging_host> <ssh_user>`
  3. `DRY_RUN=0 VPN_SUBNET=<vpn_subnet> ./scripts/restrict_k3s_api.sh <staging_host> <ssh_user>`
  4. `./scripts/apply_manifests.sh`
  5. `MODE=full STAGING_TARGET=<user@host> STAGING_SITE=<staging_site> ./scripts/migrate_dev_to_staging.sh`
  6. `./scripts/phase8_acceptance.sh <staging_site>`

## 7) Additional execution validations in this pass

### 7.1 Manifest order validation without cluster

- executed: `DRY_RUN_MODE=render ./scripts/apply_manifests.sh`
- result: `pass` (`[OK] Rendered manifests successfully`)

### 7.2 Migration workflow re-validation after pattern hardening

Issue fixed:

- backup file matching in migration script could capture private file tar for both public/private slots.

Fix:

- switched to site-specific filename patterns:
  - `*-${DEV_SITE}-database.sql.gz`
  - `*-${DEV_SITE}-site_config_backup.json`
  - `*-${DEV_SITE}-private-files.tar`
  - `*-${DEV_SITE}-files.tar`

Rehearsal command:

- `MODE=backup-only ARTIFACT_ROOT=/tmp/phase8-migration-test ./scripts/migrate_dev_to_staging.sh`

Result:

- `pass` with all expected backup artifacts produced (database + public tar + private tar + config json).

## 8) Real remote execution attempt and blocker evidence

### 8.1 Real execution attempt

Command attempted:

- `DRY_RUN=0 ./scripts/provision_k3s.sh yam-staging.vpn.internal ubuntu`

Result:

- failed immediately: `ssh: Could not resolve hostname yam-staging.vpn.internal: Name or service not known`

### 8.2 Connectivity evidence capture

Added and executed:

- `environments/staging/scripts/check_staging_access.sh yam-staging.vpn.internal ubuntu`

Evidence file:

- `artifacts/evidence/phase8/connectivity/check_20260227T182011Z.log`

Evidence summary:

- WireGuard tools: missing on this workstation (`wg` not found).
- DNS: staging host unresolved.
- Therefore remote staging-host execution cannot proceed from this host until VPN + DNS path is established.

### 8.3 Updated operator gating

Runbook now requires `check_staging_access.sh` before any remote mutation steps.

## 9) Blocker remediation patch (workstation VPN/DNS unblock)

### 9.1 Implemented changes

- Added `environments/staging/scripts/unblock_staging_access.sh`:
  - optional WireGuard install (`WG_AUTO_INSTALL=1`),
  - optional tunnel bring-up (`WG_AUTO_UP=1 WG_CONFIG=...`),
  - optional `/etc/hosts` repair (`STAGING_HOST_IP=... UPDATE_HOSTS=1`),
  - runs access gate and can execute remote sequence after pass (`RUN_SEQUENCE=1`).
- Added top-level wrappers in `environments/staging/`:
  - `check_staging_access.sh`
  - `provision_k3s.sh`
  - `setup_wireguard.sh`
  - `restrict_k3s_api.sh`
  - `apply_manifests.sh`
  - `migrate_dev_to_staging.sh`
  - `phase8_acceptance.sh`
  - `preflight.sh`
  - `generate-secrets.sh`
  - `unblock_staging_access.sh`
- Enhanced connectivity and remote scripts for DNS-less operation:
  - `check_staging_access.sh`: supports `WG_AUTO_UP`, `WG_CONFIG`, `STAGING_HOST_IP`, `SSH_HOST_OVERRIDE`.
  - `provision_k3s.sh`, `setup_wireguard.sh`, `restrict_k3s_api.sh`: support `SSH_HOST_OVERRIDE`.

### 9.2 Validation commands and results

1. `bash -n` validation for updated scripts and wrappers:
   - result: pass.
2. `cd environments/staging && ./unblock_staging_access.sh yam-staging.vpn.internal ubuntu`
   - result: fail (expected) at unresolved DNS without fallback.
3. `cd environments/staging && STAGING_HOST_IP=10.88.0.1 ./unblock_staging_access.sh yam-staging.vpn.internal ubuntu`
   - result: DNS blocker bypassed; progressed to SSH stage and failed there (expected while WG tunnel/auth still unavailable).

Evidence logs:

- `artifacts/evidence/phase8/connectivity/unblock_20260227T072842Z.log`
- `artifacts/evidence/phase8/connectivity/unblock_20260227T072843Z_with_ip.log`

### 9.3 Operational next command set

Once valid peer config and reachable staging IP are available:

1. `cd environments/staging`
2. `WG_AUTO_UP=1 WG_CONFIG=<peer-config-or-name> STAGING_HOST_IP=<staging_vpn_ip_or_reachable_ip> UPDATE_HOSTS=1 ./unblock_staging_access.sh yam-staging.vpn.internal ubuntu`
3. `./check_staging_access.sh yam-staging.vpn.internal ubuntu`
4. `DRY_RUN=0 ./provision_k3s.sh yam-staging.vpn.internal ubuntu`
5. `DRY_RUN=0 APPLY_REMOTE=1 WG_ENDPOINT=<public_host_or_ip> ./setup_wireguard.sh yam-staging.vpn.internal ubuntu`
6. `DRY_RUN=0 ./restrict_k3s_api.sh yam-staging.vpn.internal ubuntu`
7. `./apply_manifests.sh`
8. `MODE=full STAGING_TARGET=ubuntu@yam-staging.vpn.internal STAGING_SITE=yam-staging.vpn.internal ./migrate_dev_to_staging.sh`
9. `./phase8_acceptance.sh yam-staging.vpn.internal`
