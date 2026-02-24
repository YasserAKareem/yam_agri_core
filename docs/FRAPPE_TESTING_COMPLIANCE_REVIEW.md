# Frappe Testing Compliance Review (Python + UI)

Date: 2026-02-24
Scope: Evaluate current repository against Frappe Testing and UI Testing requirements.

## 1) Official baseline (from Frappe docs)

### Python / server tests (`/testing`)
- Tests should be in `test_*.py` files.
- Run from bench context using `bench --site <site> run-tests` variants.
- Ensure dev dependencies are installed before running tests.
- Tests should create/cleanup dependent records.
- Support targeted execution by app/module/doctype.

### UI tests (`/ui-testing`)
- Frappe UI testing is Cypress-based.
- Cypress does **not** rely on Selenium in Frappe's official flow.
- Tests are JavaScript files in Cypress directories for each app.
- Run with `bench --site <site> run-ui-tests <app>` (optional headless/parallel/coverage).

## 2) Current repo status

### Preparation readiness
- ✅ Docker + bench workflow documented: [infra/docker/README.md](infra/docker/README.md)
- ✅ Python tests exist:
  - [apps/yam_agri_core/tests/test_doc_validations.py](apps/yam_agri_core/tests/test_doc_validations.py)
  - [apps/yam_agri_core/yam_agri_core/yam_agri_core/tests/test_agr_cereal_001.py](apps/yam_agri_core/yam_agri_core/yam_agri_core/tests/test_agr_cereal_001.py)
- ❌ No Cypress project/config detected (`cypress.config.*`, `package.json`, cypress folders absent).
- ⚠ Selenium not configured (also not required by Frappe UI testing docs).

### Processing readiness
- ✅ Verified execution works for focused Python tests:
  - `bench --site localhost run-tests --app yam_agri_core --module yam_agri_core.yam_agri_core.tests.test_agr_cereal_001`
  - Result: 2 tests passed.
- ❌ `run-ui-tests` cannot be executed yet because Cypress suite is not present.

### Documentation readiness
- ✅ Acceptance evidence log exists: [docs/PHASE2_AT01_AT10_CHECKLIST.md](docs/PHASE2_AT01_AT10_CHECKLIST.md)
- ⚠ No dedicated UI test plan/report template yet.
- ⚠ No explicit pass/fail mapping between test commands and release gates in one place.

## 3) Compliance verdict

- Python test track: **Partially compliant** (runner works; basic tests present).
- UI test track: **Not compliant yet** with Frappe UI testing docs (Cypress suite missing).
- Selenium track: **Not applicable for Frappe-native UI testing** (docs specify Cypress; Selenium is external/custom path).

## 4) Minimum actions to reach compliance

1. Add Cypress scaffold under app scope (specs + support commands).
2. Add run instructions using `bench --site localhost run-ui-tests yam_agri_core --headless`.
3. Add at least one UI smoke spec for login + list navigation + save flow.
4. Add documentation page that maps:
   - command
   - expected result
   - evidence artifact path
5. (Optional) Add Cypress coverage (`--with-coverage`) workflow for CI.

## 5) Suggested acceptance gate

- Gate A (Python): `run-tests --app yam_agri_core` must pass.
- Gate B (UI): `run-ui-tests yam_agri_core --headless` must pass.
- Gate C (Evidence): update [docs/PHASE2_AT01_AT10_CHECKLIST.md](docs/PHASE2_AT01_AT10_CHECKLIST.md) with run date, SHA, pass/fail.
