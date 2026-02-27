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
