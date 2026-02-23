# Project Charter — YAM Agri Platform V1.1

> **SDLC Phase:** Initiation  
> **Version:** 1.2  
> **Status:** ✅ Approved — owner sign-off pending on v1.2  
> **Date:** 2026-02-23  
> **Owner:** YasserAKareem  
> **Related:** [WBS & Gantt](../planning/WBS_AND_GANTT.md) | [Backlog & Features Inventory](../planning/BACKLOG_AND_FEATURES_INVENTORY.md) | [Excel WBS+Gantt](../planning/YAM_AGRI_WBS_GANTT.xlsx)  

---

## 1. Project Overview

### 1.1 Project Name
**YAM Agri Platform — V1.1 (Quality + Traceability Core)**

### 1.2 Executive Summary
YAM Agri is a cereal-crop supply chain business operating across multiple farm, silo, store, and office sites in the Middle East (Yemen). The V1.1 release establishes the **foundational Quality + Traceability Core** on Frappe + ERPNext, enabling:

- Full lot traceability (splits, merges, blends) from harvest to shipment
- QA/QC evidence capture (tests, certificates, scale tickets, sensor data)
- Compliance controls aligned with FAO GAP (Middle East) and HACCP/ISO 22000
- AI-assisted (assistive only, never autonomous) operations
- Multi-site data isolation and role-based access control

### 1.3 Business Justification
YAM Agri aims to build a smart, valuable enterprise by using technology to:

| Business goal | Platform capability |
|---------------|-------------------|
| Win customer trust | Verifiable quality records + evidence packs |
| Protect margins | Better storage and harvest decisions via sensor data |
| Reduce waste and losses | Early-warning signals from IoT sensors |
| Comply with food-safety standards | FAO GAP + HACCP/ISO 22000 aligned workflows |
| Grow to auditor/donor portal | Structured evidence packs and audit trails |

---

## 2. Scope

### 2.1 In Scope (V1.1)

| Area | Deliverable |
|------|------------|
| Data model | 12 core DocTypes (Site, StorageBin, Device, Lot, Transfer, ScaleTicket, QCTest, Certificate, Nonconformance, EvidencePack, Complaint, Observation) |
| Traceability | Backward and forward lot tracing across splits, merges, blends |
| QA/QC controls | Test recording, certificate management, season policy gating |
| Scale integration | CSV import → ScaleTicket → Lot quantity update + mismatch flag |
| Sensor data | Universal Observation model; invalid data quarantined via `quality_flag` |
| Access control | Site isolation, RBAC via ERPNext standard roles + Role Profiles |
| AI assistance | Read-only and propose-only AI suggestions (compliance gap check, CAPA draft, evidence pack summary) |
| Dev environment | Docker Compose stack on developer laptop; Yemen-resilient setup |
| Staging environment | K3s single-node (after dev passes all acceptance tests) |

### 2.2 Out of Scope (V1.1 — deferred to V1.2+)

| Excluded item | Target release |
|---------------|---------------|
| Pre-season planning AI (backlog stages A–C) | V1.3 |
| Storage/harvest optimization AI (backlog stages D–F) | V1.2 |
| Logistics/trading/processing AI (stages G–H) | V2.0 |
| Customer/market platform AI (stage I) | V2.1+ |
| Kubernetes production deployment | After staging passes |
| SMS/USSD FarmerSMS app (TP-01) build | V1.2 |
| Mobile PWA FieldPWA (TP-02) build | V1.2 |
| External integrations (Weather API, Sentinel NDVI) | V1.2+ |
| Payments integration | V2.0+ |
| Carbon reporting | V2.1+ |

### 2.3 Assumptions

1. Frappe Framework v15/v16 + ERPNext v16 + Frappe Agriculture app are the permanent base platforms.
2. Docker Compose is the primary dev environment; Kubernetes (k3s) is the staging/production target.
3. The team operates under Yemen infrastructure constraints: daily power outages, intermittent internet, 8 GB RAM laptops.
4. All business data stays in the self-hosted Frappe instance; only anonymised/redacted context is sent to cloud LLMs.
5. AI is **assistive only** — no automated lot accept/reject, no automated recalls, no unsupervised customer communications.

### 2.4 Constraints

| Constraint | Detail |
|-----------|--------|
| **Infrastructure** | Daily power outages; offline-first design required |
| **Connectivity** | 2G/3G only at field sites; dev must work fully offline |
| **Hardware** | 8 GB RAM laptops; total Docker stack ≤ 6 GB RAM |
| **Language** | Arabic/RTL-first for all end-user interfaces |
| **Budget** | Open-source stack preferred; cloud costs minimized |
| **Security** | No secrets in Git; WireGuard VPN for staging access |
| **AI safety** | AI never executes actions autonomously |

---

## 3. Stakeholders

### 3.1 Internal Stakeholders

| ID | Persona | Job function | Platform role | Responsibility |
|----|---------|-------------|---------------|---------------|
| U6 | **Yasser (Owner)** | Agri-Business Owner | Product owner | Vision, priorities, final approvals, AI governance |
| U3 | **QA / Food Safety Inspector** | Compliance | QA Manager | QC tests, certificates, HACCP, approvals |
| U4 | **Silo / Store Operator** | Operations | Stock User | Bin monitoring, scale tickets, stock reconciliation |
| U2 | **Farm Supervisor** | Field ops | Agriculture Manager | Lot creation, GPS capture, crew scheduling |
| U5 | **Logistics Coordinator** | Logistics | Delivery User | Shipment dispatch, BOL generation |
| U7 | **System Admin / IT (Ibrahim Al-Sana'ani)** | IT / DevOps | System Manager | Infrastructure, backups, user management |
| — | **Application Developer** | Dev team | Developer | Frappe DocTypes, Python, JavaScript |

### 3.2 External Stakeholders

| ID | Persona | Interaction |
|----|---------|------------|
| U1 | **Smallholder Farmer (Ahmed Al-Shaibani)** | SMS lot registration and alerts |
| U8 | **External Auditor / Donor** | Read-only evidence pack portal |
| — | **FAO / Donor agencies** | Compliance evidence review |
| — | **Customers** | Quality certificates (indirect) |

---

## 4. Success Criteria

### 4.1 Acceptance Test Scenarios (must all pass before V1.1 is complete)

| # | Scenario | How to verify |
|---|----------|--------------|
| AT-01 | Create Site + StorageBin + Lot | Records appear in Frappe Desk |
| AT-02 | Create QCTest + attach Certificate to a Lot | Certificate linked to Lot; expiry shown |
| AT-03 | Transfer: split Lot into shipment Lot | Child Lot created; mass balance upheld |
| AT-04 | Trace backward from shipment Lot | Shows QC/certs/bin history in trace view |
| AT-05 | Trace forward from storage Lot | Shows impacted shipments + quantities |
| AT-06 | Block shipment if mandatory QC/cert missing | System prevents submit; reason shown |
| AT-07 | Import ScaleTicket CSV → quantity updates + mismatch flags | Nonconformance created on mismatch |
| AT-08 | Post sensor Observation; invalid data quarantined | `quality_flag = Quarantine` set; alert sent |
| AT-09 | Generate EvidencePack for date range + site | Pack contains all relevant docs |
| AT-10 | Site isolation: Site A user cannot see Site B data | Permission query confirms isolation |

### 4.2 Non-Functional Success Criteria

| Criterion | Target |
|----------|--------|
| Dev stack startup time | < 5 minutes on 8 GB RAM laptop |
| Frappe Desk page load | < 3 seconds on site LAN |
| Scale ticket CSV import | < 30 seconds for 500 rows |
| AI suggestion response time | < 5 seconds (local) / < 10 seconds (cloud) |
| Backup completion | < 10 minutes for full site backup |
| Data loss on power cut | Max 30 seconds of writes (InnoDB crash recovery) |

---

## 5. Project Timeline (V1.1)

> Full WBS decomposition and Gantt chart: [docs/planning/WBS_AND_GANTT.md](../planning/WBS_AND_GANTT.md) | [docs/planning/YAM_AGRI_WBS_GANTT.xlsx](../planning/YAM_AGRI_WBS_GANTT.xlsx)

### 5.1 Phase Summary

| Phase | Description | Target dates | Milestone | Exit criteria |
|-------|-------------|-------------|-----------|--------------|
| Phase 0 | Dev runtime (Docker Compose) | W1–W2 (2026-02-23 → 2026-03-06) | M0 | Stack starts; Frappe login works |
| Phase 1 | Custom app scaffolding | W2–W3 (→ 2026-03-13) | M1 | `yam_agri_core` app installs; CI green |
| Phase 2 | Core DocTypes (12) | W3–W6 (→ 2026-04-03) | M2 | AT-01, AT-10 pass |
| Phase 3 | Traceability engine | W6–W8 (→ 2026-04-17) | M3 | AT-03, AT-04, AT-05 pass |
| Phase 4 | QA/QC controls + season policy | W8–W10 (→ 2026-05-01) | M4 | AT-02, AT-06 pass |
| Phase 5 | Scale + Sensor integrations | W10–W12 (→ 2026-05-15) | M5 | AT-07, AT-08 pass |
| Phase 6 | AI Assist layer (propose-only) | W12–W14 (→ 2026-05-29) | M6 | AI suggestions visible; governance tests pass |
| Phase 7 | EvidencePack generator | W13–W15 (→ 2026-06-05) | M7 | AT-09 passes |
| Phase 8 | Staging (k3s) | W15–W18 (→ 2026-06-26) | M8 | All 10 acceptance tests pass on staging |
| Phase 9 | V1.1 release | W18–W20 (→ 2026-07-10) | M9 | Owner sign-off; release notes published; tag v1.1.0 |

### 5.2 Summary Gantt (ASCII)

```
Phase                W1  W2  W3  W4  W5  W6  W7  W8  W9 W10 W11 W12 W13 W14 W15 W16 W17 W18 W19 W20
Ph0 Dev Env          ███ ███
Ph1 App Scaffold             ███
Ph2 DocTypes (12)                ███ ███ ███
Ph3 Traceability                         ███ ███
Ph4 QA/QC + Season                               ███ ███
Ph5 Scale + Sensor                                       ███ ███
Ph6 AI Assist                                                    ███ ███
Ph7 EvidencePack                                                 ███ ███
Ph8 Staging k3s                                                          ███ ███ ███
Ph9 V1.1 Release                                                                     ███ ███
Doc Documentation    ░░░ ░░░ ░░░ ░░░ ░░░ ░░░ ░░░ ░░░ ░░░ ░░░ ░░░ ░░░ ░░░ ░░░ ░░░ ░░░ ░░░ ░░░ ░░░ ░░░
─────────────────────────────────────────────────────────────────────────────────────────────────────
Milestone            M0          M1      M2          M3      M4      M5      M6-7    M8          M9
```

### 5.3 Effort Summary

| Phase | Est. Effort |
|-------|------------|
| Ph0 Dev Environment | 7 dev-days |
| Ph1 App Scaffolding | 5 dev-days |
| Ph2 Core DocTypes (12) | 18 dev-days |
| Ph3 Traceability Engine | 12 dev-days |
| Ph4 QA/QC + Season Policy | 11 dev-days |
| Ph5 Scale + Sensor | 10 dev-days |
| Ph6 AI Assist | 12 dev-days |
| Ph7 EvidencePack | 7 dev-days |
| Ph8 Staging | 9 dev-days |
| Ph9 Release | 4 dev-days |
| Documentation (parallel) | 10 dev-days |
| **Total V1.1** | **≈ 105 dev-days** |

> **Rule:** Never start the next phase until the current phase's exit criteria are met on the dev environment, and never deploy to production until all 10 acceptance tests pass on staging.

---

## 6. Release Strategy

### 6.1 Version Roadmap

> Full backlog and features inventory: [docs/planning/BACKLOG_AND_FEATURES_INVENTORY.md](../planning/BACKLOG_AND_FEATURES_INVENTORY.md)

| Release | Target | Focus | Key backlog stages | Items |
|---------|--------|-------|--------------------|-------|
| **V1.1** | 2026-Q3 | Quality + Traceability Core | — (ERP foundation) | 12 DocTypes, 50 FRs, 10 ATs |
| V1.2 | 2026-Q4 | Storage & Harvest AI layer | D, E, F | AGR-CEREAL-028 → 055 (28 items) |
| V1.3 | 2027-Q1 | Pre-season Planning & Field Ops AI | A, B, C | AGR-CEREAL-001 → 027 (27 items) |
| V2.0 | 2027-Q3 | Logistics, Trading & Processing AI | G, H | AGR-CEREAL-056 → 071 (16 items) |
| V2.1+ | 2028+ | Customer, Market & Platform AI | I | AGR-CEREAL-072 → 080 (9 items) |

### 6.2 AI Enhancement Strategy

The 80-item backlog (`docs/20260222 YAM_AGRI_BACKLOG v1.csv`) maps every stage of the cereal supply chain to an AI capability. Three AI action modes apply:

| Mode | Description | V1.1 allowed? |
|------|-------------|--------------|
| **Read-only** | Dashboards, forecasts, analytics only; no system change | ✅ Yes |
| **Propose-only** | AI surfaces recommendation; human decides | ✅ Yes |
| **Execute-with-approval** | System prepares action; manager must confirm | ✅ Yes (with workflow gate) |
| **Autonomous** | AI executes without human confirmation | ❌ Never |

---

## 7. Risks

| Risk ID | Risk | Likelihood | Impact | Mitigation |
|---------|------|-----------|--------|-----------|
| R-01 | Power outage causes data corruption | High | High | InnoDB crash recovery; daily backups to USB + offsite |
| R-02 | Internet unavailable during Docker image pull | High | Medium | Pre-fetch images with `run.sh prefetch`; offline-images.tar |
| R-03 | Site isolation breach (user sees wrong site data) | Low | Critical | Frappe User Permissions + permission query conditions; AT-10 must pass |
| R-04 | AI suggestion executed as action without approval | Low | Critical | Workflow gate enforced server-side; no client-side bypass |
| R-05 | Secret committed to Git | Low | Critical | Pre-commit secret scan CI check; `.env.example` only |
| R-06 | MariaDB crash-recovery fails after bad shutdown | Medium | High | `restart: always` in compose; documented recovery steps |
| R-07 | Developer leaves; no knowledge transfer | Low | Medium | This documentation set; agent instruction files in `.github/agents/` |
| R-08 | Staging k3s setup blocks V1.1 release | Medium | Medium | Stage 8 is gated — Dev must pass all ATs first |

---

## 8. Governance

| Decision | Who approves |
|----------|-------------|
| Release go/no-go | Platform owner (U6 — Yasser) |
| High-risk lot actions (accept/reject/recall) | QA Manager (U3) via workflow |
| New AI model activation | QA Manager + Platform Owner |
| New team member GitHub access | Platform Owner |
| Schema migration to production | DevOps (U7) + Platform Owner |
| Secrets rotation | DevOps (U7) |

---

## 9. Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial charter — V1.1 scope |
| 1.2 | 2026-02-23 | YasserAKareem | Added WBS-linked timeline (§5), dated milestones, effort totals, Gantt ASCII (§5.2), updated roadmap (§6.1) with item counts; added links to WBS_AND_GANTT.md and BACKLOG_AND_FEATURES_INVENTORY.md |
