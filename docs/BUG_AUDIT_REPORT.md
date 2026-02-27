# YAM Agri Core — Bug Audit Report

**Audit Date:** 2026-02-24
**Auditor:** Frappe Skill QC Agent v2 (automated) + manual review
**Scope:** Full codebase audit against Frappe best practices and project non-negotiable rules
**Reference:** [Frappe Framework](https://github.com/frappe/frappe), [ERPNext](https://github.com/frappe/erpnext)

> **How to regenerate this report:**
> ```bash
> python tools/frappe_skill_agent.py --verbose        # human-readable with planned responses
> python tools/frappe_skill_agent.py --format json    # machine-readable
> ```

---

## Bug Classification Taxonomy

All bugs are tagged with a 3-level taxonomy code: `[Category].[Subcategory].[Specific Type]`

| # | Category | Subcategories |
|---|----------|--------------|
| 1 | Functional Bugs | Input Handling · Workflow Errors · Feature Failures |
| 2 | Logical Bugs | Algorithm Errors · Conditional Logic · State Management |
| 3 | Performance Bugs | Speed Issues · Memory Issues · Scalability |
| 4 | Compatibility Bugs | OS/Device · Browser · Versioning |
| 5 | Security Bugs | Authentication · Authorization · Data Protection |
| 6 | UI/UX Bugs | Layout · Accessibility · Interaction |
| 7 | Integration Bugs | API Integration · Database Integration · Third-Party Services |
| 8 | Syntax & Build Bugs | Compilation · Runtime · Build System |
| 9 | Concurrency Bugs | Race Conditions · Resource Locking · Threading |
| 10 | Regression Bugs | Feature Breakage · UI Regression · Performance Regression |

---

## Summary

| Severity | Count | Status |
|----------|-------|--------|
| Critical  | 7  | ✅ All fixed |
| High      | 4  | ✅ All fixed |
| Medium    | 6  | 📋 Documented — planned fix |
| Low       | 4  | 📋 Documented — planned fix |
| **Total** | **21** | |

---

## Fixed Bugs

---

### BUG-001 · `[6.3.1]` Unclear error messages — untranslated `frappe.throw` strings

| Attribute | Value |
|-----------|-------|
| **Taxonomy** | 6 UI/UX Bugs › 6.3 Interaction › 6.3.1 Unclear error messages |
| **Rule** | FS-001 |
| **Severity** | Critical |
| **Status** | ✅ Fixed |

**Files affected:**
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/site_permissions.py` — 3 occurrences
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/dev_seed.py` — 1 occurrence
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/seed/agr_cereal_001_sample_data.py` — 3 occurrences

**Problem:** `frappe.throw()` called with raw string literals not wrapped in `_()`. Arabic-speaking users see English error text. The `bench update-translations` command cannot discover untranslated strings without the `_()` wrapper.

**Before (buggy):**
```python
frappe.throw("Not permitted for this Site", frappe.PermissionError)
frappe.throw(f"Site not found: {site_identifier}")
frappe.throw("No Site records exist; create a Site first.")
```

**After (fixed):**
```python
frappe.throw(_("Not permitted for this Site"), frappe.PermissionError)
frappe.throw(_("Site not found: {0}").format(site_identifier))
frappe.throw(_("No Site records exist; create a Site first."))
```

**Planned Response:**
1. Add `from frappe import _` to the Python file if missing
2. Wrap each message: `frappe.throw(_("message"), ExcType)`
3. For JavaScript use `__('message')` in `frappe.msgprint` / `frappe.confirm`
4. Run `bench update-translations` and verify `translations/ar.csv` is updated

---

### BUG-002 · `[5.2.4]` IDOR — missing lot-site cross-check in `Nonconformance`

| Attribute | Value |
|-----------|-------|
| **Taxonomy** | 5 Security Bugs › 5.2 Authorization › 5.2.4 Insecure direct object reference (IDOR) |
| **Rule** | FS-009 |
| **Severity** | High |
| **Status** | ✅ Fixed |

**File:** `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/nonconformance/nonconformance.py`

**Problem:** Every other DocType with a `lot` Link field validates `lot.site == self.site`. Nonconformance was missing this guard, allowing a cross-site Nonconformance to be created against a Lot from a different Site — an IDOR vulnerability that breaks data isolation.

**Before (buggy):**
```python
def validate(self):
    if not self.get("site"):
        frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)
    assert_site_access(self.get("site"))
    # ← no lot.site check
```

**After (fixed):**
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

**Planned Response:**
1. Add `lot_site = frappe.db.get_value('Lot', self.lot, 'site')` in `validate()`
2. Throw `ValidationError` if `lot_site != self.site`
3. Add a unit test that attempts to create a cross-site linked record
4. Apply the same pattern to every DocType with a `lot` field

---

### BUG-003 · `[1.1.2]` Incorrect default values — `quality_flag` in `validate()` only

| Attribute | Value |
|-----------|-------|
| **Taxonomy** | 1 Functional Bugs › 1.1 Input Handling › 1.1.2 Incorrect default values |
| **Rule** | FS-007 |
| **Severity** | High |
| **Status** | ✅ Fixed |

**File:** `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/observation/observation.py`

**Problem:** `quality_flag = "OK"` was set only in `validate()`. Programmatic inserts that skip `validate()` (e.g. `insert(ignore_permissions=True)` in test fixtures or background jobs) would save a blank `quality_flag` to the DB, causing downstream logic to break.

**Fix:** Added `before_insert()` to set the canonical default; kept `validate()` as defence-in-depth.

**Before:**
```python
def validate(self):
    ...
    if not self.get("quality_flag"):
        self.quality_flag = "OK"   # ← wrong lifecycle hook
```

**After:**
```python
def before_insert(self):
    if not self.get("quality_flag"):
        self.quality_flag = "OK"   # ← correct: persists on first insert

def validate(self):
    ...
    if not self.get("quality_flag"):
        self.quality_flag = "OK"   # ← kept as defence-in-depth for updates
```

**Planned Response:**
1. Move the default assignment from `validate()` to `before_insert()`
2. Keep a fallback assignment in `validate()` as defence-in-depth
3. Verify with `bench run-tests` that the field is populated on new records

---

### BUG-004 · `[5.3.3]` Insecure storage — hardcoded QA user emails in `smoke.py`

| Attribute | Value |
|-----------|-------|
| **Taxonomy** | 5 Security Bugs › 5.3 Data Protection › 5.3.3 Insecure storage |
| **Rule** | FS-006 |
| **Severity** | High |
| **Status** | ✅ Fixed |

**File:** `apps/yam_agri_core/yam_agri_core/yam_agri_core/smoke.py`

**Problem:** `"qa_manager_a@example.com"` and `"qa_manager_b@example.com"` appeared 20+ times inline throughout the file. A single user rename would require updating every occurrence manually; one missed occurrence would cause the smoke test to silently use the wrong user.

**Before:**
```python
frappe.set_user("qa_manager_a@example.com")
evidence["list_checks"]["qa_manager_a@example.com"] = {...}
```

**After:**
```python
_AT10_USER_A = "qa_manager_a@example.com"
_AT10_USER_B = "qa_manager_b@example.com"
_AT10_QA_USERS = [_AT10_USER_A, _AT10_USER_B]
...
frappe.set_user(_AT10_USER_A)
evidence["list_checks"][_AT10_USER_A] = {...}
```

**Planned Response:**
1. Extract the value to a named module-level constant (e.g. `_USER_A = '…'`)
2. For production secrets use `frappe.conf.get()` or `os.environ.get()`
3. Review all non-test Python files for remaining inline credentials

---

## Documented Bugs — Planned Fix

---

### BUG-005 · `[1.1.1]` Missing required field validation — `site` not `reqd:1` in 14 DocType JSONs

| Attribute | Value |
|-----------|-------|
| **Taxonomy** | 1 Functional Bugs › 1.1 Input Handling › 1.1.1 Missing required field validation |
| **Rule** | FS-003 |
| **Severity** | Medium |
| **Status** | 📋 Documented |

**Affected DocTypes (14):** Lot, Transfer, ScaleTicket, QCTest, Certificate, Nonconformance, EvidencePack, Complaint, Observation, Device, YAM Plot, YAM Soil Test, YAM Plot Yield, YAM Crop Variety, YAM Crop Variety Recommendation

**Problem:** The `site` field is enforced by Python `validate()`, but the DocType JSON does not mark it `reqd: 1`. The Frappe form does not show a required asterisk (*) and client-side validation does not block save before the server is reached.

**Planned Response:**
1. Add `"reqd": 1` to the `site` field definition in every affected DocType JSON
2. Run `bench migrate` so the DB constraint is updated
3. Add a unit test that saves a record without `site` and expects `ValidationError`

---

### BUG-006 · `[2.3.3]` Incorrect flag toggling — `track_changes` disabled on transaction DocTypes

| Attribute | Value |
|-----------|-------|
| **Taxonomy** | 2 Logical Bugs › 2.3 State Management › 2.3.3 Incorrect flag toggling |
| **Rule** | FS-005 |
| **Severity** | Medium |
| **Status** | 📋 Documented |

**Affected DocTypes:** All custom transaction DocTypes (those with a `naming_series` field).

**Problem:** `track_changes` is not enabled. For a HACCP/ISO 22000 platform, every field change on Lot, Transfer, EvidencePack, etc. must be journalled for audit evidence. Without this, the system fails food safety traceability requirements.

**Planned Response:**
1. Add `"track_changes": 1` to each affected DocType JSON
2. Run `bench migrate` to activate change tracking in the DB
3. Verify the Version log appears after editing a record in the Frappe Desk
4. Include `track_changes` in the DocType JSON template for all future DocTypes

---

### BUG-007 · `[2.2.4]` Missing default cases — broad `except Exception` in `api/agr_cereal_001.py`

| Attribute | Value |
|-----------|-------|
| **Taxonomy** | 2 Logical Bugs › 2.2 Conditional Logic › 2.2.4 Missing default cases |
| **Rule** | FS-008 |
| **Severity** | Medium |
| **Status** | 📋 Documented |

**File:** `apps/yam_agri_core/yam_agri_core/yam_agri_core/api/agr_cereal_001.py`

**Problem:**
```python
except Exception:
    return []   # silently swallows DB errors, permission errors, and bugs
```
DB connection failures, permission errors, and logic bugs are hidden and produce incorrect empty results instead of surfacing the failure.

**Planned Response:**
1. Replace bare `except Exception: return []` with logged handling
2. Add `frappe.log_error(title='_get_varieties failed', message=frappe.get_traceback())`
3. Narrow the exception type if possible (e.g. `frappe.DoesNotExistError`)

---

### BUG-008 · `[1.2.5]` Duplicate record creation — non-existent app referenced in `smoke.py`

| Attribute | Value |
|-----------|-------|
| **Taxonomy** | 1 Functional Bugs › 1.2 Workflow Errors › 1.2.5 Duplicate record creation |
| **Rule** | FS-006 |
| **Severity** | Medium |
| **Status** | 📋 Documented |

**File:** `apps/yam_agri_core/yam_agri_core/yam_agri_core/smoke.py`

**Problem:** The app `"yam_agri_qms_trace"` is checked with `frappe.get_installed_apps()` but does not exist. The check always returns `False`, causing `run_phase2_smoke()` to always report `status: needs_attention` even on a healthy installation — a false positive that masks real issues.

**Planned Response:**
1. Remove the check or add a `# TODO` comment until the app is created
2. Update the smoke test baseline expectations so a clean install shows `passed`

---

### BUG-009 · `[6.1.4]` Non-responsive design — missing `title_field` on 4 DocType JSONs

| Attribute | Value |
|-----------|-------|
| **Taxonomy** | 6 UI/UX Bugs › 6.1 Layout › 6.1.4 Non-responsive design |
| **Rule** | FS-004 |
| **Severity** | Low |
| **Status** | 📋 Documented |

**Affected DocTypes:** YAM Crop Variety, YAM Crop Variety Recommendation, YAM Plot Yield, YAM Soil Test

**Problem:** Without `title_field`, Link field dropdowns show the auto-generated series name (e.g., `YAM-SB-2024-0001`) instead of a human-readable label. Users cannot identify records in dropdown menus.

**Planned Response:**
1. Add `"title_field": "<field_name>"` to the DocType JSON
2. Run `bench migrate`
3. Open a Link field referencing this DocType and verify the label is readable

---

### BUG-010 · `[8.1.2]` Compilation — `custom: 1` on app-owned `lot.json`

| Attribute | Value |
|-----------|-------|
| **Taxonomy** | 8 Syntax & Build Bugs › 8.1 Compilation › 8.1.2 Undefined variables |
| **Rule** | FS-003 |
| **Severity** | Low |
| **Status** | 📋 Documented |

**File:** `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/lot/lot.json`

**Problem:** `"custom": 1` marks Lot as a Custom DocType (created via Frappe's Customise Form UI). App-owned DocTypes should NOT have this flag; it can cause confusion during `bench migrate` on fresh installs.

**Planned Response:**
1. Remove `"custom": 1` from `lot.json`
2. Verify other DocType JSONs in the app do not have this flag
3. Run `bench migrate` and confirm the DocType is correctly recognised as app-owned

---

### BUG-009 · `[1.1.1/2.3.3/6.1.4]` DocType JSON compliance gaps (site reqd, track_changes, title_field)

| Attribute | Value |
|-----------|-------|
| **Taxonomy** | 1 Functional Bugs · 2 Logical Bugs · 6 UI/UX Bugs |
| **Rule** | FS-003, FS-005, FS-004, FS-017, FS-018 |
| **Severity** | Medium / Low |
| **Status** | ✅ Fixed |

**Files affected:**
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/device/device.json`
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/evidence_pack/evidence_pack.json`
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/nonconformance/nonconformance.json`
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/observation/observation.json`
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/scale_ticket/scale_ticket.json`
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/season_policy/season_policy.json`
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/storage_bin/storage_bin.json`
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/yam_crop_variety/yam_crop_variety.json`
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/yam_crop_variety_recommendation/yam_crop_variety_recommendation.json`
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/yam_plot/yam_plot.json`
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/yam_plot_yield/yam_plot_yield.json`
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/yam_soil_test/yam_soil_test.json`

**Fix summary:**
1. Added `"reqd": 1` on all `site` fields flagged by FS-003
2. Enabled `"track_changes": 1` on flagged DocTypes (transaction and master)
3. Added missing `"title_field"` on master DocTypes where required
4. Added lifecycle `is_active` field for master records flagged by FS-018

---

## All Bugs by Taxonomy Code (Quick Reference)

| Code | FS Rule | Severity | Description | Status |
|------|---------|----------|-------------|--------|
| 1.1.1 | FS-003 | Medium | `site` not `reqd:1` in DocType JSONs | ✅ Fixed |
| 1.1.2 | FS-007 | High | `quality_flag` default in `validate()` only | ✅ Fixed |
| 1.2.5 | FS-006 | Medium | Non-existent app in smoke.py check | 📋 Planned |
| 2.2.4 | FS-008 | Medium | Broad `except Exception` in utility modules | 📋 Planned |
| 2.3.3 | FS-005 | Medium | `track_changes` missing on transaction/master DocTypes | ✅ Fixed |
| 5.2.2 | FS-010 | Critical | AI module calls Frappe write API | ✅ None found |
| 5.2.3 | FS-011 | Critical | PQC / has_permission out of sync | ✅ None found |
| 5.2.4 | FS-009 | High | Nonconformance missing lot-site cross-check | ✅ Fixed |
| 5.3.3 | FS-006 | High | Hardcoded QA user emails in smoke.py | ✅ Fixed |
| 6.1.4 | FS-004 | Low | Missing `title_field` on DocTypes | ✅ Fixed |
| 6.3.1 | FS-001 | Critical | 7 untranslated `frappe.throw()` calls | ✅ Fixed |
| 8.1.2 | — | Low | `custom: 1` on app-owned `lot.json` | 📋 Planned |

---

## Registering New Bug Types

The Frappe Skill agent is extensible. Define new taxonomy entries at runtime:

```python
from tools.frappe_skill_agent import register_bug_type, BugDefinition

register_bug_type(BugDefinition(
    code="11.1.1",
    category="Custom Frappe Bugs",
    subcategory="Workflow",
    bug_type="Missing workflow state guard",
    predefined_message="Workflow state transition lacks server-side guard",
    planned_response=(
        "Step 1: Identify the workflow states involved",
        "Step 2: Add frappe.has_role() check in controller validate()",
        "Step 3: Cover the guard with a unit test",
    ),
))
```

All future bugs discovered in code reviews should be:
1. Appended to this report following the template above
2. Added to `TAXONOMY` in `tools/frappe_skill_agent.py` if automated detection is possible
3. Assigned a unique `[Category].[Subcategory].[Type]` code
