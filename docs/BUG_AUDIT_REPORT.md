# YAM Agri Core — Bug Audit Report

**Audit Date:** 2026-02-24
**Auditor:** Frappe Skill QC Agent (automated) + manual review
**Scope:** Full codebase audit against Frappe best practices and project non-negotiable rules
**Reference:** [Frappe Framework](https://github.com/frappe/frappe), [ERPNext](https://github.com/frappe/erpnext)

---

## Summary

| Severity | Count | Status |
|----------|-------|--------|
| Critical  | 3  | Fixed in this PR |
| High      | 4  | Fixed in this PR (1) + documented (3) |
| Medium    | 6  | Documented |
| Low       | 4  | Documented |
| **Total** | **17** | |

---

## Category 1: Missing i18n Translations (Critical — violates Non-Negotiable Rule #7)

**Rule**: All user-facing strings must be wrapped in `_("…")` in Python and `__("…")` in JavaScript.

### BUG-001 · `site_permissions.py` — three untranslated `frappe.throw` messages

**File:** `apps/yam_agri_core/yam_agri_core/yam_agri_core/site_permissions.py`

| Line | Before (buggy) | After (fixed) |
|------|---------------|--------------|
| 109 | `frappe.throw("No Site records exist; create a Site first.")` | `frappe.throw(_("No Site records exist; create a Site first."))` |
| 122 | `frappe.throw(f"Site not found: {site_identifier}")` | `frappe.throw(_("Site not found: {0}").format(site_identifier))` |
| 128 | `frappe.throw("Not permitted for this Site", frappe.PermissionError)` | `frappe.throw(_("Not permitted for this Site"), frappe.PermissionError)` |

**Impact:** Error messages displayed to Yemeni Arabic-speaking users are untranslated. The `_()` wrapper is also required for `bench update-translations` to discover and export these strings to `translations/ar.csv`.

**Also fixed:** Missing `from frappe import _` import in `site_permissions.py`.

**Status:** ✅ Fixed

---

## Category 2: Missing Cross-Site Validation (High)

### BUG-002 · `nonconformance.py` — no lot-site consistency check

**File:** `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/nonconformance/nonconformance.py`

**Problem:** Every other DocType that has a `lot` Link field (Complaint, ScaleTicket, QCTest, Certificate) validates that `lot.site == self.site`. Nonconformance has a `lot` field but was missing this guard, allowing a cross-site Nonconformance to be created against a Lot from a different Site.

**Before:**
```python
def validate(self):
    if not self.get("site"):
        frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)
    assert_site_access(self.get("site"))
    # ← No lot.site check! Bug.
```

**After:**
```python
def validate(self):
    if not self.get("site"):
        frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)
    assert_site_access(self.get("site"))
    lot = self.get("lot")
    if lot:
        lot_site = frappe.db.get_value("Lot", lot, "site")
        if lot_site and lot_site != self.get("site"):
            frappe.throw(_("Lot site must match Nonconformance site"), frappe.ValidationError)
```

**Status:** ✅ Fixed

---

## Category 3: Default Value Placement (High — violates Frappe coding pattern)

### BUG-003 · `observation.py` — `quality_flag` default set only in `validate()`, not `before_insert()`

**File:** `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/observation/observation.py`

**Problem:** Per Frappe best practice and the project's own coding standards, default values that must persist to the database on record creation belong in `before_insert()`. Using only `validate()` means the default is applied before save (correct), but there is no explicit documentation of intent, and programmatic inserts that bypass `validate` (e.g., `insert(ignore_permissions=True)` in test fixtures) may not set the default correctly.

The pattern also differs from how `Nonconformance` correctly sets its status default in `before_insert`.

**Fix:** Added `before_insert()` to set `quality_flag = "OK"` as the canonical default, while retaining the guard in `validate()` as a defence-in-depth fallback.

**Status:** ✅ Fixed

---

## Category 4: Hardcoded Values (High)

### BUG-004 · `smoke.py` — hardcoded test user emails

**File:** `apps/yam_agri_core/yam_agri_core/yam_agri_core/smoke.py`

**Problem:** `get_at10_readiness()` and related functions hardcode:
```python
qa_users = ["qa_manager_a@example.com", "qa_manager_b@example.com"]
```
These email addresses are used in multiple `if/elif` branches throughout the file. If the test users are renamed (e.g., for a staging environment), every reference must be updated, which is error-prone.

**Recommendation:** Extract to module-level constants:
```python
_AT10_USER_A = "qa_manager_a@example.com"
_AT10_USER_B = "qa_manager_b@example.com"
AT10_QA_USERS = [_AT10_USER_A, _AT10_USER_B]
```

**Status:** 📋 Documented — low-priority refactor (smoke.py is dev/diagnostic tooling only)

### BUG-005 · `smoke.py` — hardcoded reference to `yam_agri_qms_trace` app

**File:** `apps/yam_agri_core/yam_agri_core/yam_agri_core/smoke.py`

**Problem:**
```python
"yam_agri_qms_trace": "yam_agri_qms_trace" in (frappe.get_installed_apps() or []),
```
This app does not exist in the repository. A check for a non-existent app will always return `False`, causing the smoke test to report `status: needs_attention` even on a healthy installation.

**Recommendation:** Remove or guard this check behind a `# TODO` comment until the app is created.

**Status:** 📋 Documented

---

## Category 5: DocType JSON Schema Deficiencies (Medium)

### BUG-006 · All DocType JSONs — `site` field not marked `reqd: 1`

**Affected files (14 DocTypes):**
`lot.json`, `transfer.json`, `scale_ticket.json`, `qc_test.json`, `certificate.json`,
`nonconformance.json`, `evidence_pack.json`, `complaint.json`, `observation.json`,
`device.json`, `storage_bin.json`, `yam_plot.json`, `yam_soil_test.json`,
`yam_plot_yield.json`, `yam_crop_variety.json`, `yam_crop_variety_recommendation.json`

**Problem:** The Python controller enforces `frappe.throw(_("Every record must belong to a Site"))`, but the DocType JSON does not mark the `site` field as `"reqd": 1`. This means:
- The Frappe form will not show a red asterisk (*) to indicate the field is required.
- Client-side validation will not block save before the server is even reached.
- The enforcement is only at the Python layer (server-side), which is sufficient for security but creates a poor user experience.

**Recommendation:** Add `"reqd": 1` to the `site` field in all affected DocType JSON files.

**Status:** 📋 Documented

### BUG-007 · `lot.json` — `lot_number` not marked `reqd: 1`

**File:** `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/lot/lot.json`

**Problem:** `lot_number` is the human-readable identifier for a Lot (`title_field: "lot_number"`), but it is not marked as required in the JSON. A user can save a Lot with an empty lot_number, which makes the record invisible in list views and hard to identify.

**Recommendation:** Add `"reqd": 1` to the `lot_number` field.

**Status:** 📋 Documented

### BUG-008 · `lot.json` — `custom: 1` on an app-owned DocType

**File:** `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/lot/lot.json`

**Problem:** The Lot DocType JSON has `"custom": 1`, which marks it as a Custom DocType (created via Frappe's Customise Form UI). App-owned DocTypes should NOT have `custom: 1`. Custom DocTypes are managed differently in the database and can cause issues with `bench migrate` on fresh installs.

**Recommendation:** Remove `"custom": 1` from `lot.json` (and verify other DocType JSONs do not have this flag erroneously).

**Status:** 📋 Documented

---

## Category 6: Silent Exception Suppression (Medium)

### BUG-009 · `api/agr_cereal_001.py` — broad `except Exception` suppresses DB errors

**File:** `apps/yam_agri_core/yam_agri_core/yam_agri_core/api/agr_cereal_001.py`

**Problem:**
```python
def _get_varieties(*, site: str, crop: str) -> list[dict]:
    try:
        if frappe.db.exists("DocType", "YAM Crop Variety"):
            rows = frappe.get_all(...)
            return rows or []
    except Exception:
        return []   # Silently swallows DB errors, permission errors, etc.
    return []
```
Using a bare `except Exception` masks real errors (connection failures, permission errors, malformed queries) that should surface to the developer. The outer `return []` is also reached only when `YAM Crop Variety` does not exist, which makes the control flow confusing.

**Recommendation:** Log the error before returning:
```python
    except Exception:
        frappe.log_error(title="_get_varieties failed", message=frappe.get_traceback())
        return []
```

**Status:** 📋 Documented

---

## Category 7: Missing Audit Trail Configuration (Medium)

### BUG-010 · Most DocType JSONs missing `track_changes: 1`

**Affected DocTypes:** All custom DocTypes in the app.

**Problem:** For a food safety (HACCP/ISO 22000) platform, audit trails are critical. Frappe's `track_changes` feature records every field change with timestamp and user. Most DocType JSONs in this project have `"track_changes": null` or omit the field entirely.

**Recommendation:** Set `"track_changes": 1` on all high-value DocTypes:
- Lot, Transfer, QCTest, Certificate, Nonconformance, EvidencePack, Complaint

**Status:** 📋 Documented

---

## Category 8: Inconsistent `doc_events` vs. Controller Validation (Medium)

### BUG-011 · Inconsistent site-consistency enforcement pattern

**File:** `apps/yam_agri_core/yam_agri_core/hooks.py`

**Problem:** Cross-site lot consistency is enforced via two different mechanisms depending on the DocType:

- **QCTest and Certificate**: validated via `doc_events` in `hooks.py` pointing to `site_permissions.py` helpers (`enforce_qc_test_site_consistency`, `enforce_certificate_site_consistency`)
- **ScaleTicket, Complaint, Transfer, Observation**: validated directly inside the DocType controller's `validate()` method
- **Nonconformance**: was missing entirely (see BUG-002, now fixed)

This dual approach makes it hard to audit which DocTypes have site-consistency guards. Choosing one pattern and applying it consistently would make the codebase more maintainable.

**Recommendation:** Use the controller pattern (`validate()` in the Python controller) as the single source of truth, and remove the `doc_events` entries for QCTest/Certificate (or keep them and add equivalent `doc_events` for all other DocTypes).

**Status:** 📋 Documented

---

## Category 9: Missing `title_field` on DocType JSONs (Medium)

### BUG-012 · Several DocType JSONs missing `title_field`

**Affected files:** Most DocType JSONs except `lot.json` (which has `"title_field": "lot_number"`).

**Problem:** Without `title_field`, Frappe uses the `name` (auto-generated series) as the display value in Link field dropdowns and list views. This makes records hard to identify.

**Per Frappe convention:** Every DocType should declare `title_field` pointing to the most human-readable field (e.g., `site_name` for Site, `ticket_number` for ScaleTicket).

**Status:** 📋 Documented

---

## Category 10: Duplication (Low)

### BUG-013 · `build_site_query_condition` duplicates Administrator/System Manager checks

**File:** `apps/yam_agri_core/yam_agri_core/yam_agri_core/site_permissions.py`

**Problem:** Multiple functions (`build_site_query_condition`, `site_query_conditions`, `location_query_conditions`, `weather_query_conditions`, `crop_cycle_query_conditions`) each independently re-implement:
```python
if user in ("Administrator",):
    return None
if _user_has_role("System Manager", user=user):
    return None
```
This is a DRY violation. If the bypass logic needs to change (e.g., to support a new super-user role), it must be updated in multiple places.

**Recommendation:** Extract a private helper:
```python
def _is_unrestricted(user: str) -> bool:
    return user in ("Administrator",) or _user_has_role("System Manager", user=user)
```

**Status:** 📋 Documented

### BUG-014 · `install.py` calls the same helper functions in both `after_install` and `after_migrate`

**File:** `apps/yam_agri_core/yam_agri_core/yam_agri_core/install.py`

**Problem:** `after_install` and `after_migrate` both call the exact same set of functions. If a new helper is added to one, developers must remember to add it to the other.

**Recommendation:** Extract shared logic to a `_post_install_or_migrate()` helper that both hooks call.

**Status:** 📋 Documented

---

## Category 11: Missing Frappe `required_apps` / Module Declaration Consistency (Low)

### BUG-015 · `yam_agri` sub-package has a disconnected `__init__.py`

**File:** `apps/yam_agri_core/yam_agri_core/yam_agri/__init__.py`

**Problem:** There is an extra module directory `yam_agri/` inside the app root that is separate from the main app code (which lives in `yam_agri_core/`). This orphaned package is not referenced by any hook or business logic and may cause confusion.

**Status:** 📋 Documented

---

## Category 12: UI/JavaScript Issues (Low)

### BUG-016 · `lot.js` — client-side role check without server-side backup for `Mark Dispatched`

**File:** `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/lot/lot.js`

**Problem:**
```javascript
if (frm.doc.status === "For Dispatch" && frappe.user.has_role("QA Manager")) {
    frm.add_custom_button(__("Mark Dispatched"), () => {
        frm.set_value("status", "Dispatched");
        frm.save();
    });
}
```
The "Mark Dispatched" button sets `status = "Dispatched"` from client-side only. However, the Python controller `Lot.validate()` only enforces QA Manager for `Accepted` and `Rejected` statuses — not for `Dispatched`. A malicious user could directly send a `status = "Dispatched"` save request and bypass the client-side button guard entirely.

**Recommendation:** Add `"Dispatched"` to the server-side QA role check in `lot.py`.

**Status:** 📋 Documented

### BUG-017 · `lot.js` — `frappe.perm.get_user_permissions` API may not be available on all Frappe builds

**File:** `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/lot/lot.js`

**Problem:** The `before_save` handler uses `frappe.perm.get_user_permissions()`, guarded by an `if` check. However, `frappe.perm` is an internal API that may change between Frappe versions (the comment says "Frappe 14+" but the stack uses Frappe 16).

**Recommendation:** Use the documented `frappe.defaults.get_user_defaults("Site")` pattern or call a whitelisted API endpoint to retrieve the user's allowed sites.

**Status:** 📋 Documented

---

## Quick Reference — Files Changed by This Audit

| File | Change |
|------|--------|
| `site_permissions.py` | Added `from frappe import _`; wrapped 3 `frappe.throw` messages in `_()` |
| `doctype/nonconformance/nonconformance.py` | Added lot-site cross-check in `validate()` |
| `doctype/observation/observation.py` | Moved `quality_flag` default to `before_insert()`; kept fallback in `validate()` |
| `docs/BUG_AUDIT_REPORT.md` | This file — full bug catalogue |
| `tools/frappe_skill_agent.py` | New automated QC agent |
| `.github/copilot-instructions.md` | Enhanced with QC rules from this audit |

---

## Frappe Good-Practice References

The following Frappe framework conventions were cross-checked during this audit:

| Convention | Source | Status |
|-----------|--------|--------|
| Wrap all user strings in `_()` | [Frappe i18n docs](https://frappeframework.com/docs/user/en/guides/basics/translations) | BUG-001 fixed |
| Default values in `before_insert`, not `on_update` | [Frappe Document lifecycle](https://frappeframework.com/docs/user/en/basics/doctypes/document-lifecycle) | BUG-003 fixed |
| Use `frappe.throw` with exception type for typed errors | Frappe codebase convention | ✅ Followed |
| Register both `permission_query_conditions` AND `has_permission` | Frappe hooks docs | ✅ Followed |
| Never use `frappe.db.sql` with string interpolation | Frappe security guide | ✅ Followed |
| Mark required fields with `reqd: 1` in DocType JSON | Frappe DocType builder | BUG-006/007 documented |
| `track_changes: 1` for audit-critical DocTypes | Frappe audit trail | BUG-010 documented |
| `title_field` on every DocType | Frappe DocType best practice | BUG-012 documented |
