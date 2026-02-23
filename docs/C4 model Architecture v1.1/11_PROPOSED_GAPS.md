# Proposed Gaps — Architectural Missing Data

> **Document type:** Gap Analysis  
> **Version:** 1.1  
> **Date:** 2026-02-23  
> **Derived from:** Review of all project docs, source code, Docker Compose files, and k8s manifests  
> **Related:** [← System Landscape](10_SYSTEM_LANDSCAPE.md) | [README](00_README.md)

---

## Overview

This document records all **architectural gaps, missing components, and inconsistencies** identified during the C4 architecture documentation review. Items are categorised by severity and target release.

Each gap includes:
- What is missing
- Why it matters
- Proposed solution
- Where it appears in the C4 diagrams

---

## 1. Critical Gaps (must fix before V1.1 release)

### GAP-001 — Staging database is PostgreSQL, not MariaDB

| Field | Detail |
|-------|--------|
| **Severity** | Critical |
| **Found in** | `environments/staging/k3s-manifest.yaml` |
| **C4 reference** | [Deployment: Staging](09_DEPLOYMENT_STAGING.md) |
| **Problem** | Staging manifest uses `postgres:15` as the database. Frappe Framework **requires MariaDB** and is not compatible with PostgreSQL without significant unsupported changes. The staging database would not work with the existing Frappe installation. |
| **Evidence** | Line 104–117 of `environments/staging/k3s-manifest.yaml`: `image: postgres:15`, credentials for PostgreSQL |
| **Proposed fix** | Replace `postgres:15` with `mariadb:10.6` in the staging manifest. Use same environment variables as dev: `MYSQL_ROOT_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`. |

### GAP-002 — Redis services missing from staging manifest

| Field | Detail |
|-------|--------|
| **Severity** | Critical |
| **Found in** | `environments/staging/k3s-manifest.yaml` |
| **C4 reference** | [Deployment: Staging](09_DEPLOYMENT_STAGING.md), [Container Diagram](02_CONTAINER_DIAGRAM.md) |
| **Problem** | Staging manifest has no Redis Cache, Redis Queue, or Redis WebSocket services. Frappe requires all three for session management, background jobs, and real-time features. The Frappe pod would fail to start without Redis. |
| **Proposed fix** | Add three Redis Deployments + Services to `k3s-manifest.yaml`: `redis-cache`, `redis-queue`, `redis-socketio` — all using `redis:6.2-alpine`. Mirror the dev Docker Compose configuration. |

### GAP-003 — Frappe workers and scheduler missing from staging manifest

| Field | Detail |
|-------|--------|
| **Severity** | Critical |
| **Found in** | `environments/staging/k3s-manifest.yaml` |
| **C4 reference** | [Container Diagram](02_CONTAINER_DIAGRAM.md) |
| **Problem** | Staging manifest only deploys the `frappe` web process. There are no `queue-short`, `queue-long`, or `scheduler` Deployments. Without workers, background jobs (CSV imports, evidence pack generation, certificate expiry checks) will never execute. |
| **Proposed fix** | Add Deployments for: `frappe-worker-short` (`bench worker --queue short,default`), `frappe-worker-long` (`bench worker --queue long,default,short`), `frappe-scheduler` (`bench schedule`). All must share the `frappe-sites` PVC. |

### GAP-004 — Secrets in plain text in staging manifest

| Field | Detail |
|-------|--------|
| **Severity** | Critical |
| **Found in** | `environments/staging/k3s-manifest.yaml` lines 107–112 |
| **C4 reference** | [Security & RBAC](../Docs%20v1.1/06_SECURITY_AND_RBAC.md) |
| **Problem** | Database credentials (`POSTGRES_DB: yam_agri`, `POSTGRES_USER: yam`, `POSTGRES_PASSWORD: yam_pw`) are hardcoded in the manifest file which is committed to Git. This violates the no-secrets-in-Git rule. |
| **Proposed fix** | Create a Kubernetes Secret: `kubectl create secret generic yam-db-secret --from-literal=...`. Reference in Deployment via `valueFrom.secretKeyRef`. Use sealed-secrets or external-secrets operator for automated secret management. |

---

## 2. High Priority Gaps (should fix in V1.1)

### GAP-005 — INSTALL_APPS incomplete in staging manifest

| Field | Detail |
|-------|--------|
| **Severity** | High |
| **Found in** | `environments/staging/k3s-manifest.yaml` |
| **C4 reference** | [Deployment: Staging](09_DEPLOYMENT_STAGING.md) |
| **Problem** | Staging Frappe pod uses `INSTALL_APPS: erpnext,agriculture` — missing `yam_agri_core` and `yam_agri_qms_trace`. |
| **Proposed fix** | Update to `INSTALL_APPS: erpnext,agriculture,yam_agri_core,yam_agri_qms_trace` to match dev. |

### GAP-006 — Site isolation not applied to core QA/QC DocTypes

| Field | Detail |
|-------|--------|
| **Severity** | High |
| **Found in** | `apps/yam_agri_core/yam_agri_core/yam_agri_core/hooks.py` |
| **C4 reference** | [Component: Core Platform](03_COMPONENT_CORE_PLATFORM.md) §Key Code Flows |
| **Problem** | `permission_query_conditions` in `hooks.py` only covers 6 AGR-CEREAL DocTypes (Site, YAM Plot, YAM Soil Test, YAM Plot Yield, YAM Crop Variety, YAM Crop Variety Recommendation). The core QA/QC DocTypes (`Lot`, `QCTest`, `Certificate`, `Nonconformance`) are **not** in `permission_query_conditions`. Users with access to any site could potentially query all lots from all sites via the list API. |
| **Evidence** | `hooks.py` lines 15–22: only YAM Plot family covered |
| **Proposed fix** | Add to `hooks.py`: `"Lot": "...lot_query_conditions"`, `"QCTest": "...qctest_query_conditions"`, `"Certificate": "...cert_query_conditions"`, `"Nonconformance": "...nc_query_conditions"`. Implement corresponding query condition functions in `site_permissions.py` using `build_site_query_condition()`. |

### GAP-007 — AI Interaction Log DocType not implemented

| Field | Detail |
|-------|--------|
| **Severity** | High |
| **Found in** | `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/` |
| **C4 reference** | [Component: AI Layer](04_COMPONENT_AI_LAYER.md), [Dynamic: AI Assist](07_DYNAMIC_AI_ASSIST.md) |
| **Problem** | The AI Governance policy requires an immutable audit log of all AI interactions. No `AI Interaction Log` DocType exists in `yam_agri_core`. Without this, there is no audit trail for AI suggestions, making it impossible to verify the assistive-only guarantee or demonstrate compliance to auditors. |
| **Proposed fix** | Create `doctype/ai_interaction_log/` with fields: `timestamp`, `user`, `record_type`, `record_name`, `task`, `model_used`, `prompt_hash`, `response_hash`, `redaction_applied`, `tokens_used`, `suggestion_accepted`, `accepted_by`, `accepted_at`. Permissions: no delete, no amend. |

### GAP-008 — WebSocket server missing from staging manifest

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **Found in** | `environments/staging/k3s-manifest.yaml` |
| **C4 reference** | [Deployment: Staging](09_DEPLOYMENT_STAGING.md) |
| **Problem** | No `websocket`/`socketio` Deployment in staging. Real-time notifications (sensor alerts, lot status updates) will not work in staging. |
| **Proposed fix** | Add `frappe-websocket` Deployment using `frappe/erpnext:v16.5.0` with `node /home/frappe/frappe-bench/apps/frappe/socketio.js` command, Redis env vars, and a Service on :9000. |

---

## 3. Medium Priority Gaps (should fix before production)

### GAP-009 — Qdrant knowledge base not populated

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **Found in** | AI Layer design |
| **C4 reference** | [Component: AI Layer](04_COMPONENT_AI_LAYER.md) §RAG Knowledge Base |
| **Problem** | The RAG architecture depends on Qdrant being populated with FAO GAP documents, HACCP CCP procedures, and CAPA templates. No document ingestion pipeline or embedding scripts exist in the repository. |
| **Proposed fix** | Create `tools/rag_ingest/` with: document loader (PDF/CSV), chunking, embedding (sentence-transformers or OpenAI embeddings), Qdrant upsert scripts. Document: which FAO GAP / HACCP sources to use and their licensing. |

### GAP-010 — Field Hub sync adapter not implemented

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **Found in** | System design |
| **C4 reference** | [Component: Service Adapters](05_COMPONENT_SERVICE_ADAPTERS.md) §Proposed Gap |
| **Problem** | The Field Hub runs a local Frappe instance but there is no documented or implemented sync adapter to push offline-created records to the central platform when connectivity is restored. |
| **Proposed fix** | Design a Field Hub Sync Adapter: queue writes in a local SQLite/Redis buffer during offline periods; push to central Frappe REST API when online; handle conflict resolution (last-write-wins for sensor data; manual for Lot status). Document the sync protocol. |

### GAP-011 — MinIO not deployed in any environment

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **Found in** | `infra/docker/docker-compose.yml`, `environments/` |
| **C4 reference** | [Container Diagram](02_CONTAINER_DIAGRAM.md) |
| **Problem** | MinIO is described as the object storage solution for certificate PDFs, photos, and evidence pack ZIPs, but it is not present in either the dev Docker Compose or staging k3s manifests. Files are likely stored in the `sites-vol` filesystem (limited and not S3-compatible). |
| **Proposed fix** | Add MinIO service to `docker-compose.yml` and staging k3s manifests. Configure Frappe to use MinIO for file storage via `file_manager.yaml` site config. Document backup of MinIO data. |

### GAP-012 — Season Policy DocType and gating logic not implemented

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **Found in** | `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/` |
| **C4 reference** | [Dynamic: Lot Lifecycle](06_DYNAMIC_LOT_LIFECYCLE.md) |
| **Problem** | The current `Lot.validate()` only checks for expired Certificates before dispatch. It does not enforce a Season Policy (which QC test types are mandatory for a given crop/season). The full dispatch-blocking logic (AT-06 acceptance test) is not implemented. |
| **Proposed fix** | Create `SeasonPolicy` DocType (crop, season, is_high_risk_season, mandatory_tests table, mandatory_cert_types table). Extend `Lot.validate()` to query the applicable SeasonPolicy and block dispatch if mandatory tests/certs are missing. |

### GAP-013 — Certificate expiry 30-day advance warning not scheduled

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **Found in** | `apps/yam_agri_core/yam_agri_core/yam_agri_core/` (no scheduler hook) |
| **C4 reference** | [Component: Core Platform](03_COMPONENT_CORE_PLATFORM.md) §Frappe Framework Core — Scheduler |
| **Problem** | The Certificate DocType has an `expiry_date` field but there is no Frappe scheduled job to check for certificates expiring within 30 days and send notifications. |
| **Proposed fix** | Add to `hooks.py`: `scheduler_events = {"daily": ["yam_agri_core.yam_agri_core.schedule.check_certificate_expiry"]}`. Implement `check_certificate_expiry()` to query certificates where `expiry_date BETWEEN today AND today+30`, send Frappe notifications to QA Manager. |

### GAP-014 — TLS not configured in staging ingress

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **Found in** | `environments/staging/k3s-manifest.yaml` |
| **C4 reference** | [Deployment: Staging](09_DEPLOYMENT_STAGING.md) |
| **Problem** | Traefik entry point is set to `web` (HTTP only). No TLS termination or certificate configured. All staging traffic is unencrypted. |
| **Proposed fix** | Switch to `websecure` entry point. Either: use cert-manager + Let's Encrypt for automatic TLS, or provide a self-signed TLS secret and reference it in the Ingress spec. |

---

## 4. Lower Priority Gaps (V1.2+)

### GAP-015 — No monitoring stack

| Severity | Medium | Target | V1.2 |
|----------|--------|--------|------|
| **Detail** | No Prometheus, Grafana, or alerting in any environment. Ops team cannot measure page load times, queue depth, DB query latency, AI costs, or sensor alert response times against NFR targets. |
| **Proposed fix** | Add Prometheus + Grafana to `docker-compose.yml` and staging k3s. Instrument: Frappe gunicorn metrics, MariaDB exporter, Redis exporter, AI Gateway token costs. |

### GAP-016 — SMS Handler not implemented

| Severity | Medium | Target | V1.2 |
|----------|--------|--------|------|
| **Detail** | TP-01 FarmerSMS app (SMS Handler) is designed but not built. U1 farmers cannot register harvest lots or receive alerts via SMS. |
| **Proposed fix** | Implement `services/sms_handler/` FastAPI service with Africa's Talking webhook, Arabic SMS parser, and Frappe REST client. Add to Docker Compose and k3s manifests. |

### GAP-017 — Remote Sensing / NDVI ingestion not implemented

| Severity | Low | Target | V1.2 |
|----------|-----|--------|------|
| **Detail** | Satellite NDVI data and flood risk mapping are designed but not ingested. The Observation DocType supports `metric_type = NDVI` but no pipeline fills it. |
| **Proposed fix** | Create `services/remote_sensing/` with EODAG + Sentinel-2 ingestion. Schedule weekly NDVI pull per Site. Create Observation records with `metric_type = NDVI`. |

### GAP-018 — Disaster Recovery Plan (DRP) not documented

| Severity | Medium | Target | V1.1 documentation |
|----------|--------|--------|--------------------|
| **Detail** | No formal DRP exists. The Operations Runbook covers basic backup/restore but not: RTO/RPO targets, recovery scenarios (full data loss, single-node failure, ransomware), offsite backup validation, or DRP test schedule. |
| **Proposed fix** | Create `docs/Docs v1.1/13_DISASTER_RECOVERY.md` covering: RTO/RPO, backup validation, recovery runbooks, offsite copy verification. |

### GAP-019 — `yam_agri_qms_trace` app not documented

| Severity | Medium | Target | V1.1 documentation |
|----------|--------|--------|--------------------|
| **Detail** | The Docker Compose `backend` service installs `yam_agri_qms_trace` app alongside `yam_agri_core`. This app is not documented in any existing docs, its source code is not in `apps/`, and its purpose is unknown. |
| **Proposed fix** | Clarify the purpose of `yam_agri_qms_trace`. Either document it in the C4 diagrams as a separate component, or confirm it is a dependency that should be documented in the Container diagram. |

### GAP-020 — No health check endpoints for service adapters

| Severity | Low | Target | V1.2 |
|----------|-----|--------|------|
| **Detail** | IoT Gateway, Scale Connector, and AI Gateway have no documented health check endpoints. Docker/k3s cannot know if these services are ready/healthy. |
| **Proposed fix** | Add `GET /health` endpoint to each FastAPI service. Add `healthcheck` or `livenessProbe`/`readinessProbe` to Docker Compose and k3s manifests. |

---

## 5. Documentation Gaps

### DOC-GAP-001 — Missing EvidencePack, Complaint, Observation, ScaleTicket, Transfer DocType source

| Severity | Medium |
|----------|--------|
| **Detail** | The SDLC docs and C4 docs describe EvidencePack, Complaint, Observation, ScaleTicket, and Transfer DocTypes, but their `.json` and `.py` files do not exist in `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/`. |
| **Action** | Implement these DocTypes or confirm they are deferred to V1.2. Update C4 component diagrams to reflect actual vs planned DocTypes. |

### DOC-GAP-002 — No architectural decision record (ADR) files

| Severity | Low |
|----------|-----|
| **Detail** | Key architecture decisions (MariaDB over PostgreSQL, Docker Compose for dev, assistive-only AI) are described in prose but not formally recorded as ADRs with context, options considered, and decision rationale. |
| **Action** | Create `docs/C4 model Architecture v1.1/ADR/` folder with one file per ADR. Use MADR format (Michael Nygard template). |

### DOC-GAP-003 — No OpenAPI / Swagger spec for AI Gateway

| Severity | Low |
|----------|-----|
| **Detail** | The AI Gateway (FastAPI) would auto-generate an OpenAPI spec at `/docs` if built, but no committed spec exists for reference. |
| **Action** | Once AI Gateway is implemented, export `openapi.json` to `docs/C4 model Architecture v1.1/ai_gateway_openapi.json`. |

---

## Gap Summary Table

| ID | Description | Severity | Target |
|----|-------------|---------|--------|
| GAP-001 | Staging DB is PostgreSQL not MariaDB | Critical | V1.1 staging fix |
| GAP-002 | Redis missing from staging | Critical | V1.1 staging fix |
| GAP-003 | Frappe workers missing from staging | Critical | V1.1 staging fix |
| GAP-004 | Secrets in plain text in staging manifest | Critical | V1.1 staging fix |
| GAP-005 | INSTALL_APPS incomplete in staging | High | V1.1 staging fix |
| GAP-006 | Site isolation missing for Lot/QCTest/Cert/NC | High | V1.1 code fix |
| GAP-007 | AI Interaction Log DocType not implemented | High | V1.1 code |
| GAP-008 | WebSocket missing from staging | Medium | V1.1 staging fix |
| GAP-009 | Qdrant knowledge base not populated | Medium | V1.2 |
| GAP-010 | Field Hub sync adapter not implemented | Medium | V1.2 |
| GAP-011 | MinIO not deployed in any environment | Medium | V1.2 |
| GAP-012 | SeasonPolicy DocType + gating not implemented | Medium | V1.1 code |
| GAP-013 | Certificate expiry scheduler not implemented | Medium | V1.1 code |
| GAP-014 | TLS not configured in staging | Medium | V1.1 staging fix |
| GAP-015 | No monitoring stack | Medium | V1.2 |
| GAP-016 | SMS Handler not implemented | Medium | V1.2 |
| GAP-017 | NDVI ingestion not implemented | Low | V1.2 |
| GAP-018 | Disaster Recovery Plan not documented | Medium | V1.1 docs |
| GAP-019 | yam_agri_qms_trace app not documented | Medium | V1.1 docs |
| GAP-020 | No health check endpoints for adapters | Low | V1.2 |
| DOC-GAP-001 | Missing DocType source for 5 planned DocTypes | Medium | V1.1 |
| DOC-GAP-002 | No ADR files | Low | V1.2 |
| DOC-GAP-003 | No OpenAPI spec for AI Gateway | Low | V1.2 |

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial gap analysis — V1.1 |
