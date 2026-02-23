# C4 Model Architecture Documentation — YAM Agri Platform V1.1

> **Version:** 1.1  
> **Date:** 2026-02-23  
> **Owner:** YasserAKareem  
> **Status:** ⚠️ Draft — awaiting owner review  

---

## What is the C4 Model?

The **C4 model** is a lightweight, developer-friendly framework for visualising software architecture at four levels of abstraction, created by Simon Brown. The name stands for:

| Level | Name | Question answered | Audience |
|-------|------|------------------|---------|
| 1 | **System Context** | What does the system do and who uses it? | Everyone — business, technical, non-technical |
| 2 | **Container** | What are the major technical building blocks? | Developers, architects, DevOps |
| 3 | **Component** | What are the logical pieces inside each container? | Developers |
| 4 | **Code** | How are specific components implemented? | Developers (auto-generated where possible) |

**Supporting diagrams** complement the four levels:
- **System Landscape** — all systems operated by YAM Agri in one view
- **Dynamic diagrams** — how elements interact at runtime for key scenarios
- **Deployment diagrams** — how containers are mapped to infrastructure

---

## Notation Used in This Documentation

Because this documentation is plain Markdown (rendered on GitHub), diagrams are expressed in two formats:

1. **Mermaid code blocks** — rendered as interactive diagrams by GitHub
2. **ASCII/text diagrams** — readable fallback for any environment

### C4 Element Types

| Symbol | Type | Used for |
|--------|------|---------|
| 👤 `[Person]` | Person | A human user of the system |
| 🟦 `[Software System]` | Software System | An entire software product (internal or external) |
| 🟪 `[Container]` | Container | An application, data store, or microservice within a software system |
| 🟩 `[Component]` | Component | A logical grouping of code (module, class, layer) within a container |
| ➡️ Arrow with label | Relationship | How elements interact, with the technology used |

### Boundary Types

| Boundary | Meaning |
|----------|---------|
| Solid box | The scope of this diagram |
| Dashed box | An external system or external context |

---

## Document Map

| # | Document | C4 Level | Key content |
|---|----------|----------|-------------|
| [01](01_SYSTEM_CONTEXT.md) | **System Context** | Level 1 | YAM Agri Platform + 9 users + 6 external systems |
| [02](02_CONTAINER_DIAGRAM.md) | **Container Diagram** | Level 2 | 12 containers: Frappe, DBs, AI layer, service adapters, nginx, Field Hub |
| [03](03_COMPONENT_CORE_PLATFORM.md) | **Component: Core Platform** | Level 3 | ERPNext modules + yam_agri_core DocTypes + Frappe framework components |
| [04](04_COMPONENT_AI_LAYER.md) | **Component: AI Layer** | Level 3 | AI Gateway (PII Redactor, Prompt Builder, RAG Retriever, LLM Router, Response Sanitiser, AI Interaction Logger), Ollama, Qdrant RAG |
| [05](05_COMPONENT_SERVICE_ADAPTERS.md) | **Component: Service Adapters** | Level 3 | Scale Connector, IoT Gateway, SMS Handler, Remote Sensing |
| [06](06_DYNAMIC_LOT_LIFECYCLE.md) | **Dynamic: Lot Lifecycle** | Dynamic | Lot creation → QC test → certificate → season policy check → dispatch |
| [07](07_DYNAMIC_AI_ASSIST.md) | **Dynamic: AI Assist Flow** | Dynamic | AI compliance check → redaction → LLM → suggestion → user action |
| [08](08_DEPLOYMENT_DEV.md) | **Deployment: Dev** | Deployment | Docker Compose stack on developer laptop (Yemen-resilient) |
| [09](09_DEPLOYMENT_STAGING.md) | **Deployment: Staging** | Deployment | k3s single-node cluster on staging server |
| [10](10_SYSTEM_LANDSCAPE.md) | **System Landscape** | Landscape | All internal + external systems in one view |
| [11](11_PROPOSED_GAPS.md) | **Proposed Gaps** | — | Missing architectural components and documentation gaps identified |

---

## Architecture Summary (One-Line per Level)

| Level | Summary |
|-------|---------|
| **Context** | YAM Agri Platform serves 9 personas across Yemen cereal supply chain using SMS, mobile PWA, Frappe Desk, and a read-only auditor portal, integrating with weather APIs, FAO databases, satellite imagery, and SMS gateways. |
| **Containers** | Frappe + ERPNext + yam_agri_core (Python/JS), MariaDB 10.6, Redis ×3, AI Gateway (FastAPI), IoT Gateway (Python/MQTT), Scale Connector (Python), nginx (reverse proxy), Field Hub (offline Raspberry Pi node), MinIO (object storage), Qdrant (vector store). |
| **Components (Core Platform)** | 13 DocTypes across 3 modules (ERPNext ERP, Frappe Agriculture, yam_agri_core custom), site isolation via permission query conditions, Frappe REST/RPC API, background job workers, scheduled certificate expiry check. |
| **Deployment** | Dev: Docker Compose (8 services, ~3 GB RAM, Yemen offline-resilient). Staging: k3s single-node (Traefik ingress, PVC storage, WireGuard VPN). Production: k3s multi-node (future V2.0+). |

---

## Key Architecture Decisions (ADRs)

| ID | Decision | Rationale |
|----|----------|----------|
| ADR-01 | **Frappe + ERPNext as permanent base** | Best OSS ERP fit; DocType engine eliminates boilerplate; REST API auto-generated |
| ADR-02 | **MariaDB 10.6 (not PostgreSQL)** | Frappe Framework requires MariaDB; InnoDB crash recovery for Yemen power cuts |
| ADR-03 | **Offline-first Field Hub** | Yemen has daily power outages and intermittent connectivity; 7-day offline operation needed |
| ADR-04 | **AI assistive-only (no autonomous)** | Food safety context: incorrect automated lot accept/recall = real harm; human must decide |
| ADR-05 | **AI Gateway as mandatory redaction layer** | Farmer PII, pricing, and customer IDs must never reach external LLMs |
| ADR-06 | **Universal Observation model for all sensors** | Avoids vendor lock-in; one DocType handles temperature, humidity, NDVI, irrigation, refrigerators |
| ADR-07 | **Site isolation via Frappe permission query conditions** | Server-side enforcement; cannot be bypassed by client |
| ADR-08 | **Docker Compose for dev; k3s for staging/production** | Compose is simpler and lighter; k3s provides production-grade orchestration when needed |
| ADR-09 | **Arabic/RTL-first UI design** | Primary users (farmers, operators) are Arabic-speaking; broken Arabic = broken product |
| ADR-10 | **SMS-based FarmerSMS (no smartphone required)** | U1 farmers have only feature phones; forcing a smartphone excludes them |

---

## Related Documentation

| Document set | Location |
|-------------|---------|
| SDLC Documentation Set | `docs/Docs v1.1/` |
| Smart Farm Architecture (11-layer deep dive) | `docs/SMART_FARM_ARCHITECTURE.md` |
| Touchpoint App Blueprint | `docs/TOUCHPOINT_APP_BLUEPRINT.md` |
| User Persona & Journey Maps | `docs/PERSONA_JOURNEY_MAP.md` |
| RBAC & Org Chart | `docs/planning/RBAC_AND_ORG_CHART.md` |
| Blueprint Playbook | `docs/BLUEPRINT_PLAYBOOK_BEGINNER.md` |

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial C4 architecture documentation set — V1.1 |
