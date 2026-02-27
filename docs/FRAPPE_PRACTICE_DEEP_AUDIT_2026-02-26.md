# YAM Agri Core Deep Audit (Frappe Practice)

Date: 2026-02-26  
Repository: `yam_agri_core`  
Audit mode: static code/config audit + standards comparison + reorganization plan

## 1) Objective

Evaluate the project against Frappe ecosystem practices (framework + official docs), then produce a concrete reorganization and fix plan with implementation phases.

## 2) Scope and Method

### 2.1 Scope scanned

- Full repo topology, with deep focus on `apps/yam_agri_core/yam_agri_core/yam_agri_core`.
- Hooks, install/migrate lifecycle, DocTypes, permissions, API, seed/smoke utilities, tests, packaging, CI workflows, and docs.
- Metadata and fixtures strategy.

### 2.2 Evidence collection

- File inventory and structural metrics:
  - `rg --files`
  - `find ... | wc -l`
  - `wc -l` on high-impact modules
- Static rule scans:
  - whitelisted method coverage
  - permission hook coverage
  - broad exception and direct DB-write hotspots
- Local quality scripts:
  - `python3 tools/check_packaging_consistency.py` (passed)
  - `python3 tools/frappe_skill_agent.py --format json` (0 findings with current rule set)
  - `python3 -m py_compile` over app Python files (passed)

### 2.3 Environment constraints during audit

- `pytest` is not installed in this shell (`python3 -m pytest` failed with `No module named pytest`), so runtime test execution could not be validated here.

## 3) Frappe Baseline References Used

- Frappe app structure and generated layout:
  - https://docs.frappe.io/framework/user/en/basics/apps
- Hooks behavior (`fixtures`, `after_migrate`, `permission_query_conditions`, `has_permission`):
  - https://docs.frappe.io/framework/user/en/python-api/hooks
- Important permission note from Frappe docs:
  - `permission_query_conditions` affects `frappe.db.get_list`, not `frappe.db.get_all`
- Required app/dependency guidance:
  - https://docs.frappe.io/framework/user/en/bench/reference/required-app
- Patch workflow conventions (`patches.txt`, once-per-site patch execution):
  - https://frappe.io/blog/engineering/frappe-developer-tips-make-your-patches-write-their-own-success-stories
- Frappe testing style (`UnitTestCase`, `IntegrationTestCase`, test execution model):
  - https://docs.frappe.io/framework/user/en/testing

## 4) Current-State Findings

Severity model used here: `Critical` / `High` / `Medium` / `Low`.

### 4.1 Critical

1. Lifecycle overload in `after_migrate` and `after_install`.
- Evidence:
  - `apps/yam_agri_core/yam_agri_core/yam_agri_core/install.py` lines 7-52
  - Calls include permission mutations, workflow materialization, workspace rewriting, and dev seeding in shared lifecycle hooks.
- Why this is critical:
  - In Frappe practice, one-time schema/data changes should be handled by patches; repeatedly mutating desk/workspace/data on each migrate increases drift risk and complicates rollback/debug.

2. No active patch chain despite migration behavior in code.
- Evidence:
  - `apps/yam_agri_core/yam_agri_core/patches.txt` lines 1-7 (comments only, no patch entries)
- Why this is critical:
  - Migration intent is present but not captured as explicit versioned patch steps, reducing traceability and deployment determinism across sites.

### 4.2 High

1. Over-concentrated modules with mixed responsibilities.
- Evidence:
  - `dev_seed.py` 2335 lines
  - `smoke.py` 1536 lines
  - `workspace_setup.py` 979 lines
  - `site_permissions.py` 514 lines
  - `api/ai_assist.py` 520 lines
- Why this matters:
  - These files combine domain logic, QA data generation, migration helpers, and runtime behavior; this increases regression surface and review burden.

2. Runtime app package contains tooling-centric test suite.
- Evidence:
  - `apps/yam_agri_core/yam_agri_core/yam_agri_core/tests/test_frappe_skill_agent.py` lines 1-220+
  - Imports repository `tools/` by path surgery (`sys.path` mutation, line 17).
- Why this matters:
  - This test targets a repo tool, not app runtime behavior; it creates coupling between app package and repo layout.

3. Hooks dependency expression is likely misaligned with documented expectation.
- Evidence:
  - `apps/yam_agri_core/yam_agri_core/hooks.py` line 12: `required_apps = ["frappe/erpnext"]`
  - Frappe docs show `required_apps` as installed app names (example: `["erpnext"]`) and use pyproject for dependency ranges.
- Why this matters:
  - Ambiguous dependency declaration can produce install/migrate surprises across benches.

### 4.3 Medium

1. Version string drift across metadata.
- Evidence:
  - `hooks.py` line 9: `1.1.0-dev`
  - package and setup: `1.1.0.dev0`
- Why this matters:
  - Inconsistent user/admin-visible versioning complicates release tracing.

2. README test command drift.
- Evidence:
  - Root `README.md` line 74 references `python -m pytest tests/ -v` from `apps/yam_agri_core`.
  - Actual tests live under `apps/yam_agri_core/yam_agri_core/yam_agri_core/tests/`.
- Why this matters:
  - New contributors will run the wrong command and get false setup failures.

3. Workspace export strategy is placeholder-only + runtime reconstruction.
- Evidence:
  - Workspace JSON files contain only `doctype` and `name` fields.
  - Real content is synthesized in `workspace_setup.py`.
- Why this matters:
  - Exported artifacts are not the source of truth; behavior is encoded procedurally in a large module and executed in lifecycle hooks.

4. Permission implementation has high duplication cost.
- Evidence:
  - `site_permissions.py` includes many thin wrappers for query and has-permission methods.
- Why this matters:
  - Current parity is good, but future doctype additions are error-prone and require touching many map entries/functions.

### 4.4 Low

1. Global desk-route rewrite in bundled JS may conflict with evolving Desk routes.
- Evidence:
  - `public/js/yam_agri_core.bundle.js` lines 1-35
- Why this matters:
  - This is framework-fragile and should be scoped carefully or removed if no longer needed.

2. Lot form client script has grown into a large mixed-concern controller.
- Evidence:
  - `doctype/lot/lot.js` lines 1-288
- Why this matters:
  - UI behavior, AI dialogs, policy hints, and transition guards are tightly packed in one file.

## 5) Strengths Preserved

- Core site-isolation model is consistently enforced in server-side controllers and API endpoints (`assert_site_access` usage is pervasive).
- `permission_query_conditions` and `has_permission` maps are currently in parity.
- Packaging consistency check is already present and currently passing.
- Security checks exist around artifact path traversal in scale-ticket import.

## 6) Target Reorganization (Proposed)

Keep Frappe’s native generated structure intact, but modularize shared logic and move non-runtime concerns out of the hot path.

### 6.1 Proposed application layout

```text
apps/yam_agri_core/yam_agri_core/yam_agri_core/
  api/
    ai_assist.py
    observation_monitoring.py
    scale_ticket_import.py
    agr_cereal_001.py
  permissions/
    site_scope.py
    doctype_access.py
    hooks_registry.py
  services/
    workspace/
      ensure.py
      sidebar.py
    qa/
      dispatch_gate.py
      nonconformance.py
    seed/
      baseline.py
      phase4.py
      phase5.py
  doctype/
    ... (controllers remain in native Frappe locations)
  patches/
    v1_2/
      migrate_lot_crop_links.py
      normalize_workspace_records.py
      migrate_permission_defaults.py
```

### 6.2 Test layout target

```text
apps/yam_agri_core/yam_agri_core/yam_agri_core/tests/
  unit/
    ... pure Python helpers
  integration/
    ... IntegrationTestCase / UnitTestCase for DocTypes and APIs
  security/
    ... permission and IDOR tests
tools/tests/
  test_frappe_skill_agent.py   # moved out of app runtime test package
```

## 7) Fix Plan (Phased)

## Phase 0: Stabilize Baseline (1-2 days)

- Freeze current behavior with smoke snapshots:
  - export key DocType/workspace/permission state.
- Correct contributor docs:
  - fix test commands and bench execution examples.
- Align version strings (`hooks.py` vs package metadata).

Exit criteria:
- Documentation commands run without path confusion.
- Version appears consistent in package and app hooks.

## Phase 1: Migration Hygiene (2-3 days)

- Introduce real patch modules under `patches/` and populate `patches.txt`.
- Move one-time transforms out of `after_migrate`:
  - lot crop normalization
  - any historical workspace normalization
  - any one-time permission defaults
- Keep `after_migrate` only for light idempotent sync checks.

Exit criteria:
- `patches.txt` contains explicit ordered patch entries.
- `after_migrate` no longer performs heavy historical migrations.

## Phase 2: Decompose Large Modules (4-6 days)

- Split `site_permissions.py` into:
  - site scope resolver
  - query-condition builders
  - has-permission evaluators
- Split `dev_seed.py` by dataset/baseline concern.
- Split `workspace_setup.py` by workspace, sidebar, and diagnostics concerns.
- Keep public function signatures stable to avoid hook breakage.

Exit criteria:
- No module over ~400 lines except where Frappe controller constraints require.
- Existing hooks still resolve and migrate successfully.

## Phase 3: Test Modernization (3-5 days)

- Add Frappe-native integration tests (`IntegrationTestCase`) for:
  - site isolation (read/list/direct fetch)
  - lot dispatch policy gates
  - scale ticket mismatch + NC creation
  - API permission/role gates
- Relocate non-app tool tests (`test_frappe_skill_agent.py`) to `tools/tests`.
- Keep pure Python unit tests for deterministic algorithm modules.

Exit criteria:
- Bench-run test suite covers critical workflows.
- Tooling tests are separated from app runtime tests.

## Phase 4: Workspace and UI Cleanup (2-4 days)

- Decide single source of truth for workspaces:
  - either proper exported workspace docs (preferred)
  - or minimal runtime synthesis with clearly bounded scope
- Reduce fragile desk path rewrite logic in global bundle.
- Extract Lot AI UI logic into a dedicated client module.

Exit criteria:
- Workspace behavior reproducible without hidden procedural drift.
- Global JS no longer rewrites generic desk routes unnecessarily.

## 8) Prioritized Work Backlog

1. Create patch framework and migrate historical operations from `after_migrate`.  
2. Split `dev_seed.py` and `workspace_setup.py` by concern.  
3. Refactor permission module into composable units while preserving hook API names.  
4. Move tool tests out of app package and add Frappe integration tests.  
5. Fix metadata/docs drift (`required_apps`, version, README test command).  
6. Simplify global JS route rewrite and reduce Lot client-script surface area.  

## 9) Risk Register

- Risk: hook path breakage during refactor.
  - Mitigation: keep compatibility adapter functions in old module paths until next major version.
- Risk: migrate-time behavior changes across existing sites.
  - Mitigation: run patch dry-runs in staging and compare metadata exports before/after.
- Risk: hidden dependence on current workspace synthesis.
  - Mitigation: snapshot existing workspace docs, assert critical links in integration checks.

## 10) Immediate First Sprint Recommendation

If you want fastest risk reduction with minimal feature churn, execute this order:

1. Phase 1 (migration hygiene)  
2. Phase 0 metadata/doc cleanup items  
3. Phase 3 security/integration tests for site isolation and import APIs  
4. Phase 2 decomposition  
5. Phase 4 UI/workspace cleanup  

---

## Appendix A: Key Repository Evidence Anchors

- Hooks and lifecycle: `apps/yam_agri_core/yam_agri_core/hooks.py`, `apps/yam_agri_core/yam_agri_core/yam_agri_core/install.py`
- Permission centralization: `apps/yam_agri_core/yam_agri_core/yam_agri_core/site_permissions.py`
- Workspace synthesis: `apps/yam_agri_core/yam_agri_core/yam_agri_core/workspace_setup.py`
- Seed and acceptance scenarios: `apps/yam_agri_core/yam_agri_core/yam_agri_core/dev_seed.py`, `apps/yam_agri_core/yam_agri_core/yam_agri_core/smoke.py`
- Tool test coupling inside app tests: `apps/yam_agri_core/yam_agri_core/yam_agri_core/tests/test_frappe_skill_agent.py`
- Patches placeholder: `apps/yam_agri_core/yam_agri_core/patches.txt`

