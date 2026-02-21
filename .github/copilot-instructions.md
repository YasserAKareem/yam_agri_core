# Copilot Instructions for YAM Agri Core

## Project Overview
This repository is the infrastructure and configuration layer for the **YAM Agri Platform** — a cereal-crop supply chain quality and traceability system. It is built on top of **Frappe Framework** and **ERPNext**, with the **Frappe Agriculture** app installed.

The platform manages:
- Lot traceability across splits, merges, and blends
- QA/QC tests and certificates (FAO GAP Middle East + HACCP/ISO 22000)
- Scale tickets (weights) and sensor evidence (bins, refrigerators)
- Evidence packs for audits and customers
- Hybrid AI assistance (assistive only — AI never executes risky actions automatically)

## Repository Structure

```
yam_agri_core/
├── .github/                  # GitHub configuration (this file, workflows, etc.)
├── docs/                     # Playbooks and design documents
├── environments/             # Per-environment configs (dev, staging, production)
│   ├── dev/
│   ├── staging/
│   └── production/
├── infra/
│   ├── compose/              # Docker Compose files for dev
│   ├── docker/               # Docker configs and run scripts
│   └── frappe_docker/        # Frappe-specific Docker setup
└── compose_rendered.yml      # Rendered compose for reference
```

## Technology Stack
- **Framework**: [Frappe](https://frappeframework.com/) (Python/JavaScript)
- **ERP**: ERPNext v16
- **Agriculture Module**: Frappe Agriculture app
- **Database**: MariaDB 10.6
- **Cache/Queue**: Redis
- **Container Runtime**: Docker + Docker Compose (dev), Kubernetes/k3s (staging/production)
- **Web Server**: nginx

## Key Domain Concepts

### Core DocTypes (V1.1)
- **Site** — farm, silo, store, or office location
- **StorageBin** — physical bin within a site
- **Device** — IoT sensor or scale device
- **Lot** — harvest, storage, or shipment lot (primary traceability unit)
- **Transfer** — split, merge, or blend operation between lots
- **ScaleTicket** — weight measurement record
- **QCTest** — quality control test result
- **Certificate** — compliance certificate (expiry-checked)
- **Nonconformance** — CAPA (Corrective and Preventive Action) record
- **EvidencePack** — audit evidence bundle
- **Complaint** — customer complaint record
- **Observation** — universal model for sensor/derived signals (bins, refrigerators, weather, irrigation, remote sensing)

### Non-Negotiable Business Rules
1. Every record **must** belong to a Site
2. Users should **not** see other sites' data by default (site isolation)
3. High-risk actions **require approval** from QA Manager
4. AI is **assistive only** — no automatic lot accept/reject, no automatic recalls, no unsupervised customer communications
5. **Never commit secrets** — use `.env.example` files only, never `.env` with real credentials

## Development Guidelines

### Frappe Development
- Custom DocTypes live in the `yam_agri_core` Frappe app (mounted into the Frappe bench)
- Follow [Frappe coding standards](https://frappeframework.com/docs/user/en/guides/app-development)
- Use `bench` commands inside the container for migrations, fixtures, and app management
- Server-side scripts: Python (Frappe controllers)
- Client-side scripts: JavaScript (Frappe client scripts / Form scripts)

### Docker / Infrastructure
- Dev environment uses Docker Compose; run via `infra/docker/run.sh`
- Supported `run.sh` commands: `up`, `down`, `logs`, `shell`, `init`, `reset`
- Do **not** start with Kubernetes until the Docker Compose dev environment works
- Do **not** commit `.env` files with real passwords or tokens

### Environment Variables
- Always use `.env.example` as a template; copy to `.env` locally and fill in values
- Key variables: `DB_ROOT_PASSWORD`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `SITE_NAME`, `ADMIN_PASSWORD`

### Security
- Enforce site-level data isolation via Frappe's permission system
- Use approval workflows for any destructive or high-risk operations
- AI gateway must redact PII, pricing, and customer IDs before sending to any external LLM
- Log AI interaction hashes and record references for auditability

### Testing & Acceptance
Before marking a feature complete, verify these acceptance scenarios manually:
1. Create Site → StorageBin → Lot
2. Create QCTest and attach Certificate to a Lot
3. Transfer: split a Lot into a shipment Lot
4. Trace backward from shipment Lot (shows QC/certs/bin history)
5. Trace forward from storage Lot (shows impacted shipments and quantities)
6. Block a shipment when mandatory QC/cert is missing (season policy enforcement)
7. Import a ScaleTicket CSV — quantities update and mismatches flag as Nonconformance
8. Post a sensor Observation — invalid data is quarantined (quality_flag set)
9. Generate an EvidencePack for a date range and site
10. Confirm Site A user cannot see Site B data

## What NOT to Do
- Do **not** integrate many sensor vendors at once — use the universal Observation model
- Do **not** let AI execute risky actions (accepts, recalls, customer comms) in V1.1
- Do **not** commit secrets to GitHub
- Do **not** start Kubernetes before Docker Compose dev works
- Do **not** modify production until staging passes acceptance tests
