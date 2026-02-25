# Phase 4 Acceptance Checklist (AT-02, AT-06, Dispatch Gate)

This checklist is the repeatable validation baseline for Phase 4 dispatch-gate readiness.

## Scope

- AT-02: required QC/Certificate evidence gates dispatch.
- AT-06: stale QC and expired Certificate block dispatch until refreshed.
- Regression bundle: seeded data + AT-02 + AT-06 + AT-10 + smoke.

## Preconditions

- Dev stack is healthy:
  - `cd infra/docker`
  - `bash preflight.sh`
- Site has required apps installed:
  - `erpnext`
  - `agriculture`
  - `yam_agri_core`
  - `yam_agri_qms_trace`
- AT-10 readiness is complete:
  - `bench --site localhost execute yam_agri_core.yam_agri_core.smoke.get_at10_readiness`
  - expected `{"status":"ready" ...}`

## Artifact Locations

- Evidence collector output dir: `artifacts/evidence/phase4_at02_at06/`
- Report JSON: `artifacts/evidence/phase4_at02_at06/evidence_report.json`
- Screenshots dir: `artifacts/evidence/phase4_at02_at06/screenshots/`

## AT-02 (Season Policy required evidence)

### Command

- `bench --site localhost execute yam_agri_core.yam_agri_core.smoke.run_at02_automated_check`

### Expected result

- `status=pass`
- `evidence.blocked_without_evidence=true`
- `evidence.allowed_with_evidence=true`

### Evidence fields to log

- `policy`, `lot`, `qc_test`, `certificate`
- `blocked_error` and `allow_error`

## AT-06 (Stale/Expired evidence revalidation)

### Command

- `bench --site localhost execute yam_agri_core.yam_agri_core.smoke.run_at06_automated_check`

### Expected result

- `status=pass`
- `evidence.blocked_with_stale_or_expired=true`
- `evidence.allowed_after_refresh=true`

### Evidence fields to log

- `policy`, `lot`
- `stale_qc_test`, `expired_certificate`
- `fresh_qc_test`, `valid_certificate`
- `blocked_error` and `allow_error`

## Full Regression Bundle (single run window)

1. Seed balanced dataset:
   - `bench --site localhost execute yam_agri_core.yam_agri_core.dev_seed.seed_m4_balanced_samples --kwargs '{"confirm":1,"target_records":140}'`
2. Run acceptance checks:
   - `bench --site localhost execute yam_agri_core.yam_agri_core.smoke.run_at02_automated_check`
   - `bench --site localhost execute yam_agri_core.yam_agri_core.smoke.run_at06_automated_check`
   - `bench --site localhost execute yam_agri_core.yam_agri_core.smoke.run_at10_automated_check`
   - `bench --site localhost execute yam_agri_core.yam_agri_core.smoke.run_phase2_smoke`
3. Capture visual/report artifacts:
   - `python tools/evidence_capture/run_evidence_collector.py --scenario tools/evidence_capture/scenario.phase4_at02_at06.json`

### Exit criteria

- All commands return pass/ok in same run window.
- Evidence report and screenshots are generated under `artifacts/evidence/phase4_at02_at06/`.
- Run log entry is appended below with timestamp, commit SHA, and key IDs.

## Run Log Template

- Date:
- Environment:
- Tester:
- Commit SHA:
- Seed result:
- AT-02: PASS/FAIL
- AT-06: PASS/FAIL
- AT-10: PASS/FAIL
- Smoke: PASS/FAIL
- Evidence report path:
- CI run URL / Run ID / Conclusion:
- Blockers:
- Follow-up actions:

## Run Log Entries

### 2026-02-24 (M4 implementation baseline run)

- Date: 2026-02-24
- Environment: dev (`localhost`, docker bench wrapper)
- Tester: Copilot (automated)
- Commit SHA: `5b2dbb8` (baseline prior to this implementation batch)
- Seed result:
  - Command: `bench --site localhost execute yam_agri_core.yam_agri_core.dev_seed.seed_m4_balanced_samples --kwargs '{"confirm":1,"target_records":140}'`
  - Result: `{"status":"ok","seed_tag":"20260224115220","target_records":140,"core_total":144,"created_records":0}`
- AT-02: PASS
  - Result: `status=pass`
  - Evidence: `policy=YAM-SP-2026-00001`, `lot=YAM-LOT-2026-00019`, `qc_test=YAM-QCT-2026-00032`, `certificate=YAM-CERT-2026-00019`
- AT-06: PASS
  - Result: `status=pass`
  - Evidence: `policy=YAM-SP-2026-00004`, `lot=YAM-LOT-2026-00020`, `stale_qc_test=YAM-QCT-2026-00033`, `expired_certificate=YAM-CERT-2026-00020`
- AT-10: PASS
  - Result: `status=pass`
- Smoke: PASS
  - Result: `status=ok`
- Evidence report path:
  - `artifacts/evidence/phase4_at02_at06/evidence_report.json`
  - `artifacts/evidence/phase4_at02_at06/screenshots/`
- Collector summary:
  - `captured_at=2026-02-24T20:02:37.975085+00:00`
  - Bench execute results in report: `run_at02_automated_check=pass`, `run_at06_automated_check=pass`, `run_at10_automated_check=pass`, `run_phase2_smoke=ok`
- CI run URL / Run ID / Conclusion:
  - Pending for implementation commit SHA (to be appended after push).
- Blockers:
  - None blocking this baseline run.
- Follow-up actions:
  - Append CI metadata for this implementation commit after push.
  - Refresh WBS statuses after this evidence entry is committed.

### 2026-02-24 (Seed realism validation rerun)

- Date: 2026-02-24
- Environment: dev (`localhost`, docker bench wrapper)
- Tester: Copilot (automated)
- Seed result:
  - Command: `bench --site localhost execute yam_agri_core.yam_agri_core.dev_seed.seed_m4_balanced_samples --kwargs '{"confirm":1,"target_records":180}'`
  - Result: `{"status":"ok","seed_tag":"20260224115833","target_records":180,"core_total":182,"created_records":19}`
- Validation checks:
  - `run_at02_automated_check`: `status=pass`
  - `run_at06_automated_check`: `status=pass`
- Notes:
  - This rerun confirms the updated seed creation path executes with additional record generation (`created_records=19`).

### 2026-02-24 (CI metadata for M4 implementation commits)

- Implementation commit SHA: `33866dbde2db899584b6e1d42ff5c908e6fa977f`
  - `CI` run: `22343716476` -> `failure`
    - URL: `https://github.com/YasserAKareem/yam_agri_core/actions/runs/22343716476`
    - Job summary: `Python lint (ruff)=failure`, all other CI jobs success.
  - `Packaging Metadata` run: `22343716609` -> `failure` (non-gating for this acceptance flow)
- Remediation commit SHA: `b6b5b6ea34f5bd1e149968192be16e7f42b6d9bf`
  - `CI` run: `22343761795` -> `success`
    - URL: `https://github.com/YasserAKareem/yam_agri_core/actions/runs/22343761795`
  - `Packaging Metadata` run: `22343761861` -> `failure` (tracked separately)

### 2026-02-24 (CI metadata for AT-06 cross-site enhancement)

- Commit SHA: `20dc3a2e525ab97c1d42c914d961341f8d1e8aa5`
  - `CI` run: `22343974792` -> `success`
    - URL: `https://github.com/YasserAKareem/yam_agri_core/actions/runs/22343974792`
  - `Packaging Metadata` run: `22343974787` -> `failure` (non-gating for this acceptance flow)

### 2026-02-25 (M4 + AT03/AT04/AT05 bench run request on localsite)

- Date: 2026-02-25
- Environment: dev (docker bench wrapper via `infra/docker/run.sh`)
- Tester: Copilot (automated)
- Commit SHA: `16537b118c4edbea8bf2fb1d6532fd1643e429e4`
- Bench commands requested:
  - `bench --site localsite execute yam_agri_core.yam_agri_core.smoke.run_m4_gate_automated_check`
  - `bench --site localsite execute yam_agri_core.yam_agri_core.smoke.run_at03_automated_check`
  - `bench --site localsite execute yam_agri_core.yam_agri_core.smoke.run_at04_automated_check`
  - `bench --site localsite execute yam_agri_core.yam_agri_core.smoke.run_at05_automated_check`
- Result:
  - `run_m4_gate_automated_check`: BLOCKED (`404 Not Found: localsite does not exist`)
  - `run_at03_automated_check`: BLOCKED (`404 Not Found: localsite does not exist`)
  - `run_at04_automated_check`: BLOCKED (`404 Not Found: localsite does not exist`)
  - `run_at05_automated_check`: BLOCKED (`404 Not Found: localsite does not exist`)
- Site inventory check:
  - `bench list-sites` output: `dev.local`, `localhost`
- CI run URL / Run ID / Conclusion:
  - `CI` run: `22372521701` -> `success`
    - URL: `https://github.com/YasserAKareem/yam_agri_core/actions/runs/22372521701`
  - `Packaging Metadata` run: `22372521714` -> `success`
    - URL: `https://github.com/YasserAKareem/yam_agri_core/actions/runs/22372521714`
- Blockers:
  - Requested site `localsite` is not present in this bench environment.
- Follow-up actions:
  - Re-run the same commands on the actual `localsite` bench once that site exists, or confirm switching to `localhost`/`dev.local` for local validation.

### 2026-02-25 (Phase 4 acceptance run window on localhost)

- Date: 2026-02-25
- Environment: dev (`localhost`, docker bench wrapper)
- Tester: Copilot (automated)
- Site decision: current `<site>` is authoritative for this run window (`localhost`).
- Commit SHA: `5852c7b` (pre-evidence-doc update)
- Command results:
  - `run_m4_gate_automated_check`: `status=pass`
  - `run_at03_automated_check`: `status=pass`
  - `run_at04_automated_check`: `status=pass`
  - `run_at05_automated_check`: `status=pass`
- AT-02/AT-06 gate proof:
  - AT-02 evidence: `policy=YAM-SP-2026-00001`, `lot=YAM-LOT-2026-00049`, `qc_test=YAM-QCT-2026-00066`, `certificate=YAM-CERT-2026-00043`
  - AT-02 blocked reason: `Cannot dispatch: missing or stale required QC tests: AT02-MOISTURE`
  - AT-06 evidence: `policy=YAM-SP-2026-00004`, `lot=YAM-LOT-2026-00050`, `cross_site=v3qdo4nkun`
  - AT-06 blocked reasons:
    - cross-site invalid blocked: `Lot site must match QCTest site`
    - stale/expired blocked: `Cannot dispatch: missing or stale required QC tests: AT06-MOISTURE`
- Trace proof (AT-03/04/05):
  - Split transfer: `YAM-TRF-2026-00020`, qty `120.0`
  - Backward chain: `count=1`, `trace_found=true`
  - Forward chain: `count=1`, `trace_found=true`
- CI run URL / Run ID / Conclusion:
  - Pending (append after pushing this evidence commit SHA).
- Blockers:
  - None for localhost execution window.
- Follow-up actions:
  - Refresh WBS and promote Phase 4 rows to `Partial/Done`.
  - Append CI metadata for this run window SHA after push.
