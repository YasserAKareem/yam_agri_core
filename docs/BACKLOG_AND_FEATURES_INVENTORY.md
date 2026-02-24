# YAM Agri Platform — Backlog & Features Inventory

> **Document type:** Backlog Registry + Feature Inventory  
> **Version:** 1.0  
> **Date:** 2026-02-23  
> **Owner:** YasserAKareem  
> **Status:** ✅ Baseline — 80 backlog items catalogued  
> **Related:** [Project Charter](../Docs%20v1.1/01_PROJECT_CHARTER.md) | [WBS & Gantt](WBS_AND_GANTT.md) | [SRS](../Docs%20v1.1/02_REQUIREMENTS_SPECIFICATION.md)

---

## 1. Inventory Overview

This document is the **single source of truth** for all planned features across every release of the YAM Agri Platform. It combines:

1. **V1.1 Feature Inventory** — the 12 core DocTypes + acceptance tests + non-functional requirements  
2. **AI Backlog (AGR-CEREAL-001 → 080)** — 80 AI-augmented capabilities mapped to 9 supply-chain stages  
3. **Integration Feature Inventory** — cross-domain integrations applicable to future releases  
4. **Release Roadmap** — which items ship in which release  

---

## 2. V1.1 Core Feature Inventory

### 2.1 Core DocTypes (12)

| # | DocType | Purpose | Acceptance Test | V1.1? |
|---|---------|---------|----------------|-------|
| 1 | **Site** | Farm / Silo / Store / Office location master | AT-01, AT-10 | ✅ |
| 2 | **StorageBin** | Physical bin within a Site | AT-01, AT-08 | ✅ |
| 3 | **Device** | IoT sensor, scale, or camera | AT-08 | ✅ |
| 4 | **Lot** | Primary traceability unit (harvest/storage/shipment) | AT-01–AT-06 | ✅ |
| 5 | **Transfer** | Split / Merge / Blend operations | AT-03 | ✅ |
| 6 | **ScaleTicket** | Weight measurement record | AT-07 | ✅ |
| 7 | **QCTest** | Quality control test result | AT-02 | ✅ |
| 8 | **Certificate** | Compliance cert (FAO GAP / HACCP / Export) | AT-02, AT-06 | ✅ |
| 9 | **Nonconformance** | CAPA record | AT-07, AT-08 | ✅ |
| 10 | **EvidencePack** | Audit evidence bundle | AT-09 | ✅ |
| 11 | **Complaint** | Customer complaint record | — | ✅ |
| 12 | **Observation** | Universal sensor/IoT signal | AT-08 | ✅ |

### 2.2 V1.1 Functional Requirements Summary

| Req Group | Count | Key IDs | Status |
|-----------|-------|---------|--------|
| Site & Location (FR-SITE) | 4 | FR-SITE-01–04 | Planned Ph2 |
| Lot Management (FR-LOT) | 9 | FR-LOT-01–09 | Planned Ph2–Ph3 |
| Transfer Operations (FR-TRF) | 4 | FR-TRF-01–04 | Planned Ph3 |
| QC Tests & Certificates (FR-QC) | 5 | FR-QC-01–05 | Planned Ph4 |
| Scale Tickets (FR-SCL) | 4 | FR-SCL-01–04 | Planned Ph5 |
| Observations / IoT (FR-OBS) | 5 | FR-OBS-01–05 | Planned Ph5 |
| Nonconformances / CAPA (FR-CAPA) | 4 | FR-CAPA-01–04 | Planned Ph4 |
| Evidence Packs (FR-EVP) | 4 | FR-EVP-01–04 | Planned Ph7 |
| AI Assistance (FR-AI) | 6 | FR-AI-01–06 | Planned Ph6 |
| Auth & Access Control (FR-AUTH) | 5 | FR-AUTH-01–05 | Planned Ph2 |
| **Total V1.1 FRs** | **50** | | |

### 2.3 V1.1 Acceptance Tests

| AT # | Scenario | Phase | Status |
|------|----------|-------|--------|
| AT-01 | Create Site + StorageBin + Lot | Ph2 | ⬜ Pending |
| AT-02 | Create QCTest + attach Certificate to Lot | Ph4 | ✅ Automated + Evidenced |
| AT-03 | Transfer: split Lot into shipment Lot | Ph3 | ⬜ Pending |
| AT-04 | Trace backward from shipment Lot | Ph3 | ⬜ Pending |
| AT-05 | Trace forward from storage Lot | Ph3 | ⬜ Pending |
| AT-06 | Block shipment if mandatory QC/cert missing | Ph4 | ✅ Automated + Evidenced |
| AT-07 | Import ScaleTicket CSV → qty update + mismatch NC | Ph5 | ⬜ Pending |
| AT-08 | Sensor Observation: invalid data quarantined | Ph5 | ⬜ Pending |
| AT-09 | Generate EvidencePack for date range + site | Ph7 | ⬜ Pending |
| AT-10 | Site isolation: Site A user cannot see Site B | Ph2 | ⬜ Pending |

### 2.4 V1.1 Non-Functional Requirements

| NFR Group | Key Targets |
|-----------|-------------|
| Performance | Page load ≤ 3 s LAN; CSV import ≤ 30 s/500 rows; trace ≤ 5 s; AI ≤ 10 s |
| Security | No secrets in Git; WireGuard VPN; PII redaction; HTTPS |
| Availability | InnoDB crash recovery; offline 7 days; `restart: always` |
| i18n | Arabic/RTL UI; GSM-safe SMS |
| Data Integrity | Site field mandatory; mass-balance server-side; quarantine propagation blocked |
| Maintainability | All changes in `yam_agri_core` app; no core patches; docs updated each release |

---

## 3. AI Backlog — Full Inventory (AGR-CEREAL-001 → 080)

### Stage Legend

| Stage | Supply Chain Phase | Target Release |
|-------|--------------------|---------------|
| A | Pre-season Planning | V1.3 |
| B | Input Procurement | V1.3 |
| C | Field Ops & Planting | V1.3 |
| D | In-season Crop Management | V1.2 |
| E | Harvest Operations | V1.2 |
| F | Storage Management | V1.2 |
| G | Logistics & Trading | V2.0 |
| H | Processing & Manufacturing | V2.0 |
| I | Customer & Market | V2.1+ |

### AI Mode Legend

| Mode | Description | V1.1 Allowed? |
|------|-------------|--------------|
| Read-only | Dashboards / forecasts / analytics; no writes | ✅ Yes |
| Propose-only | AI surfaces recommendation; human decides | ✅ Yes |
| Execute-with-approval | System prepares action; manager confirms | ✅ Yes (with workflow gate) |
| Autonomous | AI executes without human confirmation | ❌ Never |

---

### Stage A — Pre-season Planning (10 items) — Target: V1.3

| ID | Feature | AI Mode | Actionability | KPIs | Target |
|----|---------|---------|---------------|------|--------|
| AGR-CEREAL-001 | Crop/Variety Selection | Optimization + Prediction | Propose-only | Margin/ha; Yield/ha; Rotation compliance | V1.3 |
| AGR-CEREAL-002 | Fertility Plan Optimization | Optimization | Propose-only | Nutrient efficiency; Cost/ha; Yield stability | V1.3 |
| AGR-CEREAL-003 | Planting Window Prediction | Prediction | Propose-only | On-time planting %; Yield delta; Replant rate | V1.3 |
| AGR-CEREAL-004 | Planning Impact Simulation | Simulation | Read-only | CO2e/ton; Soil health proxy; Audit readiness | V1.3 |
| AGR-CEREAL-005 | Acreage Aggregation Forecast | Forecasting | Read-only | Acreage forecast error; Downstream stockouts | V1.3 |
| AGR-CEREAL-006 | Budget Scenario Engine | Simulation | Read-only | Budget variance; ROI accuracy | V1.3 |
| AGR-CEREAL-007 | Irrigation Feasibility & Plan | Optimization + Prediction | Propose-only | Water use efficiency; Stress days reduced | V1.3 |
| AGR-CEREAL-008 | Disease-Resistant Variety Reco | Prediction | Propose-only | Disease incidence; Fungicide cost reduction | V1.3 |
| AGR-CEREAL-009 | Field Accessibility Risk | Prediction | Propose-only | Delay days; Compaction events | V1.3 |
| AGR-CEREAL-010 | Geo-Regulatory Input Flags | RAG-docs + Rules | Read-only | Violations prevented; Audit pass rate | V1.3 |

**Key integrations:** GIS/field boundaries, soil tests, weather/climate, historical yields, regulatory databases.

---

### Stage B — Input Procurement (8 items) — Target: V1.3

| ID | Feature | AI Mode | Actionability | KPIs | Target |
|----|---------|---------|---------------|------|--------|
| AGR-CEREAL-011 | Input Demand Forecast | Forecasting | Propose-only | Stockout %; Excess inventory $; Service level | V1.3 |
| AGR-CEREAL-012 | Supplier Risk Scoring | Risk scoring | Propose-only | Defect rate; Delivery reliability; Loss prevention | V1.3 |
| AGR-CEREAL-013 | Forward Buying Scenarios | Simulation | Read-only | Cost savings; Hedge effectiveness | V1.3 |
| AGR-CEREAL-014 | Receiving Match Automation | Document AI + Anomaly | Execute-with-approval | Receiving cycle time; Mismatch rate; Expiry incidents | V1.3 |
| AGR-CEREAL-015 | SDS & Restricted Use Validation | RAG-docs | Read-only | Violations prevented; Audit readiness | V1.3 |
| AGR-CEREAL-016 | Deliveries vs Field Schedule | Optimization | Propose-only | Idle time; Missed windows | V1.3 |
| AGR-CEREAL-017 | RFQ Comparison Copilot | Copilot | Propose-only | Cycle time; Contract quality; Savings | V1.3 |
| AGR-CEREAL-018 | Fair Input Allocation | Optimization | Propose-only | Allocation satisfaction; Yield loss avoided | V1.3 |

**Key integrations:** Price feeds, supplier DBs, purchase history, acreage plans, safety data sheets.

---

### Stage C — Field Ops & Planting (9 items) — Target: V1.3

| ID | Feature | AI Mode | Actionability | KPIs | Target |
|----|---------|---------|---------------|------|--------|
| AGR-CEREAL-019 | Planter Calibration Anomaly | Anomaly detection | Execute-with-approval | Emergence uniformity; Replant %; Yield delta | V1.3 |
| AGR-CEREAL-020 | Work Orders & Notes Copilot | Copilot | Propose-only | Documentation completeness; Audit pass rate | V1.3 |
| AGR-CEREAL-021 | Crew & Machine Scheduling | Optimization | Propose-only | Utilization; Overtime; On-time ops % | V1.3 |
| AGR-CEREAL-022 | Compaction Risk Advisor | Prediction | Propose-only | Soil damage events; Delay days | V1.3 |
| AGR-CEREAL-023 | Fuel/Parts Stock Forecast | Forecasting | Propose-only | Downtime; Emergency purchases | V1.3 |
| AGR-CEREAL-024 | Seed Lot Capture | Workflow automation | Execute-with-approval | Traceability completeness; Recall time reduction | V1.3 |
| AGR-CEREAL-025 | Stand Count via Vision | Vision | Read-only | Detection speed; Replant decision accuracy | V1.3 |
| AGR-CEREAL-026 | Deviation Impact Analytics | Analytics copilot | Read-only | Variance visibility; Corrective actions taken | V1.3 |
| AGR-CEREAL-027 | Safety Incident Risk | Risk prediction | Propose-only | Incident rate; Near-miss closure time | V1.3 |

**Key integrations:** GPS telemetry, machine sensors, soil moisture, HR/crew schedules, CCTV vision.

---

### Stage D — In-season Crop Management (12 items) — Target: V1.2

| ID | Feature | AI Mode | Actionability | KPIs | Target |
|----|---------|---------|---------------|------|--------|
| AGR-CEREAL-028 | Stress-to-Prescription | Vision + Decision support | Propose-only | Response time; Yield loss avoided | V1.2 |
| AGR-CEREAL-029 | Disease Identification | Vision | Propose-only | Diagnosis accuracy; Fungicide ROI | V1.2 |
| AGR-CEREAL-030 | Irrigation Optimizer | Optimization | Execute-with-approval | Water savings; Stress days reduced | V1.2 |
| AGR-CEREAL-031 | Variable Rate Nitrogen | Optimization + Explainability | Propose-only | Protein targets hit; N efficiency | V1.2 |
| AGR-CEREAL-032 | Pest Outbreak Predictor | Prediction | Propose-only | Detection lead time; Yield loss avoided | V1.2 |
| AGR-CEREAL-033 | Localized Recommendations | RAG-docs + Prediction | Propose-only | Adoption rate; Performance uplift | V1.2 |
| AGR-CEREAL-034 | Spray Timing Advisor | Prediction + Rules | Propose-only | Efficacy; Drift incidents; Re-spray rate | V1.2 |
| AGR-CEREAL-035 | Calibrated Yield Forecast | Probabilistic forecasting | Read-only | Forecast error; Usefulness score | V1.2 |
| AGR-CEREAL-036 | Loss Assessment Assist | Vision + Anomaly | Propose-only | Claim cycle time; Dispute rate | V1.2 |
| AGR-CEREAL-037 | Soil Health Tracking | Analytics + Estimation | Read-only | Reporting cycle time; Data completeness | V1.2 |
| AGR-CEREAL-038 | Alert Ranking | Alert ranking | Read-only | Alert action rate; False alert rate | V1.2 |
| AGR-CEREAL-039 | Data Quality Guardrails | Anomaly + Data validation | Execute-with-approval | Data error rate; Model stability | V1.2 |

**Key integrations:** Satellite NDVI (Sentinel-2), drone imagery, weather APIs, IoT soil sensors, ERP cost data.

---

### Stage E — Harvest Operations (8 items) — Target: V1.2

| ID | Feature | AI Mode | Actionability | KPIs | Target |
|----|---------|---------|---------------|------|--------|
| AGR-CEREAL-040 | Harvest Window Predictor | Prediction | Propose-only | Losses avoided; Drying cost reduction | V1.2 |
| AGR-CEREAL-041 | Combine Settings Optimizer | Optimization | Propose-only | Loss %; Throughput; Fuel/ton | V1.2 |
| AGR-CEREAL-042 | Harvest-to-Truck Dispatch | Dispatch optimization | Execute-with-approval | Idle time; Turnaround time | V1.2 |
| AGR-CEREAL-043 | Mycotoxin Risk Flags | Prediction + Anomaly | Propose-only | Contamination incidents; Rejected loads | V1.2 |
| AGR-CEREAL-044 | Yield Map Insights | Analytics copilot | Propose-only | Action adoption; Next-season uplift | V1.2 |
| AGR-CEREAL-045 | Harvest Predictive Maintenance | Predictive maintenance | Propose-only | Unplanned downtime; Repair cost | V1.2 |
| AGR-CEREAL-046 | Harvest Cost Visibility | Analytics automation | Read-only | Cost visibility latency; Margin variance | V1.2 |
| AGR-CEREAL-047 | Silo Intake Scheduling | Scheduling optimization | Execute-with-approval | Queue time; Reject rate | V1.2 |

**Key integrations:** Combine telemetry, ScaleTicket data (from V1.1), weather, QCTest data (from V1.1), GPS truck tracking.

---

### Stage F — Storage Management (8 items) — Target: V1.2

| ID | Feature | AI Mode | Actionability | KPIs | Target |
|----|---------|---------|---------------|------|--------|
| AGR-CEREAL-048 | Aeration Control | Anomaly + Control optimization | Execute-with-approval | Spoilage %; Energy cost; Hotspot incidents | V1.2 |
| AGR-CEREAL-049 | Blend Optimization | Optimization | Propose-only | Contract compliance %; Revenue/ton | V1.2 |
| AGR-CEREAL-050 | Shrink/Theft Detection | Anomaly detection | Read-only | Shrink %; Detection lead time | V1.2 |
| AGR-CEREAL-051 | Storage Inspection Copilot | Copilot + Checklist | Propose-only | Inspection completeness; Findings reduced | V1.2 |
| AGR-CEREAL-052 | Inventory Reconciliation | Anomaly + Automation | Execute-with-approval | Reconciliation time; Adjustment rate | V1.2 |
| AGR-CEREAL-053 | Moisture Out-of-Spec Predictor | Prediction | Propose-only | Rework reduced; Spec compliance | V1.2 |
| AGR-CEREAL-054 | Capacity Constraint Feedback | Constraint optimization | Propose-only | Overflow events; Emergency transport cost | V1.2 |
| AGR-CEREAL-055 | IoT Security Monitoring | Security anomaly | Read-only | Incident rate; Time-to-detect | V1.2 |

**Key integrations:** Bin sensor Observations (from V1.1), Lot transfer data, aeration hardware APIs, camera feeds.

---

### Stage G — Logistics & Trading (7 items) — Target: V2.0

| ID | Feature | AI Mode | Actionability | KPIs | Target |
|----|---------|---------|---------------|------|--------|
| AGR-CEREAL-056 | Routing with Constraints | Optimization | Execute-with-approval | On-time %; Cost/ton-km | V2.0 |
| AGR-CEREAL-057 | Export Docs Automation | Document AI | Execute-with-approval | Doc error rate; Cycle time | V2.0 |
| AGR-CEREAL-058 | Freight Billing Anomalies | Anomaly detection | Propose-only | Dispute rate; Overpayment prevented | V2.0 |
| AGR-CEREAL-059 | In-transit Quality Risk | Anomaly + Prediction | Propose-only | Rejected loads; Claims reduced | V2.0 |
| AGR-CEREAL-060 | Cargo Theft/Diversion | Anomaly detection | Read-only | Theft incidents; Detection lead time | V2.0 |
| AGR-CEREAL-061 | Shipment Carbon Reporting | Estimation + Reporting automation | Read-only | Reporting cycle time; Auditability | V2.0 |
| AGR-CEREAL-062 | Exception Management Copilot | Workflow copilot | Propose-only | Resolution time; Service level | V2.0 |

**Key integrations:** ERPNext Delivery Notes, GPS tracking, customs APIs, freight carrier APIs, EvidencePack (V1.1).

---

### Stage H — Processing & Manufacturing (9 items) — Target: V2.0

| ID | Feature | AI Mode | Actionability | KPIs | Target |
|----|---------|---------|---------------|------|--------|
| AGR-CEREAL-063 | Incoming Lot Classification | Classification + Anomaly | Execute-with-approval | Reject accuracy; Contamination incidents | V2.0 |
| AGR-CEREAL-064 | Process Parameter Optimization | Optimization | Propose-only | Yield; Energy/ton; Throughput | V2.0 |
| AGR-CEREAL-065 | Packaging Line PdM | Predictive maintenance | Propose-only | Downtime; Defect rate | V2.0 |
| AGR-CEREAL-066 | HACCP Evidence Builder | RAG-docs + Evidence automation | Read-only | Audit prep time; Findings reduced | V2.0 |
| AGR-CEREAL-067 | Batch Scheduling with Constraints | Scheduling optimization | Propose-only | Throughput; Changeover time; OEE | V2.0 |
| AGR-CEREAL-068 | Formulation Optimizer | Optimization + Simulation | Propose-only | Time-to-formulate; Quality pass rate | V2.0 |
| AGR-CEREAL-069 | Label/Allergen Compliance | Rules + Document AI | Execute-with-approval | Label compliance; Recall prevention | V2.0 |
| AGR-CEREAL-070 | Yield Loss RCA Copilot | Analytics copilot | Read-only | Yield variance explained; Corrective action rate | V2.0 |
| AGR-CEREAL-071 | Provenance Query during Incidents | Traceability graph + RAG | Read-only | Time-to-trace; Containment time | V2.0 |

**Key integrations:** QCTest + Certificate + EvidencePack (V1.1), ERPNext Manufacturing module, HACCP plan DB.

---

### Stage I — Customer & Market (9 items) — Target: V2.1+

| ID | Feature | AI Mode | Actionability | KPIs | Target |
|----|---------|---------|---------------|------|--------|
| AGR-CEREAL-072 | Retail Demand Forecast | Forecasting | Read-only | Forecast error; Stockouts %; Waste % | V2.1+ |
| AGR-CEREAL-073 | Allocation Optimization | Optimization | Propose-only | Service level; Transport cost | V2.1+ |
| AGR-CEREAL-074 | Expiry Waste Predictor | Prediction | Propose-only | Waste %; Markdown effectiveness | V2.1+ |
| AGR-CEREAL-075 | Pricing & Promo Optimizer | Optimization | Propose-only | Margin; Volume; Promo ROI | V2.1+ |
| AGR-CEREAL-076 | Complaint-to-Lot Linkage | NLP + Traceability | Read-only | Time-to-trace; Repeat complaint rate | V2.1+ |
| AGR-CEREAL-077 | Fill-rate Anomaly Monitor | Anomaly detection | Read-only | Fill-rate; Late orders | V2.1+ |
| AGR-CEREAL-078 | Recall Execution Automation | Workflow automation | Execute-with-approval | Time-to-remove; % units recovered | V2.1+ |
| AGR-CEREAL-079 | Assortment Optimization | Analytics + Clustering | Propose-only | Sales lift; OOS reduction | V2.1+ |
| AGR-CEREAL-080 | End-to-End Margin Copilot | Analytics copilot | Read-only | Margin visibility time; Leakage recovered | V2.1+ |

**Key integrations:** Customer portals, ERP Sales module, Complaint DocType (V1.1), Lot traceability (V1.1).

---

## 4. Backlog Item Status Tracker

| ID | Stage | Target Release | Status | Implemented? |
|----|-------|---------------|--------|-------------|
| AGR-CEREAL-001 | A | V1.3 | 🟡 In Progress | Partial (recommender stub in `api/agr_cereal_001.py`) |
| AGR-CEREAL-002–010 | A | V1.3 | ⬜ Backlog | Not started |
| AGR-CEREAL-011–018 | B | V1.3 | ⬜ Backlog | Not started |
| AGR-CEREAL-019–027 | C | V1.3 | ⬜ Backlog | Not started |
| AGR-CEREAL-028–039 | D | V1.2 | ⬜ Backlog | Not started |
| AGR-CEREAL-040–047 | E | V1.2 | ⬜ Backlog | Not started |
| AGR-CEREAL-048–055 | F | V1.2 | ⬜ Backlog | Not started |
| AGR-CEREAL-056–062 | G | V2.0 | ⬜ Backlog | Not started |
| AGR-CEREAL-063–071 | H | V2.0 | ⬜ Backlog | Not started |
| AGR-CEREAL-072–080 | I | V2.1+ | ⬜ Backlog | Not started |

---

## 5. Release Roadmap Summary

```
V1.1  (2026-Q3)   Quality + Traceability Core (12 DocTypes, 50 FRs, 10 ATs)
  └─ Foundation for all future AI backlog items

V1.2  (2026-Q4)   Storage & Harvest AI (Stages D, E, F — 28 items)
  └─ Depends on V1.1 Observation, Lot, QCTest, ScaleTicket DocTypes

V1.3  (2027-Q1)   Pre-season Planning & Field Ops AI (Stages A, B, C — 27 items)
  └─ Depends on V1.1 Site, StorageBin, Device; V1.2 sensor integrations

V2.0  (2027-Q3)   Logistics, Trading & Processing AI (Stages G, H — 16 items)
  └─ Depends on V1.1 EvidencePack, Transfer, ScaleTicket; V1.3 full platform

V2.1+ (2028+)     Customer, Market & Platform AI (Stage I — 9 items)
  └─ Depends on full supply-chain traceability from V1.1–V2.0
```

---

## 6. AI Mode Distribution (All 80 Items)

| AI Mode | Count | % | Notes |
|---------|-------|---|-------|
| Propose-only | 39 | 49% | Largest group — human always decides |
| Read-only | 20 | 25% | Analytics, dashboards, forecasts |
| Execute-with-approval | 21 | 26% | Requires QA Manager / workflow gate |
| **Autonomous** | **0** | **0%** | **Never implemented per platform rules** |

---

## 7. Integration Feature Inventory (Cross-Domain)

These integration capabilities span multiple backlog items and are tracked separately from the AI backlog.

### 7.1 Data Integrations (External)

| Integration | Backlog items | Target release | Type |
|-------------|--------------|---------------|------|
| Weather API (OpenWeatherMap / meteoblue) | AGR-003, 007, 032, 034, 040 | V1.2 | REST pull |
| Sentinel-2 NDVI (satellite) | AGR-028, 035, 037 | V1.2 | GEE / STAC API |
| Soil lab data upload | AGR-002, 031, 037 | V1.3 | CSV + manual |
| MQTT IoT sensor stream | AT-08 / FR-OBS-01 | V1.1 | MQTT broker |
| SMS gateway (Africa's Talking) | TP-01 FarmerSMS | V1.2 | Webhook |
| GPS/telematics (truck/machine) | AGR-042, 056, 060 | V2.0 | REST / FTP |
| Customs / export docs API | AGR-057 | V2.0 | REST |
| Freight carrier API | AGR-056, 058 | V2.0 | REST |
| Retail POS / customer portal | AGR-072–080 | V2.1+ | REST |
| Carbon emission factor DB | AGR-004, 061 | V2.0 | Static lookup |

### 7.2 Internal Integrations (ERPNext Modules)

| ERPNext Module | Connects to YAM feature | Target release |
|----------------|------------------------|---------------|
| Stock (Warehouse / Bin) | StorageBin, Lot transfers | V1.1 |
| Quality Management | QCTest, Nonconformance | V1.1 |
| Agriculture (CropCycle, WaterAnalysis) | Lot, Site | V1.1 |
| HR (Employee, Department) | RBAC / Role Profiles | V1.1 |
| Manufacturing (BOM, Work Order) | Processing AI (Stage H) | V2.0 |
| Selling (Sales Order, Delivery Note) | Shipment Lot, Logistics | V2.0 |
| Accounts (Cost Center) | Budget AI (Stage A) | V1.3 |
| CRM (Issue → Complaint) | Complaint DocType | V1.1 |

### 7.3 Touchpoint App Integrations

| App | Persona | Channel | Target release |
|-----|---------|---------|---------------|
| TP-01 FarmerSMS | Smallholder farmer (U1) | SMS / USSD | V1.2 |
| TP-02 FieldPWA | Farm Supervisor (U2) | Mobile PWA (offline-first) | V1.2 |
| TP-03 Auditor Portal | External Auditor (U8) | Web (read-only) | V1.2 |
| TP-04 Donor Dashboard | FAO / Donors | Web (read-only) | V1.3 |

---

## 8. Priority Matrix

| Priority | Criteria | Example items |
|----------|----------|---------------|
| **P0 — Must V1.1** | Blocks compliance, traceability, or site isolation | All 12 DocTypes, AT-01–AT-10, FR-AUTH-03 |
| **P1 — Should V1.1** | Significantly improves quality or safety | AI Compliance Check (FR-AI-01), CAPA workflow |
| **P2 — Nice V1.1** | Useful but not blocking | Auditor portal stub, mobile form hints |
| **P3 — V1.2** | Storage/Harvest AI enablers | AGR-CEREAL-028–055 |
| **P4 — V1.3** | Planning & Field Ops AI | AGR-CEREAL-001–027 |
| **P5 — V2.0+** | Logistics, processing, customer AI | AGR-CEREAL-056–080 |

---

## 9. Backlog Governance

1. **Item lifecycle:** Idea → Backlog → Refined → Sprint Ready → In Progress → Done → Released
2. **Refinement:** Each backlog item must have: Acceptance Criteria, DocType list, API sketch, and security review notes before "Sprint Ready"
3. **Prioritisation:** Product Owner reviews backlog every 2 weeks; re-prioritise based on business value and dependencies
4. **AI items:** All AI features require AI Governance sign-off (FR-AI-04 to FR-AI-06 must pass) before merge
5. **Site isolation rule:** Every new DocType must include a `site` link field and permission query condition from day one

---

## 10. Document History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial backlog & features inventory — 80 items catalogued |
