# M3 Release Gate Checklist

This checklist defines the minimum release-gate routine for Milestone 3.

## Scope

- Trigger before any move from dev to staging for M3 work items.
- Keep evidence links in `docs/PHASE2_AT01_AT10_CHECKLIST.md` run logs.

## Gate Criteria

1. **Schema**
   - Required DocType/field changes are migrated successfully.
2. **Validation**
   - Server-side validation blocks invalid and cross-site inconsistent writes.
3. **Permissions / Isolation**
   - Site isolation checks pass for list and direct-read access.
4. **Workflow**
   - Target workflow transitions for this release pass on a clean site.
5. **Evidence**
   - Repeatable automated checks pass and are logged with date + commit SHA.

## Execution Steps (per release candidate)

1. Run acceptance checks
   - `bench --site localhost execute yam_agri_core.yam_agri_core.smoke.run_at01_automated_check`
   - `bench --site localhost execute yam_agri_core.yam_agri_core.smoke.run_at10_automated_check`
2. Run CI-aligned local checks
   - `ruff check apps/yam_agri_core`
   - `ruff format apps/yam_agri_core --check`
   - `pytest apps/yam_agri_core/yam_agri_core/yam_agri_core/tests/test_agr_cereal_001.py -v`
3. Refresh planning artifacts
   - `python tools/refresh_wbs_milestones.py`
   - `python tools/refresh_wbs_rows.py`
4. Capture evidence
   - Add a run-log entry with date, environment, tester, commit SHA, command list, pass/fail, blockers.
   - Attach GitHub Actions `ci.yml` success URL for the same commit.

## Exit Rule

Mark M3 row(s) as `Done` only when all five categories are complete and evidence is current for the release candidate.