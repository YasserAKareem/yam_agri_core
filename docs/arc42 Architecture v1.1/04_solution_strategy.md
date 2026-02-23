# arc42 §4 — Solution Strategy

> **arc42 Section:** 4  
> **Version:** 1.1  
> **Status:** ⚠️ Draft  
> **Date:** 2026-02-23  
> **Related SDLC doc:** [03_SYSTEM_ARCHITECTURE.md §7](../Docs%20v1.1/03_SYSTEM_ARCHITECTURE.md)  
> **Related ADRs:** [arc42 §9 — Architecture Decisions](09_architecture_decisions.md)

---

The solution strategy describes the **fundamental decisions and approaches** that shape the architecture. Each entry maps a quality goal or constraint to the chosen strategy.

---

## 4.1 Technology Decisions

| # | Decision | Strategy | Rationale |
|---|---------|---------|---------|
| SD-01 | **ERP platform: Frappe + ERPNext** | Use Frappe Framework v16 + ERPNext v16 as the mandatory base | Provides DocType engine, workflow, RBAC, REST API, Desk UI, audit trail — avoids building from scratch; see [ADR-001](09_architecture_decisions.md) |
| SD-02 | **Custom app: `yam_agri_core`** | Implement all domain-specific DocTypes, hooks, and business logic in a separate Frappe app | Keeps customisations isolated from core; survives `bench update`; see [ADR-002](09_architecture_decisions.md) |
| SD-03 | **Database: MariaDB 10.6** | Use MariaDB as the single relational store | Frappe's only supported DB; InnoDB provides crash recovery; see TC-04 |
| SD-04 | **AI: assistive-only with gateway** | All AI calls pass through a FastAPI AI Gateway that redacts PII and logs interactions; suggestions are text-only | Enforces AI safety at the architectural level; prevents any code path from triggering autonomous AI actions; see [ADR-003](09_architecture_decisions.md) |
| SD-05 | **Offline-first: Field Hub edge node** | Each site has a Raspberry Pi 4 running a minimal Frappe node; PouchDB/offline sync queue | Yemen infrastructure constraint; 7-day offline operation required; see IC-01, IC-02 |
| SD-06 | **Container runtime: Docker Compose (dev) / k3s (staging)** | Docker Compose for developer laptops; k3s for staging and production | Reproducible dev; lightweight Kubernetes for staging; see [ADR-004](09_architecture_decisions.md) |
| SD-07 | **Object storage: MinIO** | Self-hosted S3-compatible storage for certificates, photos, EvidencePack PDFs | No dependency on cloud S3; works fully offline; S3 API compatibility |
| SD-08 | **Vector store: Qdrant (V1.2+)** | Qdrant for RAG-based AI agents | Deferred to V1.2; not required for V1.1 assistive AI tasks |
| SD-09 | **Local LLM: Ollama + Llama 3.2 Q4** | Run Llama 3.2 3B Q4 locally via Ollama for offline AI | Fits in 4 GB RAM on Field Hub; works without internet |
| SD-10 | **SMS gateway: Africa's Talking (V1.2)** | Africa's Talking for inbound/outbound SMS with Yemeni operators | Supports MTN, STC, Y-telecom; webhook-based; deferred to V1.2 |

---

## 4.2 Architectural Approach

### Top-Down: Frappe as the System of Record

```
Everything lives in Frappe/MariaDB.
AI layers sit on top and suggest — they never write.
Integration adapters translate external formats into Frappe records.
```

This means:
- **Frappe DocTypes are the source of truth** for all business entities
- **All business rules are enforced server-side** in Python controllers (`validate`, `on_submit`, `before_cancel`)
- **Client-side validation is UX only** — never relied upon for correctness
- **AI Gateway is stateless** — it reads context from Frappe, suggests, and returns text

### Key Patterns

| Pattern | Application |
|---------|-----------|
| **Command/Query separation** | Read-only AI analysis never writes; write operations require human submission |
| **Event hooks (Frappe)** | `validate`, `on_submit`, `on_cancel`, `after_insert` hooks enforce business rules |
| **Permission Query Conditions** | Server-side SQL injection into all list queries ensures site isolation |
| **Workflow state machine** | Frappe Workflow manages state transitions with role-based transition guards |
| **Universal model (Observation)** | Single DocType handles all sensor types via `metric_type` field — avoids per-sensor schemas |
| **Evidence bundling** | EvidencePack aggregates cross-DocType evidence for audit — no denormalisation needed |

---

## 4.3 Achieving Quality Goals

| Quality goal | Strategy |
|-------------|---------|
| **Data integrity** | Server-side mass-balance check in Transfer `validate` hook; MariaDB transactions; docstatus workflow prevents re-submission |
| **Site isolation** | Frappe `permission_query_conditions` hook + `User Permission` records; enforced at SQL query level |
| **Resilience** | `restart: always` on all Docker services; InnoDB crash recovery; daily Restic backups |
| **AI safety** | AI Gateway architecture (SD-04); no Frappe write API exposed to AI; suggestions stored as read-only text fields |
| **Maintainability** | Custom app isolation (SD-02); `run.sh` script; comprehensive SDLC docs + this arc42 set; `bench` commands documented |

---

## 4.4 Build vs. Buy Decisions

| Component | Decision | Rationale |
|-----------|----------|---------|
| ERP core | **Use Frappe/ERPNext** | 10+ years of production use; supports our scale; OSS |
| Agriculture module | **Use Frappe Agriculture** | Provides Crop/CropCycle DocTypes; extends naturally |
| Lot traceability | **Build in `yam_agri_core`** | No existing OSS solution for cereal-specific lot tracing with Yemen constraints |
| AI assistance | **Build minimal FastAPI gateway + Ollama** | Flexibility to swap LLMs; enforcement of redaction and safety; no vendor lock-in |
| Scale integration | **Build CSV importer** | Scale vendors provide CSV; no standard SOAP/REST API in low-cost scales |
| IoT integration | **Build MQTT subscriber** | Standard MQTT protocol; no vendor-specific SDK dependency |
| Object storage | **Use MinIO** | S3-compatible OSS; self-hosted |
| Search | **Use Frappe built-in search** | Sufficient for V1.1; Qdrant deferred to V1.2 |

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial section — V1.1 |
