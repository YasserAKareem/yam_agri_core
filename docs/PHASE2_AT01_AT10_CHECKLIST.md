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

### AT-01 Steps

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

### AT-01 Expected Results

- Cannot save `StorageBin`, `Lot`, `Transfer`, or `ScaleTicket` without `site`.
- `Lot.crop` must resolve to an existing `Crop` record.
- Cross-site link mismatches are blocked (e.g., Site B lot on Site A transfer).
- Quantities enforce non-negative and domain constraints.

### AT-01 Evidence to capture

- Screenshots or record IDs for created Site/StorageBin/Lot/Transfer/ScaleTicket.
- Any validation error messages encountered and their conditions.

## AT-10: Site isolation (Site A user cannot see Site B)

### AT-10 Steps

1. Login as `qa_manager_a` (Site A only permission).
2. Open list views for: `Site`, `Lot`, `StorageBin`, `Transfer`, `ScaleTicket`, `QCTest`, `Certificate`, `Nonconformance`, `EvidencePack`, `Complaint`, `Device`, `Observation`.
3. Confirm Site B records do not appear in list/search/report.
4. Attempt direct access by URL/name of a Site B document.
5. Repeat key checks as `qa_manager_b` for inverse isolation.

### AT-10 Expected Results

- Query-level filtering hides other-site records in list/report/search.
- Record-level checks deny direct open/update when site is unauthorized.
- Administrator/System Manager can still access all sites.

### AT-10 Evidence to capture

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

### 2026-02-24 (AT-10 readiness audit)

- Date: 2026-02-24
- Environment (dev/staging): dev (`localhost` site)
- Tester: Copilot (automated readiness audit)
- Commit SHA: `9288e19`
- Executed Command:
  - `bench --site localhost execute yam_agri_core.yam_agri_core.smoke.get_at10_readiness`
- Result: `status=not_ready`
- Readiness details:
  - `sites.count=1` (need at least 2 sites)
  - `qa_users.existing=[]` (need `qa_manager_a@example.com`, `qa_manager_b@example.com`)
  - `qa_roles.entries=[]` (roles not assigned yet)
  - `site_permissions.entries=[]` (no user-site isolation mappings yet)
  - `location_bridge.site_field_present=true`, `mapped_locations_count=0`
- Immediate setup actions before manual AT-10 execution:
  1. Create Site B (second site).
  2. Create users `qa_manager_a@example.com` and `qa_manager_b@example.com`.
  3. Assign required roles (at least `QA Manager` + list access roles).
  4. Add User Permissions:
     - `qa_manager_a@example.com` -> Site A only
     - `qa_manager_b@example.com` -> Site B only
  5. Create at least one `Location` per site and set `Location.site`.

### 2026-02-24 (AT-10 readiness after provisioning)

- Date: 2026-02-24
- Environment (dev/staging): dev (`localhost` site)
- Tester: Copilot (automated provisioning + readiness check)
- Executed Command:
  - `bench --site localhost execute yam_agri_core.yam_agri_core.smoke.get_at10_readiness`
- Result: `status=ready`
- Applied setup changes:
  - Created Site B: `v3qdo4nkun` (`site_name=Site B`)
  - Created users: `qa_manager_a@example.com`, `qa_manager_b@example.com`
  - Assigned role: `QA Manager` to both users
  - Added site permissions:
    - `qa_manager_a@example.com` -> `eilf0e3t1b`
    - `qa_manager_b@example.com` -> `v3qdo4nkun`
  - Created and mapped locations:
    - `AT10-Location-A` -> `eilf0e3t1b`
    - `AT10-Location-B` -> `v3qdo4nkun`
- Notes:
  - Environment is now ready for manual AT-10 execution with cross-user evidence capture.

### 2026-02-24 (AT-10 automated execution)

- Date: 2026-02-24
- Environment (dev/staging): dev (`localhost` site)
- Tester: Copilot (automated execution)
- Executed Command:
  - `bench --site localhost execute yam_agri_core.yam_agri_core.smoke.run_at10_automated_check`
- Result: `status=pass`
- Evidence summary:
  - `qa_manager_a@example.com`
    - list checks: `lots_only_site_a=true`, `bins_only_site_a=true`
    - direct read cross-site: `lot_b_read_allowed=false`, `bin_b_read_allowed=false`
  - `qa_manager_b@example.com`
    - list checks: `lots_only_site_b=true`, `bins_only_site_b=true`
    - direct read cross-site: `lot_a_read_allowed=false`, `bin_a_read_allowed=false`
- Fixes applied before pass:
  - Added record-level `has_permission` hooks for site-scoped DocTypes.
  - Replaced `frappe.has_role` usage with runtime-compatible role checks via `frappe.get_roles`.
  - Added migration guard to enforce minimum `Custom DocPerm` rows for `Lot` and `StorageBin` (`QA Manager` and `System Manager`).
