# System Architecture — YAM Agri Platform V1.1

> **SDLC Phase:** Design  
> **Version:** 1.1  
> **Status:** ⚠️ Draft  
> **Date:** 2026-02-23  
> **Related:** [Requirements Specification](02_REQUIREMENTS_SPECIFICATION.md) | [Data Model](04_DATA_MODEL.md)  
> **Deep reference:** `docs/SMART_FARM_ARCHITECTURE.md` (full 11-layer detail)

---

## 1. Architecture Principles

| Principle | Application |
|-----------|-------------|
| **Offline-first** | Every field component must work for ≥ 7 days with no internet |
| **Arabic/RTL-first** | All end-user interfaces must be fully usable in Arabic |
| **Solar-resilient** | Components designed for power-cut recovery; `restart: always` |
| **AI assistive only** | AI never executes actions; it proposes only |
| **Site isolation** | Users see only their assigned sites; enforced server-side |
| **OSS-preferred** | Open-source technology stack wherever possible |
| **ERP as system of record** | All data lives in Frappe/ERPNext; AI layers sit on top |

---

## 2. System Overview — 11-Layer Stack

```
╔══════════════════════════════════════════════════════════════════════════╗
║  LAYER 11 — User Persona & Customer Journey Map                         ║
║  9 personas: Farmer · Supervisor · Inspector · Operator · Logistics     ║
║  Owner · Admin · Auditor · AI Copilot                                   ║
╠══════════════════════════════════════════════════════════════════════════╣
║  LAYER 10 — Touchpoints (9 apps)                                        ║
║  TP-01 FarmerSMS · TP-02 FieldPWA · TP-03 InspectorApp                 ║
║  TP-04 SiloDashboard · TP-05 LogisticsApp · TP-06 OwnerPortal           ║
║  TP-07 AdminPanel · TP-08 AuditorPortal · TP-09 AICopilotPanel          ║
╠══════════════════════════════════════════════════════════════════════════╣
║  LAYER 9 — External Integrations & Ecosystem                            ║
║  Weather APIs · FAO databases · Commodity prices · Donor/NGO portals   ║
╠══════════════════════════════════════════════════════════════════════════╣
║  LAYER 8 — Local AI Marketplace                                         ║
║  MLflow Model Registry · Prompt store · Tool registry · Ollama serving  ║
╠══════════════════════════════════════════════════════════════════════════╣
║  LAYER 7 — AI Agent & Intelligence Layer                                ║
║  OpenJiuwen SDK · ComplianceAgent · AnomalyAgent · SummaryAgent         ║
║  CopilotAgent · Local LLM (Llama 3) · Cloud LLM (GPT-4o, Claude)       ║
╠══════════════════════════════════════════════════════════════════════════╣
║  LAYER 6 — Service Adapters                                             ║
║  AI Gateway · IoT Gateway · Scale Connector · Remote Sensing Ingestor   ║
║  SMS Handler · Data Quality Guard                                       ║
╠══════════════════════════════════════════════════════════════════════════╣
║  LAYER 5 — Core Business Platform                                       ║
║  Frappe Framework + ERPNext v16 + Frappe Agriculture + yam_agri_core    ║
╠══════════════════════════════════════════════════════════════════════════╣
║  LAYER 4 — Data & Storage                                               ║
║  MariaDB 10.6 · Redis 7 · MinIO/S3 · Qdrant · InfluxDB · DuckDB        ║
╠══════════════════════════════════════════════════════════════════════════╣
║  LAYER 3 — Connectivity & Sync                                          ║
║  Site LAN · 4G/satellite uplink · SMS gateway · Mesh Wi-Fi              ║
║  WireGuard VPN · PouchDB offline sync queue                             ║
╠══════════════════════════════════════════════════════════════════════════╣
║  LAYER 2 — Field Hub (Edge Computing)                                   ║
║  Raspberry Pi 4 · Offline Frappe node · Local LLM cache (Ollama)        ║
║  MariaDB · Redis · MQTT broker · Supervisord watchdog                   ║
╠══════════════════════════════════════════════════════════════════════════╣
║  LAYER 1 — Physical / Farm Edge                                         ║
║  IoT sensors · Scales · Cameras · SMS handsets · Solar PV + battery     ║
╚══════════════════════════════════════════════════════════════════════════╝
```

> **V1.1 scope:** Layers 1–5 are the primary build target. Layers 6–11 are partially implemented (AI Gateway, Scale Connector, basic Frappe Desk touchpoints). Full Layer 6–11 build is V1.2+.

---

## 3. Layer Detail (V1.1 Scope)

### 3.1 Layer 1 — Physical / Farm Edge

| Component | Primary choice | OSS/low-cost alternative | Yemen adaptation |
|-----------|---------------|--------------------------|-----------------|
| Soil/moisture sensors | EnviroNODE | DIY Arduino + capacitive (< $5) | Solar-charged; IP65-rated |
| Temperature & humidity | Davis Instruments | DHT22 + ESP32 (< $3) | Weatherproof; battery backup |
| Bin aeration sensor | Ag-Electronics | CO₂ + temp array (RPi Pico) | Hardened for dusty silos |
| Refrigerator probe | iButton DS18B20 | DS18B20 + ESP8266 | Low-power sleep mode |
| Weighbridge / scale | Mettler Toledo | HX711 load-cell kit | Manual CSV fallback when offline |
| GPS tag | Quectel L89 | U-blox NEO-6M (< $8) | Tracks lot movement |
| Farmer handset | Android 4G | Nokia feature phone (2G SMS) | SMS data entry for U1 |
| Power | Grid + backup | **Solar PV + LiFePO₄ battery** | **Primary power — grid unreliable** |

### 3.2 Layer 2 — Field Hub (Edge Computing)

Each site has one **Field Hub** — a ruggedised Raspberry Pi 4 running a minimal offline Frappe node.

| Component | Primary | OSS alternative | Yemen adaptation |
|-----------|---------|----------------|-----------------|
| Hub hardware | Raspberry Pi 4 (4 GB) | Orange Pi 5 | Fanless; 12 V solar input |
| Local Frappe node | frappe-bench (minimal) | Same | Offline-capable; sync queue |
| Local LLM cache | OpenJiuwen + Ollama | Ollama alone | Q4 model fits in 4 GB RAM |
| Local DB | MariaDB 10.6 | SQLite | Replication via binlog when online |
| Local queue | Redis | NATS.io | Buffers sensor readings during outages |
| MQTT broker | Mosquitto | EMQX CE | TLS auth; local retain for offline |
| Watchdog | supervisord | systemd + cron | Auto-restart on power-cycle |

### 3.3 Layer 3 — Connectivity & Sync

**Design rule:** every Field Hub must operate **fully offline for 7 days** and sync when connectivity returns.

| Channel | Technology | OSS/free alternative | Yemen notes |
|---------|-----------|----------------------|------------|
| Primary WAN | 4G LTE (local SIM) | 3G fallback | Yemen: MTN, STC, Y-telecom |
| Backup WAN | Starlink / Thuraya | Iridium Go | ~$30/month |
| SMS data entry | Africa's Talking | RapidPro (OSS) | U1 farmers lot data via SMS |
| Site LAN | 802.11ac Wi-Fi mesh | OpenWRT + Batman-adv | TP-Link EAP225 |
| Offline sync | Frappe offline queue + PouchDB | CouchDB replication | Works in browser PWA |
| MQTT sync | MQTT bridge (Mosquitto) | EMQX cluster bridge | QoS 1; reconnect-on-link |
| VPN | **WireGuard** | Tailscale | Minimal bandwidth; resilient |

### 3.4 Layer 4 — Data & Storage

| Component | Primary | OSS alternative | Notes |
|-----------|---------|----------------|-------|
| Relational DB | **MariaDB 10.6** | PostgreSQL 16 | Frappe requires MariaDB |
| Cache / queue | **Redis 7** | Valkey | Session cache + job queue |
| Object storage | MinIO (self-hosted S3) | SeaweedFS | Certificate PDFs, photos |
| Vector store | **Qdrant** | Milvus, FAISS | AI RAG agents |
| Time-series | **InfluxDB OSS** | TimescaleDB | IoT Observation data |
| Analytics | **DuckDB** (embedded) | Trino | Offline analytics on Field Hub |
| Backup | **Restic + Rclone** | Duplicati | Encrypted; offsite S3 |

### 3.5 Layer 5 — Core Business Platform (Primary V1.1 Target)

```
┌────────────────────────────────────────────────────────┐
│                  Frappe Framework v16                  │
│  ┌──────────────┐  ┌────────────┐  ┌───────────────┐  │
│  │   ERPNext    │  │  Frappe    │  │ yam_agri_core │  │
│  │    v16       │  │Agriculture │  │  (custom app) │  │
│  │              │  │    app     │  │               │  │
│  │ • Purchase   │  │            │  │ • Site        │  │
│  │ • Sales      │  │ • Crop     │  │ • StorageBin  │  │
│  │ • Inventory  │  │   Cycle    │  │ • Device      │  │
│  │ • Finance    │  │ • Water    │  │ • Lot         │  │
│  │ • HR         │  │   Analysis │  │ • Transfer    │  │
│  │ • CRM        │  │ • Disease  │  │ • ScaleTicket │  │
│  │              │  │   Tracking │  │ • QCTest      │  │
│  └──────────────┘  └────────────┘  │ • Certificate │  │
│                                    │ • Nonconformance│ │
│                                    │ • EvidencePack│  │
│                                    │ • Complaint   │  │
│                                    │ • Observation │  │
│                                    └───────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Frappe Framework Core                  │  │
│  │  DocType engine · Workflow · Permissions ·       │  │
│  │  REST/RPC API · WebSockets · File manager ·      │  │
│  │  Scheduler · Email/SMS · Desk UI · Print formats │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

### 3.6 Layer 6 — Service Adapters (Partial V1.1)

| Service | Function | Technology | V1.1 status |
|---------|----------|-----------|-------------|
| **Scale Connector** | CSV → ScaleTicket → Lot quantity + mismatch flag | Python CSV parser + Frappe REST | ✅ V1.1 |
| **IoT Gateway** | MQTT → Observation + validation | Python + Mosquitto | ✅ V1.1 basic |
| **AI Gateway** | Redact PII → route prompt → log hash → suggest | FastAPI + OpenJiuwen | ✅ V1.1 basic |
| SMS Handler | Structured SMS → Lot/ScaleTicket | Africa's Talking webhook | 🔲 V1.2 |
| Remote Sensing | Satellite NDVI → Observation | EODAG + Sentinel-2 | 🔲 V1.2 |
| Data Quality Guard | Great Expectations validation | Python | 🔲 V1.2 |

---

## 4. Development Environment Architecture

### 4.1 Docker Compose Stack (Dev)

```
┌─────────────────────────────────────────────────────┐
│                Docker Compose (Dev)                  │
│                                                     │
│  ┌───────────┐  ┌───────────┐  ┌───────────────┐  │
│  │  frappe   │  │  worker   │  │  scheduler    │  │
│  │  (web)    │  │  (RQ)     │  │  (cron)       │  │
│  │  :8000    │  │           │  │               │  │
│  └─────┬─────┘  └─────┬─────┘  └───────┬───────┘  │
│        │               │                │           │
│  ┌─────▼───────────────▼────────────────▼───────┐  │
│  │               MariaDB 10.6 (:3306)           │  │
│  └───────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────┐ │
│  │  Redis Queue (:6379)  Redis Cache (:6380)      │ │
│  └────────────────────────────────────────────────┘ │
│  ┌───────────┐  ┌───────────┐                       │
│  │   nginx   │  │ socketio  │                       │
│  │  (:80)    │  │  (:9000)  │                       │
│  └───────────┘  └───────────┘                       │
└─────────────────────────────────────────────────────┘
```

**Memory budget (8 GB RAM laptop):**

| Service | Approximate RAM |
|---------|----------------|
| MariaDB 10.6 | ~400 MB |
| Redis (×3) | ~50 MB each |
| Frappe/ERPNext workers | ~1.5–2 GB |
| nginx | ~50 MB |
| **Total** | **~2.5–3 GB** |

### 4.2 Staging Architecture (k3s — Post-Dev)

- Single-node k3s on the staging server
- Frappe Helm chart or custom manifests
- Traefik ingress controller
- Persistent volumes for MariaDB data and MinIO files
- WireGuard VPN for access
- Separate namespaces for `frappe` and `services`

### 4.3 Production Architecture (Future — V2.0+)

- Multi-node k3s cluster
- MariaDB replication (primary + replica)
- MinIO distributed mode
- Redis Sentinel
- Prometheus + Grafana monitoring
- Automated Restic backups to offsite S3

---

## 5. Data Flow Diagrams

### 5.1 Lot Creation & QC Evidence Flow

```
Farmer/Supervisor
      │
      ▼
 [FieldPWA / Desk]
 Create Lot (Draft)
      │
      ▼
 [Scale Connector]
 Import ScaleTicket CSV ──▶ Update Lot qty
      │                          │
      │               mismatch? ▼
      │               [Nonconformance created]
      ▼
 [QA Inspector]
 Create QCTest ──────────────────▶ Attach to Lot
 Create Certificate ─────────────▶ Attach to Lot
      │
      ▼
 [Season Policy check]
 All required tests/certs present + not expired?
      │ YES                          │ NO
      ▼                              ▼
 Lot → Released             Block submit + show gap
      │
      ▼
 [Logistics Coordinator]
 Create Shipment Lot (Transfer: split)
```

### 5.2 Sensor Observation Flow

```
[IoT Sensor / Device]
      │ MQTT publish
      ▼
[Field Hub MQTT Broker (Mosquitto)]
      │ subscribe
      ▼
[IoT Gateway (Python)]
   Validate: units? range?
      │ VALID                 │ INVALID
      ▼                       ▼
[Observation: quality_flag=Valid]  [Observation: quality_flag=Quarantine]
      │                                     │
      ▼                                     ▼
 Alert check:                      Do NOT use for automation
 threshold exceeded?
      │ YES
      ▼
 Frappe Notification → QA Inspector / Operator
```

### 5.3 AI Assist Flow

```
[User in Frappe Desk]
 "Check compliance for LOT-001"
      │
      ▼
[yam_agri_core API]
 Gather lot data (local — no PII to external)
      │
      ▼
[AI Gateway (FastAPI)]
 Redact: PII, pricing, customer IDs
 Build prompt: compliance context only
      │
      ▼
[LLM — local Ollama or cloud (OpenAI/Claude)]
 Generate compliance gap list
      │
      ▼
[AI Gateway]
 Log: hash, record ref, user, model, timestamp
 Return: suggestion text
      │
      ▼
[Frappe Desk — AI Suggestion Panel]
 Display suggestion to user
 User: Accept (creates Nonconformance tasks) or Dismiss
```

---

## 6. Security Architecture

See full detail in [06_SECURITY_AND_RBAC.md](06_SECURITY_AND_RBAC.md).

**Summary:**
- All secrets via environment variables; never in Git
- HTTPS enforced on all external endpoints
- WireGuard VPN for staging access
- Frappe User Permissions enforce site isolation
- AI Gateway redacts all sensitive data before external LLM calls
- Full audit log of all admin actions and AI interactions

---

## 7. Technology Summary

| Layer | Primary stack | OSS alternative |
|-------|-------------|----------------|
| Core ERP | Frappe v16 + ERPNext v16 | — (no realistic swap) |
| Agriculture module | Frappe Agriculture | Custom ERPNext build |
| Database | MariaDB 10.6 | PostgreSQL (with adapter) |
| Cache | Redis 7 | Valkey |
| Object storage | MinIO | SeaweedFS |
| Vector store | Qdrant | FAISS, Milvus |
| AI orchestration | OpenJiuwen SDK | LangGraph, LangChain |
| Local LLM | Ollama + Llama 3.2 (Q4) | vLLM, llama.cpp |
| Cloud LLM | GPT-4o / Claude 3.5 | Cohere Command R+ |
| Edge compute | Raspberry Pi 4 | Orange Pi 5 |
| Connectivity | WireGuard + 4G LTE | Tailscale |
| SMS | Africa's Talking | RapidPro (OSS) |
| Maps | OpenStreetMap + Leaflet | — (no Google Maps) |
| CI/CD | GitHub Actions | — |
| Container runtime | Docker Compose (dev) / k3s (staging) | — |

---

## 8. Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial architecture document — V1.1 |
