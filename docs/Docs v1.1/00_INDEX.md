# YAM Agri Platform — Documentation Index (V1.1)

> **Version:** 1.1  
> **Status:** Active  
> **Last updated:** 2026-02-23  
> **Owner:** YasserAKareem  

---

## About This Documentation Set

This folder contains the **complete SDLC documentation set** for the YAM Agri Platform V1.1 (Quality + Traceability Core). It follows the Software Development Life Cycle (SDLC) structure and is the authoritative reference for the platform.

All documents in this set supersede scattered notes in the parent `docs/` folder for V1.1 scope. The parent folder's files remain as historical references.

---

## Document Map

| # | Document | Purpose | Audience |
|---|----------|---------|----------|
| [01](01_PROJECT_CHARTER.md) | **Project Charter** | Scope, objectives, stakeholders, constraints, success criteria | All team members, owner, stakeholders |
| [02](02_REQUIREMENTS_SPECIFICATION.md) | **Requirements Specification (SRS)** | Functional & non-functional requirements | Developers, QA, product owner |
| [03](03_SYSTEM_ARCHITECTURE.md) | **System Architecture** | 11-layer architecture, technology choices, data flows | Developers, DevOps, architects |
| [04](04_DATA_MODEL.md) | **Data Model** | DocTypes, fields, relationships, data dictionary | Developers, QA, DBAs |
| [05](05_API_SPECIFICATION.md) | **API Specification** | REST/RPC API reference, authentication, examples | Developers, integrators |
| [06](06_SECURITY_AND_RBAC.md) | **Security & RBAC** | Role-based access control, site isolation, security controls | Developers, QA, IT admin |
| [07](07_TEST_PLAN.md) | **Test Plan** | Test strategy, acceptance scenarios, test cases | QA engineers, developers, owner |
| [08](08_DEPLOYMENT_GUIDE.md) | **Deployment Guide** | Dev, staging, production deployment procedures | DevOps, IT admin |
| [09](09_OPERATIONS_RUNBOOK.md) | **Operations Runbook** | Day-to-day ops, monitoring, backup, incident response | IT admin, DevOps |
| [10](10_COMPLIANCE_AND_QUALITY.md) | **Compliance & Quality** | FAO GAP, HACCP, ISO 22000 control point matrix | QA manager, owner, auditors |
| [11](11_AI_GOVERNANCE.md) | **AI Governance** | AI safety policy, assistive-only rules, audit trail | All team, AI developers, auditors |
| [12](12_RELEASE_NOTES.md) | **Release Notes** | V1.1 changelog, known gaps, upgrade path | All team, owner |

---

## SDLC Phase Map

```
Phase 1 — Initiation        → 01_PROJECT_CHARTER.md
Phase 2 — Requirements      → 02_REQUIREMENTS_SPECIFICATION.md
Phase 3 — Design            → 03_SYSTEM_ARCHITECTURE.md
                              04_DATA_MODEL.md
                              05_API_SPECIFICATION.md
                              06_SECURITY_AND_RBAC.md
Phase 4 — Implementation    → 03, 04, 05 (developer reference)
Phase 5 — Testing           → 07_TEST_PLAN.md
Phase 6 — Deployment        → 08_DEPLOYMENT_GUIDE.md
Phase 7 — Operations        → 09_OPERATIONS_RUNBOOK.md
Phase 8 — Compliance        → 10_COMPLIANCE_AND_QUALITY.md
          AI Governance      → 11_AI_GOVERNANCE.md
Phase 9 — Release/Closure   → 12_RELEASE_NOTES.md
```

---

## Quick Links for Roles

| Role | Start here |
|------|-----------|
| **Platform Owner (U6 / Yasser)** | [Project Charter](01_PROJECT_CHARTER.md) → [Release Notes](12_RELEASE_NOTES.md) |
| **Application Developer** | [Data Model](04_DATA_MODEL.md) → [API Specification](05_API_SPECIFICATION.md) → [Architecture](03_SYSTEM_ARCHITECTURE.md) |
| **QA / Compliance Engineer** | [Test Plan](07_TEST_PLAN.md) → [Compliance & Quality](10_COMPLIANCE_AND_QUALITY.md) |
| **DevOps / IT Admin (U7)** | [Deployment Guide](08_DEPLOYMENT_GUIDE.md) → [Operations Runbook](09_OPERATIONS_RUNBOOK.md) |
| **External Auditor (U8)** | [Compliance & Quality](10_COMPLIANCE_AND_QUALITY.md) → [AI Governance](11_AI_GOVERNANCE.md) |
| **New Team Member** | [Project Charter](01_PROJECT_CHARTER.md) → [Architecture](03_SYSTEM_ARCHITECTURE.md) → [Security & RBAC](06_SECURITY_AND_RBAC.md) |

---

## Related Documents (Parent Folder)

| File | Notes |
|------|-------|
| `../BLUEPRINT_PLAYBOOK_BEGINNER.md` | Full beginner-friendly playbook (source of many V1.1 decisions) |
| `../SMART_FARM_ARCHITECTURE.md` | Deep 11-layer architecture reference |
| `../TOUCHPOINT_APP_BLUEPRINT.md` | 9 touchpoint apps screen inventory |
| `../PERSONA_JOURNEY_MAP.md` | 9 user personas and journey maps |
| `../planning/RBAC_AND_ORG_CHART.md` | RBAC baseline and org chart mapping |
| `../AGENTS_AND_MCP_BLUEPRINT.md` | Copilot agent and MCP configuration |
| `../Enterprise-Value-Map.md` | Business value drivers compass |
| `../GITHUB_SETUP_BLUEPRINT.md` | GitHub teams, branch protection, CI setup |
| `../backlog/AGR-CEREAL-001.md` | Crop variety recommendation backlog item |
| `../20260222 YAM_AGRI_BACKLOG v1.csv` | 80-item product backlog |

---

## Document Status Legend

| Status | Meaning |
|--------|---------|
| ✅ Complete | Reviewed and approved for V1.1 |
| ⚠️ Draft | Under review; may change |
| 🔲 Stub | Created with proposed content; needs owner review |
| ❌ Missing | Identified as needed; not yet written |

All documents in this folder are marked **⚠️ Draft** until formally reviewed by the platform owner.

---

## Proposed Additions (Missing Data Identified)

The following documents and content areas were identified as gaps during the documentation review. They are proposed for V1.1 completion or V1.2:

| Gap | Proposed document / section | Priority |
|-----|---------------------------|----------|
| Season Policy Matrix | `10_COMPLIANCE_AND_QUALITY.md` §5 | High — required for lot gating |
| FAO GAP Middle East control checklist | `10_COMPLIANCE_AND_QUALITY.md` §3 | High — compliance baseline |
| HACCP Hazard Analysis table | `10_COMPLIANCE_AND_QUALITY.md` §4 | High — ISO 22000 |
| DocType field-level validation rules | `04_DATA_MODEL.md` §3 | High — developer reference |
| Workflow state machine diagrams | `04_DATA_MODEL.md` §6 | High — Lot / QCTest / Certificate |
| Incident Response Playbook | `09_OPERATIONS_RUNBOOK.md` §7 | Medium — ops maturity |
| Disaster Recovery Plan (DRP) | New doc: `13_DISASTER_RECOVERY.md` | Medium — staging / production |
| SMS command grammar (full EBNF) | `05_API_SPECIFICATION.md` §6 | Medium — FarmerSMS integration |
| Data Retention & Privacy Policy | New doc: `14_DATA_PRIVACY.md` | Medium — donor/NGO requirements |
| Capacity Planning guide | `09_OPERATIONS_RUNBOOK.md` §8 | Low — pre-production |
| AI Model Card (per model) | `11_AI_GOVERNANCE.md` §6 | Low — AI governance |
| Org Chart diagram (visual) | `06_SECURITY_AND_RBAC.md` §2 | Low — onboarding aid |
