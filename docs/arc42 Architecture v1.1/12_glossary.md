# arc42 §12 — Glossary

> **arc42 Section:** 12  
> **Version:** 1.1  
> **Status:** ⚠️ Draft  
> **Date:** 2026-02-23  
> **Audience:** All team members, new developers, external auditors

---

This glossary defines domain-specific and architecture-specific terms used throughout the YAM Agri Platform documentation. Terms are alphabetically ordered within categories.

---

## 12.1 Domain Terms (Agriculture / Supply Chain)

| Term | Definition |
|------|-----------|
| **Aflatoxin B1** | A mycotoxin (mould byproduct) that is a critical food safety hazard in cereal grains; limits set by Codex Alimentarius and EU regulations (≤ 2 ppb in cereals for EU export) |
| **Blend** | A Transfer operation that combines multiple source Lots with different characteristics (e.g., crop varieties) into a single destination Lot, recording mix ratios |
| **CAPA** | Corrective and Preventive Action — a structured process for identifying the root cause of a nonconformance and implementing corrective measures to prevent recurrence |
| **Certificate** | A compliance certificate with an expiry date, issued by an accredited body (e.g., FAO GAP, HACCP, phytosanitary, export certificate) and attached to a Lot or Site |
| **CCP** | Critical Control Point — a step in the food production/storage process where control measures must be applied to prevent or reduce food safety hazards to acceptable levels (HACCP term) |
| **Codex Alimentarius** | International food safety standards published by the FAO/WHO Codex Alimentarius Commission; sets maximum limits for mycotoxins, pesticide residues, and other hazards |
| **Complaint** | A customer complaint record linked to a Lot and CAPA workflow |
| **Device** | An IoT sensor, scale, or camera registered to a Site and optionally a StorageBin |
| **EvidencePack** | An audit evidence bundle that groups all QC tests, certificates, scale tickets, observations, and nonconformances for a given Site/period/Lot for auditors or customers |
| **FAO GAP** | Good Agricultural Practices as defined by the Food and Agriculture Organization of the United Nations, adapted for the Middle East context |
| **HACCP** | Hazard Analysis and Critical Control Points — a systematic preventive food safety approach that identifies physical, chemical, and biological hazards in production processes |
| **Harvest Lot** | A Lot of type "Harvest" representing grain collected from the field at a specific GPS location and date |
| **ISO 22000** | International standard for Food Safety Management Systems (FSMS), integrating HACCP principles with management system requirements |
| **Lot** | The primary traceability unit in YAM Agri — a batch of cereal grain tracked through the supply chain from harvest to shipment. Can be of type: Harvest, Storage, Shipment, or Processing |
| **Merge** | A Transfer operation that combines multiple source Lots of the same type into a single destination Lot |
| **Mycotoxin** | Toxic compounds produced by certain moulds that grow on grain; a primary food safety concern for cereal storage |
| **Nonconformance** | A record of a quality or compliance issue; initiates a CAPA workflow |
| **Observation** | A universal record of a sensor or derived signal reading (e.g., bin temperature, humidity, NDVI, rainfall) with a quality flag |
| **Phytosanitary Certificate** | An official document issued by the Ministry of Agriculture certifying that a plant product has been inspected and is free from pests and diseases; required for export |
| **quality_flag** | A field on Observation records indicating data quality: `Valid` (in range), `Warning` (near threshold), or `Quarantine` (out of range; not used for automated decisions) |
| **QCTest** | A quality control test result attached to a Lot, recording test type, laboratory, result values (moisture %, protein %, mycotoxin ppb, etc.), and pass/fail status |
| **Scale Ticket** | A weight measurement record from a physical or digital weighbridge/scale, imported via CSV or entered manually |
| **Season Policy** | A configurable rule specifying which QC tests and certificates are mandatory for a given crop and season before a Lot can be shipped |
| **Shipment Lot** | A Lot of type "Shipment" created from a Storage Lot via a Transfer (Split), representing grain dispatched to a customer or another site |
| **Site** | A physical location operated by YAM Agri: Farm, Silo, Store, or Office |
| **Site Isolation** | The guarantee that a user assigned to Site A cannot read, write, or access any records belonging to Site B |
| **Split** | A Transfer operation that divides a single source Lot into multiple destination Lots |
| **Storage Lot** | A Lot of type "Storage" representing grain held in a StorageBin |
| **StorageBin** | A physical bin, compartment, or storage unit within a Site (silo cell, flat store section, refrigerator) |
| **Transfer** | A record of a Split, Merge, or Blend operation between Lots; enforces mass balance |

---

## 12.2 Architecture / Technology Terms

| Term | Definition |
|------|-----------|
| **ADR** | Architecture Decision Record — a concise document capturing a significant architectural decision, its context, options considered, and rationale |
| **AI Gateway** | A FastAPI microservice that is the mandatory intermediary between Frappe and all LLMs; enforces redaction, whitelisting, logging, and returns suggestion text only |
| **arc42** | A pragmatic template for software architecture documentation (https://arc42.org); provides 12 standardised sections covering goals, constraints, structure, runtime, deployment, decisions, quality, and risks |
| **bench** | The Frappe command-line tool for managing Frappe installations: `bench new-site`, `bench migrate`, `bench update`, `bench start`, etc. |
| **C4 model** | A hierarchical diagramming method (Context → Container → Component → Code) for software architecture; the C4 model diagrams for this project are in `docs/C4 model Architecture v1.1/` |
| **Custom app** | A Frappe app that extends the base platform with domain-specific DocTypes and business logic; `yam_agri_core` is YAM Agri's custom app |
| **Docker Compose** | A tool for defining and running multi-container Docker applications; used for the YAM Agri development environment |
| **DocType** | Frappe's fundamental building block — a managed database table with built-in RBAC, REST API, workflow, audit trail, and form UI generation |
| **docstatus** | Frappe's document lifecycle field: 0 = Saved/Draft, 1 = Submitted, 2 = Cancelled |
| **ERPNext** | An open-source Enterprise Resource Planning application built on Frappe Framework; provides finance, inventory, HR, CRM, and manufacturing modules |
| **FastAPI** | A modern Python web framework for building APIs; used to implement the AI Gateway service |
| **Field Hub** | A per-site edge computing node (Raspberry Pi 4) running a minimal offline Frappe instance for offline-first field operations |
| **Frappe** | An open-source full-stack web application framework built with Python and JavaScript, providing the DocType engine, Desk UI, REST API, and workflow system |
| **Frappe Agriculture** | A Frappe app providing agricultural DocTypes (Crop, CropCycle, WaterAnalysis, PlotLand, etc.) |
| **gitleaks** | An open-source secret scanning tool that detects accidentally committed API keys, passwords, and other secrets in Git repositories |
| **hooks.py** | The Frappe app configuration file that registers event hooks, permission query conditions, document events, and scheduled tasks |
| **InnoDB** | The default storage engine for MariaDB/MySQL; provides ACID transactions and crash recovery (Write-Ahead Logging) |
| **IoT Gateway** | A Python MQTT subscriber service that receives sensor readings from devices and creates Observation records in Frappe |
| **k3s** | A lightweight, certified Kubernetes distribution optimised for edge and IoT environments; used for YAM Agri staging and production |
| **LLM** | Large Language Model — an AI model trained on large text datasets, capable of generating human-like text; examples: GPT-4o (OpenAI), Claude (Anthropic), Llama (Meta) |
| **MariaDB** | An open-source relational database management system (RDBMS); a fork of MySQL; required by Frappe Framework |
| **MinIO** | An open-source, self-hosted object storage server with S3-compatible API; used for storing file attachments (certificates, photos, EvidencePack PDFs) |
| **MQTT** | Message Queuing Telemetry Transport — a lightweight publish/subscribe messaging protocol designed for IoT devices on constrained networks |
| **Ollama** | An open-source tool for running large language models locally on commodity hardware |
| **permission_query_conditions** | A Frappe hook that injects SQL WHERE conditions into every list query for a DocType; used to enforce site isolation |
| **PouchDB** | A JavaScript database that syncs with CouchDB/Frappe offline queue; enables browser-based offline data entry |
| **Qdrant** | An open-source vector database; planned for V1.2+ RAG (Retrieval-Augmented Generation) AI features |
| **RAG** | Retrieval-Augmented Generation — an AI technique that retrieves relevant documents from a vector store before generating a response, improving accuracy and grounding |
| **Redis** | An in-memory data structure store used by Frappe for job queues (RQ), session cache, and real-time WebSocket pub/sub |
| **Restic** | An open-source backup tool; used for encrypted, deduplicated backups of the Frappe site data |
| **Role Profile** | A Frappe/ERPNext construct that bundles multiple standard roles into a named profile for easy assignment to users |
| **RQ** | Redis Queue — a Python library for queuing and processing background jobs; used by Frappe workers |
| **run.sh** | The convenience shell script at `infra/docker/run.sh` that wraps Docker Compose commands: `up`, `down`, `logs`, `shell`, `init`, `reset`, `backup`, `restore`, `prefetch` |
| **User Permission** | A Frappe record that restricts a user to specific values of a Link field (e.g., restrict user to SITE-FARM-001 only) |
| **WireGuard** | A modern, fast, and secure VPN protocol; used to protect access to staging and production environments |
| **yam_agri_core** | The custom Frappe app containing all YAM Agri-specific DocTypes, business logic, and hooks |

---

## 12.3 Acronyms

| Acronym | Expansion |
|---------|----------|
| ADR | Architecture Decision Record |
| API | Application Programming Interface |
| AT | Acceptance Test |
| CAPA | Corrective and Preventive Action |
| CCP | Critical Control Point |
| CI/CD | Continuous Integration / Continuous Deployment |
| CSV | Comma-Separated Values |
| DRP | Disaster Recovery Plan |
| ERP | Enterprise Resource Planning |
| FAO | Food and Agriculture Organization of the United Nations |
| GAP | Good Agricultural Practices |
| GPS | Global Positioning System |
| HACCP | Hazard Analysis and Critical Control Points |
| HTTPS | Hypertext Transfer Protocol Secure |
| IoT | Internet of Things |
| ISO | International Organization for Standardization |
| LLM | Large Language Model |
| MQTT | Message Queuing Telemetry Transport |
| NDVI | Normalised Difference Vegetation Index |
| NFR | Non-Functional Requirement |
| PII | Personally Identifiable Information |
| RBAC | Role-Based Access Control |
| RAG | Retrieval-Augmented Generation |
| REST | Representational State Transfer |
| RTL | Right-to-Left (text direction, as in Arabic) |
| SDLC | Software Development Life Cycle |
| SMS | Short Message Service |
| SRS | Software Requirements Specification |
| TLS | Transport Layer Security |
| VPN | Virtual Private Network |
| YAM | Yemen Agri Management (business name) |

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial glossary — V1.1 |
