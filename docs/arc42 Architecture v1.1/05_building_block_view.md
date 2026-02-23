# arc42 §5 — Building Block View

> **arc42 Section:** 5  
> **Version:** 1.1  
> **Status:** ⚠️ Draft  
> **Date:** 2026-02-23  
> **Related SDLC doc:** [03_SYSTEM_ARCHITECTURE.md](../Docs%20v1.1/03_SYSTEM_ARCHITECTURE.md) | [04_DATA_MODEL.md](../Docs%20v1.1/04_DATA_MODEL.md)  
> **Related C4 docs:** [`docs/C4 model Architecture v1.1/`](../C4%20model%20Architecture%20v1.1/)

---

The building block view shows the **static decomposition** of the system into components, modules, and their relationships.

---

## 5.1 Level 1 — Whitebox: YAM Agri Platform

At the top level, the system decomposes into five major blocks:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        YAM Agri Platform                                 │
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────┐    │
│  │  Core Business  │  │  Service        │  │  AI Assistance       │    │
│  │  Platform       │  │  Adapters       │  │  Layer               │    │
│  │  (Layer 5)      │  │  (Layer 6)      │  │  (Layer 7)           │    │
│  │                 │  │                 │  │                      │    │
│  │  Frappe +       │  │  Scale          │  │  AI Gateway          │    │
│  │  ERPNext +      │◄─│  Connector      │  │  (FastAPI)           │    │
│  │  yam_agri_core  │  │  IoT Gateway    │  │  Ollama/LLMs         │    │
│  │                 │  │  AI Gateway IF  │  │  AI Interaction Log  │    │
│  └────────┬────────┘  └────────┬────────┘  └──────────────────────┘    │
│           │                    │                                         │
│  ┌────────▼────────────────────▼────────────────────────────────────┐   │
│  │                  Data & Storage (Layer 4)                         │   │
│  │  MariaDB 10.6  · Redis 7  · MinIO/S3  · (Qdrant V1.2+)          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                  Field Hub / Edge (Layer 2)                       │   │
│  │  Raspberry Pi · Offline Frappe · Ollama · MQTT Broker · Redis    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Level 1 Block Descriptions

| Block | Responsibility | Technology |
|-------|---------------|-----------|
| **Core Business Platform** | All business DocTypes, workflows, rules, RBAC, REST API, UI | Frappe v16 + ERPNext v16 + yam_agri_core |
| **Service Adapters** | Translate external data (CSV, MQTT, SMS) into Frappe records | Python: CSV parser, MQTT subscriber, SMS handler |
| **AI Assistance Layer** | Route AI requests, redact PII, call LLMs, log interactions, return suggestions | FastAPI (AI Gateway) + Ollama + LLM APIs |
| **Data & Storage** | Persistent relational, cache, object, vector storage | MariaDB, Redis, MinIO, (Qdrant V1.2+) |
| **Field Hub / Edge** | Offline operation per site; sensor ingestion; local AI cache | Raspberry Pi 4 + minimal Frappe + Mosquitto + Ollama |

---

## 5.2 Level 2 — Whitebox: Core Business Platform (`yam_agri_core`)

The `yam_agri_core` Frappe app contains all custom business logic:

```
yam_agri_core/
├── hooks.py                    ← App hooks (permission_query_conditions, doc_events)
├── permissions.py              ← Site isolation: get_permission_query_conditions
├── doctypes/
│   ├── site/                   ← Site master
│   ├── storage_bin/            ← StorageBin master
│   ├── device/                 ← IoT device registry
│   ├── lot/                    ← Primary traceability unit
│   │   ├── lot.py              ← validate(), on_submit() — mass balance, season policy check
│   │   └── lot.js              ← Desk form script — trace view, AI suggest button
│   ├── transfer/               ← Split/merge/blend operations
│   │   └── transfer.py         ← validate() — quantity balance; on_submit() — update lots
│   ├── scale_ticket/           ← Weight measurements
│   │   └── scale_ticket.py     ← mismatch detection → Nonconformance auto-create
│   ├── qc_test/                ← Quality test results
│   ├── certificate/            ← Compliance certificates
│   │   └── certificate.py      ← expiry_check() — scheduled daily
│   ├── nonconformance/         ← CAPA records
│   ├── evidence_pack/          ← Audit evidence bundles
│   │   └── evidence_pack.py    ← generate() — aggregates records for period/site
│   ├── complaint/              ← Customer complaints
│   ├── observation/            ← Universal sensor data
│   │   └── observation.py      ← quality_flag logic; threshold alerts
│   └── season_policy/          ← Mandatory QC/cert rules
├── scale/
│   └── importer.py             ← CSV → ScaleTicket batch import
├── iot/
│   └── gateway.py              ← MQTT → Observation pipeline
├── ai/
│   └── gateway_client.py       ← Frappe-side AI Gateway call client
└── traceability/
    ├── backward.py             ← Trace-backward engine (recursive parent lot lookup)
    └── forward.py              ← Trace-forward engine (recursive child lot lookup)
```

### Key DocType Dependencies

```
Site ─────────────────────────────────────────────────────┐
  │                                                        │
  ├── StorageBin ── Device                                 │
  │                                                        │
  ├── Lot ─────────┬── QCTest ── Certificate               │
  │    │            ├── ScaleTicket                        │
  │    │            ├── Observation                        │
  │    │            ├── Nonconformance                     │
  │    │            └── EvidencePack                       │
  │    │                                                    │
  │    └── Transfer (source_lots / destination_lots)       │
  │                                                        │
  └── SeasonPolicy (crop + season → mandatory tests/certs) │
                                                           │
  All DocTypes have a mandatory `site` Link field ─────────┘
```

---

## 5.3 Level 2 — Whitebox: Service Adapters

### Scale Connector

```
CSV file (manual upload or scheduled)
    │
    ▼
scale/importer.py
    ├── Parse and validate rows
    ├── Match ticket_no to Lot (lot field)
    ├── Create ScaleTicket records (Frappe REST API)
    ├── Calculate net_weight; compare to Lot.declared_qty_kg
    └── If mismatch > tolerance: create Nonconformance (nc_type = "Weight Mismatch")
```

### IoT Gateway

```
MQTT broker (Mosquitto, port 1883)
    │  topic: yam/{site}/{device}/observation
    ▼
iot/gateway.py (MQTT subscriber — Python paho-mqtt)
    ├── Parse JSON payload
    ├── Look up Device record by device_id + site
    ├── Validate: value within threshold_min / threshold_max
    ├── Set quality_flag: Valid / Warning / Quarantine
    ├── Create Observation record via Frappe REST API
    └── If threshold exceeded: POST Frappe notification to assigned roles
```

### AI Gateway (FastAPI service)

```
POST /suggest  ←── Frappe (yam_agri_core/ai/gateway_client.py)
    │
    ├── Authenticate caller (service bearer token)
    ├── Validate task type (whitelist: compliance_check, capa_draft, evidence_narrative)
    ├── REDACT: PII, pricing, customer IDs (regex + entity rules)
    ├── Build minimal prompt from redacted context
    ├── Route to LLM:
    │     ├── Ollama (local): POST http://ollama:11434/api/generate
    │     └── Cloud (if configured): OpenAI / Anthropic HTTPS API
    ├── Log: prompt_hash + response_hash + user + record + model + tokens
    └── Return: { "suggestion": "...", "log_hash": "..." }
```

---

## 5.4 Level 1 — 11-Layer Stack Reference

The full 11-layer architecture (defined in `docs/SMART_FARM_ARCHITECTURE.md`) is summarised here for reference:

| Layer | Name | V1.1 scope |
|-------|------|-----------|
| 11 | User Personas & Journey Maps | 9 personas defined; Frappe Desk is primary interface |
| 10 | Touchpoints (9 apps) | Frappe Desk in V1.1; dedicated touchpoints in V1.2+ |
| 9 | External Integrations | Weather/NDVI deferred to V1.2+ |
| 8 | AI Marketplace | MLflow/Prompt store deferred to V1.2+ |
| 7 | AI Agent & Intelligence | AI Gateway (basic); Ollama; compliance_check, capa_draft, evidence_narrative |
| 6 | Service Adapters | Scale Connector ✅; IoT Gateway ✅ basic; SMS Handler 🔲 V1.2 |
| 5 | Core Business Platform | **Primary V1.1 build target** — Frappe + ERPNext + yam_agri_core |
| 4 | Data & Storage | MariaDB ✅; Redis ✅; MinIO ✅; Qdrant 🔲 V1.2+; InfluxDB 🔲 V1.2+ |
| 3 | Connectivity & Sync | Site LAN ✅; WireGuard VPN ✅; PouchDB sync 🔲 V1.2 |
| 2 | Field Hub (Edge) | Architecture designed; deployment deferred post-dev |
| 1 | Physical / Farm Edge | IoT sensors and scales connected via MQTT / CSV |

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial section — V1.1 |
