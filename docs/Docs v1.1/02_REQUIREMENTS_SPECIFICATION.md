# Software Requirements Specification (SRS) — YAM Agri Platform V1.1

> **SDLC Phase:** Requirements  
> **Version:** 1.1  
> **Status:** ⚠️ Draft  
> **Date:** 2026-02-23  
> **Related:** [Project Charter](01_PROJECT_CHARTER.md) | [Data Model](04_DATA_MODEL.md)

---

## 1. Introduction

### 1.1 Purpose
This document specifies the functional and non-functional requirements for the YAM Agri Platform V1.1 (Quality + Traceability Core). It serves as the contract between the product owner, business stakeholders, and the development team.

### 1.2 Scope
Requirements cover the `yam_agri_core` Frappe custom app and its integration with Frappe Framework, ERPNext v16, and Frappe Agriculture. Out-of-scope items are listed in [01_PROJECT_CHARTER.md §2.2](01_PROJECT_CHARTER.md).

### 1.3 Definitions

| Term | Definition |
|------|-----------|
| **Lot** | A batch of cereal-crop grain tracked through the supply chain (harvest, storage, shipment) |
| **Transfer** | A split, merge, or blend operation between Lots |
| **ScaleTicket** | A weight measurement record from a physical or digital scale |
| **QCTest** | A quality control test result attached to a Lot |
| **Certificate** | A compliance certificate (FAO GAP, HACCP, export) with an expiry date |
| **Nonconformance** | A CAPA (Corrective and Preventive Action) record for a quality or compliance issue |
| **EvidencePack** | An audit evidence bundle grouping all relevant documents for a Lot/Site/period |
| **Observation** | A universal sensor/derived signal record (bin temperature, refrigerator probe, weather, NDVI) |
| **Site** | A physical location: farm, silo, store, or office |
| **StorageBin** | A physical bin or compartment within a Site |
| **Device** | An IoT sensor, scale, or camera device registered to a Site |
| **Season Policy** | A configurable rule specifying which QC tests and certificates are mandatory for a given crop/season before a Lot can be shipped |
| **Site isolation** | The guarantee that a user assigned to Site A cannot read or write records belonging to Site B |
| **quality_flag** | A field on Observation records that marks data as `Valid`, `Warning`, or `Quarantine` |

---

## 2. Stakeholder Needs Summary

| Stakeholder | Primary need |
|-------------|-------------|
| Platform owner (U6) | Single source of truth for grain lot quality across all sites |
| QA Inspector (U3) | Structured test entry, certificate management, CAPA workflow |
| Silo Operator (U4) | Real-time bin status, scale weight capture, alert triage |
| Farm Supervisor (U2) | Quick lot creation in the field; GPS tagging; offline support |
| Logistics Coordinator (U5) | Shipment lot status; dispatch blocking when compliance incomplete |
| IT Admin (U7) | Reliable infrastructure; backup/restore; user access management |
| External Auditor (U8) | Evidence packs with full audit trail; compliance summary |

---

## 3. Functional Requirements

### FR-SITE: Site & Location Management

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-SITE-01 | System shall allow creation of Sites with type (Farm / Silo / Store / Office), location, GPS coordinates, and active status | Must |
| FR-SITE-02 | Each Site shall have zero or more StorageBins identified by bin code, capacity (tonnes), and current status | Must |
| FR-SITE-03 | Each StorageBin shall link to one or more Devices (sensors, scales) | Should |
| FR-SITE-04 | System shall prevent users from viewing or editing records of Sites they are not assigned to via User Permissions | Must |

### FR-LOT: Lot Management & Traceability

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-LOT-01 | System shall allow creation of Lots with type (Harvest / Storage / Shipment), crop, variety, quantity (kg), site, storage bin, and harvest date | Must |
| FR-LOT-02 | Every Lot record shall be linked to a Site; system shall reject Lots without a Site | Must |
| FR-LOT-03 | Lot status workflow: Draft → Received → In Storage → Released → Shipped / Rejected | Must |
| FR-LOT-04 | System shall track the parent Lot(s) for every Transfer operation (split / merge / blend) | Must |
| FR-LOT-05 | Trace-backward: given a Lot, system shall display all upstream Lots, QC tests, certificates, and storage bin history | Must |
| FR-LOT-06 | Trace-forward: given a Lot, system shall display all downstream Lots and impacted shipment quantities | Must |
| FR-LOT-07 | Mass-balance enforcement: outgoing quantity across all Transfers from a Lot must not exceed the Lot's available quantity (tolerance configurable) | Must |
| FR-LOT-08 | System shall block submission of a Shipment Lot if the applicable Season Policy's mandatory QC tests or certificates are missing or expired | Must |
| FR-LOT-09 | Lot records shall support photo attachments (field GPS photo, inspection photos) | Should |

### FR-TRANSFER: Transfer Operations

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-TRF-01 | System shall support three Transfer types: Split (one parent → multiple children), Merge (multiple parents → one child), Blend (multiple parents → one child with mix ratios) | Must |
| FR-TRF-02 | Each Transfer shall record: date, operator, type, source Lot(s) with quantities, destination Lot(s) with quantities, and notes | Must |
| FR-TRF-03 | System shall update parent Lot available quantity upon Transfer submission | Must |
| FR-TRF-04 | Transfer submission requires QA Manager approval if the destination is a Shipment Lot (configurable) | Should |

### FR-QC: QC Tests & Certificates

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-QC-01 | System shall allow QCTest records with: Lot, test type, test date, laboratory, result fields (moisture %, protein %, mycotoxin ppb, visual score), pass/fail status, and attachments | Must |
| FR-QC-02 | System shall track mandatory test types per Season Policy (e.g., mycotoxin gating during high-risk season) | Must |
| FR-QC-03 | Certificate records shall include: type (FAO GAP / HACCP / Export / Other), issuing body, issue date, expiry date, file attachment, and linked Lot(s) or Site | Must |
| FR-QC-04 | System shall automatically check certificate expiry and flag/block operations on Lots that have expired certificates | Must |
| FR-QC-05 | QCTest and Certificate records shall be visible in the Lot detail view | Must |

### FR-SCALE: Scale Tickets & Weights

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-SCL-01 | System shall support CSV import of ScaleTickets (columns: ticket number, date, operator, gross weight, tare weight, net weight, lot reference, scale device) | Must |
| FR-SCL-02 | ScaleTicket import shall map tickets to existing Lots and update Lot quantity | Must |
| FR-SCL-03 | System shall detect quantity mismatches (imported weight vs. Lot declared weight > configurable tolerance) and create a Nonconformance record automatically | Must |
| FR-SCL-04 | Manual ScaleTicket entry shall also be supported via Frappe Desk form | Should |

### FR-OBS: Observations (Sensor / IoT Data)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-OBS-01 | Observation records shall capture: device, site, storage bin (optional), timestamp, metric type (temperature / humidity / moisture / CO₂ / NDVI / etc.), value, unit, and quality_flag | Must |
| FR-OBS-02 | System shall validate sensor readings against configured range thresholds; out-of-range readings shall be flagged as `Quarantine` | Must |
| FR-OBS-03 | Quarantined Observations shall not be used in automated decisions or AI suggestions without explicit override | Must |
| FR-OBS-04 | System shall send alerts (Frappe notification) when an Observation exceeds a critical threshold (e.g., bin temperature > 35 °C) | Must |
| FR-OBS-05 | Observations shall be linkable to a StorageBin, Lot, or Site for evidence purposes | Should |

### FR-CAPA: Nonconformances & CAPA

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-CAPA-01 | Nonconformance records shall capture: date, type (Weight Mismatch / Test Failure / Sensor Alert / Customer Complaint), severity (Critical / Major / Minor), description, root cause, corrective action, and status | Must |
| FR-CAPA-02 | CAPA workflow: Open → Under Investigation → Corrective Action Assigned → Verification → Closed | Must |
| FR-CAPA-03 | Closure of a Critical Nonconformance shall require QA Manager approval | Must |
| FR-CAPA-04 | System shall link Nonconformance to the Lot, Site, and/or Certificate that triggered it | Must |

### FR-EVIDENCE: Evidence Packs

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-EVP-01 | System shall generate an EvidencePack for a given Site, date range, and optional Lot | Must |
| FR-EVP-02 | An EvidencePack shall bundle: all QC tests, all certificates, all scale tickets, key Observations, and Nonconformance records for the specified scope | Must |
| FR-EVP-03 | EvidencePack shall be exportable as PDF and as a ZIP of linked files | Must |
| FR-EVP-04 | AI may draft a narrative summary of an EvidencePack (propose-only; user must approve before sending) | Should |

### FR-AI: AI Assistance

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-AI-01 | System shall provide an AI Compliance Check: given a Lot, AI analyses and lists missing QC tests / expired certificates / open nonconformances | Should |
| FR-AI-02 | AI shall draft a suggested corrective action plan for an open Nonconformance (user must review and submit) | Should |
| FR-AI-03 | AI shall summarise an EvidencePack into a human-readable narrative (user must approve before sending to auditor) | Should |
| FR-AI-04 | All AI calls shall route through the AI Gateway which redacts PII, pricing, and customer IDs before sending to any external LLM | Must |
| FR-AI-05 | All AI interactions shall be logged with: timestamp, record reference, prompt hash, response hash, user who triggered it, and whether suggestion was accepted or rejected | Must |
| FR-AI-06 | AI shall never automatically accept or reject Lots, initiate recalls, or send customer communications | Must |

### FR-AUTH: Authentication & Access Control

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-AUTH-01 | System shall use Frappe's built-in authentication (username + password, optional TOTP 2FA) | Must |
| FR-AUTH-02 | Role-based access control shall use ERPNext standard roles mapped to Role Profiles per job function | Must |
| FR-AUTH-03 | Site isolation shall be enforced via Frappe User Permissions: each user is assigned one or more Sites | Must |
| FR-AUTH-04 | New users shall have no Site access by default until explicitly assigned by System Manager | Must |
| FR-AUTH-05 | High-risk actions (lot approve/reject/recall, certificate override, CAPA close) shall require QA Manager workflow approval | Must |

---

## 4. Non-Functional Requirements

### NFR-PERF: Performance

| ID | Requirement |
|----|-------------|
| NFR-PERF-01 | Frappe Desk page load time ≤ 3 seconds on site LAN (100 Mbps) |
| NFR-PERF-02 | CSV scale ticket import: ≤ 30 seconds for 500 rows |
| NFR-PERF-03 | Trace-backward query: ≤ 5 seconds for a Lot with 10 generations of ancestors |
| NFR-PERF-04 | AI suggestion response: ≤ 5 seconds (local Ollama) / ≤ 10 seconds (cloud LLM) |
| NFR-PERF-05 | Dev Docker Compose stack startup: ≤ 5 minutes on 8 GB RAM laptop |

### NFR-SEC: Security

| ID | Requirement |
|----|-------------|
| NFR-SEC-01 | No plaintext secrets in Git repository; all secrets via environment variables from `.env` (never committed) |
| NFR-SEC-02 | HTTPS enforced for all external-facing endpoints; self-signed TLS acceptable for dev |
| NFR-SEC-03 | WireGuard VPN required for staging server access |
| NFR-SEC-04 | AI Gateway must redact PII (names, phone numbers), pricing, and customer IDs before any external LLM call |
| NFR-SEC-05 | All admin actions logged in Frappe's audit log |

### NFR-AVAIL: Availability & Resilience

| ID | Requirement |
|----|-------------|
| NFR-AVAIL-01 | Dev stack: InnoDB crash recovery operational after ungraceful power loss |
| NFR-AVAIL-02 | Field Hub (edge node) must operate fully offline for ≥ 7 days and sync when connectivity returns |
| NFR-AVAIL-03 | All Docker services configured with `restart: always` for automatic recovery after power restore |
| NFR-AVAIL-04 | Daily automated backup to local path; manual offsite backup procedure documented |

### NFR-I18N: Internationalisation

| ID | Requirement |
|----|-------------|
| NFR-I18N-01 | All end-user-facing UI text (forms, alerts, notifications) must be available in Arabic (RTL) |
| NFR-I18N-02 | SMS messages to farmers must use GSM 7-bit Arabic-safe encoding |
| NFR-I18N-03 | Frappe Desk may remain in English for developer/admin roles |

### NFR-DATA: Data Quality & Integrity

| ID | Requirement |
|----|-------------|
| NFR-DATA-01 | Every record must have a `site` field populated; server-side validation must reject records without a site |
| NFR-DATA-02 | Lot mass balance must be enforced server-side, not only client-side |
| NFR-DATA-03 | Sensor readings flagged `Quarantine` must not propagate to any automated decision without explicit override |
| NFR-DATA-04 | All record modifications must be captured in Frappe's document version history |

### NFR-MAINT: Maintainability

| ID | Requirement |
|----|-------------|
| NFR-MAINT-01 | All DocTypes and customisations developed as part of the `yam_agri_core` Frappe custom app (no core patches) |
| NFR-MAINT-02 | Every SDLC document in `docs/Docs v1.1/` reviewed and updated before each release |
| NFR-MAINT-03 | `run.sh` helper script supports: up, down, logs, shell, init, reset, backup, restore, prefetch, offline-init |

---

## 5. External Interface Requirements

### 5.1 CSV Import Interface
- Scale ticket CSV must support columns: `ticket_no`, `date`, `operator`, `gross_weight_kg`, `tare_weight_kg`, `net_weight_kg`, `lot`, `device`
- Rows with missing mandatory fields must be rejected with a row-level error report

### 5.2 IoT Sensor Interface (MQTT)
- Device publishes to topic: `yam/{site_code}/{device_id}/observation`
- Payload: JSON `{ "metric": "temperature", "value": 28.5, "unit": "C", "ts": "2026-02-23T10:00:00Z" }`
- IoT Gateway subscribes, validates, and creates Observation DocType records via Frappe REST API

### 5.3 SMS Interface (TP-01 FarmerSMS — V1.2)
- Africa's Talking webhook POST to `{site}/api/method/yam_agri_core.sms.handle_inbound`
- SMS commands defined in `05_API_SPECIFICATION.md §6`

### 5.4 AI Gateway Interface
- Internal FastAPI service at `http://ai-gateway:8001`
- Frappe calls: `POST /suggest` with `{ "lot": "<id>", "task": "compliance_check" }`
- Response: `{ "suggestion": "...", "log_hash": "...", "model": "..." }`

---

## 6. Constraints & Dependencies

| Constraint | Detail |
|-----------|--------|
| Frappe Framework | v15 / v16 (MariaDB required; no PostgreSQL in V1.1) |
| ERPNext | v16 — standard roles used as permission baseline |
| Frappe Agriculture app | Installed and active (provides Crop, CropCycle, WaterAnalysis DocTypes) |
| MariaDB | 10.6 LTS |
| Redis | v7 |
| Docker | v24+ / Docker Compose v2.x |
| Python | 3.11+ (Frappe requirement) |
| Node.js | 18 LTS (Frappe Desk build requirement) |

---

## 7. Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial SRS for V1.1 |
