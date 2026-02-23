# C4 System Landscape Diagram

> **C4 Type:** System Landscape  
> **Scope:** All software systems operated by or integrated with YAM Agri Co.  
> **Version:** 1.1  
> **Date:** 2026-02-23  
> **Related:** [← Deployment: Staging](09_DEPLOYMENT_STAGING.md) | [Proposed Gaps →](11_PROPOSED_GAPS.md)

---

## Purpose

The System Landscape diagram shows **all software systems** in scope for the YAM Agri business — both the systems that YAM Agri owns/operates and the external systems it depends on. This is a zoom-out view that gives the complete picture beyond the YAM Agri Platform itself.

It answers: **What are all the software systems in play, and how do they relate?**

---

## Diagram

```mermaid
C4Context
    title System Landscape — YAM Agri Co. (V1.1)

    %% ─── YAM Agri Personnel ──────────────────────────────────────────────────
    Person(farmer,    "U1 · Smallholder Farmer",   "Feature phone + 2G SMS")
    Person(field_ops, "U2–U4 · Field Ops",         "Farm Supervisor, QA Inspector,\nSilo Operator")
    Person(office,    "U5–U6 · Office",            "Logistics Coordinator,\nAgri-Business Owner")
    Person(itadmin,   "U7 · IT Admin",             "System management, DevOps")
    Person(auditor,   "U8 · External Auditor",     "Donor or certification auditor")

    %% ─── Internal Systems (YAM Agri owns) ───────────────────────────────────
    Enterprise_Boundary(yam_boundary, "YAM Agri Co. Systems") {

        System(yam_core, "YAM Agri Platform",
            "Core quality and traceability system.\nFrappe + ERPNext + yam_agri_core.\nManages: lots, QC, certificates, sensors,\nevidence packs, CAPA, scale tickets.")

        System(field_hub, "Field Hub Network",
            "Raspberry Pi 4 edge nodes\nat each farm and silo site.\nOffline Frappe instance + local LLM.\nSyncs to central platform.")

        System(ai_gateway, "AI Gateway",
            "PII redaction + LLM routing layer.\nFastAPI microservice.\nLogs all AI interactions.\nAssistive only — no autonomous actions.")

        System(ollama_sys, "Local LLM (Ollama)",
            "Offline AI inference.\nLlama 3.2 3B Q4.\nRuns on Field Hub and/or central server.")

        System(iot_gw_sys, "IoT Gateway",
            "MQTT subscriber + sensor validation.\nCreates Observation records.\nTriggers alerts for out-of-range readings.")

        System(scale_sys, "Scale Connector",
            "CSV importer for weighbridge data.\nCreates ScaleTickets.\nDetects weight mismatches → CAPA.")

        System(minio_sys, "MinIO Object Storage",
            "Self-hosted S3-compatible storage.\nStores: certificate PDFs, photos,\nevidence pack ZIPs, QC attachments.")

        System(qdrant_sys, "Qdrant Vector Store",
            "Vector embeddings for AI RAG.\nFAO GAP, HACCP, CAPA knowledge base.")

        System(monitoring, "Monitoring Stack\n(Planned V1.2)",
            "[Planned]\nPrometheus + Grafana.\nMonitors: container health, DB query time,\nRedis queue depth, AI latency, costs.")
    }

    %% ─── External Systems ────────────────────────────────────────────────────
    System_Ext(sms_gw,   "SMS Gateway\n(Africa's Talking)",   "Inbound/outbound SMS for U1 farmers.\nCheapest MENA SMS provider.")
    System_Ext(llm_cloud, "Cloud LLM APIs\n(OpenAI / Anthropic)", "GPT-4o-mini, Claude 3 Haiku.\nFallback when local LLM insufficient.")
    System_Ext(weather,  "Open-Meteo",                        "Free weather data API.\nRainfall, temperature, humidity forecasts.")
    System_Ext(ndvi,     "Sentinel Hub / ESA",                "Free-tier satellite imagery.\nNDVI, flood risk derived indices.")
    System_Ext(fao_db,   "FAO / Codex / GIEWS",              "FAO GAP standards, Codex MRL tables,\nGIEWS commodity price signals.")
    System_Ext(iot_hw,   "IoT Hardware",                      "Sensors (temp, humidity, CO₂, moisture),\nscales, cameras — MQTT or CSV output.")
    System_Ext(github,   "GitHub",                            "Source code repository, CI/CD\n(GitHub Actions), issue tracking.")
    System_Ext(docker_hub,"Docker Hub",                       "Base Docker images:\nfrappe/erpnext:v16.5.0, mariadb:10.6.")
    System_Ext(wireguard, "WireGuard VPN",                    "Secure tunnel for staging/production\nserver access by developers.")
    System_Ext(iati,     "IATI / Donor Portal",               "International Aid Transparency Initiative.\nDonor reporting export (read-only).")

    %% ─── Relationships: YAM Systems ─────────────────────────────────────────
    Rel(farmer,    sms_gw,      "Sends SMS lot commands", "2G SMS")
    Rel(sms_gw,    yam_core,    "Delivers inbound SMS", "HTTPS webhook")
    Rel(field_ops, yam_core,    "Frappe Desk + mobile PWA", "HTTPS")
    Rel(office,    yam_core,    "Owner portal + logistics app", "HTTPS")
    Rel(itadmin,   yam_core,    "Frappe Desk + CLI", "SSH via WireGuard")
    Rel(auditor,   yam_core,    "Read-only evidence portal", "HTTPS")

    Rel(yam_core,  field_hub,   "Syncs records to edge nodes\nwhen connectivity available", "Frappe REST + offline queue")
    Rel(yam_core,  ai_gateway,  "Requests AI suggestions", "HTTP REST :8001")
    Rel(yam_core,  scale_sys,   "Receives scale ticket imports", "Frappe REST API")
    Rel(yam_core,  minio_sys,   "Stores/retrieves files", "S3 API")

    Rel(ai_gateway, ollama_sys,  "Routes AI tasks (offline-first)", "HTTP :11434")
    Rel(ai_gateway, llm_cloud,   "Routes AI tasks (cloud fallback,\nPII redacted)", "HTTPS")
    Rel(ai_gateway, qdrant_sys,  "RAG vector retrieval", "gRPC :6333")

    Rel(iot_hw,    iot_gw_sys,  "Streams sensor readings", "MQTT :8883")
    Rel(iot_gw_sys, yam_core,   "Creates Observation records", "Frappe REST")

    Rel(yam_core,  weather,     "Fetches weather data", "HTTPS REST")
    Rel(yam_core,  ndvi,        "Fetches NDVI/flood indices", "HTTPS REST")
    Rel(yam_core,  fao_db,      "Retrieves standards + prices", "HTTPS REST / CSV")
    Rel(yam_core,  iati,        "Exports donor compliance data", "IATI XML")

    Rel(itadmin,   github,      "Manages repo, reviews PRs, monitors CI", "HTTPS")
    Rel(itadmin,   wireguard,   "Connects to staging/production servers", "WireGuard UDP")
    Rel(github,    yam_core,    "CI/CD deploys updates", "GitHub Actions")
    Rel(docker_hub, yam_core,   "Provides base container images", "Docker pull")

    UpdateLayoutConfig($c4ShapeInRow="4", $c4BoundaryInRow="1")
```

---

## ASCII — System Landscape Overview

```
═══════════════════════════════════════════════════════════════════════════
                       YAM AGRI CO. — SYSTEM LANDSCAPE
═══════════════════════════════════════════════════════════════════════════

  USERS                    INTERNAL SYSTEMS                EXTERNAL SYSTEMS
  ─────                    ────────────────                ────────────────

  [U1 Farmer]──SMS────────▶[SMS → YAM Agri Platform]◀────[SMS Gateway
                                                            Africa's Talking]

  [U2-U4 Field Ops]─HTTPS─▶[     YAM AGRI PLATFORM    ]───[Weather API
                            │                         │     Open-Meteo]
  [U5-U6 Office]────HTTPS──▶│  Frappe + ERPNext v16   │
                            │  + yam_agri_core         │───[Satellite NDVI
  [U7 IT Admin]─────SSH VPN▶│                         │     Sentinel Hub]
                            │  Site isolation RBAC     │
  [U8 Auditor]──────HTTPS──▶│  Lot traceability        │───[FAO / Codex
                            │  QA/QC controls          │     GIEWS]
                            │  AI assistance           │
                            └──────────┬───────────────┘───[IoT Hardware]
                                       │                    MQTT → sensors
                            ┌──────────▼───────────────┐
                            │ Service Layer             │
                            │ [IoT Gateway]             │
                            │ [Scale Connector]         │
                            │ [AI Gateway]◄─────────────┼──[Cloud LLM API
                            │   ├──[Ollama Local LLM]   │   OpenAI/Anthropic]
                            │   └──[Qdrant RAG]         │
                            │ [MinIO Object Storage]    │
                            │ [Field Hub Network]        │
                            │ [Monitoring] (V1.2+)      │
                            └───────────────────────────┘
                                                        ───[GitHub CI/CD]
                                                        ───[Docker Hub]
                                                        ───[WireGuard VPN]
                                                        ───[IATI/Donors]
```

---

## System Classification

### YAM Agri Owned / Self-Hosted Systems

| System | Status | Deploy target |
|--------|--------|--------------|
| YAM Agri Platform (Frappe/ERPNext) | ✅ V1.1 | Docker Compose / k3s |
| Field Hub Network (Raspberry Pi) | ✅ V1.1 (edge) | Physical hardware per site |
| AI Gateway (FastAPI) | ✅ V1.1 (basic) | Docker service / k3s pod |
| Local LLM / Ollama | ✅ V1.1 | Docker service / k3s pod |
| IoT Gateway (MQTT subscriber) | ✅ V1.1 (basic) | Docker service / k3s pod |
| Scale Connector | ✅ V1.1 | Docker service / k3s pod |
| MinIO Object Storage | 🔲 V1.2 planned | k3s pod / standalone |
| Qdrant Vector Store | 🔲 V1.2 planned | k3s pod / standalone |
| Monitoring Stack (Prometheus/Grafana) | 🔲 V1.2 planned | k3s pod |
| SMS Handler | 🔲 V1.2 planned | Docker service / k3s pod |

### External Systems Integrated

| External system | Integration type | V1.1 status |
|----------------|-----------------|------------|
| Africa's Talking (SMS) | HTTPS webhook + REST API | 🔲 V1.2 |
| OpenAI / Anthropic (Cloud LLM) | HTTPS REST (via AI Gateway) | ✅ V1.1 basic |
| Open-Meteo (Weather) | HTTPS REST | 🔲 V1.2 |
| Sentinel Hub / ESA (NDVI) | HTTPS REST | 🔲 V1.2 |
| FAO / Codex / GIEWS | HTTPS REST + bulk CSV | 🔲 V1.2 |
| IoT Hardware (MQTT) | MQTT over TLS :8883 | ✅ V1.1 basic |
| GitHub (CI/CD) | GitHub Actions | ✅ V1.1 |
| Docker Hub | Docker pull | ✅ V1.1 |
| WireGuard VPN | UDP tunnel | ✅ V1.1 |
| IATI / Donor Portal | XML export | 🔲 V2.0 |

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial system landscape diagram — V1.1 |
