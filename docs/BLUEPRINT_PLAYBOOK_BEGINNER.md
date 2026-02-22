
Below is a beginner-friendly, repo-ready version of the "YAM Agri Platform Blueprint Playbook (Detailed)", updated for your new setup:

- Restarting clean on a new machine
- Track A: Docker Compose first (Dev), Kubernetes later (Staging)
- You're not a coder, so everything is written as "do this, expect that"
- Includes folder structure, scripts, acceptance checks, and issue list
- Uses your chosen standards: FAO GAP (Middle East) + HACCP/ISO 22000 mindset
- Includes your real-world scenario: 5 locations + office + stores + refrigerators
- Assumes you are using Frappe + ERPNext + Frappe Agriculture app
- Includes the AI Enhancement Roadmap and integration plan for the 80-item backlog (`docs/20260222 YAM_AGRI_BACKLOG v1.csv`)
- Includes Yemen-specific design constraints (Section 20) and cross-references the Smart Farm Architecture (`docs/SMART_FARM_ARCHITECTURE.md`)
- Touchpoint apps blueprint: `docs/TOUCHPOINT_APP_BLUEPRINT.md` (9 apps, screen inventories, offline rules, build checklists)
- Deep persona profiles and customer journey maps: `docs/PERSONA_JOURNEY_MAP.md` (9 personas, 44 acceptance test scenarios)




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

## 17) Cross-Industry & Supply Chain Integration Reference

This section maps items from `docs/Integration Feature Inventory.csv` that are **directly relevant to YAM Agri**. The inventory covers 480 AI capabilities across 35 industries; three domains are particularly important for the cereal supply chain: **Agriculture**, **Food & Beverage**, and **Logistics & Transportation**.

> **How to use this section:** When a backlog item (Stage A–I) needs an AI capability listed here, reference the Feature no. when creating the GitHub Issue. The "Open-source providers" column in the CSV tells you which OSS tools to evaluate before committing to a commercial option.

---

### 17.1) Agriculture-Specific Integrations (Feature #91–100)

These features extend or complement the YAM Agri backlog items directly.

| Feature # | Sub-domain | Priority | Mandatory | Key OSS tools | Backlog link |
|-----------|-----------|----------|-----------|---------------|--------------|
| #91 | Crop disease detection (vision) | P1 | No | Qdrant, FAISS, OpenCV, LlamaIndex | AGR-CEREAL-029 |
| #92 | Yield forecasting | P2 | No | Ray, Trino, Grafana, Feast, Seldon | AGR-CEREAL-035, 040 |
| #93 | Precision irrigation control | P1 | No | Qdrant, Argo Workflows, Haystack, Ray | AGR-CEREAL-007, 030 |
| #94 | Soil health analytics | P2 | No | Rasa, Feast, Trino, PyTorch | AGR-CEREAL-037 |
| #95 | Farm equipment predictive maintenance | P2 | No | Milvus, Grafana, Prometheus, Haystack | AGR-CEREAL-045, 095 |
| #96 | Supply planning for agri-inputs | P2 | No | spaCy, Seldon, scikit-learn, Haystack | AGR-CEREAL-011, 096 |
| #97 | Livestock health monitoring | P2 | No | Weaviate, dbt, Rasa, Qdrant, Haystack | N/A (cereal-crop scope only) |
| #98 | Commodity price intelligence | P2 | No | Feast, spaCy, PyTorch, OpenTelemetry | AGR-CEREAL-075 |
| #99 | Traceability & provenance analytics | P2 | No | Ray, MLflow, Feast, Kafka, Kubeflow | AGR-CEREAL-071, 076 |
| #100 | Weather risk micro-forecasting | P1 | No | LangChain, Weaviate, TensorFlow, Ray | AGR-CEREAL-003, 100 |

**Implementation notes:**
- Feature #91 (Crop disease vision) and #93 (Precision irrigation) are P1 — implement alongside Stage C/D backlog items
- Feature #99 (Traceability & provenance analytics) maps directly onto the `EvidencePack` and `Transfer` DocTypes already in V1.1
- Feature #100 (Weather risk micro-forecasting) feeds the Observation DocType; use the IoT gateway introduced in Phase 5

---

### 17.2) Food & Beverage Integrations (Feature #191–200)

These are relevant because YAM Agri stores, processes, and ships cereal crops — the F&B compliance and quality features apply.

| Feature # | Sub-domain | Priority | Mandatory | Key OSS tools | Backlog link |
|-----------|-----------|----------|-----------|---------------|--------------|
| #191 | Demand forecasting | P2 | No | Seldon, FAISS, dbt, MLflow, Milvus | AGR-CEREAL-072 |
| #192 | Quality inspection (vision) | P1 | No | Argo Workflows, OpenCV, scikit-learn, spaCy | AGR-CEREAL-025, 029 |
| #193 | Recipe formulation optimization | P2 | No | Milvus, Grafana, Haystack, LlamaIndex | AGR-CEREAL-049, 068 |
| #194 | Shelf-life prediction | P2 | No | Kafka, Rasa, LlamaIndex, Feast | AGR-CEREAL-074 |
| **#195** | **Food safety compliance analytics** | **P0** | **Yes (HACCP/ISO 22000 certification requirement)** | Haystack, ONNX, Argo Workflows, spaCy, PyTorch | AGR-CEREAL-066 |
| #196 | Waste reduction optimization | P1 | No | PostgreSQL, Ray, FAISS, Hugging Face Transformers | AGR-CEREAL-049, 054 |
| #197 | Supply planning & procurement | P2 | No | Rasa, Milvus, spaCy, PyTorch, MLflow | AGR-CEREAL-011, 073 |
| #198 | Menu personalization | P1 | No | LangChain, Weaviate, PyTorch, Seldon, Ray | AGR-CEREAL-079 |
| #199 | Customer feedback sentiment | P1 | No | PostgreSQL, Feast, Ray, Argo Workflows | AGR-CEREAL-076 |
| #200 | Equipment maintenance prediction | P2 | No | dbt, Prometheus, Airflow, OpenCV | AGR-CEREAL-045, 065 |

**Implementation notes:**
- Feature **#195 (Food safety compliance analytics)** is P0/Mandatory — this is a direct complement to the HACCP evidence work in Phase 4 and the `EvidencePack` DocType
- Feature #192 (Quality inspection vision) requires an image ingestion pipeline; plan for V1.3+ using OpenCV
- Feature #194 (Shelf-life prediction) feeds directly into the Observation + Certificate expiry chain already in V1.1

---

### 17.3) Logistics & Transportation Integrations (Feature #61–70)

Cereal crops must move from farm → silo → store → customer; these features make that movement smarter and more traceable.

| Feature # | Sub-domain | Priority | Mandatory | Key OSS tools | Backlog link |
|-----------|-----------|----------|-----------|---------------|--------------|
| #61 | Route optimization | P2 | No | KServe, OpenTelemetry, dbt, PyTorch, scikit-learn | AGR-CEREAL-056 |
| #62 | ETA prediction | P2 | No | Weaviate, OpenTelemetry, Feast, Airflow, dbt | AGR-CEREAL-059 |
| #63 | Warehouse picking optimization | P2 | No | MLflow, Airflow, Kubeflow, scikit-learn, Feast | AGR-CEREAL-047, 054 |
| #64 | Last-mile delivery optimization | P1 | No | MLflow, ONNX, OpenTelemetry, Qdrant | AGR-CEREAL-056 |
| #65 | Fleet predictive maintenance | P2 | No | Weaviate, spaCy, FAISS, Airflow, PostgreSQL | AGR-CEREAL-045 |
| #66 | Cargo theft risk analytics | P1 | No | Kubeflow, FAISS, Qdrant, spaCy, Grafana | AGR-CEREAL-060 |
| #67 | Customs & trade compliance | P1 | No | Weaviate, dbt, PyTorch, Haystack, Argo Workflows | AGR-CEREAL-057, 067 |
| #68 | Demand forecasting for shipping | P1 | No | Weaviate, Kafka, Haystack, dbt, Trino | AGR-CEREAL-068, 072 |
| #69 | Document automation (BOL/invoices) | P2 | No | MLflow, Argo Workflows, Haystack, Ray, Prometheus | AGR-CEREAL-057 |
| #70 | Carbon footprint optimization | P1 | No | Grafana, Kubeflow, Hugging Face Transformers, dbt | AGR-CEREAL-061 |

**Implementation notes:**
- Feature #67 (Customs & trade compliance) and #69 (Document automation) both feed the `Export Docs Automation` backlog item (AGR-CEREAL-057) — implement together in V2.0
- Feature #70 (Carbon footprint optimization) supports the `Shipment Carbon Reporting` item (AGR-CEREAL-061); use Grafana for visualisation

---

## 18) Human-AI Interaction & UX Standards

The inventory defines 70 UX patterns (Feature #411–480) that apply to **every** AI-assisted feature in YAM Agri. These must be implemented before any AI feature goes to production, regardless of domain.

> Reference file: `docs/Integration Feature Inventory.csv` — Domain: "Human-AI Interaction & UX"

### 18.1) Mandatory UX patterns (P0 — must implement in every AI screen)

These 5 patterns are marked `Mandatory: Yes` in the inventory. They are non-negotiable for every AI feature deployed on the YAM Agri platform:

| Feature # | UX Pattern | Why it matters for YAM Agri | Key OSS tools |
|-----------|-----------|------------------------------|---------------|
| **#413** | **Human-in-the-loop approvals** | Every AI suggestion (lot accept/reject, dispatch, recall) requires a human approval step before any action | OpenTelemetry, LlamaIndex, Ray, Qdrant, Great Expectations |
| **#421** | **Source citation UX** | Users must see which data (sensor reading, QCTest, certificate) the AI used to make a suggestion | scikit-learn, TensorFlow, Prometheus, OpenCV, Ray |
| **#438** | **Privacy-first defaults** | PII, pricing, and customer IDs must be redacted before reaching the AI gateway | dbt, LlamaIndex, Rasa, Grafana, Milvus |
| **#439** | **Audit trail visibility** | All AI interactions must be logged and visible to the QA Manager | Haystack, Milvus, Airflow, PyTorch, scikit-learn |
| **#467** | **Tool permission consent dialogs** | Operators must explicitly grant permission before any AI tool accesses a DocType or external service | dbt, Feast, Ray, KServe, Milvus |

**Implementation rule:** Before any AI feature is released, all five patterns above must be verified in the acceptance test checklist.

---

### 18.2) High-priority UX patterns (P1 — implement by V1.2)

These patterns are recommended for all AI screens and should be in place before the first AI-enhanced release (V1.2):

| Feature # | UX Pattern | YAM Agri application |
|-----------|-----------|---------------------|
| #411 | Explainability panels | Show which sensor/QC data drove a suggestion on the Lot and EvidencePack screens |
| #423 | Error recovery flows | Graceful fallback when AI gateway is unavailable; system continues without AI |
| #424 | Bias & fairness disclosures | Visible notice on any screen where AI scores or ranks lots |
| #426 | Adaptive onboarding | Guide new operators through AI-assisted screens with inline tips |
| #427 | Guarded autonomy controls | Per-feature toggle to disable AI suggestions (admin/QA Manager only) |
| #429 | Context boundary indicators | Show clearly what time window and sites the AI analysis covers |
| #430 | Data sensitivity indicators | Flag when a suggestion was based on incomplete or quarantined Observation data |
| #440 | Escalation to human expert | One-click escalation to QA Manager when confidence is low |
| #446 | Domain glossary and term hints | Inline tooltips for agricultural/HACCP terminology in AI-generated text |
| #447 | Translation and locale switching | Arabic/English toggle for all AI output panels (Middle East operations) |
| #448 | Action confirmation for high-risk steps | Double-confirmation step before Execute-with-approval actions run |
| #457 | Personal data redaction previews | Show operator a preview of what will be redacted before sending to AI gateway |
| #458 | PII detection UX warnings | Visual warning banner if a prompt appears to contain unredacted PII |
| #473 | Hallucination detection flags | Show confidence score and flag low-confidence AI outputs in a different colour |
| #474 | Fallback to search/manual mode | Every AI panel must have a "do this manually" link |

---

### 18.3) UX implementation approach in Frappe

Since YAM Agri runs on Frappe, these UX patterns are implemented as:

1. **Frappe Form scripts** — client-side JavaScript that renders AI suggestion panels, approval buttons, and confidence scores on DocType forms
2. **Frappe Custom Print Formats** — for source citation and audit trail export on EvidencePacks
3. **Frappe Notification rules** — for PII detection warnings and action confirmation dialogs
4. **Frappe Workspace dashboards** — for explainability panels and UX telemetry
5. **AI Gateway middleware** — handles redaction, logging, fallback, and consent checks before any call reaches the LLM

**Design rule:** Every AI-assisted Frappe form must follow this layout:
```
[AI Suggestion Panel]
  ├─ Suggestion text (with confidence score)
  ├─ Source data citations (links to QCTest / Observation / Certificate records)
  ├─ Redaction preview (what was hidden from the AI)
  └─ Action buttons: [Approve] [Reject] [Escalate to QA Manager] [Do manually]
```

---

## 19) Local AI Marketplace Plan

The inventory defines 60 AI Marketplace & Ecosystem features (Feature #351–410). For YAM Agri, the strategy is to deploy a **private, local AI marketplace** on the existing Frappe stack — not a public cloud marketplace. This keeps data on-premise, within the Middle East data-residency requirements, and under YAM Agri's full control.

> Reference file: `docs/Integration Feature Inventory.csv` — Domain: "AI Marketplace & Ecosystem"

### 19.1) What "local AI marketplace" means for YAM Agri

A local AI marketplace is a **self-hosted catalog** of AI models, prompts, workflows, and data connectors that operators can browse, activate, and configure — without sending data to a third-party cloud.

**Architecture:**
```
Frappe (ERPNext + yam_agri_core)
    └── AI Gateway (local)
            ├── Model catalog  ←── local marketplace
            ├── Prompt & asset store
            ├── Tool/plugin registry
            ├── Usage metering & cost dashboard
            └── LLM backend (self-hosted: Ollama / vLLM / local LLaMA)
                    or redacted-proxy to cloud via AI Gateway middleware (see Section 18.3)
```

---

### 19.2) Mandatory marketplace features (P0 — must implement before any model goes to production)

| Feature # | Marketplace capability | Why mandatory | Key OSS tools |
|-----------|----------------------|---------------|---------------|
| **#361** | **Trust & safety policy engine** | Ensures every model meets YAM Agri's data governance and HACCP safe-use rules before activation | Prometheus, PyTorch, Feast, FAISS, spaCy |
| **#362** | **Identity & access federation** | Ties marketplace model access to Frappe user roles (QA Manager, Operator, Admin) | LangChain, Great Expectations, Rasa, Airflow, Grafana |
| **#363** | **Compliance evidence center** | Records which model version produced which AI suggestion, required for HACCP and ISO 22000 audits | Feast, KServe, Hugging Face Transformers, Kafka, Prometheus |
| **#365** | **Security scanning for assets** | Scans models and prompt packs for malicious content or data leakage risks before deployment | LlamaIndex, Trino, Kafka, Haystack, Weaviate, Milvus |

---

### 19.3) High-priority marketplace features (P1 — implement in V1.2–V2.0)

| Feature # | Marketplace capability | Priority | Key OSS tools |
|-----------|----------------------|----------|---------------|
| #353 | Provider onboarding | P1 | FAISS, Milvus, Kafka, dbt, Grafana, LangChain |
| #354 | Licensing & terms management | P1 | Hugging Face Transformers, Prometheus, MLflow, LangChain |
| #357 | Prompt & asset store | P1 | Prometheus, LlamaIndex, Qdrant, Airflow, spaCy |
| #358 | Tool/plugin registry | P1 | FAISS, Great Expectations, Rasa, PostgreSQL, Trino |
| #369 | Multi-model routing marketplace | P1 | dbt, Rasa, KServe, Great Expectations, Feast, PostgreSQL |
| #370 | Vector DB & retrieval offerings | P1 | Grafana, Airflow, LlamaIndex, PyTorch, Milvus, TensorFlow |
| #371 | Enterprise procurement workflows | P1 | PostgreSQL, Prometheus, spaCy, Seldon, Haystack, Feast |
| #374 | Model lineage & provenance | P1 | Trino, Argo Workflows, Haystack, Great Expectations, Milvus |
| #375 | AI app packaging & distribution | P1 | scikit-learn, Haystack, TensorFlow, Kafka, spaCy, Trino |
| #382 | Self-hosted deployment bundles | P2 | Prometheus, spaCy, Grafana, Qdrant, Hugging Face Transformers |
| #386 | Incident response coordination | P1 | Seldon, Qdrant, KServe, Ray, dbt, Haystack |
| #387 | Model evaluation attestations | P1 | PostgreSQL, Hugging Face Transformers, LangChain, Trino, Rasa |
| #389 | Cost benchmarking dashboard | P1 | Grafana, Kubeflow, Argo Workflows, Milvus, KServe, Haystack |
| #390 | Latency benchmarking dashboard | P1 | Seldon, OpenTelemetry, TensorFlow, Great Expectations, Kafka |
| #392 | Jurisdictional compliance packs | P1 | Prometheus, LangChain, OpenCV, Rasa, OpenTelemetry, ONNX |
| #394 | Marketplace API gateway | P1 | spaCy, PostgreSQL, ONNX, Ray, Haystack, OpenCV |
| #395 | Webhook/event integrations | P1 | Milvus, OpenTelemetry, Trino, KServe, Kafka |
| #407 | Workflow marketplace | P1 | spaCy, Weaviate, Prometheus, PostgreSQL, Airflow, Ray |
| #408 | Reference architectures library | P1 | scikit-learn, PyTorch, Prometheus, Seldon, KServe, Haystack |
| #409 | SDKs and CLI tooling | P1 | FAISS, Prometheus, LangChain, dbt, Milvus, Kubeflow |

---

### 19.4) Local marketplace deployment phases

| Phase | What gets deployed | When |
|-------|-------------------|------|
| **M1 — Catalog & Governance** | Model catalog (#351), Trust & safety policy engine (#361), Identity & access federation (#362), Compliance evidence center (#363), Security scanning (#365) | Alongside V1.2 |
| **M2 — Prompt & Tool Store** | Prompt & asset store (#357), Tool/plugin registry (#358), Licensing & terms mgmt (#354), Model lineage (#374) | V1.2–V1.3 |
| **M3 — Routing & Evaluation** | Multi-model routing (#369), Vector DB offerings (#370), Model evaluation attestations (#387), Cost & latency benchmarks (#389, #390) | V2.0 |
| **M4 — Full Self-service** | Workflow marketplace (#407), Agent template marketplace (#406), Blueprints for verticals (#405), SDKs & CLI (#409) | V2.1+ |

**Deployment rule:** The local marketplace **must be self-hosted** (on the same Kubernetes node as Frappe staging/production). No model or prompt data leaves the YAM Agri infrastructure perimeter without explicit operator consent and redaction.

---

### 19.5) Recommended OSS stack for the local AI marketplace

Based on the inventory's open-source provider recommendations across all three domains:

| Layer | Recommended OSS tools | Purpose |
|-------|----------------------|---------|
| LLM serving | KServe, Seldon, vLLM / Ollama | Host and serve local models |
| Vector store | Qdrant, Milvus, FAISS, Weaviate | Semantic search for model catalog and RAG |
| Workflow orchestration | Argo Workflows, Airflow | Model deployment and evaluation pipelines |
| Observability | Prometheus, Grafana, OpenTelemetry | Cost, latency, and usage dashboards |
| Data pipelines | dbt, Feast, Trino | Feature stores and data connectors |
| Model registry | MLflow | Track model versions, lineage, and evaluations |
| LLM framework | LangChain, LlamaIndex, Haystack | RAG, chains, agents |
| Data validation | Great Expectations | Input/output quality guardrails |
| NLP / embeddings | Hugging Face Transformers, spaCy | Local model inference |

---

---

## 20) Yemen Context — Design Constraints & Commitments

> **Full architecture details:** See `docs/SMART_FARM_ARCHITECTURE.md` for the complete 9-layer user stack, technology map, and Yemen adaptation guide.

YAM Agri operates in Yemen — a context with specific constraints that shape every technology and design decision. This section commits the platform to specific choices that address those constraints. These are **not optional**: a solution that works only with good internet and reliable power is not a solution for Yemen.

---

### 20.1) The Five Yemen Constraints

| Constraint | Impact on the platform |
|-----------|------------------------|
| **1. Unreliable / absent power** | All field sites run on solar PV + LiFePO₄ battery; low-power edge hardware only |
| **2. Poor rural connectivity** | 7-day offline operation required; sync-when-available; SMS as primary farmer input channel |
| **3. Arabic language primary** | All UI, AI output, alerts, and SMS must support Arabic/RTL from day one |
| **4. Low digital literacy** | PWA with icon-based navigation; AI copilot drafts text; SMS-based workflows for field farmers |
| **5. Water scarcity** | Irrigation Optimizer and groundwater monitoring are the highest-priority IoT + AI features |

---

### 20.2) Architecture Reference

The complete smart farm stack is documented in `docs/SMART_FARM_ARCHITECTURE.md`. It covers:

- **9 technology layers** from farm-edge sensors (Layer 1) to external integrations (Layer 9)
- **9 user personas** (Smallholder Farmer → External Auditor/Donor)
- **Frappe + ERPNext + OpenJiuwen** integration points with OSS alternatives for every component
- **OpenJiuwen AI Agent SDK** workflows with local Ollama fallback for offline operation
- **Yemen-specific decisions** for power, connectivity, localisation, data sovereignty, and water

---

### 20.3) Offline-First Rules (mandatory for all features)

1. Every Frappe form that a field user (U2, U3, U4) needs must work **without internet**
2. The PWA (Progressive Web App) must queue changes in PouchDB and sync when connectivity returns
3. Every AI feature must have a **"do this manually" fallback** — AI down = system still works
4. SMS data entry must cover at minimum: Lot creation, weight entry, and basic alerts
5. All backups must run **locally first**; cloud replication is secondary, not primary

---

### 20.4) Yemen Crop & Site Fixtures

Pre-load these as Frappe fixtures in `yam_agri_core`:

**Crops (Item types):**
- Sorghum / دُخن
- Wheat / قمح
- Millet / ذُرة
- Barley / شعير
- Corn / ذرة شامية

**Sites (governorates / typical locations):**
- Taiz (تعز) — highland farming
- Lahj (لحج) — coastal plain
- Abyan (أبين) — wadi agriculture
- Hodeidah / Hudaydah (الحديدة) — coastal grain hub
- Hadhramaut (حضرموت) — dryland farming

**Units of measure (add to ERPNext UoM):**
- Mudd (مُد) ≈ 1.5 kg (traditional)
- Kayl (كيل) ≈ 7.5 kg (traditional)
- Thumn (ثُمن) ≈ 60 kg (traditional sack)
- Quintal = 100 kg (modern standard)
- Metric Ton = 1,000 kg

#### Frappe fixture snippets (example)

Add these fixtures to your app so they are created on site install or when you reload fixtures.
Place the file at `apps/yam_agri_core/yam_agri_core/fixtures/yemen_fixtures.json` and commit it to the repo.

Example content (minimal fields shown — adapt to your DocType field names):

```json
{
  "Item": [
    {"item_code": "SORGHUM", "item_name": "Sorghum / دُخن", "item_group": "Products"},
    {"item_code": "WHEAT", "item_name": "Wheat / قمح", "item_group": "Products"},
    {"item_code": "MILLET", "item_name": "Millet / ذُرة", "item_group": "Products"},
    {"item_code": "BARLEY", "item_name": "Barley / شعير", "item_group": "Products"},
    {"item_code": "CORN", "item_name": "Corn / ذرة شامية", "item_group": "Products"}
  ],

  "Site": [
    {"site_name": "Taiz", "description": "Taiz (تعز) — highland farming"},
    {"site_name": "Lahj", "description": "Lahj (لحج) — coastal plain"},
    {"site_name": "Abyan", "description": "Abyan (أبين) — wadi agriculture"},
    {"site_name": "Hodeidah", "description": "Hodeidah (الحديدة) — coastal grain hub"},
    {"site_name": "Hadhramaut", "description": "Hadhramaut (حضرموت) — dryland farming"}
  ],

  "UOM": [
    {"uom_name": "Mudd", "symbol": "مُد", "conversion_factor_to_kg": 1.5},
    {"uom_name": "Kayl", "symbol": "كيل", "conversion_factor_to_kg": 7.5},
    {"uom_name": "Thumn", "symbol": "ثُمن", "conversion_factor_to_kg": 60},
    {"uom_name": "Quintal", "symbol": "Quintal", "conversion_factor_to_kg": 100},
    {"uom_name": "Metric Ton", "symbol": "t", "conversion_factor_to_kg": 1000}
  ]
}
```

How to import these fixtures (dev / bench container):

```bash
# copy the fixture into the app (host) and commit
# then, inside the bench/frappe container run one of:
# reload the app's doc definitions (will pick up fixtures defined in the app)
bench --site site1.local reload-doc yam_agri_core

# or use the UI: Setup → Data Import (import the JSON as needed)
```

Notes:
- Adjust the fixture keys/field names to match your custom DocTypes if you use custom fields.
- You can also export fixtures from a configured site using `bench export-fixtures` and then commit the generated JSON.

---

### 20.5) Water Monitoring (highest-priority Observation type)

Because over 90% of Yemen's water is used in agriculture and groundwater is rapidly depleting, the Observation DocType must include these signal types from V1.1:

| Signal type | Sensor / source | Alert threshold |
|-------------|----------------|----------------|
| Soil moisture (%) | Capacitive sensor | < 25% → irrigation alert |
| Borehole water level (m) | Ultrasonic level sensor | < critical depth → escalate |
| Irrigation flow rate (L/min) | Flow meter | > expected by 20% → leak alert |
| Rainfall (mm) | Rain gauge / Open-Meteo | > 20 mm/day → flood risk alert |
| Reservoir level (%) | Float sensor | < 30% → ration alert |

---

### 20.6) What This Means for the Build Order

Revised build priority for Yemen context:

1. ✅ V1.1 core (as planned) — but **add offline PWA and Arabic fixtures from sprint 1**
2. ✅ Field Hub deployment guide (`docs/runbooks/field-hub-setup.md`) before any site goes live
3. ✅ SMS data entry handler (Layer 6) — before any farmer training
4. ✅ Water Observation alerts (layer 1+5) — first sensor type to go live
5. ✅ Arabic UI validation by a native Arabic speaker before V1.1 UAT
6. 🔜 V1.2: Irrigation Optimizer AI (AGR-CEREAL-030) + Mycotoxin Risk Flags (AGR-CEREAL-043)

---

---

## 21) Touchpoints & Persona Reference Map

This section connects every user to their app, their journey, and their test scenarios. It is the single-table entry point to navigate the three companion documents.

| # | Persona | Touchpoint app | App blueprint | Journey map | Test scenarios |
|---|---------|---------------|--------------|-------------|---------------|
| U1 | Smallholder Farmer | TP-01 FarmerSMS | §2 TOUCHPOINT_APP_BLUEPRINT | §U1 PERSONA_JOURNEY_MAP | U1-T01 → T06 |
| U2 | Farm Supervisor | TP-02 FieldPWA | §3 TOUCHPOINT_APP_BLUEPRINT | §U2 PERSONA_JOURNEY_MAP | U2-T01 → T05 |
| U3 | QA Inspector | TP-03 InspectorApp | §4 TOUCHPOINT_APP_BLUEPRINT | §U3 PERSONA_JOURNEY_MAP | U3-T01 → T05 |
| U4 | Silo Operator | TP-04 SiloDashboard | §5 TOUCHPOINT_APP_BLUEPRINT | §U4 PERSONA_JOURNEY_MAP | U4-T01 → T05 |
| U5 | Logistics Coordinator | TP-05 LogisticsApp | §6 TOUCHPOINT_APP_BLUEPRINT | §U5 PERSONA_JOURNEY_MAP | U5-T01 → T05 |
| U6 | Agri-Business Owner | TP-06 OwnerPortal | §7 TOUCHPOINT_APP_BLUEPRINT | §U6 PERSONA_JOURNEY_MAP | U6-T01 → T04 |
| U7 | System Admin | TP-07 AdminPanel | §8 TOUCHPOINT_APP_BLUEPRINT | §U7 PERSONA_JOURNEY_MAP | U7-T01 → T04 |
| U8 | External Auditor/Donor | TP-08 AuditorPortal | §9 TOUCHPOINT_APP_BLUEPRINT | §U8 PERSONA_JOURNEY_MAP | U8-T01 → T04 |
| U9 | AI Copilot | TP-09 AICopilotPanel | §10 TOUCHPOINT_APP_BLUEPRINT | §U9 PERSONA_JOURNEY_MAP | U9-T01 → T07 |

### How the three companion documents relate

```
BLUEPRINT_PLAYBOOK_BEGINNER.md    ←  master playbook (this file)
    │
    ├── SMART_FARM_ARCHITECTURE.md  ← 11-layer technology stack
    │       ├── Layer 10: Touchpoints summary table
    │       └── Layer 11: Persona summary table
    │
    ├── TOUCHPOINT_APP_BLUEPRINT.md ← build blueprint per app
    │       ├── Screen inventories
    │       ├── Technology choices + OSS alternatives
    │       ├── Offline rules
    │       ├── Build checklists (GitHub Issues)
    │       └── Acceptance tests per app
    │
    └── PERSONA_JOURNEY_MAP.md     ← deep persona profiles
            ├── Profile cards (9 personas)
            ├── Customer journey maps (6 stages each)
            ├── Pain points & delight moments
            ├── Yemen-specific context
            ├── Acceptance test scenarios (44 total)
            └── Cross-persona journey: a grain lot through all 9 personas
```

### Master acceptance test count

| Priority | Tests | When they must pass |
|----------|-------|-------------------|
| P0 | U1-T01–T06, U2-T01–T05, U3-T01–T05, U9-T01–T07 (23 tests) | Before V1.1 release |
| P1 | U4-T01–T05, U5-T01–T05, U6-T01–T04, U7-T01–T04 (18 tests) | Before V1.2 release |
| P2 | U8-T01–T04 (4 tests) | Before V2.0 release |

---

---

## What changed vs the earlier blueprint

- Added **Owner's Vision & Business Purpose** section (Section 0)
- Added explicit **AI Enhancement Roadmap** with release phases V1.1 → V2.1+ (Section 12)
- Added **Backlog Integration Plan** with stage-by-stage tables for all 80 items (Stages A–I) (Section 13)
- Fixed all **markdown formatting** inconsistencies (headings, code blocks, lists)
- Updated **Work queue** to reference specific backlog IDs and release phases (Section 14)
- Clarified **Frappe+ERPNext as the permanent base layer** for all AI features
- Reinforced the **safe, assistive-only AI** principle with action-mode detail for every backlog item
- Added **Cross-Industry & Supply Chain Integration Reference** (Section 17) — Agriculture, Food & Beverage, and Logistics items from the Integration Feature Inventory, mapped to backlog IDs
- Added **Human-AI Interaction & UX Standards** (Section 18) — 5 mandatory and 15 high-priority UX patterns from the inventory, with Frappe implementation guidance
- Added **Local AI Marketplace Plan** (Section 19) — 4-phase deployment plan for a private, self-hosted AI marketplace on the Frappe/k3s stack, with mandatory governance features and OSS stack recommendations
- Committed `docs/Integration Feature Inventory.csv` (480 items) to the repository as the authoritative integration reference
- Added **Yemen Context section** (Section 20) — five design constraints, offline-first rules, Yemen crop/site fixtures, water monitoring priorities, and revised build order
- Created `docs/SMART_FARM_ARCHITECTURE.md` — 11-layer user stack architecture (added Layer 10: Touchpoints and Layer 11: Persona/Journey Map to the previous 9 layers)
- Created `docs/TOUCHPOINT_APP_BLUEPRINT.md` — build blueprint for all 9 touchpoint apps with screen inventories, offline rules, and build checklists
- Created `docs/PERSONA_JOURNEY_MAP.md` — deep persona profiles and customer journey maps for all 9 personas with 44 acceptance test scenarios
- Added Section 21 — Touchpoints & Persona Reference Map with master test count and doc relationship diagram

---

## Next steps

1. Finish V1.1 foundation (Phases 0–6 above)
2. Run all 10 acceptance tests in Section 11 in staging
3. Then pick the first V1.2 items from Stage D/E/F backlog — start with `AGR-CEREAL-038`, `AGR-CEREAL-039`, and `AGR-CEREAL-043`
4. Before any AI feature goes live, implement the 5 mandatory UX patterns from Section 18.1 (Features #413, #421, #438, #439, #467)
5. Deploy the M1 Local AI Marketplace (Section 19.4) alongside V1.2 — this is the governance foundation for all AI models
6. Use `docs/Integration Feature Inventory.csv` as the reference when selecting OSS tools for each backlog feature
7. Create a GitHub Issue for each backlog item as you approach its release phase
8. Both CSVs are the source of truth: `docs/20260222 YAM_AGRI_BACKLOG v1.csv` for what to build, `docs/Integration Feature Inventory.csv` for how to build it with the right tools
9. Read `docs/SMART_FARM_ARCHITECTURE.md` before designing any new Layer 1–3 component — it defines the Yemen-specific hardware, power, and connectivity decisions that cannot be changed later
10. Use `docs/TOUCHPOINT_APP_BLUEPRINT.md` as the build reference for any touchpoint app — all screens, build checklists, and per-app acceptance tests are there
11. Use `docs/PERSONA_JOURNEY_MAP.md` as the test reference — run U1-T01 through U9-T07 to validate every release; P0 tests must pass before V1.1 ships
