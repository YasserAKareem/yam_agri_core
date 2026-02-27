# Release Notes — YAM Agri Platform V1.1

> **SDLC Phase:** Release / Closure  
> **Version:** 1.1  
> **Status:** ⚠️ Draft — staging release gate deferred (Phase 8 access dependency)  
> **Date:** 2026-02-27  
> **Related:** [Project Charter](01_PROJECT_CHARTER.md) | [Test Plan](07_TEST_PLAN.md)

---

## V1.1 — Quality + Traceability Core

**Release target:** Pending acceptance test completion on staging  
**Release type:** Initial production release  
**Platform:** Frappe v16 + ERPNext v16 + Frappe Agriculture + yam_agri_core custom app

---

## 1. What's New in V1.1

### 1.1 Core DocTypes (13)

| DocType | Description |
|---------|-------------|
| **Site** | Master record for farm, silo, store, and office locations |
| **StorageBin** | Physical bin/compartment within a Site; status tracking |
| **Device** | IoT sensor, scale, or camera device registered to a Site |
| **Lot** | Primary traceability unit — Harvest, Storage, or Shipment grain batch |
| **Transfer** | Split, merge, or blend operations between Lots with mass-balance enforcement |
| **ScaleTicket** | Weight measurement records; CSV import with automatic mismatch detection |
| **QCTest** | Quality control test results (moisture, protein, mycotoxin, visual inspection) |
| **Certificate** | Compliance certificates with automatic expiry checking |
| **Nonconformance** | CAPA records with workflow (Open → Investigation → Action → Verification → Closed) |
| **EvidencePack** | Audit evidence bundle generator for a Site/period/Lot |
| **Complaint** | Customer complaint records linked to Lots and CAPA |
| **Observation** | Universal sensor/derived signal model with quality_flag validation |

Plus:
| DocType | Description |
|---------|-------------|
| **SeasonPolicy** | Configures mandatory QC tests and certificates per crop/season for shipment gating |

### 1.2 Traceability Engine

- **Backward trace:** From any Lot, see all upstream ancestors, QC tests, certificates, and storage bin history
- **Forward trace:** From any Lot, see all downstream shipments and impacted quantities
- **Mass-balance enforcement:** Transfer quantities validated server-side; cannot over-transfer

### 1.3 QA/QC Controls

- Season Policy gating: configurable mandatory tests and certificates per crop/season; blocks shipment until met
- Certificate expiry checking: automatic expiry flag + 30-day advance notification
- Scale ticket mismatch detection: auto-creates Nonconformance on weight variance > tolerance
- Sensor Observation validation: out-of-range readings quarantined (`quality_flag = Quarantine`)

### 1.4 AI Assistance (Propose-Only)

- **Compliance Check:** AI analyses a Lot and lists missing QC tests, expired certificates, open nonconformances
- **CAPA Draft:** AI drafts a suggested corrective action plan for a Nonconformance (user must review and submit)
- **Evidence Narrative:** AI drafts a human-readable summary for an EvidencePack (user must approve before sending)
- All AI calls routed through AI Gateway with PII/pricing redaction and full audit logging
- AI is **assistive only** — no autonomous actions permitted

### 1.5 Crop/Variety Recommendation (AGR-CEREAL-001)

- Deterministic, explainable variety recommender
- API method: `yam_agri_core.yam_agri_core.api.agr_cereal_001.get_variety_recommendations`
- Script Report: `YAM Crop Variety Recommendations`
- Demo data script included

### 1.6 Access Control & Site Isolation

- RBAC via ERPNext standard roles mapped to Role Profiles
- Site isolation enforced at both User Permissions level and permission query condition level
- High-risk actions (lot release, CAPA closure, certificate override) require QA Manager workflow approval
- New users have zero Site access by default

### 1.7 Dev Environment (Docker Compose)

- Full Docker Compose stack: Frappe + ERPNext + Agriculture + yam_agri_core
- `run.sh` helper with 11 commands (up, down, logs, shell, init, reset, backup, restore, prefetch, offline-init, status)
- Yemen-resilient: offline image archive, InnoDB crash recovery, solar-power restart configuration
- Memory-efficient: total stack ~2.5–3 GB RAM

### 1.8 SDLC Documentation Set (Docs v1.1)

New comprehensive documentation set in `docs/Docs v1.1/`:

| Document | Coverage |
|----------|---------|
| 00_INDEX.md | Navigation and doc map |
| 01_PROJECT_CHARTER.md | Scope, objectives, stakeholders, risks |
| 02_REQUIREMENTS_SPECIFICATION.md | Functional + non-functional requirements |
| 03_SYSTEM_ARCHITECTURE.md | 11-layer architecture + data flows |
| 04_DATA_MODEL.md | 13 DocTypes + fields + workflows |
| 05_API_SPECIFICATION.md | REST/RPC/AI Gateway API reference |
| 06_SECURITY_AND_RBAC.md | RBAC, site isolation, secrets, AI security |
| 07_TEST_PLAN.md | 10 acceptance tests + 10 unit tests |
| 08_DEPLOYMENT_GUIDE.md | Dev/staging/production deployment |
| 09_OPERATIONS_RUNBOOK.md | Day-to-day ops, backup, monitoring |
| 10_COMPLIANCE_AND_QUALITY.md | FAO GAP + HACCP + ISO 22000 mapping |
| 11_AI_GOVERNANCE.md | AI safety policy + audit log + model governance |
| 12_RELEASE_NOTES.md | This document |

---

## 2. Known Gaps (Identified — Deferred to V1.2+)

The following items were identified during documentation review as gaps in V1.1. They are tracked for future releases:

| Gap | Priority | Target release |
|-----|----------|---------------|
| Season Policy Matrix (actual values per crop/season) | High | V1.1 — QA Manager to complete |
| FAO GAP Middle East full control checklist | High | V1.1 — QA Manager to complete |
| HACCP Hazard Analysis formal worksheet | High | V1.1 — QA Manager to complete |
| DocType field-level validation rules (complete) | High | V1.1 completion |
| Workflow state machine diagrams (visual) | High | V1.1 completion |
| FarmerSMS app (TP-01) — SMS lot registration | High | V1.2 |
| FieldPWA (TP-02) — mobile offline app | High | V1.2 |
| Weather API integration (Open-Meteo) | Medium | V1.2 |
| Sentinel NDVI remote sensing | Medium | V1.2 |
| Incident Response Playbook | Medium | V1.1 completion |
| Disaster Recovery Plan | Medium | V1.1 completion |
| Data Retention & Privacy Policy | Medium | V1.1 completion |
| AI Model Card (per model) | Low | V1.2 |
| Org Chart diagram (visual) | Low | V1.1 completion |
| Prometheus + Grafana monitoring stack | Low | V1.2 |
| Vehicle inspection / transport hygiene log | Low | V1.2 |
| Soil health test (Frappe Agriculture) | Low | V1.2 |

---

## 3. Acceptance Test Status

| Test | Description | Dev | Staging |
|------|-------------|-----|---------|
| AT-01 | Create Site + StorageBin + Lot | ✅ | 🔲 |
| AT-02 | QCTest + Certificate attach | ✅ | 🔲 |
| AT-03 | Transfer: split Lot | ✅ | 🔲 |
| AT-04 | Trace backward | ✅ | 🔲 |
| AT-05 | Trace forward | ✅ | 🔲 |
| AT-06 | Block shipment on missing QC/cert | ✅ | 🔲 |
| AT-07 | Scale ticket CSV import + mismatch | ✅ | 🔲 |
| AT-08 | Sensor Observation quarantine | ✅ | 🔲 |
| AT-09 | EvidencePack generation | ✅ | 🔲 |
| AT-10 | Site isolation | ✅ | 🔲 |

**Status legend:** ✅ Passed · ❌ Failed · 🔲 Not yet run

Staging status remains pending due unresolved remote access path (`yam-staging.vpn.internal`) from current operator workstation.

---

## 4. Dependencies & Versions

| Dependency | Version | Notes |
|-----------|---------|-------|
| Frappe Framework | v16 (v15 also supported) | Core platform |
| ERPNext | v16 | ERP module |
| Frappe Agriculture | Latest (main branch) | Crop, CropCycle, WaterAnalysis DocTypes |
| yam_agri_core | V1.1 | This release |
| MariaDB | 10.6 LTS | Database |
| Redis | 7 | Cache and queue |
| Python | 3.11+ | Runtime |
| Node.js | 18 LTS | Asset build |
| Docker Engine | 24+ | Container runtime |
| Docker Compose | v2.x | Dev orchestration |

---

## 5. Migration Notes

### 5.1 Fresh Installation

No migration required for fresh installations. Follow [08_DEPLOYMENT_GUIDE.md §3](08_DEPLOYMENT_GUIDE.md).

### 5.2 Upgrading from Pre-V1.1

There is no formal pre-V1.1 version. If upgrading from a development snapshot:

```bash
bash run.sh backup  # always backup first
bash run.sh shell
bench --site ${SITE_NAME} migrate
bench --site ${SITE_NAME} clear-cache
```

---

## 6. Breaking Changes

None — this is the initial V1.1 release.

---

## 7. Version Roadmap

| Release | Focus | Status |
|---------|-------|--------|
| **V1.1** | Quality + Traceability Core (this release) | ⚠️ In progress (staging gate deferred) |
| V1.2 | Storage & Harvest AI layer (stages D, E, F) | 🔲 Planned |
| V1.3 | Pre-season Planning & Field Ops AI (stages A, B, C) | 🔲 Planned |
| V2.0 | Logistics, Trading & Processing AI (stages G, H) | 🔲 Future |
| V2.1+ | Customer, Market & Platform AI (stage I) | 🔲 Future |

---

## 8. Sign-Off

| Role | Name | Sign-off | Date |
|------|------|---------|------|
| Platform Owner (U6) | Yasser | 🔲 Pending | — |
| QA Manager (U3) | TBD | 🔲 Pending | — |
| IT Admin (U7) | Ibrahim Al-Sana'ani | 🔲 Pending | — |

---

## 9. Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial release notes — V1.1 |
| 1.1 | 2026-02-27 | Codex | Updated dev acceptance status and recorded Phase 8 staging access defer gate |
