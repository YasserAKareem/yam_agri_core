# C4 Level 2 — Container Diagram

> **C4 Level:** 2 — Container  
> **Version:** 1.1  
> **Date:** 2026-02-23  
> **Related:** [← System Context](01_SYSTEM_CONTEXT.md) | [Component: Core Platform →](03_COMPONENT_CORE_PLATFORM.md)

---

## Purpose

The Container diagram zooms into the **YAM Agri Platform** software system and shows its major technical building blocks — the **containers**. In C4 terms, a "container" is any separately deployable unit: a web application, API server, database, background worker, mobile app, or data store.

This diagram answers: **What are the major technical pieces and how do they talk to each other?**

---

## Diagram

```mermaid
C4Container
    title Container Diagram — YAM Agri Platform V1.1

    Person(farmer,    "U1 Farmer",           "Feature phone + 2G SMS")
    Person(webuser,   "U2–U6 Web Users",     "Browser or mobile PWA")
    Person(itadmin,   "U7 IT Admin",         "CLI + SSH/VPN")
    Person(auditor,   "U8 Auditor",          "Read-only browser")

    System_Ext(sms_gw,  "SMS Gateway\n(Africa's Talking)", "Inbound/outbound SMS")
    System_Ext(llm_api, "Cloud LLM API\n(OpenAI/Anthropic)", "AI completions")
    System_Ext(iot_hw,  "IoT Hardware\n(Sensors & Scales)", "MQTT readings, CSV files")

    System_Boundary(yam, "YAM Agri Platform") {

        %% ── Edge / Field ───────────────────────────────────────────────────────
        Container(field_hub, "Field Hub", "Raspberry Pi 4\nfrappe-bench (minimal) + Ollama",
            "Offline-capable edge node at each farm/silo.\nSyncs to central when connectivity available.\nRuns local LLM for offline AI suggestions.")

        %% ── Reverse Proxy ──────────────────────────────────────────────────────
        Container(nginx, "nginx", "nginx:alpine",
            "Reverse proxy and SSL termination.\nRoutes HTTP/HTTPS to Frappe backend.\nServes static assets.")

        %% ── Core Platform ──────────────────────────────────────────────────────
        Container(frappe, "Frappe + ERPNext + yam_agri_core\n(Backend)", "Python 3.11 / Gunicorn\nFrappe Framework v16\nERPNext v16 + Frappe Agriculture\nyam_agri_core custom app",
            "Core business platform.\nExposes Frappe REST/RPC API.\nEnforces RBAC and site isolation.\nManages all DocTypes and workflows.\nRuns on gunicorn (2 workers, 4 threads).")

        Container(worker_short, "Background Worker\n(Short Queue)", "Python / RQ (Redis Queue)",
            "Processes short background jobs:\nnotifications, cache invalidation,\nAPI callbacks.")

        Container(worker_long, "Background Worker\n(Long Queue)", "Python / RQ (Redis Queue)",
            "Processes long-running jobs:\nCSV scale ticket imports,\nevidence pack generation,\nscheduled certificate expiry checks.")

        Container(scheduler, "Scheduler", "Python / Frappe bench schedule",
            "Runs scheduled jobs on cron:\ndaily certificate expiry check,\nweekly backup trigger,\nhourly sensor threshold check.")

        Container(websocket, "WebSocket Server", "Node.js\nfrappe/socketio.js",
            "Provides real-time push notifications\nto Frappe Desk UI via WebSockets.\nUsed for alert pop-ups, live lot status.")

        %% ── Databases & Storage ────────────────────────────────────────────────
        ContainerDb(mariadb, "MariaDB 10.6", "MariaDB 10.6\nInnoDB storage engine",
            "Primary relational database.\nHolds all Frappe DocType tables\n(Site, Lot, QCTest, Certificate,\nObservation, etc.).\nInnoDB crash-recovery for power cuts.")

        ContainerDb(redis_cache, "Redis Cache", "Redis 6.2-alpine",
            "Frappe session cache, page cache,\nDocType metadata cache.")

        ContainerDb(redis_queue, "Redis Queue", "Redis 6.2-alpine",
            "RQ (Redis Queue) job broker.\nShort and long background job queues.")

        ContainerDb(redis_ws, "Redis WebSocket", "Redis 6.2-alpine",
            "Pub/sub bus for WebSocket\nreal-time event delivery.")

        ContainerDb(minio, "MinIO / Object Storage", "MinIO (self-hosted S3-compatible)",
            "Stores binary files:\ncertificate PDFs, QC test attachments,\nevidence pack ZIPs, photos.\nS3-compatible API.")

        ContainerDb(qdrant, "Qdrant Vector Store", "Qdrant OSS",
            "Vector embeddings for AI RAG.\nStores embedded FAO GAP docs,\nHACCP procedures, CAPA knowledge base\nfor retrieval-augmented AI suggestions.")

        %% ── AI Layer ───────────────────────────────────────────────────────────
        Container(ai_gateway, "AI Gateway", "Python / FastAPI",
            "Mandatory redaction + routing layer.\nRedacts PII, pricing, customer IDs\nbefore any external LLM call.\nLogs all AI interaction hashes.\nRoutes to local Ollama or cloud LLM.")

        Container(ollama, "Local LLM (Ollama)", "Ollama + Llama 3.2 (3B Q4)",
            "Local, offline LLM inference.\nQ4-quantised model fits in 4 GB RAM.\nUsed when internet is unavailable\nor for low-latency suggestions.")

        %% ── Service Adapters ───────────────────────────────────────────────────
        Container(iot_gw, "IoT Gateway", "Python / Mosquitto MQTT subscriber",
            "Subscribes to MQTT sensor topics.\nValidates readings against thresholds.\nCreates Observation DocType records\nvia Frappe REST API.\nSets quality_flag = Quarantine\nfor out-of-range readings.")

        Container(scale_conn, "Scale Connector", "Python",
            "Parses scale ticket CSV files.\nMaps tickets to Lot records.\nUpdates Lot quantities.\nCreates Nonconformance on mismatch.")

        Container(sms_handler, "SMS Handler\n(V1.2)", "Python / FastAPI webhook",
            "[Planned V1.2]\nReceives inbound SMS from Africa's Talking.\nParses Arabic/English lot commands.\nCreates Lot/ScaleTicket records\nvia Frappe REST API.")
    }

    %% ── Relationships ──────────────────────────────────────────────────────────
    Rel(farmer,    sms_gw,      "Sends lot commands,\nreceives alerts", "2G SMS")
    Rel(sms_gw,    sms_handler, "POST inbound SMS webhook", "HTTPS")
    Rel(sms_handler, frappe,    "Create Lot / ScaleTicket", "Frappe REST API (HTTPS)")

    Rel(webuser,   nginx,       "Opens Frappe Desk\nor mobile PWA", "HTTPS")
    Rel(auditor,   nginx,       "Views evidence packs\nread-only portal", "HTTPS")
    Rel(itadmin,   frappe,      "Runs bench commands,\nmanages users", "CLI (Docker exec)")

    Rel(nginx,     frappe,      "Proxies HTTP requests", "HTTP :8000")
    Rel(nginx,     websocket,   "Proxies WebSocket", "WS :9000")

    Rel(frappe,    mariadb,     "Reads/writes all DocType data", "SQL :3306")
    Rel(frappe,    redis_cache, "Reads/writes session\nand page cache", "Redis protocol :6379")
    Rel(frappe,    redis_queue, "Enqueues background jobs", "Redis protocol :6380")
    Rel(frappe,    minio,       "Stores and retrieves\nfile attachments", "S3 API (HTTPS)")
    Rel(frappe,    ai_gateway,  "Requests AI suggestions\n(compliance, CAPA, evidence)", "HTTP REST :8001")

    Rel(websocket, redis_cache, "Subscribes to cache events", "Redis protocol :6379")
    Rel(websocket, redis_queue, "Subscribes to queue events", "Redis protocol :6380")
    Rel(websocket, redis_ws,    "Pub/sub for real-time events", "Redis protocol :6381")

    Rel(worker_short, redis_queue, "Polls short job queue", "Redis protocol :6380")
    Rel(worker_short, mariadb,     "Reads/writes job results", "SQL :3306")
    Rel(worker_long,  redis_queue, "Polls long job queue", "Redis protocol :6380")
    Rel(worker_long,  mariadb,     "Reads/writes job results", "SQL :3306")
    Rel(scheduler,    frappe,      "Triggers scheduled Frappe jobs", "Internal bench call")

    Rel(ai_gateway, ollama,   "Routes to local LLM\nwhen offline/preferred", "HTTP REST :11434")
    Rel(ai_gateway, llm_api,  "Routes to cloud LLM\nwhen online (redacted)", "HTTPS REST")
    Rel(ai_gateway, qdrant,   "Vector retrieval for RAG\n(FAO GAP, HACCP docs)", "gRPC :6333")

    Rel(iot_hw,    iot_gw,    "Publishes sensor readings", "MQTT over TLS :8883")
    Rel(iot_gw,    frappe,    "Creates Observation records", "Frappe REST API (HTTPS)")

    Rel(scale_conn, frappe,   "Creates/updates ScaleTicket\nand Lot records", "Frappe REST API (HTTPS)")

    Rel(field_hub,  frappe,   "Syncs DocType records\nwhen connectivity available", "Frappe REST API (HTTPS)\noffline queue when down")

    UpdateLayoutConfig($c4ShapeInRow="4", $c4BoundaryInRow="1")
```

---

## ASCII Fallback — Container Overview

```
╔══════════════════════════════════════════════════════════════════════════════════════════╗
║                            YAM AGRI PLATFORM — CONTAINERS                               ║
╠══════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                          ║
║  EDGE (FIELD)              REVERSE PROXY        CORE PLATFORM                            ║
║  ─────────────             ────────────         ─────────────                            ║
║  [Field Hub              ] [nginx              ] [Frappe + ERPNext   ]                   ║
║   Raspberry Pi 4            Alpine               + yam_agri_core      [WebSocket Server] ║
║   frappe-bench (minimal)    SSL termination       Python / Gunicorn    Node.js            ║
║   Ollama Q4 LLM             Routes HTTP/WS        REST/RPC API         Frappe socketio.js ║
║                                                                                          ║
║                                                  [Background Worker ] [Background Worker] ║
║                                                   Short Queue          Long Queue         ║
║                                                   Python / RQ          Python / RQ        ║
║                                                                                          ║
║                                                  [Scheduler         ]                    ║
║                                                   bench schedule                         ║
║                                                   Cron-based jobs                        ║
║                                                                                          ║
╠═══════════════════════╦═══════════════════════╦══════════════════════════════════════════╣
║  DATABASES & STORAGE  ║  AI LAYER             ║  SERVICE ADAPTERS                        ║
║  ─────────────────    ║  ────────────         ║  ─────────────────                       ║
║  [MariaDB 10.6      ] ║  [AI Gateway       ]  ║  [IoT Gateway        ]                   ║
║   Primary DB            ║   FastAPI              ║   Python / MQTT sub                   ║
║   All DocType tables    ║   PII redaction         ║   MQTT → Observation                  ║
║                         ║   PII routing + log     ║                                       ║
║  [Redis Cache       ] ║  [Ollama (Local LLM)]  ║  [Scale Connector    ]                  ║
║   Session/page cache    ║   Llama 3.2 Q4          ║   Python CSV parser                  ║
║                         ║   Offline inference      ║   CSV → ScaleTicket                  ║
║  [Redis Queue       ]  ║                          ║                                       ║
║   RQ job broker         ║  [Qdrant Vector DB  ]  ║  [SMS Handler (V1.2) ]                 ║
║                         ║   RAG embeddings         ║   FastAPI webhook                    ║
║  [Redis WebSocket   ]  ║   FAO GAP / HACCP        ║   SMS → Lot/Ticket                    ║
║   Pub/sub events         ║   knowledge base         ║   [PLANNED V1.2]                    ║
║                          ║                          ║                                      ║
║  [MinIO / S3        ]  ║                          ║                                       ║
║   Files: PDFs, photos   ║                          ║                                       ║
║   EvidencePack ZIPs     ║                          ║                                       ║
╚═══════════════════════╩═══════════════════════╩══════════════════════════════════════════╝
```

---

## Container Inventory

| Container | Technology | Port(s) | Responsibility |
|-----------|-----------|---------|---------------|
| **nginx** | nginx:alpine | :80, :443 → :8080 | Reverse proxy, SSL termination, static assets |
| **Frappe Backend** | Python 3.11, Gunicorn, Frappe v16, ERPNext v16 | :8000 | Core business logic, REST/RPC API, RBAC, DocType engine |
| **Background Worker (Short)** | Python, RQ | — | Short background jobs (notifications, cache) |
| **Background Worker (Long)** | Python, RQ | — | Long jobs (CSV import, evidence pack generation) |
| **Scheduler** | Python, bench schedule | — | Cron-triggered Frappe scheduled jobs |
| **WebSocket Server** | Node.js, socketio.js | :9000 | Real-time push notifications to Frappe Desk |
| **MariaDB 10.6** | mariadb:10.6 | :3306 | Primary relational data store |
| **Redis Cache** | redis:6.2-alpine | :6379 | Session and page cache |
| **Redis Queue** | redis:6.2-alpine | :6380 | RQ job broker |
| **Redis WebSocket** | redis:6.2-alpine | :6381 | WebSocket pub/sub bus |
| **MinIO** | MinIO OSS | :9000 (API), :9001 (console) | Binary file storage (S3-compatible) |
| **Qdrant** | Qdrant OSS | :6333 (gRPC), :6334 (HTTP) | Vector store for AI RAG |
| **AI Gateway** | Python, FastAPI | :8001 | PII redaction, LLM routing, AI interaction logging |
| **Ollama (Local LLM)** | Ollama | :11434 | Local offline LLM inference (Llama 3.2 3B Q4) |
| **IoT Gateway** | Python, Mosquitto subscriber | — | MQTT sensor ingestion → Observation records |
| **Scale Connector** | Python | — | CSV scale ticket parsing → ScaleTicket records |
| **SMS Handler** | Python, FastAPI | :8002 | [V1.2] Inbound SMS parsing → Lot/ScaleTicket records |
| **Field Hub** | Raspberry Pi 4, frappe-bench (minimal), Ollama | — | Offline edge node; syncs to central when online |

---

## Communication Protocols Summary

| From | To | Protocol | Notes |
|------|----|---------|-------|
| Browser / PWA | nginx | HTTPS | TLS-terminated at nginx |
| nginx | Frappe Backend | HTTP | Internal Docker network |
| nginx | WebSocket Server | WS | Internal Docker network |
| Frappe Backend | MariaDB | MySQL protocol | :3306; Docker network |
| Frappe Backend | Redis Cache/Queue | Redis protocol | :6379–:6381 |
| Frappe Backend | MinIO | S3 API (HTTPS) | Internal or external |
| Frappe Backend | AI Gateway | HTTP REST | :8001; internal service |
| AI Gateway | Ollama | HTTP REST | :11434; internal |
| AI Gateway | Cloud LLM | HTTPS REST | External; PII redacted |
| AI Gateway | Qdrant | gRPC | :6333; internal |
| IoT Hardware | IoT Gateway | MQTT over TLS | :8883 |
| IoT Gateway | Frappe Backend | Frappe REST API | HTTPS |
| Scale Connector | Frappe Backend | Frappe REST API | HTTPS or internal |
| SMS Gateway | SMS Handler | HTTPS webhook | POST callback |
| SMS Handler | Frappe Backend | Frappe REST API | Internal |
| Field Hub | Frappe Backend | Frappe REST API | HTTPS over 4G/satellite |

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial container diagram — V1.1 |
