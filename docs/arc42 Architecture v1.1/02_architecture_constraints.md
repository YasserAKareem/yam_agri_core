# arc42 §2 — Architecture Constraints

> **arc42 Section:** 2  
> **Version:** 1.1  
> **Status:** ⚠️ Draft  
> **Date:** 2026-02-23  
> **Related SDLC doc:** [01_PROJECT_CHARTER.md §2.4](../Docs%20v1.1/01_PROJECT_CHARTER.md) | [02_REQUIREMENTS_SPECIFICATION.md §6](../Docs%20v1.1/02_REQUIREMENTS_SPECIFICATION.md)

---

Constraints are conditions that **cannot be changed** by the architecture. They narrow the solution space. Any architecture decision that conflicts with a constraint is invalid.

---

## 2.1 Technical Constraints

| ID | Constraint | Consequence for architecture |
|----|-----------|------------------------------|
| TC-01 | **Frappe Framework v15/v16 is the mandatory base platform** — no alternative ERP/framework | All business logic must be implemented as Frappe DocType controllers, hooks, and workflows; no standalone microservices for core data |
| TC-02 | **ERPNext v16 must be installed** — standard ERPNext roles and DocTypes are available | Use ERPNext's Role system and standard DocTypes (Customer, Supplier, Item) rather than reinventing them |
| TC-03 | **Frappe Agriculture app must be installed** — provides Crop, CropCycle, WaterAnalysis | Lot and QCTest DocTypes extend Frappe Agriculture concepts |
| TC-04 | **MariaDB 10.6 is the only supported database** — Frappe does not support PostgreSQL in V1.1 | Schema must comply with MariaDB limitations; no PostgreSQL-only features |
| TC-05 | **Python 3.11+ required** — Frappe minimum version | All custom server-side code in Python 3.11+ |
| TC-06 | **Node.js 18 LTS required** — Frappe Desk build | Front-end customisation uses Frappe's JavaScript/Desk framework |
| TC-07 | **Docker Compose v2.x for dev** — the standard dev environment | Dev setup must be reproducible via `docker compose up`; no native bench install required for development |
| TC-08 | **Total Docker stack ≤ 6 GB RAM** — hardware constraint (8 GB laptop) | Services must be configured with memory limits; heavy services (vector DB, InfluxDB) are deferred to V1.2+ |
| TC-09 | **All custom code inside `yam_agri_core` Frappe app** — no core patches | `bench update` must not break customisations; all hooks in `hooks.py` |
| TC-10 | **Redis 7 for queue and cache** | Frappe job queues, session cache, and real-time updates rely on Redis |

---

## 2.2 Organisational Constraints

| ID | Constraint | Consequence |
|----|-----------|-------------|
| OC-01 | **Team is small (1–3 developers)** — limited bandwidth | Architecture must minimise operational complexity; prefer convention over configuration |
| OC-02 | **Open-source stack preferred** — budget constraint | All infrastructure components must have an OSS option; no mandatory paid SaaS in the critical path |
| OC-03 | **Secrets must never be committed to Git** — security policy | `.env.example` only in repo; all credentials injected at runtime via environment variables |
| OC-04 | **AI is assistive only — non-negotiable** — owner/governance rule | Architecture must make it structurally impossible for AI to write, submit, or amend any DocType without human action |
| OC-05 | **Production deployment blocked until staging passes all 10 acceptance tests** — project rule | Architecture must support the staged rollout: dev → staging → production |
| OC-06 | **No Kubernetes until Docker Compose dev environment works** — phased rule | K3s staging architecture is designed but not deployed until Phase 8 |

---

## 2.3 Regulatory and Compliance Constraints

| ID | Constraint | Consequence |
|----|-----------|-------------|
| RC-01 | **FAO GAP (Middle East) compliance** — required for export markets | QCTest DocType must capture all FAO GAP mandatory test types; SeasonPolicy must gate on required tests |
| RC-02 | **HACCP (ISO 22000:2018) compliance** — food safety management system | Six Critical Control Points (CCPs) must be enforced via Observation monitoring + Season Policy + Nonconformance workflow |
| RC-03 | **Yemen Ministry of Agriculture phytosanitary requirements** — export prerequisite | Certificate DocType must support phytosanitary certificate type with per-shipment validity |
| RC-04 | **EU Aflatoxin limits** — export requirement (aflatoxin B1 ≤ 2 ppb cereals) | QCTest.mycotoxin_ppb must be gated by SeasonPolicy; system blocks shipment above limit |
| RC-05 | **PII protection** — donor/NGO requirement | AI Gateway must redact PII before any external LLM call; personal data retention defined in data model |
| RC-06 | **Arabic/RTL-first UI** — legal/business requirement in Yemen | All user-facing strings translatable; Frappe internationalisation must be active |

---

## 2.4 Infrastructure Constraints (Yemen Context)

| ID | Constraint | Consequence |
|----|-----------|-------------|
| IC-01 | **Daily power outages** — average 8–12 hours/day in Yemen | InnoDB crash recovery must be operational; all Docker services set `restart: always`; UPS or solar recommended |
| IC-02 | **Internet unreliable** — 2G/3G at field sites; may be unavailable for days | Offline-first design; Field Hub must operate 7 days standalone; Docker images cached locally |
| IC-03 | **8 GB RAM laptops for development** — hardware ceiling | Docker Compose memory limits enforced; total stack target ≤ 3 GB RAM on dev |
| IC-04 | **Arabic-language end users at field sites** | Frappe Desk translation and RTL CSS must be tested; SMS messages must use Arabic-safe encoding |
| IC-05 | **No reliable cloud access from production sites** | MinIO local object storage preferred over S3; all essential services self-hosted |

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial section — V1.1 |
