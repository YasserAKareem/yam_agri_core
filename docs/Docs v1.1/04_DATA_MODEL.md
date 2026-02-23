# Data Model — YAM Agri Platform V1.1

> **SDLC Phase:** Design  
> **Version:** 1.1  
> **Status:** ⚠️ Draft  
> **Date:** 2026-02-23  
> **Related:** [Requirements Specification](02_REQUIREMENTS_SPECIFICATION.md) | [System Architecture](03_SYSTEM_ARCHITECTURE.md)

---

## 1. Overview

The YAM Agri data model is built on **Frappe DocTypes** — Frappe's managed table abstraction. Every DocType is a database table with:
- Built-in audit trail (created, modified, created_by, modified_by, docstatus)
- Workflow support (via Frappe Workflow)
- REST API auto-generated
- Role-based read/write/submit/cancel/amend permissions

**V1.1 DocTypes (13 custom):**

| # | DocType | Module | Type | Description |
|---|---------|--------|------|-------------|
| 1 | [Site](#2-site) | yam_agri_core | Master | Physical location (farm/silo/store/office) |
| 2 | [StorageBin](#3-storagebin) | yam_agri_core | Master | Physical bin/compartment within a Site |
| 3 | [Device](#4-device) | yam_agri_core | Master | IoT sensor, scale, or camera device |
| 4 | [Lot](#5-lot) | yam_agri_core | Transactional | Grain batch (harvest/storage/shipment) |
| 5 | [Transfer](#6-transfer) | yam_agri_core | Transactional | Split/merge/blend between Lots |
| 6 | [ScaleTicket](#7-scaleticket) | yam_agri_core | Transactional | Weight measurement record |
| 7 | [QCTest](#8-qctest) | yam_agri_core | Transactional | Quality control test result |
| 8 | [Certificate](#9-certificate) | yam_agri_core | Transactional | Compliance certificate |
| 9 | [Nonconformance](#10-nonconformance) | yam_agri_core | Transactional | CAPA record |
| 10 | [EvidencePack](#11-evidencepack) | yam_agri_core | Transactional | Audit evidence bundle |
| 11 | [Complaint](#12-complaint) | yam_agri_core | Transactional | Customer complaint record |
| 12 | [Observation](#13-observation) | yam_agri_core | Transactional | Sensor/derived signal record |
| 13 | [SeasonPolicy](#14-seasonpolicy) | yam_agri_core | Settings | Mandatory QC/cert rules per crop/season |

---

## 2. Site

**Purpose:** Master record for every physical location operated by YAM Agri.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | Data | ✅ | Auto-generated or manual (e.g., `SITE-FARM-001`) |
| `site_name` | Data | ✅ | Display name (e.g., "Al-Asbahi Farm, Taiz") |
| `site_type` | Select | ✅ | Farm / Silo / Store / Office |
| `address` | Text | | Free-text address |
| `governorate` | Data | | Governorate / region |
| `gps_lat` | Float | | Latitude (decimal degrees) |
| `gps_lng` | Float | | Longitude (decimal degrees) |
| `is_active` | Check | ✅ | Default: 1 (active) |
| `notes` | Text | | Free-text notes |

**Key constraints:**
- Every other DocType has a mandatory `site` link field pointing to this DocType
- System Manager creates/manages Sites; end users cannot create Sites

---

## 3. StorageBin

**Purpose:** A physical bin, compartment, or storage unit within a Site.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | Data | ✅ | Auto-generated (e.g., `BIN-001`) |
| `bin_code` | Data | ✅ | Human-readable code (e.g., `A-12`) |
| `site` | Link → Site | ✅ | Parent site |
| `bin_type` | Select | ✅ | Silo / Flat Store / Refrigerator / Other |
| `capacity_kg` | Float | ✅ | Maximum capacity in kg |
| `current_crop` | Link → Crop | | Currently stored crop (from Frappe Agriculture) |
| `current_lot` | Link → Lot | | Currently assigned Lot |
| `status` | Select | ✅ | Empty / In Use / Maintenance |
| `last_cleaned_date` | Date | | Date of last cleaning/fumigation |
| `notes` | Text | | Free-text notes |

---

## 4. Device

**Purpose:** Registers an IoT sensor, scale, or camera device to a Site/Bin.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | Data | ✅ | Auto-generated (e.g., `DEV-001`) |
| `device_code` | Data | ✅ | Unique device identifier |
| `device_type` | Select | ✅ | Temperature Sensor / Humidity Sensor / CO₂ Sensor / Moisture Sensor / Scale / Camera / GPS Tracker / Other |
| `site` | Link → Site | ✅ | Assigned site |
| `storage_bin` | Link → StorageBin | | Assigned bin (optional) |
| `manufacturer` | Data | | Device manufacturer |
| `model` | Data | | Device model |
| `serial_no` | Data | | Serial number |
| `installation_date` | Date | | |
| `last_calibration_date` | Date | | |
| `calibration_due_date` | Date | | Alert generated when overdue |
| `is_active` | Check | ✅ | Default: 1 |

---

## 5. Lot

**Purpose:** The primary traceability unit. Represents a batch of grain at any stage.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | Data | ✅ | Auto-generated (e.g., `LOT-2026-001`) |
| `lot_type` | Select | ✅ | Harvest / Storage / Shipment / Processing |
| `status` | Select | ✅ | Draft / Received / In Storage / Released / Shipped / Rejected |
| `site` | Link → Site | ✅ | Current or origin site |
| `storage_bin` | Link → StorageBin | | Current storage bin (for Storage Lots) |
| `crop` | Link → Crop | ✅ | Crop type (from Frappe Agriculture) |
| `variety` | Data | | Crop variety name |
| `season` | Data | ✅ | e.g., "2026-Spring" |
| `declared_qty_kg` | Float | ✅ | Quantity declared at receipt |
| `available_qty_kg` | Float | ✅ | Quantity available (after transfers) |
| `harvest_date` | Date | | For Harvest Lots |
| `receipt_date` | Date | | For Storage/Shipment Lots |
| `farmer` | Link → Supplier | | Originating farmer (U1) |
| `parent_lots` | Table | | Child table: link(s) to parent Lot(s) via Transfer |
| `gps_lat` | Float | | GPS at capture |
| `gps_lng` | Float | | GPS at capture |
| `notes` | Text | | |

**Workflow states:** `Draft → Received → In Storage → Released → Shipped` or `→ Rejected`

**Validation rules:**
- `available_qty_kg` must always be ≤ `declared_qty_kg`
- Cannot submit a Shipment Lot if Season Policy requirements are unmet (server-side check)
- Cannot delete a Lot that has child Lots via Transfer

---

## 6. Transfer

**Purpose:** Records a split, merge, or blend operation between Lots.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | Data | ✅ | Auto-generated (e.g., `TRF-2026-001`) |
| `transfer_type` | Select | ✅ | Split / Merge / Blend |
| `transfer_date` | Date | ✅ | |
| `operator` | Link → User | ✅ | User who performed the transfer |
| `site` | Link → Site | ✅ | Site where transfer occurred |
| `source_lots` | Table | ✅ | Child table: source Lot + quantity transferred |
| `destination_lots` | Table | ✅ | Child table: destination Lot + quantity received |
| `notes` | Text | | |

**Validation rules:**
- Sum of `source_lots.qty` must equal sum of `destination_lots.qty` (±tolerance)
- Source Lot `available_qty_kg` must be ≥ quantity transferred
- System decrements source Lot and increments destination Lot on submit

---

## 7. ScaleTicket

**Purpose:** Records a weight measurement from a physical or digital scale.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | Data | ✅ | Auto-generated or ticket number |
| `ticket_no` | Data | ✅ | Scale system ticket number |
| `site` | Link → Site | ✅ | |
| `device` | Link → Device | | Scale device |
| `ticket_date` | Datetime | ✅ | |
| `operator` | Link → User | ✅ | |
| `lot` | Link → Lot | ✅ | Associated Lot |
| `gross_weight_kg` | Float | ✅ | |
| `tare_weight_kg` | Float | ✅ | |
| `net_weight_kg` | Float | ✅ | Computed: gross − tare |
| `mismatch_flag` | Check | | Set if net weight deviates from Lot declared qty > tolerance |
| `tolerance_pct` | Float | | Configurable tolerance (default: 2%) |
| `import_batch` | Data | | CSV import batch reference |
| `notes` | Text | | |

---

## 8. QCTest

**Purpose:** Records a quality control test result for a Lot.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | Data | ✅ | Auto-generated |
| `lot` | Link → Lot | ✅ | Tested Lot |
| `site` | Link → Site | ✅ | Test site |
| `test_type` | Select | ✅ | Moisture / Protein / Mycotoxin / Visual Inspection / Germination / Pesticide Residue / Heavy Metals / Other |
| `test_date` | Date | ✅ | |
| `laboratory` | Data | | Testing laboratory name |
| `tested_by` | Link → User | ✅ | |
| `moisture_pct` | Float | | Result: moisture % |
| `protein_pct` | Float | | Result: protein % |
| `mycotoxin_ppb` | Float | | Result: mycotoxin (ppb) |
| `visual_score` | Select | | Pass / Acceptable / Fail |
| `overall_result` | Select | ✅ | Pass / Fail |
| `certificate` | Link → Certificate | | Certificate issued for this test |
| `notes` | Text | | |
| `attachments` | Attach | | PDF lab report |

---

## 9. Certificate

**Purpose:** Tracks compliance certificates with expiry enforcement.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | Data | ✅ | Auto-generated |
| `cert_type` | Select | ✅ | FAO GAP / HACCP / Export / ISO 22000 / Phytosanitary / Other |
| `site` | Link → Site | ✅ | |
| `lot` | Link → Lot | | Associated Lot (optional — some certs are site-level) |
| `issuing_body` | Data | ✅ | Name of certifying body |
| `issue_date` | Date | ✅ | |
| `expiry_date` | Date | ✅ | |
| `is_expired` | Check | | System-computed: expiry_date < today |
| `certificate_file` | Attach | | PDF scan |
| `status` | Select | ✅ | Active / Expired / Revoked |
| `notes` | Text | | |

**Automated checks:**
- Scheduled job runs daily: flags certificates where `expiry_date < today + 30 days` with a warning notification
- Server-side submit validator on Lot: blocks if linked mandatory Certificate is `Expired` or `Revoked`

---

## 10. Nonconformance

**Purpose:** CAPA (Corrective and Preventive Action) record for quality/compliance issues.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | Data | ✅ | Auto-generated (e.g., `NC-2026-001`) |
| `nc_type` | Select | ✅ | Weight Mismatch / Test Failure / Sensor Alert / Customer Complaint / Certificate Issue / Other |
| `severity` | Select | ✅ | Critical / Major / Minor |
| `status` | Select | ✅ | Open / Under Investigation / Corrective Action Assigned / Verification / Closed |
| `site` | Link → Site | ✅ | |
| `lot` | Link → Lot | | Associated Lot |
| `certificate` | Link → Certificate | | Associated Certificate |
| `description` | Text | ✅ | Description of the nonconformance |
| `root_cause` | Text | | Root cause analysis |
| `corrective_action` | Text | | Corrective action plan |
| `assigned_to` | Link → User | | Responsible person |
| `due_date` | Date | | |
| `closed_date` | Date | | |
| `closed_by` | Link → User | | |
| `ai_suggestion` | Text | | AI-drafted CAPA suggestion (assistive only; user must review) |
| `notes` | Text | | |

**Workflow:** `Open → Under Investigation → Corrective Action Assigned → Verification → Closed`

**Validation:** Critical Nonconformance closure requires QA Manager role approval via Frappe Workflow.

---

## 11. EvidencePack

**Purpose:** Bundles all relevant documents for an audit or customer evidence request.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | Data | ✅ | Auto-generated (e.g., `EP-2026-001`) |
| `site` | Link → Site | ✅ | |
| `from_date` | Date | ✅ | Period start |
| `to_date` | Date | ✅ | Period end |
| `lot` | Link → Lot | | Optional — scope to a single Lot |
| `generated_by` | Link → User | ✅ | |
| `generated_on` | Datetime | ✅ | |
| `qc_tests` | Table | | Child table: linked QCTest records |
| `certificates` | Table | | Child table: linked Certificate records |
| `scale_tickets` | Table | | Child table: linked ScaleTicket records |
| `observations` | Table | | Child table: key Observation records |
| `nonconformances` | Table | | Child table: linked Nonconformance records |
| `narrative` | Long Text | | AI-drafted narrative (assistive only; user must approve before sending) |
| `export_pdf` | Attach | | Generated PDF export |
| `status` | Select | ✅ | Draft / Finalised / Sent to Auditor |

---

## 12. Complaint

**Purpose:** Customer complaint record linked to Lots and Nonconformance.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | Data | ✅ | Auto-generated |
| `site` | Link → Site | ✅ | |
| `customer` | Link → Customer | | ERPNext Customer |
| `complaint_date` | Date | ✅ | |
| `complaint_type` | Select | ✅ | Quality / Quantity / Delivery / Documentation / Other |
| `description` | Text | ✅ | |
| `lot` | Link → Lot | | Impacted Lot |
| `nonconformance` | Link → Nonconformance | | Linked CAPA |
| `status` | Select | ✅ | Open / Under Review / Resolved / Closed |
| `resolution` | Text | | |
| `resolved_by` | Link → User | | |
| `resolved_date` | Date | | |

---

## 13. Observation

**Purpose:** Universal model for all sensor and derived signal readings.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | Data | ✅ | Auto-generated |
| `device` | Link → Device | ✅ | Source device |
| `site` | Link → Site | ✅ | |
| `storage_bin` | Link → StorageBin | | Source bin (optional) |
| `lot` | Link → Lot | | Associated Lot (optional) |
| `timestamp` | Datetime | ✅ | Time of measurement |
| `metric_type` | Select | ✅ | Temperature / Humidity / Moisture / CO₂ / NDVI / Flood Index / Rainfall / Irrigation Flow / Other |
| `value` | Float | ✅ | Measured value |
| `unit` | Data | ✅ | Unit of measurement (e.g., "°C", "%", "ppm") |
| `quality_flag` | Select | ✅ | Valid / Warning / Quarantine |
| `alert_sent` | Check | | Whether an alert notification was sent |
| `threshold_min` | Float | | Configured lower threshold |
| `threshold_max` | Float | | Configured upper threshold |
| `notes` | Text | | |

**Validation rules:**
- `value < threshold_min` or `value > threshold_max` → `quality_flag = Warning` or `Quarantine`
- Quarantined Observations are not used in automated decisions

---

## 14. SeasonPolicy

**Purpose:** Configures which QC tests and certificates are mandatory before a Lot of a given crop/season can be shipped.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | Data | ✅ | Auto-generated |
| `crop` | Link → Crop | ✅ | Applies to this crop |
| `season` | Data | ✅ | e.g., "2026-Spring" |
| `is_high_risk_season` | Check | | If checked: mycotoxin gating applies |
| `mandatory_tests` | Table | ✅ | Child table: required QCTest types |
| `mandatory_cert_types` | Table | ✅ | Child table: required Certificate types |
| `is_active` | Check | ✅ | Default: 1 |
| `notes` | Text | | |

> ⚠️ **Proposed addition:** A Season Policy Matrix document is needed to define the initial policy values for each crop/season combination. See `00_INDEX.md` proposed additions.

---

## 5. Entity Relationship Summary

```
Site ──────────┬── StorageBin ──── Device
               │
               ├── Lot ───────────┬── QCTest ──── Certificate
               │    │              ├── ScaleTicket
               │    │              ├── Nonconformance
               │    │              └── EvidencePack
               │    │
               │    └── Transfer (source/dest Lots)
               │
               ├── Observation ── Device
               │
               └── Certificate (site-level)
```

---

## 6. Workflow State Machines

### 6.1 Lot Workflow

```
[Draft]
   │  (receive at site)
   ▼
[Received]
   │  (move to bin)
   ▼
[In Storage]
   │  (release for shipment — requires Season Policy check)
   ▼
[Released]
   │  (shipment dispatched)
   ▼
[Shipped]

From any state → [Rejected] (requires QA Manager approval)
```

### 6.2 QCTest Workflow

```
[Draft]
   │  (complete test)
   ▼
[Submitted]
   │  (QA Manager review — for Critical tests)
   ▼
[Approved] or [Rejected]
```

### 6.3 Nonconformance Workflow

```
[Open]
   │  (investigation begins)
   ▼
[Under Investigation]
   │  (corrective action assigned)
   ▼
[Corrective Action Assigned]
   │  (verification complete)
   ▼
[Verification]
   │  (closure — Critical: requires QA Manager)
   ▼
[Closed]
```

---

## 7. Naming Conventions

| DocType | Naming series |
|---------|--------------|
| Site | `SITE-####` |
| StorageBin | `BIN-####` |
| Device | `DEV-####` |
| Lot | `LOT-{YYYY}-####` |
| Transfer | `TRF-{YYYY}-####` |
| ScaleTicket | `SCL-{YYYY}-####` |
| QCTest | `QCT-{YYYY}-####` |
| Certificate | `CERT-{YYYY}-####` |
| Nonconformance | `NC-{YYYY}-####` |
| EvidencePack | `EP-{YYYY}-####` |
| Complaint | `COMP-{YYYY}-####` |
| Observation | `OBS-{YYYY}-####` |
| SeasonPolicy | `SP-{CROP}-{SEASON}` |

---

## 8. Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial data model document — V1.1 |
