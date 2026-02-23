# arc42 §9 — Architecture Decisions (ADRs)

> **arc42 Section:** 9  
> **Version:** 1.1  
> **Status:** ⚠️ Draft  
> **Date:** 2026-02-23  
> **Format:** Architecture Decision Records (ADR) — lightweight format

---

Architecture Decision Records (ADRs) document **significant decisions** made during architecture design, including the context, options considered, and rationale. They are immutable — a superseded decision gets a new ADR rather than being edited.

---

## ADR-001 — Use Frappe Framework + ERPNext as the Core Platform

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-02-23 |
| **Deciders** | Platform Owner (U6) |

### Context

YAM Agri needs a platform that provides: data modelling, RBAC, workflows, REST API, audit trail, file management, and a multi-language UI — all within a low-budget, self-hosted, open-source stack.

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| Frappe + ERPNext | Mature OSS; includes inventory, finance, HR; Arabic support; active community | Framework lock-in; MariaDB-only |
| Django + custom | Maximum flexibility | Build everything from scratch; high cost |
| Odoo | Feature-rich ERP | License cost for enterprise features; heavier |
| Custom microservices | Technology choice freedom | Extreme build cost for small team |

### Decision

Use **Frappe Framework v16 + ERPNext v16 + Frappe Agriculture** as the mandatory base platform.

### Consequences

- All DocTypes must follow Frappe conventions
- MariaDB 10.6 is the only supported database
- Cannot use frameworks that conflict with Frappe's frontend (Vue.js, React) for core Desk views
- ERPNext standard roles must be used; no custom role names

---

## ADR-002 — Implement Domain Logic in a Separate Frappe App (`yam_agri_core`)

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-02-23 |
| **Deciders** | Platform Owner (U6), Lead Developer |

### Context

Custom business logic could be added by patching ERPNext core files, or by creating a separate Frappe app.

### Decision

All custom DocTypes, hooks, and business logic are implemented in a dedicated **`yam_agri_core`** Frappe app.

### Rationale

- `bench update` will not overwrite custom code
- Custom app can be version-controlled independently
- Clear separation: what is YAM-specific vs. what comes from ERPNext
- App can be installed on a clean Frappe bench; no state entanglement

### Consequences

- Every custom DocType must be created in the `yam_agri_core` app
- No direct modification of `frappe` or `erpnext` or `agriculture` source files
- Cross-app relationships (e.g., Lot → ERPNext Supplier) use Frappe Link fields

---

## ADR-003 — AI is Assistive Only, Enforced via AI Gateway Architecture

| Field | Value |
|-------|-------|
| **Status** | Accepted — non-negotiable |
| **Date** | 2026-02-23 |
| **Deciders** | Platform Owner (U6) |

### Context

AI-assisted features (compliance checks, CAPA drafts, evidence narratives) are needed. There is a risk that AI actions could be automated without human oversight, leading to food safety or compliance failures.

### Decision

All AI interactions must:
1. Pass through a **dedicated AI Gateway** (FastAPI service) that enforces redaction and whitelisting
2. Return **only suggestion text** — never DocType writes, API calls, or workflow transitions
3. Be **logged immutably** with prompt/response hashes
4. **Require explicit human action** before any suggestion affects a business record

The `ai_suggestion` field on DocTypes is **read-only** — it cannot trigger any action.

### Consequences

- AI Gateway is an independently deployable service
- Cloud LLM calls are always redacted — PII never leaves the platform
- AI is gracefully degraded if the Gateway is down (not a critical dependency)
- AI cannot be used to bypass any workflow approval gate

---

## ADR-004 — Docker Compose for Dev; k3s for Staging/Production

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-02-23 |
| **Deciders** | Platform Owner (U6), DevOps (U7) |

### Context

The team needs a reproducible developer environment on 8 GB RAM laptops (Yemen constraints) and a production-grade deployment target.

### Decision

- **Development:** Docker Compose v2.x — `infra/compose/docker-compose.yml` + `infra/docker/run.sh`
- **Staging / Production:** k3s (lightweight Kubernetes) — deployed only after all acceptance tests pass on dev

### Rationale

- Docker Compose is the simplest reproducible dev environment; no Kubernetes knowledge required
- k3s is the lightest Kubernetes distribution; runs on a single VPS for staging
- Production can scale k3s to multi-node without architecture change

### Consequences

- Dev stack must fit in ≤ 6 GB RAM (8 GB laptop minus OS)
- k3s manifests must be maintained in `infra/k8s/` (V1.2+)
- Never deploy to k3s staging until Docker Compose dev passes all 10 acceptance tests

---

## ADR-005 — Universal Observation Model for All Sensor Types

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-02-23 |
| **Deciders** | Lead Developer |

### Context

The system must handle many sensor types: bin temperature, humidity, moisture, CO₂, NDVI, rainfall, irrigation flow, refrigerator probes, and more (future: weather, flood index).

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| One DocType per sensor type | Typed schema; easy validation | Schema explosion; maintenance burden for each new sensor |
| **Universal Observation DocType** (chosen) | Single schema; extensible | Less typed; `metric_type` + `value` + `unit` pattern |
| Time-series DB only (InfluxDB) | Optimised for time-series | No Frappe integration; separate query; V1.2+ complexity |

### Decision

Use a **single `Observation` DocType** with `metric_type`, `value`, `unit`, `quality_flag` fields. This handles all current and planned sensor types.

### Consequences

- New sensor types are added by extending the `metric_type` select field — no schema migration
- Validation rules are type-agnostic (threshold_min / threshold_max per device)
- MariaDB stores all observations; InfluxDB migration path available for high-frequency V1.2+ data
- Reporting must filter by `metric_type`; no separate tables per sensor

---

## ADR-006 — Frappe Permission Query Conditions for Site Isolation

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-02-23 |
| **Deciders** | Lead Developer |

### Context

Site isolation must be enforced for all DocTypes with a `site` field. Simple Frappe User Permissions alone may be bypassable via direct API calls.

### Decision

Implement **`permission_query_conditions`** hooks in `hooks.py` for every DocType that has a `site` field. These hooks inject a SQL `WHERE site IN (...)` condition into every list query, including direct API list queries.

### Consequences

- Site isolation is enforced at the database query level — not just the UI
- Direct API calls (`/api/resource/Lot`) are also filtered — no bypass possible
- New DocTypes with `site` fields must add a corresponding hook in `hooks.py`
- Performance: permission query adds a small overhead; acceptable for expected data volumes

---

## ADR-007 — MinIO for Object Storage (Self-hosted S3)

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-02-23 |
| **Deciders** | DevOps (U7), Platform Owner (U6) |

### Context

Certificate PDFs, inspection photos, EvidencePack exports, and other binary files need reliable storage. Options include cloud S3, MinIO, or Frappe's local file system.

### Decision

Use **MinIO** (self-hosted, S3-compatible) as the object store.

### Rationale

- Works fully offline — no internet dependency
- S3 API compatibility means migration to AWS S3 is possible later
- Frappe has a built-in S3 file storage backend
- Free and open-source; no storage cost

### Consequences

- MinIO container must be in all deployment environments
- MinIO data volume must be included in backup strategy
- Object URLs are internal (`minio:9000`); nginx proxies external access

---

## ADR-008 — Ollama + Llama 3.2 (Q4) as the Primary Local LLM

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-02-23 |
| **Deciders** | Platform Owner (U6), QA Manager (U3) |

### Context

AI assistance requires an LLM. Options: cloud-only (OpenAI/Claude), local-only (Ollama), or hybrid.

### Decision

**Primary:** Ollama serving Llama 3.2 3B Q4 (quantised) — local, offline-capable.  
**Fallback:** OpenAI GPT-4o-mini or Claude 3 Haiku — cloud, with PII redaction mandatory.

### Rationale

- Llama 3.2 3B Q4 fits in ~2 GB RAM — compatible with Field Hub (4 GB RAM)
- Works fully offline — critical for Yemen infrastructure
- Cloud fallback for cases where local model quality is insufficient
- All cloud calls go through AI Gateway with mandatory redaction

### Consequences

- Ollama container must be available in the AI stack
- Model quality is lower than GPT-4o; sufficient for compliance_check and capa_draft tasks
- Cloud fallback requires internet and API keys (optional; env var controlled)
- New models must go through the model activation procedure (see [11_AI_GOVERNANCE.md §6.2](../Docs%20v1.1/11_AI_GOVERNANCE.md))

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial ADR set — V1.1 (ADR-001 through ADR-008) |
