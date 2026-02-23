# Test Plan — YAM Agri Platform V1.1

> **SDLC Phase:** Testing  
> **Version:** 1.1  
> **Status:** ⚠️ Draft  
> **Date:** 2026-02-23  
> **Related:** [Requirements Specification](02_REQUIREMENTS_SPECIFICATION.md) | [Project Charter](01_PROJECT_CHARTER.md)

---

## 1. Test Strategy

### 1.1 Testing Approach

YAM Agri V1.1 uses a **manual acceptance test** strategy (the owner, Yasser, approves without writing code). The platform owner can verify acceptance tests by:
1. Logging into Frappe Desk at `http://localhost:8000/desk`
2. Following the step-by-step procedures in Section 4 below
3. Checking that all exit criteria listed in each test case are met

Automated tests (Python unit tests in `yam_agri_core/tests/`) are added by the developer for critical business rule validations.

### 1.2 Test Levels

| Level | Description | Who runs it |
|-------|-------------|------------|
| Unit tests | Python functions for validation logic (mass balance, season policy check) | Developer (automated in CI) |
| Integration tests | DocType create/submit/workflow transitions | Developer (automated in CI) |
| **Acceptance tests (AT)** | End-to-end business scenarios (Section 4) | Platform Owner / QA Manager (manual) |
| Security tests | Site isolation check, secret scan | Developer + CI |
| Performance tests | Page load, CSV import timing | Developer (manual spot check) |
| Regression tests | Re-run all ATs after any change | Before each release |

### 1.3 Test Environments

| Environment | Purpose | When used |
|-------------|---------|----------|
| Dev (Docker Compose) | Development and unit/integration testing | Daily |
| Dev (with test data) | Acceptance test execution | Before staging deploy |
| Staging (k3s) | UAT and performance testing | After dev passes all ATs |
| Production | Not used for testing | Never |

---

## 2. Test Data

### 2.1 Minimum Seed Data Required

Before running acceptance tests, ensure the following are set up:

| Entity | Required | Example |
|--------|----------|---------|
| Sites | 2 (for isolation test) | `SITE-FARM-001`, `SITE-SILO-002` |
| StorageBins | 3 | `BIN-A01`, `BIN-A02`, `BIN-B01` |
| Devices | 2 | `DEV-SCALE-001`, `DEV-TEMP-001` |
| Crops | 2 | `Wheat`, `Sorghum` (from Frappe Agriculture) |
| Users | 3 | `site_a_user`, `qa_manager`, `admin` |
| SeasonPolicy | 1 | `SP-Wheat-2026-Spring` (requires: Moisture test + Mycotoxin test + FAO GAP cert) |

### 2.2 Demo Data Script

```bash
bench --site yam.localhost execute yam_agri_core.yam_agri_core.seed.agr_cereal_001_sample_data.create_sample_data \
  --kwargs '{"confirm": 1, "site_name": "SITE-FARM-001", "crop_name": "Wheat", "plot_name": "P-001"}'
```

---

## 3. Test Case Inventory

### 3.1 Unit / Integration Tests (Automated)

| Test ID | Function | Assertion |
|---------|----------|-----------|
| UT-001 | `Lot.validate()` | Reject if `site` is empty |
| UT-002 | `Lot.validate()` | Reject if `available_qty_kg > declared_qty_kg` |
| UT-003 | `Transfer.validate()` | Reject if source Lot available qty < transfer qty |
| UT-004 | `Transfer.on_submit()` | Source Lot available_qty decrements correctly |
| UT-005 | `Transfer.on_submit()` | Destination Lot available_qty increments correctly |
| UT-006 | `Lot.before_submit()` | Reject Shipment Lot if Season Policy mandatory test missing |
| UT-007 | `Lot.before_submit()` | Reject Shipment Lot if mandatory Certificate is expired |
| UT-008 | `Observation.validate()` | Set quality_flag = Quarantine when value > threshold_max |
| UT-009 | `ScaleTicket.on_submit()` | Create Nonconformance if mismatch > tolerance |
| UT-010 | Permission query | Site A user cannot fetch Site B Lot via list API |

---

## 4. Acceptance Test Scenarios (Manual)

Each test is structured as: **Precondition → Steps → Expected result (pass/fail)**.

---

### AT-01: Create Site + StorageBin + Lot

**Precondition:** System admin logged in; no existing test data.

**Steps:**
1. Go to yam_agri_core → Site → New
2. Fill in: Site Name = "Test Farm 1", Site Type = Farm, is_active = Yes → Save
3. Go to StorageBin → New → fill: Bin Code = "T-01", Site = "Test Farm 1", Bin Type = Silo, Capacity = 5000 kg → Save
4. Go to Lot → New → fill: Lot Type = Harvest, Crop = Wheat, Season = 2026-Spring, Site = "Test Farm 1", Declared Qty = 3000 kg → Save

**Expected result:**
- ✅ All three records saved without errors
- ✅ Site, StorageBin, and Lot appear in their respective list views
- ✅ Lot status = Draft

---

### AT-02: Create QCTest + Attach Certificate to a Lot

**Precondition:** AT-01 completed; Lot "LOT-2026-001" exists.

**Steps:**
1. Go to QCTest → New → fill: Lot = LOT-2026-001, Test Type = Moisture, Test Date = today, Tested By = current user, Moisture % = 12.5, Overall Result = Pass → Submit
2. Go to Certificate → New → fill: Cert Type = FAO GAP, Site = "Test Farm 1", Lot = LOT-2026-001, Issuing Body = "FAO", Issue Date = today, Expiry Date = one year from today → Submit
3. Open LOT-2026-001 → check linked QCTest and Certificate sections

**Expected result:**
- ✅ QCTest created and linked to Lot
- ✅ Certificate created, status = Active
- ✅ Lot detail view shows both QCTest and Certificate in their child tables

---

### AT-03: Transfer — Split Lot into Shipment Lot

**Precondition:** LOT-2026-001 with available_qty = 3000 kg.

**Steps:**
1. Go to Transfer → New
2. Fill: Transfer Type = Split, Site = "Test Farm 1", Source Lots = [LOT-2026-001, qty = 1500]
3. Destination Lots = [new Lot: Lot Type = Shipment, qty = 1500]
4. Submit Transfer

**Expected result:**
- ✅ Transfer submitted without errors
- ✅ LOT-2026-001 `available_qty_kg` now = 1500 (was 3000)
- ✅ New Shipment Lot created with `declared_qty_kg = 1500`
- ✅ Transfer record shows parent-child relationship

---

### AT-04: Trace Backward from Shipment Lot

**Precondition:** AT-03 completed; Shipment Lot exists.

**Steps:**
1. Open Shipment Lot created in AT-03
2. Click "Trace Backward" button (or call API: `/api/method/yam_agri_core.api.traceability.trace_backward?lot=<shipment_lot>`)

**Expected result:**
- ✅ Response shows LOT-2026-001 as ancestor
- ✅ Shows linked QCTest (Moisture - Pass) from AT-02
- ✅ Shows linked Certificate (FAO GAP - Active) from AT-02
- ✅ Shows storage bin "T-01" in bin history

---

### AT-05: Trace Forward from Storage Lot

**Precondition:** AT-03 completed; LOT-2026-001 is the storage lot.

**Steps:**
1. Open LOT-2026-001
2. Click "Trace Forward" button (or call API: `/api/method/yam_agri_core.api.traceability.trace_forward?lot=LOT-2026-001`)

**Expected result:**
- ✅ Response shows Shipment Lot as descendant
- ✅ Shows impacted quantity: 1500 kg
- ✅ Shows Shipment Lot status

---

### AT-06: Block Shipment if Mandatory QC/Cert Missing

**Precondition:** SeasonPolicy `SP-Wheat-2026-Spring` requires: Moisture test + Mycotoxin test + FAO GAP cert.

**Steps:**
1. Create a new Shipment Lot for Wheat / 2026-Spring season with NO QCTests and NO Certificates
2. Attempt to submit the Shipment Lot

**Expected result:**
- ✅ System blocks submission with error message listing the missing requirements:
  - "Mycotoxin test required by 2026-Spring season policy"
  - "Moisture test required by 2026-Spring season policy"
  - "FAO GAP certificate required"
- ✅ Lot status remains Draft

---

### AT-07: Import ScaleTicket CSV — Quantity Update + Mismatch Flag

**Precondition:** LOT-2026-001 exists with declared_qty = 3000 kg. Scale ticket CSV prepared.

**CSV content:**
```csv
ticket_no,date,operator,gross_weight_kg,tare_weight_kg,net_weight_kg,lot,device
SCL-001,2026-02-23,admin,3150,150,3000,LOT-2026-001,DEV-SCALE-001
SCL-002,2026-02-23,admin,2350,150,2200,LOT-2026-001,DEV-SCALE-001
```

**Steps:**
1. Go to Scale Ticket Import → Upload `scale_tickets.csv`, Site = "Test Farm 1", Tolerance = 2%
2. Click Import

**Expected result:**
- ✅ SCL-001 imported; net_weight (3000 kg) matches declared_qty → no mismatch
- ✅ SCL-002 imported; net_weight (2200 kg) deviates from declared_qty by > 2% → `mismatch_flag = True`
- ✅ Nonconformance record created automatically for SCL-002 mismatch

---

### AT-08: Post Sensor Observation — Invalid Data Quarantined

**Precondition:** Device `DEV-TEMP-001` configured with threshold_max = 35 °C.

**Steps:**
1. Create an Observation: Device = DEV-TEMP-001, Site = "Test Farm 1", Bin = BIN-A01, Metric Type = Temperature, Value = 42, Unit = °C
2. Save

**Expected result:**
- ✅ Observation saved with `quality_flag = Quarantine` (value 42 > threshold_max 35)
- ✅ Frappe notification sent to Operator / QA Manager
- ✅ Quarantined observation NOT used in any automated compliance decision

---

### AT-09: Generate EvidencePack for Date Range + Site

**Precondition:** AT-01 through AT-08 completed; data exists for SITE-FARM-001.

**Steps:**
1. Go to EvidencePack → New
2. Fill: Site = "Test Farm 1", From Date = 2026-02-01, To Date = 2026-02-28
3. Click "Generate Pack"

**Expected result:**
- ✅ EvidencePack created containing:
  - At least 1 QCTest (from AT-02)
  - At least 1 Certificate (from AT-02)
  - At least 2 ScaleTickets (from AT-07)
  - At least 1 Observation (from AT-08)
  - At least 1 Nonconformance (from AT-07)
- ✅ PDF export works
- ✅ EvidencePack status = Draft (ready for review before sending to auditor)

---

### AT-10: Site Isolation — Site A User Cannot See Site B Data

**Precondition:** Two sites exist (SITE-A, SITE-B). User `site_a_user` has User Permission for SITE-A only.

**Steps:**
1. Create Lot in SITE-A (LOT-A-001) and Lot in SITE-B (LOT-B-001)
2. Login as `site_a_user`
3. Go to Lot list view

**Expected result:**
- ✅ List view shows only LOT-A-001
- ✅ LOT-B-001 is NOT visible
- ✅ Direct URL: `/app/lot/LOT-B-001` returns permission error (403)
- ✅ API call: `GET /api/resource/Lot/LOT-B-001` returns 403 PermissionError

---

## 5. Non-Functional Test Checks

| Check | Method | Pass criteria |
|-------|--------|--------------|
| Page load time | Browser DevTools Network tab | List view < 3 seconds |
| CSV import (500 rows) | Prepare 500-row CSV and time the import | < 30 seconds |
| Dev stack startup | `time bash run.sh up` | < 5 minutes |
| Backup completion | `bash run.sh backup` and measure time | < 10 minutes |
| Memory usage | `docker stats` during normal use | Total < 3 GB |

---

## 6. Defect Classification

| Severity | Definition | Expected resolution |
|---------|------------|-------------------|
| **Critical** | Blocks an acceptance test; data loss or security breach | Fix before V1.1 release |
| **Major** | Core feature broken; workaround exists but impacts operations | Fix before V1.1 release |
| **Minor** | UI issue, cosmetic, or edge case | Fix before or at V1.1 |
| **Enhancement** | Nice to have; not blocking | Schedule in V1.2 backlog |

---

## 7. Test Sign-Off Checklist

Before V1.1 is declared complete, the following must all be checked:

- [ ] AT-01 through AT-10 all pass on Dev environment
- [ ] AT-01 through AT-10 all pass on Staging (k3s)
- [ ] UT-001 through UT-010 all pass in CI
- [ ] No Critical or Major defects open
- [ ] Secret scan CI check passes on `main` branch
- [ ] Docker Compose stack starts clean on a fresh machine
- [ ] Memory usage < 3 GB during AT execution
- [ ] Platform owner (Yasser) has signed off on all 10 acceptance tests

---

## 8. Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial test plan — V1.1 |
