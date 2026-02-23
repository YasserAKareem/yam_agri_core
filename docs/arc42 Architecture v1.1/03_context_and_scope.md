# arc42 §3 — System Scope and Context

> **arc42 Section:** 3  
> **Version:** 1.1  
> **Status:** ⚠️ Draft  
> **Date:** 2026-02-23  
> **Related SDLC doc:** [02_REQUIREMENTS_SPECIFICATION.md §5](../Docs%20v1.1/02_REQUIREMENTS_SPECIFICATION.md) | [03_SYSTEM_ARCHITECTURE.md §5](../Docs%20v1.1/03_SYSTEM_ARCHITECTURE.md)  
> **Related C4 doc:** [`docs/C4 model Architecture v1.1/01_SYSTEM_CONTEXT.md`](../C4%20model%20Architecture%20v1.1/01_SYSTEM_CONTEXT.md)

---

## 3.1 Business Context

The YAM Agri Platform sits at the **centre of the cereal-crop supply chain** for YAM Agri's Yemen operations. It connects:

- **Upstream inputs**: farm harvest data, IoT sensor readings, scale weight measurements
- **Internal operations**: quality control, storage management, lot traceability, CAPA
- **Downstream outputs**: shipment dispatch, audit evidence packs, compliance certificates

### Business Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Business Context                                     │
│                                                                              │
│  ┌──────────────┐      SMS lot data        ┌──────────────────────────┐     │
│  │ Smallholder  │ ─────────────────────►   │                          │     │
│  │ Farmer (U1)  │                          │                          │     │
│  └──────────────┘                          │                          │     │
│                                            │   YAM Agri Platform      │     │
│  ┌──────────────┐      IoT MQTT readings   │   (Frappe + ERPNext      │     │
│  │  IoT Devices │ ─────────────────────►   │    + yam_agri_core)      │     │
│  │  (sensors,   │                          │                          │     │
│  │   scales)    │                          │  • Lot traceability      │     │
│  └──────────────┘                          │  • QA/QC evidence        │     │
│                                            │  • Season policy gating  │     │
│  ┌──────────────┐      Scale CSV files     │  • Sensor monitoring     │     │
│  │  Weighbridge │ ─────────────────────►   │  • CAPA management       │     │
│  │  / Scale     │                          │  • Evidence packs        │     │
│  └──────────────┘                          │  • AI assistance         │     │
│                                            │                          │     │
│  ┌──────────────┐   ◄─ Evidence packs      │                          │     │
│  │  External    │   ◄─ Audit reports        │                          │     │
│  │  Auditor /   │                          │                          │     │
│  │  Donor (U8)  │   compliance queries ─►  │                          │     │
│  └──────────────┘                          └──────────┬───────────────┘     │
│                                                       │                     │
│  ┌──────────────┐   ◄─ Compliance cert     AI suggestions (text only)       │
│  │  Customers   │                                     │                     │
│  └──────────────┘                                     ▼                     │
│                                            ┌──────────────────────────┐     │
│  ┌──────────────┐   read-only context ─►  │  AI Gateway + LLMs       │     │
│  │  Internal    │   ◄─ suggestion text     │  (local Ollama /         │     │
│  │  Users       │                          │   cloud GPT-4o/Claude)   │     │
│  │  U2/U3/U4/   │                          └──────────────────────────┘     │
│  │  U5/U6/U7    │                                                            │
│  └──────────────┘                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### External Actors and Interfaces

| Actor | Type | Interface | Direction | V1.1 status |
|-------|------|-----------|-----------|-------------|
| Smallholder Farmer (U1) | Human | SMS (Africa's Talking) | Inbound | 🔲 V1.2 |
| Farm Supervisor (U2) | Human | Frappe Desk / FieldPWA | Bidirectional | ✅ V1.1 (Desk) |
| QA Inspector (U3) | Human | Frappe Desk | Bidirectional | ✅ V1.1 |
| Silo Operator (U4) | Human | Frappe Desk / SiloDashboard | Bidirectional | ✅ V1.1 (Desk) |
| Logistics Coordinator (U5) | Human | Frappe Desk | Bidirectional | ✅ V1.1 |
| Owner (U6) | Human | Frappe Desk / OwnerPortal | Read-heavy | ✅ V1.1 (Desk) |
| IT Admin (U7) | Human | Frappe Desk + SSH/run.sh | Admin | ✅ V1.1 |
| External Auditor (U8) | Human | AuditorPortal (read-only) | Read-only | 🔲 V1.2 |
| IoT Devices / Sensors | Technical | MQTT (Mosquitto) | Inbound | ✅ V1.1 basic |
| Weighbridge / Scale | Technical | CSV file import | Inbound | ✅ V1.1 |
| AI Gateway / LLMs | Technical | Internal FastAPI REST | Outbound (suggestion only) | ✅ V1.1 basic |
| FAO / Donor portals | Technical | EvidencePack PDF/ZIP export | Outbound | ✅ V1.1 |
| Weather / NDVI APIs | Technical | EODAG / Sentinel-2 REST | Inbound | 🔲 V1.2 |

---

## 3.2 Technical Context

The technical context shows the **system boundaries and communication protocols** between the YAM Agri Platform and its neighbours.

### Technical Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Technical Context                                    │
│                                                                              │
│  ┌─────────────┐                                                             │
│  │  Browser    │  HTTP/WebSocket (Frappe Desk)                               │
│  │  (User)     │ ────────────────────────────► ┌─────────────────────────┐  │
│  └─────────────┘                               │                         │  │
│                                                │   YAM Agri Platform     │  │
│  ┌─────────────┐  JSON over MQTT               │                         │  │
│  │  IoT Device │ ────────────────────────────► │  nginx (:80/:443)       │  │
│  └─────────────┘                               │  Frappe web (:8000)     │  │
│                                                │  RQ workers             │  │
│  ┌─────────────┐  CSV file upload              │  Scheduler              │  │
│  │  Scale /    │ ────────────────────────────► │  socketio (:9000)       │  │
│  │  Weighbridge│                               │  MariaDB 10.6 (:3306)   │  │
│  └─────────────┘                               │  Redis queue (:6379)    │  │
│                                                │  Redis cache (:6380)    │  │
│  ┌─────────────┐  REST/JSON (internal)         │  AI Gateway (:8001)     │  │
│  │  AI Gateway │ ◄──────────────────────────── │                         │  │
│  │  (FastAPI)  │ ─────────────────────────────►│                         │  │
│  └──────┬──────┘  suggestion text              │                         │  │
│         │                                      └─────────────────────────┘  │
│  ┌──────▼──────┐  HTTPS / API                                               │
│  │  Ollama     │  (local, no internet needed)                               │
│  │  (local LLM)│                                                            │
│  └─────────────┘                                                            │
│                                                                              │
│  ┌─────────────┐  HTTPS / OpenAI/Anthropic API (redacted context only)      │
│  │  Cloud LLM  │ ◄───────────────────────────── AI Gateway                  │
│  │  (GPT-4o /  │                                                            │
│  │   Claude)   │                                                            │
│  └─────────────┘                                                            │
│                                                                              │
│  ┌─────────────┐  WireGuard VPN (admin access)                              │
│  │  Developer /│ ────────────────────────────► Frappe Platform              │
│  │  IT Admin   │                                                            │
│  └─────────────┘                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Communication Channel Details

| Channel | Protocol | Format | Auth | Direction |
|---------|----------|--------|------|-----------|
| User browser ↔ Frappe | HTTP/WebSocket | HTML / JSON | Session cookie + CSRF | Bidirectional |
| IoT Device → MQTT Broker | MQTT 3.1.1 | JSON | TLS client cert | Inbound only |
| MQTT Broker → IoT Gateway | MQTT subscribe | JSON | Same TLS session | Internal |
| Scale CSV → Frappe | HTTP multipart/POST | CSV | Frappe session | Inbound |
| Frappe → AI Gateway | HTTP/REST | JSON | Service bearer token | Outbound |
| AI Gateway → Ollama | HTTP/REST | JSON | Local only | Outbound |
| AI Gateway → Cloud LLM | HTTPS/REST | JSON | API key (env var) | Outbound (redacted) |
| DevOps → Staging | WireGuard VPN + SSH | — | WireGuard key + SSH key | Inbound admin |
| Frappe → MinIO | S3 HTTP API | Binary | Access key (env var) | Bidirectional |

---

## 3.3 External Interface Specifications

### 3.3.1 MQTT IoT Interface

- **Topic pattern:** `yam/{site_code}/{device_id}/observation`
- **Payload schema:**

```json
{
  "metric": "temperature",
  "value": 28.5,
  "unit": "C",
  "ts": "2026-02-23T10:00:00Z"
}
```

- The IoT Gateway subscribes, validates range, and creates an `Observation` record via Frappe REST API.

### 3.3.2 Scale Ticket CSV Interface

- **Method:** HTTP multipart POST to `/api/method/yam_agri_core.scale.import_csv`
- **Required columns:** `ticket_no`, `date`, `operator`, `gross_weight_kg`, `tare_weight_kg`, `net_weight_kg`, `lot`, `device`
- **Response:** JSON with row-level import results and error report

### 3.3.3 AI Gateway Interface

- **Base URL:** `http://ai-gateway:8001` (internal Docker network only)
- **POST /suggest** — request AI assistance

```json
Request:  { "lot": "LOT-2026-001", "task": "compliance_check" }
Response: { "suggestion": "...", "log_hash": "sha256:...", "model": "llama3.2:3b" }
```

- All PII, pricing, and customer IDs are redacted before the prompt leaves the gateway.

### 3.3.4 SMS Interface (V1.2 — Africa's Talking)

- **Webhook POST** to `{site}/api/method/yam_agri_core.sms.handle_inbound`
- SMS command grammar defined in [`docs/Docs v1.1/05_API_SPECIFICATION.md §6`](../Docs%20v1.1/05_API_SPECIFICATION.md)
- **Status:** 🔲 V1.2

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial section — V1.1 |
