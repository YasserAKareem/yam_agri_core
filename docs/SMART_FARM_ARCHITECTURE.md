# Smart Farm, Farmer & Agri-Business — Full User Stack Architecture

> **Platform:** Frappe + ERPNext + Frappe Agriculture + OpenJiuwen AI Agent SDK  
> **Context:** Yemen — conflict-affected, connectivity-constrained, water-scarce, solar-powered  
> **Design commitment:** offline-first, Arabic/RTL-first, solar-powered edge, assistive-AI only

---

## 1) User Personas & Their Needs

> **Deep profiles and journey maps:** `docs/PERSONA_JOURNEY_MAP.md` — Layer 11 of this stack

| # | Persona | Where they work | Key need | Device / Connectivity |
|---|---------|----------------|----------|----------------------|
| U1 | **Smallholder Farmer** | Field / remote farm | Simple task input, weather & irrigation alerts | Feature phone + SMS; occasional 2G/3G |
| U2 | **Farm Supervisor** | Farm site | Lot creation, weight capture, crew scheduling | Android tablet; offline PWA; 3G when available |
| U3 | **QA / Food Safety Inspector** | Farm + silo | QC tests, certificates, HACCP checklists | Laptop or tablet; site Wi-Fi or 4G |
| U4 | **Silo / Store Operator** | Silo / warehouse | Bin monitoring, scale tickets, stock reconciliation | Desktop or tablet; on-premise LAN |
| U5 | **Logistics Coordinator** | Office / field | Shipment dispatch, route planning, truck tracking | Smartphone + 4G |
| U6 | **Agri-Business Owner (YAM)** | Office / anywhere | Dashboards, margin, compliance reports, AI insights | Desktop + laptop; broadband |
| U7 | **System Admin / IT** | Office / remote | Platform config, backups, user management | Laptop; broadband |
| U8 | **External Auditor / Donor** | Remote / office | Evidence packs, audit trails, compliance certificates | Read-only web portal |
| U9 | **AI Copilot (non-human)** | AI Gateway | Suggestions, anomaly flags, summaries | Internal API calls only |

---

## 2) Full Stack Architecture

The stack has **11 layers**. Each layer is designed to degrade gracefully when connectivity or power fails.

```
╔══════════════════════════════════════════════════════════════════════════╗
║  LAYER 11 — User Persona & Customer Journey Map                         ║
║  (9 personas: Farmer, Supervisor, Inspector, Operator, Logistics,       ║
║   Owner, Admin, Auditor, AI Copilot — full journey maps + test refs)    ║
╠══════════════════════════════════════════════════════════════════════════╣
║  LAYER 10 — Touchpoints                                                 ║
║  (FarmerSMS · FieldPWA · InspectorApp · SiloDashboard · LogisticsApp   ║
║   · OwnerPortal · AdminPanel · AuditorPortal · AICopilotPanel)          ║
╠══════════════════════════════════════════════════════════════════════════╣
║  LAYER 9 — External Integrations & Ecosystem                            ║
║  (Weather APIs, FAO databases, commodity prices, donor/NGO portals)     ║
╠══════════════════════════════════════════════════════════════════════════╣
║  LAYER 8 — Local AI Marketplace                                         ║
║  (Private model catalog, prompt store, tool registry)                   ║
╠══════════════════════════════════════════════════════════════════════════╣
║  LAYER 7 — AI Agent & Intelligence Layer                                ║
║  (OpenJiuwen SDK + local LLM — workflow agents, RAG, anomaly detection) ║
╠══════════════════════════════════════════════════════════════════════════╣
║  LAYER 6 — Service Adapters                                             ║
║  (AI Gateway, IoT Gateway, Scale Connector, Remote Sensing ingestor)    ║
╠══════════════════════════════════════════════════════════════════════════╣
║  LAYER 5 — Core Business Platform                                       ║
║  (Frappe Framework + ERPNext + Frappe Agriculture + yam_agri_core)      ║
╠══════════════════════════════════════════════════════════════════════════╣
║  LAYER 4 — Data & Storage                                               ║
║  (MariaDB, Redis, MinIO/S3, Qdrant/Milvus vector store)                 ║
╠══════════════════════════════════════════════════════════════════════════╣
║  LAYER 3 — Connectivity & Sync                                          ║
║  (Site LAN, 4G/satellite uplink, SMS gateway, mesh Wi-Fi, sync queue)  ║
╠══════════════════════════════════════════════════════════════════════════╣
║  LAYER 2 — Field Hub (Edge Computing)                                   ║
║  (Raspberry Pi / industrial PC — offline Frappe node, local AI cache)  ║
╠══════════════════════════════════════════════════════════════════════════╣
║  LAYER 1 — Physical / Farm Edge                                         ║
║  (IoT sensors, scales, cameras, SMS handsets, solar power)             ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

## 3) Layer-by-Layer Technology Map

### Layer 1 — Physical / Farm Edge

| Component | Primary choice | OSS / low-cost alternative | Yemen adaptation |
|-----------|---------------|---------------------------|-----------------|
| Soil/moisture sensors | EnviroNODE, Sentek | DIY Arduino + capacitive sensors (< $5) | Solar-charged; IP65-rated for dust |
| Temperature & humidity | Davis Instruments | DHT22 + ESP32 (< $3) | Weatherproof housing; battery backup |
| Bin aeration sensor | Ag-Electronics | Custom CO₂ + temp array (RPi Pico) | Hardened for dusty silo environments |
| Refrigerator probe | iButton DS18B20 | DS18B20 + ESP8266 Wi-Fi node | Low-power sleep mode between readings |
| Weighbridge / scale | Mettler Toledo | Open-source HX711 load-cell kit | Manual CSV fallback when offline |
| Field camera | Hikvision IP cam | ESP32-CAM module (< $10) | Solar + 32 GB local SD buffer |
| GPS tag | Quectel L89 | U-blox NEO-6M (< $8) | Tracks lot movement between sites |
| Farmer handset | Android 4G | Nokia feature phone (2G SMS) | SMS-based data entry for U1 farmers |
| Power | Grid + backup | **Solar PV + LiFePO₄ battery** | **Primary power — grid unreliable** |

---

### Layer 2 — Field Hub (Edge Computing)

Each farm/silo has one **Field Hub** — a small, ruggedised computer that runs a minimal local stack and syncs to central when connectivity is available.

| Component | Primary choice | OSS alternative | Yemen adaptation |
|-----------|---------------|----------------|-----------------|
| Hub hardware | Raspberry Pi 4 (4 GB) | Orange Pi 5 / Rock Pi 4 | Fanless case; passive cooling; 12 V solar input |
| Local Frappe node | frappe-bench (minimal) | **frappe-bench** (same, self-hosted) | Offline-capable; sync queue to central |
| Local LLM cache | **OpenJiuwen** (cached model) | Ollama + Llama 3 / Mistral | Q4-quantised model fits in 4 GB RAM |
| Local DB | MariaDB 10.6 (same as central) | SQLite for ultra-light nodes | Replication via binlog when online |
| Local message queue | Redis (lightweight) | NATS.io | Buffers sensor readings during outages |
| Sensor data broker | MQTT (Mosquitto) | EMQX CE / VerneMQ | TLS auth; local retain for offline |
| Time sync | chrony (NTP) | GPS-disciplined clock (u-blox) | No internet NTP fallback: GPS clock |
| Watchdog | supervisord | systemd + bash cron | Auto-restart on power-cycle |
| Storage | 128 GB SSD | 64 GB industrial SD | Wear-levelling SD for < $15 |

---

### Layer 3 — Connectivity & Sync

**Design rule:** every field hub must operate **fully offline for 7 days** and sync when connectivity returns.

| Channel | Technology | OSS / free alternative | Yemen adaptation |
|---------|-----------|------------------------|-----------------|
| Primary WAN | 4G LTE (local SIM) | 3G fallback | Yemen operators: MTN, STC, Y-telecom |
| Backup WAN | **Starlink** or Thuraya satellite | Iridium Go (SMS only) | Starlink increasingly available; ~$30/mo |
| SMS data entry | Twilio SMS API | **Africa's Talking** (cheaper) | U1 farmers send lot data via structured SMS |
| Site LAN | 802.11ac Wi-Fi mesh | **OpenWRT + Batman-adv mesh** | TP-Link EAP225 flashed with OpenWRT |
| Offline sync | Frappe's offline queue + PouchDB | CouchDB replication | PouchDB works in browser PWA without install |
| MQTT broker sync | MQTT bridge (Mosquitto) | EMQX cluster bridge | Reconnect-on-link with QoS 1 |
| VPN / secure tunnel | **WireGuard** | OpenVPN, Tailscale | WireGuard: minimal bandwidth, resilient |
| Sync conflict resolution | Frappe document versioning | Custom last-write-wins | Manual conflict resolution for critical lots |

---

### Layer 4 — Data & Storage

| Component | Primary choice | OSS alternative | Notes |
|-----------|---------------|----------------|-------|
| Relational DB | **MariaDB 10.6** | PostgreSQL 16 | Frappe requires MariaDB; PG via Postgres adapter |
| Cache / queue broker | **Redis 7** | Valkey (Redis OSS fork) | Session cache + background job queue |
| Object / file storage | MinIO (self-hosted S3) | SeaweedFS, Ceph | Certificate PDFs, photos, evidence packs |
| Vector store | **Qdrant** | Milvus, Weaviate, FAISS | Used by OpenJiuwen RAG agents |
| Time-series (sensors) | **InfluxDB OSS** | TimescaleDB (PG extension) | Observation data from IoT gateway |
| Feature store | **Feast** | Hopsworks FS (OSS) | Pre-computed features for ML models |
| Data warehouse | **DuckDB** (embedded) | Trino (for multi-node) | Offline analytics; runs on Field Hub |
| Backup | **Restic + Rclone** | Duplicati | Encrypted; pushes to MinIO + offsite S3 |

---

### Layer 5 — Core Business Platform

This is the **permanent base** — all data lives here; all other layers connect to it.

```
┌────────────────────────────────────────────────────────┐
│                  Frappe Framework                      │
│  ┌──────────────┐  ┌────────────┐  ┌───────────────┐  │
│  │   ERPNext    │  │  Frappe    │  │ yam_agri_core │  │
│  │  (v16+)      │  │Agriculture │  │  (custom app) │  │
│  │              │  │    app     │  │               │  │
│  │ • Purchase   │  │            │  │ • Lot         │  │
│  │ • Sales      │  │ • Crop     │  │ • Transfer    │  │
│  │ • Inventory  │  │   Cycle    │  │ • QCTest      │  │
│  │ • Finance    │  │ • Water    │  │ • Certificate │  │
│  │ • HR         │  │   Analysis │  │ • EvidencePack│  │
│  │ • CRM        │  │ • Disease  │  │ • Observation │  │
│  │              │  │   Tracking │  │ • ScaleTicket │  │
│  └──────────────┘  └────────────┘  └───────────────┘  │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Frappe Framework core                  │  │
│  │  DocType engine · Workflow · Permissions ·       │  │
│  │  REST/RPC API · WebSockets · File manager ·      │  │
│  │  Scheduler · Email/SMS · Desk UI · Print formats │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

| Frappe capability | OSS alternative | Notes |
|------------------|----------------|-------|
| **Frappe Framework** | Odoo (heavier), Django + Wagtail | Frappe is the best fit — no realistic OSS swap |
| **ERPNext** | Odoo Community, Dolibarr | ERPNext is the preferred OSS ERP on Frappe |
| **Frappe Agriculture** | Custom build on ERPNext | Available free on GitHub: frappe/agriculture |
| Frappe Desk (web UI) | React custom UI via Frappe API | Desk is included; custom Vue/React for mobile |
| **Frappe Payments** | ERPNext Accounting | Built-in; no third-party needed |
| **Frappe Insights** | Metabase (OSS), Apache Superset | Better dashboards than built-in Frappe reports |
| Background jobs | Frappe's RQ (Redis Queue) | Celery if decoupled workers needed |
| Notifications | Frappe Notifications + Twilio | ntfy.sh (OSS push) or Firebase FCM |

---

### Layer 6 — Service Adapters

These micro-services sit between the physical world and the Frappe platform.

| Service | Function | Primary tech | OSS alternative |
|---------|----------|-------------|----------------|
| **IoT Gateway** | Ingest MQTT sensor readings → Observation DocType | Python + Mosquitto subscriber | Node-RED (visual), Telegraf + InfluxDB |
| **Scale Connector** | CSV / serial port → ScaleTicket DocType | Python CSV parser + Frappe REST | Apache NiFi (OSS), Airbyte |
| **AI Gateway** | Redact PII → route prompt → log hash → return suggestion | FastAPI + OpenJiuwen SDK | LiteLLM proxy (OSS), LocalAI |
| **Remote Sensing Ingestor** | Satellite NDVI / flood index → Observation | Python + Sentinel Hub API | EODAG (OSS), OpenEO |
| **SMS Handler** | Structured SMS from farmer → Lot/ScaleTicket | Africa's Talking webhook | Gammu (GSM modem), RapidPro (OSS) |
| **Data Quality Guard** | Validate + quarantine bad sensor readings | Great Expectations | Soda Core (OSS), dbt tests |

---

### Layer 7 — AI Agent & Intelligence Layer

**OpenJiuwen** is the primary AI agent SDK. It orchestrates LLM workflows that call Frappe APIs, vector stores, and external data — always in assistive mode.

```
┌─────────────────────────────────────────────────────────────────┐
│               OpenJiuwen AI Agent Layer                         │
│                                                                 │
│  ┌────────────────────┐    ┌──────────────────────────────────┐ │
│  │   Workflow Agents  │    │        Agent Tools               │ │
│  │                    │    │                                  │ │
│  │ • ComplianceAgent  │───▶│ • FrappeAPITool (REST calls)     │ │
│  │   "What's missing  │    │ • QdrantRAGTool (doc retrieval)  │ │
│  │    for this lot?"  │    │ • WeatherTool (NOAA/Open-Meteo)  │ │
│  │                    │    │ • AlertRankingTool               │ │
│  │ • AnomalyAgent     │───▶│ • RedactionTool (PII strip)      │ │
│  │   Sensor hotspot   │    │ • SMSTool (Africa's Talking)     │ │
│  │   detection        │    │ • LogHashTool (audit trail)      │ │
│  │                    │    └──────────────────────────────────┘ │
│  │ • SummaryAgent     │                                         │
│  │   Evidence pack    │    ┌──────────────────────────────────┐ │
│  │   narrative        │    │        LLM Backend               │ │
│  │                    │───▶│                                  │ │
│  │ • CopilotAgent     │    │ Local (offline-first):           │ │
│  │   Work order text, │    │  • Ollama + Llama 3.2 (3B Q4)   │ │
│  │   CAPA draft       │    │  • Mistral 7B Q4 via vLLM        │ │
│  │                    │    │                                  │ │
│  └────────────────────┘    │ Cloud (when online):             │ │
│                            │  • OpenAI GPT-4o (via redaction) │ │
│                            │  • Cohere Command R+             │ │
│                            │  • Anthropic Claude 3.5 Sonnet   │ │
│                            └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

| AI capability | OpenJiuwen component | OSS alternative |
|---------------|---------------------|----------------|
| Workflow orchestration | `openjiuwen.core.workflow` | LangGraph, Prefect |
| LLM call management | `openjiuwen.core.foundation.llm` | LiteLLM, LangChain |
| Agent runner | `openjiuwen.core.runner` | AutoGen, CrewAI |
| Prompt optimisation | Built-in auto-optimiser | DSPy (OSS) |
| RAG / vector retrieval | `QdrantRAGTool` (custom) | LlamaIndex, Haystack |
| Streaming output | Built-in async IO | LangChain streaming |
| Checkpoint / recovery | Built-in state save | LangGraph checkpointers |
| Observability | Built-in full-link tracing | LangSmith OSS, Phoenix |
| Local LLM inference | Ollama (separate service) | vLLM, llama.cpp |

---

### Layer 8 — Local AI Marketplace

A **private, self-hosted** catalog of models, prompts, and tools — no external calls unless explicitly enabled.

| Component | Primary tech | OSS alternative | Notes |
|-----------|-------------|----------------|-------|
| Model catalog UI | **MLflow Model Registry** | BentoML, KServe | Track versions, lineage, attestations |
| Prompt & asset store | **LlamaHub** (local mirror) | Custom Frappe DocType | Store approved prompts as Frappe docs |
| Tool/plugin registry | Custom FastAPI registry | Frappe DocType + webhooks | Each tool has trust + version metadata |
| Model serving | **Ollama** (local) + **KServe** | Seldon Core, BentoML | Ollama for dev; KServe for prod |
| Access control | **Frappe RBAC** | OPA (Open Policy Agent) | Roles: QA Manager can activate models |
| Compliance evidence | **MLflow** experiment tracking | Aim (OSS) | Links model version to every AI output |
| Security scanning | **Garak** (LLM red-team) | custom prompt fuzzer | Run before any new model activates |
| Observability | **Prometheus + Grafana** | OpenTelemetry + Jaeger | Latency, cost, error-rate per model |

---

### Layer 9 — External Integrations & Ecosystem

| Integration | Service | OSS / free alternative | Yemen relevance |
|-------------|---------|------------------------|----------------|
| Weather data | Open-Meteo API (free) | NOAA GFS, ERA5 (Copernicus) | Critical: 90% water used in agri |
| Satellite/NDVI | Sentinel Hub (ESA free tier) | **EODAG + Sentinel-2** | Crop stress detection via free imagery |
| Commodity prices | FAO GIEWS, World Bank API | FAOSTAT bulk CSV | Yemen import-dependent; price signals matter |
| Standards library | FAO eAGRIS, CODEX Alimentarius | FAO open data portal | HACCP / FAO GAP document RAG |
| Donor / NGO portal | Read-only Frappe API key | IATI standard XML export | UNDP, FAO, WFP integration |
| SMS / voice | Africa's Talking (low-cost) | RapidPro (OSS) | Cheapest SMS in MENA region |
| Maps | OpenStreetMap + Leaflet.js | Google Maps (cost) | OSM Yemen maps; offline tiles via Nominatim |
| Payments | ERPNext built-in | Frappe Payments app | Bank transfer / hawala-compatible records |
| Carbon reporting | OpenGHG (OSS) | Scope 3 spreadsheet | Shipment carbon for donor requirements |
| Export compliance | UN Comtrade API (free) | WTO tariff docs PDF + RAG | Yemen export regulations via RAG agent |

---

### Layer 10 — Touchpoints

The **9 touchpoint apps** are the UI surfaces through which users interact with the platform. Each app is built for one primary persona and uses the Frappe REST API as its data backbone.

| App | Persona | Channel | Offline | Details |
|-----|---------|---------|---------|---------|
| **TP-01 FarmerSMS** | U1 Smallholder Farmer | SMS / USSD (Africa's Talking) | ✅ 100% | Structured Arabic SMS commands; no smartphone required |
| **TP-02 FieldPWA** | U2 Farm Supervisor | Mobile PWA (Android tablet) | ✅ 7-day | PouchDB offline queue; OSM offline map; GPS lot capture |
| **TP-03 InspectorApp** | U3 QA Inspector | Tablet PWA + Frappe Desk | ⚠️ Wi-Fi | HACCP checklist, QCTest, certificate, evidence pack |
| **TP-04 SiloDashboard** | U4 Silo Operator | Desktop Frappe Desk | ⚠️ LAN | Bin SVG map, CSV scale import, alert triage |
| **TP-05 LogisticsApp** | U5 Logistics Coordinator | Mobile PWA + map | ⚠️ 4G | Shipment, BOL/document generation, GPS tracking |
| **TP-06 OwnerPortal** | U6 Agri-Business Owner | Web dashboard | ❌ Broadband | KPI dashboard, margin copilot, compliance status |
| **TP-07 AdminPanel** | U7 System Admin | Frappe Desk + CLI | ❌ Server | System health, backups, user management, model registry |
| **TP-08 AuditorPortal** | U8 External Auditor/Donor | Read-only web | ❌ Internet | Evidence packs, compliance summary, IATI export |
| **TP-09 AICopilotPanel** | U9 AI Copilot (embedded) | Embedded component | ✅ Local Ollama | Standard AI suggestion panel embedded in all apps |

> **Full blueprint:** `docs/TOUCHPOINT_APP_BLUEPRINT.md`

---

### Layer 11 — User Persona & Customer Journey Map

The **9 user personas** are the human (and AI) actors who use the platform. Each persona has a full customer journey map, pain points, delight moments, Yemen-specific context, and acceptance test scenarios.

| Persona | Role | Primary touchpoint | Key journey stages |
|---------|------|-------------------|--------------------|
| **U1 Smallholder Farmer** | Grain supplier | TP-01 FarmerSMS | Awareness → First SMS → Regular lot reporting |
| **U2 Farm Supervisor** | Field operations | TP-02 FieldPWA | Onboarding → Daily routine → Offline resilience |
| **U3 QA Inspector** | Food safety | TP-03 InspectorApp | Receiving inspection → HACCP audit → Evidence pack |
| **U4 Silo Operator** | Storage management | TP-04 SiloDashboard | Morning check → Alert triage → Reconciliation |
| **U5 Logistics Coordinator** | Shipment management | TP-05 LogisticsApp | Planning → Document generation → In-transit tracking |
| **U6 Agri-Business Owner** | Strategic oversight | TP-06 OwnerPortal | Daily review → Margin analysis → Donor preparation |
| **U7 System Admin** | Platform operations | TP-07 AdminPanel | Health check → Backup verification → User management |
| **U8 External Auditor/Donor** | Compliance verification | TP-08 AuditorPortal | Portal access → Evidence review → IATI export |
| **U9 AI Copilot** | Assistive intelligence | TP-09 AICopilotPanel | Model activation → Invocation → Suggestion → Fallback |

> **Full journey maps:** `docs/PERSONA_JOURNEY_MAP.md`  
> **Master test reference:** See `PERSONA_JOURNEY_MAP.md` — Test Reference Matrix (U1-T01 through U9-T07)


---

## 4) Data Flow: Farmer to Auditor

```
[U1 Farmer] ──SMS──▶ [SMS Handler] ──▶ [Frappe Lot DocType]
                                              │
[Layer 1 sensors] ──MQTT──▶ [IoT Gateway] ──▶ [Observation DocType]
                                              │
[Weighbridge CSV] ──▶ [Scale Connector] ──▶ [ScaleTicket DocType]
                                              │
                                    [Frappe Workflow Engine]
                                              │
                          ┌───────────────────┼──────────────────────┐
                          ▼                   ▼                      ▼
                  [QCTest DocType]   [Certificate DocType]  [Nonconformance]
                                              │
                          [AI Gateway] ◀──── [User trigger (U3/U4)]
                                │
                    [OpenJiuwen ComplianceAgent]
                                │
                        [Suggestion panel]
                        (approve / reject)
                                │
                    [EvidencePack DocType]
                                │
                [U8 Auditor read-only portal] ──▶ PDF export
```

---

## 5) Mobile & Offline User Interfaces

| User (Persona) | Interface type | Technology | Offline support |
|----------------|---------------|-----------|----------------|
| U1 Farmer | Structured SMS commands | Africa's Talking / RapidPro | ✅ Fully offline |
| U2 Farm Supervisor | **Progressive Web App (PWA)** | Frappe + PouchDB offline | ✅ 7-day offline queue |
| U3 QA Inspector | Frappe Desk (mobile view) | Frappe built-in responsive | ⚠️ Partial (Wi-Fi required) |
| U4 Silo Operator | Frappe Desk (desktop/tablet) | Frappe Desk | ⚠️ On-premise LAN |
| U5 Logistics | Mobile PWA + map | Frappe + Leaflet OSM | ⚠️ 4G required for maps |
| U6 Business Owner | Frappe Desk + Insights dashboard | Frappe + Apache Superset | ❌ Requires internet |
| U7 Admin | Frappe Desk + CLI | bench CLI | ❌ Requires server access |
| U8 Auditor | Read-only Frappe portal | Frappe Desk (guest role) | ❌ Requires internet |

### Arabic / RTL requirements
- Frappe built-in Arabic translation + RTL CSS — **enabled by default**
- All AI-generated text must pass through **Arabic NLP normalisation** (use CAMeL-Tools OSS)
- SMS messages to U1 farmers in Arabic (Africa's Talking supports Arabic encoding)
- All form labels, error messages, and AI suggestion panels must be bilingual (AR/EN toggle)

---

## 6) Security Architecture

| Concern | Control | OSS tool |
|---------|---------|---------|
| Authentication | Frappe built-in + MFA (TOTP) | PyOTP + QR code |
| Authorisation | Frappe RBAC (role-based) + site isolation | OPA for advanced policies |
| Data in transit | TLS 1.3 everywhere + WireGuard VPN | Let's Encrypt (Certbot) |
| Data at rest | MariaDB encrypted tablespaces | LUKS disk encryption |
| PII redaction | AI Gateway redaction layer | presidio (Microsoft OSS) |
| Secrets management | Docker secrets / k3s Secrets | **Vault** (HashiCorp OSS) |
| Vulnerability scanning | Trivy (container images) | Grype (Anchore OSS) |
| LLM prompt injection | Garak red-teaming + guardrails | NeMo Guardrails (NVIDIA OSS) |
| Audit logs | Frappe Activity Log + immutable WORM | Loki (Grafana OSS) |
| Backup integrity | Restic checksums | Restic built-in |

---

## 7) Infrastructure Deployment Map

### Dev (single laptop / GitHub Codespace)
```
Docker Compose
├── frappe-worker
├── frappe-web (nginx)
├── mariadb
├── redis
├── minio
├── qdrant
├── mqtt-broker (Mosquitto)
└── ollama (local LLM)
```

### Staging / Production (on-premise server, Aden or Sana'a office)
```
k3s single-node cluster (solar + UPS powered)
├── Namespaces
│   ├── frappe/          (web, worker, scheduler, nginx)
│   ├── data/            (mariadb, redis, minio, qdrant, influxdb)
│   ├── ai/              (ollama, openjiuwen-gateway, kserve)
│   ├── iot/             (mosquitto, iot-gateway, scale-connector)
│   └── observability/   (prometheus, grafana, loki)
├── Persistent volumes    (local SSD + MinIO replication to satellite S3)
├── Ingress              (Traefik + Let's Encrypt)
└── WireGuard VPN        (field hubs ↔ central server)
```

### Field Hub (each farm / silo site)
```
Raspberry Pi 4 (or equivalent)
├── frappe-lite (offline node, MariaDB, Redis)
├── mosquitto (MQTT broker for sensors)
├── iot-gateway (Python MQTT→Frappe)
├── ollama (Q4 quantised Llama 3.2 3B)
└── sync-agent (WireGuard + Frappe replication)
```

---

## 8) Yemen-Specific Design Constraints & Decisions

### 8.1) Power: Solar-first design

| Constraint | Design decision |
|-----------|----------------|
| Grid unreliable / absent in rural areas | All field hubs and sensor nodes run on solar + LiFePO₄ battery |
| UPS for silo/office servers | 2-hour UPS + automatic graceful shutdown after 30 min |
| Low-power sensors | ESP32 deep-sleep between readings (< 1 mA idle) |
| Server power budget | k3s on mini-PC (Beelink EQ12, 10 W idle) preferred over rack server |

### 8.2) Connectivity: Offline-first, sync-when-available

| Constraint | Design decision |
|-----------|----------------|
| Rural areas: no internet for days | 7-day offline operation mandatory (Field Hub + PouchDB PWA) |
| Bandwidth < 1 Mbps when connected | Sync only diffs (Frappe document versioning); compress with Brotli |
| SMS is most reliable rural channel | U1 farmers use structured SMS for lot data entry; system parses and creates DocTypes |
| Satellite available in some areas | Starlink terminal at central office; field hubs use 4G/3G |
| Mesh Wi-Fi for silo sites | OpenWRT + batman-adv mesh covers multi-building silo complexes |

### 8.3) Localisation: Arabic and Yemen context

| Constraint | Design decision |
|-----------|----------------|
| Arabic primary language | Frappe Arabic translation enabled; RTL layout; all UI strings bilingual |
| Yemen-specific cereal crops | Sorghum (دُخن), wheat (قمح), millet (ذُرة) as primary Lot crop types |
| Yemen governorates as Site names | Taiz, Lahj, Abyan, Hodeidah/Hudaydah, Hadhramaut pre-loaded as Site fixtures |
| Hijri calendar used in some contexts | Frappe supports dual calendar; show both Gregorian and Hijri dates |
| Local units (Mudd, Kayl, Thumn) | Custom UoM DocType entries for traditional Yemeni grain measures |
| Hawala payment system | ERPNext Journal Entry used to record hawala transfers as payment receipts |

### 8.4) Data sovereignty and security

| Constraint | Design decision |
|-----------|----------------|
| No cloud dependency for core operations | All DocTypes, workflows, and LLM inference run on-premise first |
| Conflict risk: server seizure / damage | Encrypted off-site backup via Restic → satellite S3 (Backblaze B2) |
| Limited IT staff | `run.sh` script abstracts all operations; bench CLI for advanced tasks |
| Low digital literacy (some users) | PWA with icon-based navigation; AI copilot drafts text for illiterate operators |
| Donor/NGO audit requirements | Evidence packs auto-include IATI-compatible metadata; read-only donor portal |

### 8.5) Water & agriculture specifics

| Constraint | Design decision |
|-----------|----------------|
| 90% of water used in agriculture | Irrigation Optimizer agent (AGR-CEREAL-030) is highest-priority AI feature |
| Groundwater depletion | Observation DocType tracks borehole depth + flow rate; alert at threshold |
| Rain-fed farming in highland areas | Weather micro-forecast (Feature #100) triggers planting window predictions |
| Flood risk in coastal lowlands | Sentinel-2 flood index ingested as Observation (remote sensing ingestor) |
| Mycotoxin risk during humid season | Mycotoxin Risk Flag agent (AGR-CEREAL-043) critical for Hodeidah/Hudaydah + Taiz storage |

---

## 9) Technology Summary Table

| Layer | Component | Chosen stack | Best OSS alternative | Licence |
|-------|-----------|-------------|---------------------|---------|
| L1 | IoT sensors | ESP32 + DHT22/DS18B20 | EnviroNODE (proprietary) | MIT / CC |
| L1 | Power | Solar PV + LiFePO₄ | Grid (unreliable) | — |
| L1 | Connectivity | 4G SIM / Starlink | 3G / Thuraya satellite | — |
| L2 | Edge hardware | Raspberry Pi 4 | Orange Pi 5, Beelink EQ12 | — |
| L2 | Edge OS | Raspberry Pi OS Lite | Ubuntu Server 22.04 | GPL |
| L2 | Edge Frappe | frappe-bench (lite config) | Same | MIT |
| L2 | Edge LLM | Ollama + Llama 3.2 3B Q4 | llama.cpp, LM Studio | MIT/Llama |
| L2 | MQTT broker | Mosquitto | EMQX CE, VerneMQ | EPL / Apache |
| L3 | VPN | WireGuard | OpenVPN, Tailscale | GPL |
| L3 | Mesh Wi-Fi | OpenWRT + batman-adv | DD-WRT | GPL |
| L3 | SMS gateway | Africa's Talking | RapidPro, Gammu | Free tier / AGPL |
| L3 | Offline sync | PouchDB + Frappe queue | CouchDB replication | Apache |
| L4 | RDBMS | MariaDB 10.6 | PostgreSQL 16 | GPL |
| L4 | Cache | Redis 7 / Valkey | KeyDB | BSD |
| L4 | Object storage | MinIO | SeaweedFS, Ceph | AGPL |
| L4 | Vector store | Qdrant | Milvus, Weaviate, FAISS | Apache |
| L4 | Time-series | InfluxDB OSS | TimescaleDB | MIT / Apache |
| L4 | Backup | Restic + Rclone | Duplicati, BorgBackup | BSD / LGPL |
| L5 | Framework | Frappe 15+ | — (no swap) | MIT |
| L5 | ERP | ERPNext v16 | Odoo CE (heavier) | GPL |
| L5 | Agri module | Frappe Agriculture | Custom ERPNext module | MIT |
| L5 | Custom app | yam_agri_core | — | MIT (project) |
| L5 | Dashboards | Frappe Insights + Superset | Metabase | MIT / Apache |
| L6 | IoT adapter | Python MQTT subscriber | Node-RED, Telegraf | Apache |
| L6 | AI gateway | FastAPI + OpenJiuwen | LiteLLM proxy, LocalAI | MIT / Apache |
| L6 | Scale adapter | Python CSV + Frappe REST | Apache NiFi, Airbyte | — / Apache |
| L6 | SMS handler | Africa's Talking webhook | RapidPro webhooks | AGPL |
| L6 | Data quality | Great Expectations | Soda Core, dbt tests | Apache |
| L7 | AI SDK | **OpenJiuwen** (Python) | LangChain, LlamaIndex | Apache |
| L7 | LLM router | OpenJiuwen LLMComponent | LiteLLM | MIT |
| L7 | Workflow engine | OpenJiuwen Workflow | LangGraph, Prefect | MIT / Apache |
| L7 | RAG | Qdrant + LlamaIndex | FAISS + Haystack | Apache |
| L7 | Local inference | Ollama | vLLM, llama.cpp | MIT |
| L7 | Cloud LLM | OpenAI / Anthropic | Cohere, Together AI | Commercial |
| L7 | PII redaction | Presidio (Microsoft OSS) | spaCy NER custom | MIT |
| L8 | Model registry | MLflow | BentoML Registry | Apache |
| L8 | Model serving | Ollama + KServe | Seldon Core, BentoML | Apache |
| L8 | LLM red-team | Garak | NeMo Guardrails | Apache |
| L8 | Observability | Prometheus + Grafana | OpenTelemetry + Jaeger | Apache |
| L9 | Weather | Open-Meteo (free) | NOAA GFS, Copernicus ERA5 | CC-BY |
| L9 | Satellite | Sentinel Hub (ESA free) | EODAG + Sentinel-2 | Free / Apache |
| L9 | Maps | OpenStreetMap + Leaflet | Google Maps (cost) | ODbL / BSD |
| L9 | SMS | Africa's Talking | Twilio (expensive) | Commercial (low cost) |

---

## 10) Yemen Context: What to Build First vs What to Defer

### Build immediately (critical for Yemen operations)
1. **Offline-capable Field Hub** (Layer 2) — no internet = no value otherwise
2. **SMS data entry handler** (Layer 3/6) — U1 farmers cannot use smartphones
3. **Solar power documentation** in `infra/docker/.env.example` and deployment runbooks
4. **Arabic RTL Frappe configuration** — all UI must work in Arabic from day one
5. **Water Observation alerts** — groundwater depletion is the #1 agricultural risk
6. **7-day offline sync** — WireGuard + PouchDB must be configured before go-live

### Defer until connectivity improves
1. Real-time satellite imagery (requires >5 Mbps uplink)
2. Video-based crop vision features (bandwidth-intensive)
3. Cloud-only LLM features (use local Ollama until Starlink is stable)
4. Multi-region k3s cluster (single-node is enough for Yemen scale)

### Never do in Yemen context
1. **SaaS-only tools** — must have an on-premise / offline fallback
2. **Cloud-only backups** — encrypt + store locally first, replicate when online
3. **English-only interfaces** — non-starter for smallholder farmer adoption
4. **High-power servers** — solar budget limits available watts; favour ARM/low-power

---

## 11) How OpenJiuwen Integrates with This Stack

```
Developer (Python)
    │
    └── openjiuwen SDK
            │
        Workflow definition
            ├── Start component
            ├── LLMComponent (calls Ollama / cloud LLM)
            ├── Custom ToolComponents
            │       ├── FrappeAPITool  ──────▶ Frappe REST API
            │       ├── QdrantRAGTool  ──────▶ Qdrant vector store
            │       ├── WeatherTool    ──────▶ Open-Meteo API
            │       ├── RedactionTool  ──────▶ Presidio PII stripper
            │       └── LogHashTool    ──────▶ MLflow + MariaDB audit log
            └── End component (structured output → Frappe AI suggestion field)

Frappe Desk (U3/U4 user)
    └── AI Suggestion Panel (Frappe Form script)
            ├── Shows: suggestion text + confidence
            ├── Shows: source citations (linked DocTypes)
            ├── Shows: redaction preview
            └── Buttons: [Approve] [Reject] [Escalate] [Do manually]
```

**OpenJiuwen configuration for offline mode:**
```python
# Use local Ollama when internet unavailable
import os
os.environ["API_BASE"] = os.getenv("LLM_API_BASE", "http://localhost:11434/v1")
os.environ["MODEL_NAME"] = os.getenv("LLM_MODEL", "llama3.2:3b-instruct-q4_0")
# Falls back to cloud if local Ollama times out after 5 seconds
```

---

## 12) References & Further Reading

- [OpenJiuwen SDK on PyPI](https://pypi.org/project/openjiuwen/)
- [Frappe Framework docs](https://frappeframework.com/docs)
- [Frappe Agriculture app](https://github.com/frappe/agriculture)
- [ERPNext v16 documentation](https://docs.erpnext.com/)
- [Open-Meteo free weather API](https://open-meteo.com/)
- [EODAG — open satellite data access](https://eodag.readthedocs.io/)
- [Ollama — local LLM runner](https://ollama.com/)
- [Presidio — PII detection and redaction](https://microsoft.github.io/presidio/)
- [Restic — encrypted backup](https://restic.net/)
- [WireGuard — modern VPN](https://www.wireguard.com/)
- [Africa's Talking — MENA/Africa SMS API](https://africastalking.com/)
- [OpenWRT + batman-adv mesh](https://www.open-mesh.org/projects/batman-adv/wiki)
- [CAMeL-Tools — Arabic NLP OSS](https://github.com/CAMeL-Lab/camel_tools)
- [FAO GIEWS — food price data](https://www.fao.org/giews/)
- [CARPO Yemen climate-smart agriculture report (2025)](https://carpo-bonn.org/en/publications/carpo-reports/climate-smart-agriculture-in-yemen)
- `docs/TOUCHPOINT_APP_BLUEPRINT.md` — Build blueprint for all 9 touchpoint apps (Layer 10)
- `docs/PERSONA_JOURNEY_MAP.md` — Deep persona profiles and customer journey maps (Layer 11)
