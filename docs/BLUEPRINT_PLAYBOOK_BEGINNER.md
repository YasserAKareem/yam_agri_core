
Below is a beginner-friendly, repo-ready version of the "YAM Agri Platform Blueprint Playbook (Detailed)", updated for your new setup:

- Restarting clean on a new machine
- Track A: Docker Compose first (Dev), Kubernetes later (Staging)
- You're not a coder, so everything is written as "do this, expect that"
- Includes folder structure, scripts, acceptance checks, and issue list
- Uses your chosen standards: FAO GAP (Middle East) + HACCP/ISO 22000 mindset
- Includes your real-world scenario: 5 locations + office + stores + refrigerators
- Assumes you are using Frappe + ERPNext + Frappe Agriculture app
- Includes the AI Enhancement Roadmap and integration plan for the 80-item backlog (`docs/20260222 YAM_AGRI_BACKLOG v1.csv`)




# YAM Agri Platform Blueprint Playbook (Beginner-Friendly)

---

## 0) Owner's Vision & Business Purpose

**YAM Agri** is a cereal-crop supply chain business operating across multiple farm, silo, store, and office sites in the Middle East region.

The owner's goal is to build a **smart, valuable enterprise** — not a software company — by using modern technology to:

- Win customer trust with **verifiable quality and traceability** (FAO GAP / HACCP / ISO 22000)
- Protect margins through **better storage, harvest, and logistics decisions**
- Reduce waste, losses, and compliance risk with **early warning signals**
- Gradually enhance operations with **AI assistance** as the data foundation matures

The strategy is:

1. **Foundation first** — Frappe + ERPNext gives a solid, auditable system-of-record at low cost
2. **Backlog-driven growth** — 80 prioritised ideas in `docs/20260222 YAM_AGRI_BACKLOG v1.csv` map to every stage of the cereal supply chain (Stages A–I)
3. **Safe AI only** — AI is always assistive, never autonomous; all AI suggestions require human approval before any action is taken
4. **Iterative delivery** — small, verified releases that do not disrupt daily operations

---

## 0.1) What we are building now (V1.1)
**V1.1 = Quality + Traceability Core**

The product helps YAM Agri manage cereal-crop supply chain quality from storage to customer:

- Track lots across **splits, merges, blends**
- Capture **QA/QC tests** and **certificates**
- Monitor **scale tickets** (weights) and **sensor evidence** (bins, refrigerators, etc.)
- Generate **evidence packs** for audits/customers
- Keep operations safe: approvals + audit logs
- AI is **assistive** (hybrid) and never executes risky actions automatically

### Standards (baseline)
- **FAO GAP (Middle East)** baseline checklist for good practice controls
- HACCP-style control points and ISO 22000 thinking for hazard control

---

## 1) How we will build (Track A - recommended)

We use TWO environments:

### A) Dev (on laptop/Codespaces)
**Docker Compose** for fast iteration.
- OK to reset and wipe data
- Goal: get working quickly

### B) Staging (on your new machine)
**Kubernetes (k3s)** later, after Dev works.
- production-like configuration
- used for UAT and integration testing across your 5 locations + stores

### C) Production
Not touched until staging passes acceptance tests.

---

## 2) Repo structure (what must exist)

```
yam-agri-platform/
  apps/
    yam_agri_core/         # Frappe custom app (DocTypes, workflows, reports)
  services/
    iot_gateway/           # sensor ingest + normalize into Observation
    scale_connector/       # scale ticket ingest (CSV first, API later)
    ai_gateway/            # redaction + routing to cloud LLM (hybrid)
    remote_sensing/        # later: satellite/indices ingestion
  infra/
    docker/                # dev stack (compose)
    k8s/                   # staging manifests (later)
  docs/
    policies/              # FAO GAP mapping, HACCP control points, season policy matrix
    runbooks/              # how to operate, reset, troubleshoot
```

**Important:** Do NOT commit secrets.
- Never commit `.env` with passwords/tokens.
- Only commit `.env.example`.

---

## 3) Phase 0: Prepare Dev Runtime (Docker Compose)

### Goal
You can run Frappe + ERPNext + Agriculture app on Dev reliably.

### What you need installed
- Docker Desktop
- Git
- VS Code

### Steps
1) Create these files:
   - `infra/docker/docker-compose.yml`
   - `infra/docker/.env.example`
   - `infra/docker/run.sh` (helper script)

2) `run.sh` should support:
   - `up` (start)
   - `down` (stop)
   - `logs` (view logs)
   - `shell` (open container shell)
   - `init` (create site + install apps)
   - `reset` (wipe volumes + clean rebuild)

3) Start Dev:
```bash
cd infra/docker
./run.sh up
./run.sh logs
```

You should be able to open the web UI.

If you see a login page: good.

### Exit criteria (Dev runtime is done)
- Docker stack starts without fatal errors
- You can open the login page
- ERPNext + Agriculture app appear in installed apps after init

---

## 4) Phase 1: Create Frappe custom app (yam_agri_core)

### Goal
Create a custom app where our DocTypes and workflows live.

### Steps (operator/Codex does this)
- Create `yam_agri_core`
- Install it on the dev site
- Commit generated app into `/apps/yam_agri_core`

### Exit criteria
- `yam_agri_core` appears in the site's installed apps list

---

## 5) Phase 2: Core data model (DocTypes) — V1.1 foundation

### Goal
Create the minimum system-of-record for traceability and QA/QC evidence.

### DocTypes we need (V1.1)

**Multi-site / Structure**
- Site (farm/silo/store/office)
- StorageBin
- Device

**Traceability**
- Lot (harvest/storage/shipment)
- Transfer (split/merge/blend)
- ScaleTicket

**QA/QC + Compliance**
- QCTest
- Certificate
- Nonconformance (CAPA)
- EvidencePack
- Complaint

**Evidence signals**
- Observation (universal model for sensor + derived signals)

### Non-negotiable rules
- Every record belongs to a Site
- Users should NOT see other sites by default
- High-risk actions require approval (QA Manager)

### Exit criteria
- You can create: Site, StorageBin, Lot, Transfer, QCTest, Certificate
- A Site-A user cannot see Site-B records

---

## 6) Phase 3: Traceability engine (splits, merges, blends)

### Goal
Trace backward and forward across transfers.

### What we build

**Trace Backward:**
- From shipment lot → upstream lots → bins → QC tests → certificates

**Trace Forward:**
- From storage lot → downstream shipments → blast radius quantities

**Enforcement — Mass-balance rules:**
- Outgoing quantity must not exceed available quantity (with tolerance)

### Exit criteria
- Trace backward works and shows evidence
- Trace forward works and shows impacted shipments and quantities
- Export to CSV/PDF

---

## 7) Phase 4: QA/QC controls (FAO GAP + HACCP / ISO 22000)

### Goal
Build control points with automation levels for best ROI.

### Control point automation levels

**MUST automate** (blocking, high risk, cheap ROI)
- Scale weight verification + mismatch flags
- Certificate expiry checks (block dispatch if expired unless override)
- High-risk season mycotoxin gating (block dispatch until passed)
- Refrigerator temperature monitoring in stores (alert + corrective action record)
- Recall initiation workflow (trace forward + evidence pack, approvals required)

**SHOULD semi-automate**
- Auto-create QC tasks for new lots
- Hotspot detection → Nonconformance + suggested action (approval required)

**OK manual** (still tracked)
- Visual inspection checklists with photo attachments

### Exit criteria
- Shipment is blocked if required QC/cert missing for that product/season policy
- CAPA workflow exists and is auditable

---

## 8) Phase 5: Integrations (Scales + Sensors)

### Goal
Bring real evidence into the system.

**ScaleConnector (start simple)**
- CSV import into ScaleTicket
- Map ticket → Lot quantity
- Flag mismatches → Nonconformance

**IoT Gateway (universal observation model)**
Observation supports:
- Bins: temp, humidity, moisture, CO2
- Stores: refrigerator temperature
- Weather: rainfall, humidity
- Irrigation telemetry: flow, valve state
- Remote sensing derived indices: NDVI, flood risk

Rules:
- Validate units
- Range checks
- Quarantine suspect data (`quality_flag`), don't use it for automation

### Exit criteria
- Real scale ticket updates lot quantities
- Real sensor reading attaches to correct bin/site and triggers alerts if out-of-range

---

## 9) Phase 6: Hybrid AI (assist only, safe by design)

### Goal
Use cloud LLM without leaking data and without autonomy.

### AI Gateway rules
- Redact sensitive data (PII, pricing, customer IDs)
- Send only minimal context
- Log hashes + record references
- Have fallback behavior (AI down = system still works)

### AI functions allowed in V1.1
- "What's missing for compliance on this lot?"
- Summarize nonconformance and draft corrective action checklist
- Summarize evidence pack / audit narrative

### Not allowed in V1.1
- No automatic accept/reject lots
- No automatic recalls
- No customer communications without approval

### Exit criteria
- AI suggestions are always auditable and never execute actions

---

## 10) Staging (Kubernetes) — only after Dev works

### Goal
Deploy a production-like stack on your new machine using k3s.

### Why later?
Because Kubernetes adds complexity. We only do it once the app works in Compose.

### Plan
- Use k3s single node
- Install Ingress (Traefik default is fine)
- Persistent volumes for DB and files
- Deploy Frappe stack first, then services

### Exit criteria
- `kubectl` shows node Ready
- Frappe is reachable via ingress
- UAT runs in staging without dev shortcuts

---

## 11) Acceptance tests (how YAM approves without coding)

### Must-pass scenarios
1. Create Site + StorageBin + Lot
2. Create QCTest + attach Certificate
3. Transfer: split lot → shipment lot
4. Trace backward from shipment lot (shows QC/certs/bin history)
5. Trace forward from storage lot (blast radius)
6. Block shipment when mandatory QC/cert missing (season policy)
7. Import ScaleTicket CSV updates quantities + flags mismatch
8. Post sensor Observation; invalid data is quarantined
9. EvidencePack generated for a date range + site
10. Site isolation: Site A user can't see Site B data

---

## 12) AI Enhancement Roadmap

This section describes how YAM Agri will evolve from a quality/traceability system into a **smart, AI-assisted enterprise** using the 80-item backlog in `docs/20260222 YAM_AGRI_BACKLOG v1.csv`.

### Guiding principles
- **Frappe + ERPNext is the permanent base** — all data lives in the ERP; AI layers sit on top
- **AI is always assistive** — every AI output is a suggestion; a human must approve before any action
- **Three AI action modes** (from the backlog):
  - **Read-only** — dashboards, forecasts, analytics only; no system change
  - **Propose-only** — system surfaces a recommendation; operator reviews and decides
  - **Execute-with-approval** — system prepares the action; manager approves before it runs
- **No AI autonomy** — the system never auto-accepts lots, auto-initiates recalls, or sends customer communications without approval
- **Data quality first** — AI features are only enabled once the underlying Frappe data is clean and complete for that stage

### Release phasing

| Release | Focus | Backlog stages | Approx. backlog items |
|---------|-------|----------------|-----------------------|
| V1.1 | Foundation: quality, traceability, sensor ingest | — (core ERP) | Manual controls only |
| V1.2 | Storage & harvest AI layer | D, E, F | AGR-CEREAL-028 to 055 |
| V1.3 | Pre-season planning & field ops AI layer | A, B, C | AGR-CEREAL-001 to 027 |
| V2.0 | Logistics, trading & processing AI layer | G, H | AGR-CEREAL-056 to 071 |
| V2.1+ | Customer, market & platform AI layer | I | AGR-CEREAL-072 to 080 |

> **Rule:** Never start the next release until the previous release passes its acceptance tests in staging.

---

## 13) Backlog Integration Plan — Stage-by-Stage Mapping

The full backlog is in `docs/20260222 YAM_AGRI_BACKLOG v1.csv`. Each row has:
`Idea ID | Stage | Sub-domain | Description | AI Mode | Actionability | KPIs | Risks | Integrations`

**Key column meanings:**

| Column | What it means |
|--------|--------------|
| **Idea ID** | Unique reference (e.g. `AGR-CEREAL-043`) — use as the GitHub Issue title prefix |
| **Stage** | Agricultural stage letter A–I; maps to the sections below |
| **Sub-domain** | The specific business problem this item addresses |
| **AI Mode** | The type of AI capability required (e.g. Prediction, Optimization, Copilot, Vision) |
| **Actionability** | How the AI output is used: `Read-only` (no system change), `Propose-only` (human decides), or `Execute-with-approval` (manager must confirm before anything runs) |
| **KPIs** | How to measure success once the feature is live |
| **Risks** | Key risks to manage during implementation |
| **Integrations** | External data sources or systems needed |

### How to use this plan

1. After V1.1 passes all acceptance tests, pick the **next backlog stage** below
2. For each item: create a GitHub Issue, implement as a Frappe report/script/workflow on top of existing DocTypes, then run acceptance tests
3. Never build AI functionality for a stage until the base Frappe data for that stage is verified complete

---

### Stage A — Pre-Season Planning (10 items: AGR-CEREAL-001 to 010)

**When to start:** After V1.3 is planned and Lot/Site/Field data is established

**Frappe base needed:** Site, Lot (harvest type), Observation (weather), historical QCTest records

| Idea ID | Sub-domain | AI Mode | Action mode |
|---------|-----------|---------|-------------|
| AGR-CEREAL-001 | Crop/Variety Selection | Optimization + Prediction | Propose-only |
| AGR-CEREAL-002 | Fertility Plan Optimization | Optimization | Propose-only |
| AGR-CEREAL-003 | Planting Window Prediction | Prediction | Propose-only |
| AGR-CEREAL-004 | Planning Impact Simulation | Simulation | Read-only |
| AGR-CEREAL-005 | Acreage Aggregation Forecast | Forecasting | Read-only |
| AGR-CEREAL-006 | Budget Scenario Engine | Simulation | Read-only |
| AGR-CEREAL-007 | Irrigation Feasibility & Plan | Optimization + Prediction | Propose-only |
| AGR-CEREAL-008 | Disease-Resistant Variety Reco | Prediction | Propose-only |
| AGR-CEREAL-009 | Field Accessibility Risk | Prediction | Propose-only |
| AGR-CEREAL-010 | Geo-Regulatory Input Flags | RAG-docs + Rules | Read-only |

**Safe implementation notes:**
- All items are Read-only or Propose-only — no automated writes
- Start with AGR-CEREAL-003 (Planting Window Prediction) as highest-ROI first step
- AGR-CEREAL-010 requires a document library of local regulations loaded into the AI gateway

---

### Stage B — Input Procurement & Preparation (8 items: AGR-CEREAL-011 to 018)

**When to start:** After Stage A baseline items are delivering value

**Frappe base needed:** ERPNext Purchase Orders, Supplier records, Item/Stock DocTypes

| Idea ID | Sub-domain | AI Mode | Action mode |
|---------|-----------|---------|-------------|
| AGR-CEREAL-011 | Input Demand Forecast | Forecasting | Propose-only |
| AGR-CEREAL-012 | Supplier Risk Scoring | Risk scoring | Propose-only |
| AGR-CEREAL-013 | Forward Buying Scenarios | Simulation | Read-only |
| AGR-CEREAL-014 | Receiving Match Automation | Document AI + Anomaly | Execute-with-approval |
| AGR-CEREAL-015 | SDS & Restricted Use Validation | RAG-docs | Read-only |
| AGR-CEREAL-016 | Deliveries vs Field Schedule | Optimization | Propose-only |
| AGR-CEREAL-017 | RFQ Comparison Copilot | Copilot | Propose-only |
| AGR-CEREAL-018 | Fair Input Allocation | Optimization | Propose-only |

**Safe implementation notes:**
- AGR-CEREAL-014 (Receiving Match Automation) is the only Execute-with-approval item; requires QA Manager sign-off
- AGR-CEREAL-015 requires a curated SDS/regulatory document library in the AI gateway

---

### Stage C — Field Operations & Crop Management (9 items: AGR-CEREAL-019 to 027)

**When to start:** Alongside Stage B; requires Device and Observation data flowing

**Frappe base needed:** Device, Observation, ScaleTicket, Lot (harvest), Nonconformance

| Idea ID | Sub-domain | AI Mode | Action mode |
|---------|-----------|---------|-------------|
| AGR-CEREAL-019 | Planter Calibration Anomaly | Anomaly detection | Execute-with-approval |
| AGR-CEREAL-020 | Work Orders & Notes Copilot | Copilot | Propose-only |
| AGR-CEREAL-021 | Crew & Machine Scheduling | Optimization | Propose-only |
| AGR-CEREAL-022 | Compaction Risk Advisor | Prediction | Propose-only |
| AGR-CEREAL-023 | Fuel/Parts Stock Forecast | Forecasting | Propose-only |
| AGR-CEREAL-024 | Seed Lot Capture | Workflow automation | Execute-with-approval |
| AGR-CEREAL-025 | Stand Count via Vision | Vision | Read-only |
| AGR-CEREAL-026 | Deviation Impact Analytics | Analytics copilot | Read-only |
| AGR-CEREAL-027 | Safety Incident Risk | Risk prediction | Propose-only |

**Safe implementation notes:**
- AGR-CEREAL-024 (Seed Lot Capture) and AGR-CEREAL-019 use Execute-with-approval; add to the approval workflow in Frappe before enabling
- AGR-CEREAL-025 (Vision) requires image ingestion pipeline not in V1.1 scope; plan separately

---

### Stage D — Storage & Handling (12 items: AGR-CEREAL-028 to 039)

**When to start:** V1.2 — first AI release, immediately after V1.1 acceptance tests pass

**Frappe base needed:** StorageBin, Observation (sensor data), Lot, Nonconformance

| Idea ID | Sub-domain | AI Mode | Action mode |
|---------|-----------|---------|-------------|
| AGR-CEREAL-028 | Stress-to-Prescription | Vision + Decision support | Propose-only |
| AGR-CEREAL-029 | Disease Identification | Vision | Propose-only |
| AGR-CEREAL-030 | Irrigation Optimizer | Optimization | Execute-with-approval |
| AGR-CEREAL-031 | Variable Rate Nitrogen | Optimization + Explainability | Propose-only |
| AGR-CEREAL-032 | Pest Outbreak Predictor | Prediction | Propose-only |
| AGR-CEREAL-033 | Localized Recommendations | RAG-docs + Prediction | Propose-only |
| AGR-CEREAL-034 | Spray Timing Advisor | Prediction + Rules | Propose-only |
| AGR-CEREAL-035 | Calibrated Yield Forecast | Probabilistic forecasting | Read-only |
| AGR-CEREAL-036 | Loss Assessment Assist | Vision + Anomaly | Propose-only |
| AGR-CEREAL-037 | Soil Health Tracking | Analytics + Estimation | Read-only |
| AGR-CEREAL-038 | Alert Ranking | Alert ranking | Read-only |
| AGR-CEREAL-039 | Data Quality Guardrails | Anomaly + Data validation | Execute-with-approval |

**Safe implementation notes:**
- Start with AGR-CEREAL-038 (Alert Ranking) and AGR-CEREAL-039 (Data Quality Guardrails) — these protect the data quality of all other AI features
- AGR-CEREAL-030 (Irrigation Optimizer) is Execute-with-approval; requires approval workflow before irrigation commands are dispatched

---

### Stage E — Harvest & Post-Harvest (8 items: AGR-CEREAL-040 to 047)

**When to start:** V1.2 alongside Stage D; harvest data must be flowing via ScaleTicket

**Frappe base needed:** ScaleTicket, Lot (harvest/storage), Observation, Nonconformance

| Idea ID | Sub-domain | AI Mode | Action mode |
|---------|-----------|---------|-------------|
| AGR-CEREAL-040 | Harvest Window Predictor | Prediction | Propose-only |
| AGR-CEREAL-041 | Combine Settings Optimizer | Optimization | Propose-only |
| AGR-CEREAL-042 | Harvest-to-Truck Dispatch | Dispatch optimization | Execute-with-approval |
| AGR-CEREAL-043 | Mycotoxin Risk Flags | Prediction + Anomaly | Propose-only |
| AGR-CEREAL-044 | Yield Map Insights | Analytics copilot | Propose-only |
| AGR-CEREAL-045 | Harvest Predictive Maintenance | Predictive maintenance | Propose-only |
| AGR-CEREAL-046 | Harvest Cost Visibility | Analytics automation | Read-only |
| AGR-CEREAL-047 | Silo Intake Scheduling | Scheduling optimization | Execute-with-approval |

**Safe implementation notes:**
- AGR-CEREAL-043 (Mycotoxin Risk Flags) directly supports the V1.1 QA gating already in Phase 4 — prioritise this first
- AGR-CEREAL-042 and AGR-CEREAL-047 are Execute-with-approval; add dispatch/scheduling approval workflows in Frappe

---

### Stage F — Quality & Compliance (8 items: AGR-CEREAL-048 to 055)

**When to start:** V1.2 alongside Stages D and E; HACCP evidence and certificate data must be complete

**Frappe base needed:** QCTest, Certificate, EvidencePack, Nonconformance, Observation (IoT)

| Idea ID | Sub-domain | AI Mode | Action mode |
|---------|-----------|---------|-------------|
| AGR-CEREAL-048 | Aeration Control | Anomaly + Control optimization | Execute-with-approval |
| AGR-CEREAL-049 | Blend Optimization | Optimization | Propose-only |
| AGR-CEREAL-050 | Shrink/Theft Detection | Anomaly detection | Read-only |
| AGR-CEREAL-051 | Storage Inspection Copilot | Copilot + Checklist | Propose-only |
| AGR-CEREAL-052 | Inventory Reconciliation | Anomaly + Automation | Execute-with-approval |
| AGR-CEREAL-053 | Moisture Out-of-Spec Predictor | Prediction | Propose-only |
| AGR-CEREAL-054 | Capacity Constraint Feedback | Constraint optimization | Propose-only |
| AGR-CEREAL-055 | IoT Security Monitoring | Security anomaly | Read-only |

**Safe implementation notes:**
- AGR-CEREAL-048 (Aeration Control) and AGR-CEREAL-052 (Inventory Reconciliation) are Execute-with-approval — highest value, highest risk; add to approval workflow first
- AGR-CEREAL-055 (IoT Security Monitoring) is Read-only and should be implemented early as a security safeguard

---

### Stage G — Logistics & Trading (7 items: AGR-CEREAL-056 to 062)

**When to start:** V2.0 — after storage/harvest/quality AI layer is stable

**Frappe base needed:** ERPNext Delivery Notes, Purchase/Sales Orders, Lot, Transfer, Certificate

| Idea ID | Sub-domain | AI Mode | Action mode |
|---------|-----------|---------|-------------|
| AGR-CEREAL-056 | Routing with Constraints | Optimization | Execute-with-approval |
| AGR-CEREAL-057 | Export Docs Automation | Document AI | Execute-with-approval |
| AGR-CEREAL-058 | Freight Billing Anomalies | Anomaly detection | Propose-only |
| AGR-CEREAL-059 | In-transit Quality Risk | Anomaly + Prediction | Propose-only |
| AGR-CEREAL-060 | Cargo Theft/Diversion | Anomaly detection | Read-only |
| AGR-CEREAL-061 | Shipment Carbon Reporting | Estimation + Reporting automation | Read-only |
| AGR-CEREAL-062 | Exception Management Copilot | Workflow copilot | Propose-only |

**Safe implementation notes:**
- AGR-CEREAL-057 (Export Docs Automation) is high value for the business; requires document templates in the AI gateway
- All Execute-with-approval items require a manager to confirm before documents are sent or routes are dispatched

---

### Stage H — Processing & Milling (9 items: AGR-CEREAL-063 to 071)

**When to start:** V2.0 alongside Stage G; requires milling/processing operational data

**Frappe base needed:** Lot (processed), QCTest, Certificate, EvidencePack, ERPNext Manufacturing

| Idea ID | Sub-domain | AI Mode | Action mode |
|---------|-----------|---------|-------------|
| AGR-CEREAL-063 | Incoming Lot Classification | Classification + Anomaly | Execute-with-approval |
| AGR-CEREAL-064 | Process Parameter Optimization | Optimization | Propose-only |
| AGR-CEREAL-065 | Packaging Line PdM | Predictive maintenance | Propose-only |
| AGR-CEREAL-066 | HACCP Evidence Builder | RAG-docs + Evidence automation | Read-only |
| AGR-CEREAL-067 | Batch Scheduling with Constraints | Scheduling optimization | Propose-only |
| AGR-CEREAL-068 | Formulation Optimizer | Optimization + Simulation | Propose-only |
| AGR-CEREAL-069 | Label/Allergen Compliance | Rules + Document AI | Execute-with-approval |
| AGR-CEREAL-070 | Yield Loss RCA Copilot | Analytics copilot | Read-only |
| AGR-CEREAL-071 | Provenance Query during Incidents | Traceability graph + RAG | Read-only |

**Safe implementation notes:**
- AGR-CEREAL-066 (HACCP Evidence Builder) and AGR-CEREAL-071 (Provenance Query) extend the EvidencePack DocType already built in V1.1
- AGR-CEREAL-069 (Label/Allergen Compliance) is Execute-with-approval; requires regulatory document library in AI gateway

---

### Stage I — Customer, Market & Platform (9 items: AGR-CEREAL-072 to 080)

**When to start:** V2.1+ — only after logistics, trading, and processing layers are stable

**Frappe base needed:** ERPNext CRM, Sales/Purchase Orders, Complaint, Lot, EvidencePack

| Idea ID | Sub-domain | AI Mode | Action mode |
|---------|-----------|---------|-------------|
| AGR-CEREAL-072 | Retail Demand Forecast | Forecasting | Read-only |
| AGR-CEREAL-073 | Allocation Optimization | Optimization | Propose-only |
| AGR-CEREAL-074 | Expiry Waste Predictor | Prediction | Propose-only |
| AGR-CEREAL-075 | Pricing & Promo Optimizer | Optimization | Propose-only |
| AGR-CEREAL-076 | Complaint-to-Lot Linkage | NLP + Traceability | Read-only |
| AGR-CEREAL-077 | Fill-rate Anomaly Monitor | Anomaly detection | Read-only |
| AGR-CEREAL-078 | Recall Execution Automation | Workflow automation | Execute-with-approval |
| AGR-CEREAL-079 | Assortment Optimization | Analytics + Clustering | Propose-only |
| AGR-CEREAL-080 | End-to-End Margin Copilot | Analytics copilot | Read-only |

**Safe implementation notes:**
- AGR-CEREAL-076 (Complaint-to-Lot Linkage) extends the Complaint DocType already built in V1.1 — highest-value starting point
- AGR-CEREAL-078 (Recall Execution Automation) is Execute-with-approval and the riskiest item; requires full trace-forward and legal review before enabling
- AGR-CEREAL-075 (Pricing) must be scoped carefully — AI suggests only, never submits a quote or contract

---

## 14) Work queue (GitHub Issues — ordered)

Create issues in this order:

1. Dev runtime: `infra/docker` compose + init scripts
2. Create `yam_agri_core` app + install
3. Implement V1.1 DocTypes + site permissions
4. Trace backward/forward UI + export
5. QA/QC control points + CAPA workflow + evidence packs
6. Scale connector CSV import + reconciliation
7. IoT gateway observation ingest + validation/quarantine
8. Hybrid AI gateway (redaction + logs + fallback) — V1.1 AI functions only
9. *(V1.2)* Stage D: Data Quality Guardrails + Alert Ranking (AGR-CEREAL-038, 039)
10. *(V1.2)* Stage F: Storage Inspection Copilot + Aeration Control (AGR-CEREAL-051, 048)
11. *(V1.2)* Stage E: Mycotoxin Risk Flags + Harvest Window Predictor (AGR-CEREAL-043, 040)
12. *(V1.3)* Stage A+B: Planting Window Prediction + Input Demand Forecast (AGR-CEREAL-003, 011)
13. *(V2.0+)* Stages G, H, I — as business grows

> For each backlog item, tag the GitHub Issue with its `Stage` letter and reference the `Idea ID` (e.g. `AGR-CEREAL-043`).

---

## 15) What you should NOT do (to avoid downtime)

- Don't start with Kubernetes before Dev works
- Don't integrate 20 sensor vendors at once
- Don't let AI execute risky actions in V1.1
- Don't commit secrets to GitHub
- Don't add AI features for a stage before the underlying ERP data is clean
- Don't skip the approval workflow for Execute-with-approval backlog items

---

## 16) Owner/operator responsibilities

- **YAM (Product Owner):** approve workflows, policies, UAT results, and which backlog items to prioritise next
- **Operator/Dev:** run commands, fix environment issues, implement tasks from the backlog
- **QA Manager:** defines approvals, signs off on controls, reviews all AI suggestions before action
- **AI Gateway:** assistive only — surfaces suggestions, never acts without human approval

End.

---

## What changed vs the earlier blueprint

- Added **Owner's Vision & Business Purpose** section (Section 0)
- Added explicit **AI Enhancement Roadmap** with release phases V1.1 → V2.1+ (Section 12)
- Added **Backlog Integration Plan** with stage-by-stage tables for all 80 items (Stages A–I) (Section 13)
- Fixed all **markdown formatting** inconsistencies (headings, code blocks, lists)
- Updated **Work queue** to reference specific backlog IDs and release phases (Section 14)
- Clarified **Frappe+ERPNext as the permanent base layer** for all AI features
- Reinforced the **safe, assistive-only AI** principle with action-mode detail for every backlog item

---

## Next steps

1. Finish V1.1 foundation (Phases 0–6 above)
2. Run all 10 acceptance tests in Section 11 in staging
3. Then pick the first V1.2 items from Stage D/E/F backlog — start with `AGR-CEREAL-038`, `AGR-CEREAL-039`, and `AGR-CEREAL-043`
4. Create a GitHub Issue for each backlog item as you approach its release phase
5. The backlog CSV (`docs/20260222 YAM_AGRI_BACKLOG v1.csv`) is the single source of truth for all future AI feature work
