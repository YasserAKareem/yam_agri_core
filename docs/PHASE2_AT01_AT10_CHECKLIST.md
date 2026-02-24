# Phase 2 Acceptance Checklist (AT-01, AT-10)

This checklist is the repeatable validation baseline for Phase 2 traceability readiness.

## Preconditions

- Dev stack is healthy: run from `infra/docker`
  - `bash preflight.sh`
- Site has required apps installed:
  - `erpnext`
  - `agriculture`
  - `yam_agri_core`
  - `yam_agri_qms_trace`
- At least two Sites exist for isolation test (Site A, Site B).
- Test users exist:
  - `qa_manager_a` assigned to Site A
  - `qa_manager_b` assigned to Site B

## AT-01: Site -> StorageBin -> Lot flow

### Steps

1. Create `Site A` if missing.
2. Create `StorageBin` with:
   - `site = Site A`
   - `status = Active`
   - optional `warehouse` mapping (hybrid model)
3. Create `Lot` with:
   - `site = Site A`
   - `crop` linked to canonical `Crop`
   - positive `qty_kg`
4. Create a `Transfer` within Site A and verify lot-site consistency checks.
5. Create `ScaleTicket` referencing Site A lot and optional device at Site A.

### Expected Results

- Cannot save `StorageBin`, `Lot`, `Transfer`, or `ScaleTicket` without `site`.
- `Lot.crop` must resolve to an existing `Crop` record.
- Cross-site link mismatches are blocked (e.g., Site B lot on Site A transfer).
- Quantities enforce non-negative and domain constraints.

### Evidence to capture

- Screenshots or record IDs for created Site/StorageBin/Lot/Transfer/ScaleTicket.
- Any validation error messages encountered and their conditions.

## AT-10: Site isolation (Site A user cannot see Site B)

### Steps

1. Login as `qa_manager_a` (Site A only permission).
2. Open list views for: `Site`, `Lot`, `StorageBin`, `Transfer`, `ScaleTicket`, `QCTest`, `Certificate`, `Nonconformance`, `EvidencePack`, `Complaint`, `Device`, `Observation`.
3. Confirm Site B records do not appear in list/search/report.
4. Attempt direct access by URL/name of a Site B document.
5. Repeat key checks as `qa_manager_b` for inverse isolation.

### Expected Results

- Query-level filtering hides other-site records in list/report/search.
- Record-level checks deny direct open/update when site is unauthorized.
- Administrator/System Manager can still access all sites.

### Evidence to capture

- User + role mapping used for test.
- Record IDs attempted for cross-site access.
- Pass/fail per doctype with notes.

## Run Log Template

- Date:
- Environment (dev/staging):
- Tester:
- Commit SHA:
- AT-01: PASS/FAIL
- AT-10: PASS/FAIL
- Blockers:
- Follow-up actions:

## Run Log Entries

### 2026-02-24 (Automated pre-check)

- Date: 2026-02-24
- Environment (dev/staging): dev (`localhost` site)
- Tester: Copilot (automated checks)
- Commit SHA: `e390edd`
- AT-01: PARTIAL (automated validations passed; full user-flow evidence still required)
- AT-10: PARTIAL (permission hooks/bridge verified; cross-user manual verification still required)
- Executed Commands:
  - `bench --site localhost execute yam_agri_core.yam_agri_core.install.get_lot_crop_link_status`
  - `bench --site localhost execute yam_agri_core.yam_agri_core.install.get_site_location_bridge_status`
  - `bench --site localhost execute yam_agri_core.yam_agri_core.smoke.run_phase2_smoke`
- Key Results:
  - `get_lot_crop_link_status`: `{available: true, total_lots: 22, unresolved_count: 0}`
  - `get_site_location_bridge_status`: `{available: true, total_locations: 0}`
  - `run_phase2_smoke`: `status=needs_attention` because `Weather` and `Crop Cycle` are not active DocTypes on this site.
- Blockers:
  - No mapped `Location` records yet for agriculture site-isolation bridge testing.
  - No manual two-user (`Site A`/`Site B`) execution evidence captured yet.
- Follow-up actions:
  - Seed/create `Location` records and map `Location.site`.
  - Execute manual AT-01 and AT-10 steps with `qa_manager_a` and `qa_manager_b` and attach evidence.
