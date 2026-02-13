
Below is a beginner-friendly, repo-ready version of the “YAM Agri Platform Blueprint Playbook (Detailed)”, updated for your new setup:

- Restarting clean on a new machine
- Track A: Docker Compose first (Dev), Kubernetes later (Staging)
- You’re not a coder, so everything is written as “do this, expect that”
- Includes folder structure, scripts, acceptance checks, and issue list
- Uses your chosen standards: FAO GAP (Middle East) + HACCP/ISO 22000 mindset
- Includes your real-world scenario: 5 locations + office + stores + refrigerators
- Assumes you are using Frappe + ERPNext + Frappe Agriculture app





# YAM Agri Platform Blueprint Playbook (Beginner-Friendly)

## 0) What we are building (V1.1)
**V1.1 = Quality + Traceability Core**

The product helps YAM agri co. manage cereal-crop supply chain quality from storage to customer:
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
Create this structure in the GitHub repo:



yam-agri-platform/
apps/
yam_agri_core/ # Frappe custom app (DocTypes, workflows, reports)
services/
iot_gateway/ # sensor ingest + normalize into Observation
scale_connector/ # scale ticket ingest (CSV first, API later)
ai_gateway/ # redaction + routing to cloud LLM (hybrid)
remote_sensing/ # later: satellite/indices ingestion
infra/
docker/ # dev stack (compose)
k8s/ # staging manifests (later)
docs/
policies/ # FAO GAP mapping, HACCP control points, season policy matrix
runbooks/ # how to operate, reset, troubleshoot


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


You should be able to open the web UI.

If you see a login page: good.

Exit criteria (Dev runtime is done)

Docker stack starts without fatal errors

You can open the login page

ERPNext + Agriculture app appear in installed apps after init

4) Phase 1: Create Frappe custom app (yam_agri_core)
Goal

Create a custom app where our DocTypes and workflows live.

Steps (operator/Codex does this)

Create yam_agri_core

Install it on the dev site

Commit generated app into /apps/yam_agri_core

Exit criteria

yam_agri_core appears in the site’s installed apps list

5) Phase 2: Core data model (DocTypes) - V1.1 foundation
Goal

Create the minimum system-of-record for traceability and QA/QC evidence.

DocTypes we need (V1.1)

Multi-site / Structure

Site (farm/silo/store/office)

StorageBin

Device

Traceability

Lot (harvest/storage/shipment)

Transfer (split/merge/blend)

ScaleTicket

QA/QC + Compliance

QCTest

Certificate

Nonconformance (CAPA)

EvidencePack

Complaint

Evidence signals

Observation (universal model for sensor + derived signals)

Non-negotiable rules

Every record belongs to a Site

Users should NOT see other sites by default

High-risk actions require approval (QA Manager)

Exit criteria

You can create: Site, StorageBin, Lot, Transfer, QCTest, Certificate

A Site-A user cannot see Site-B records

6) Phase 3: Traceability engine (splits, merges, blends)
Goal

Trace backward and forward across transfers.

What we build

Trace Backward:

From shipment lot → upstream lots → bins → QC tests → certificates

Trace Forward:

From storage lot → downstream shipments → blast radius quantities

Enforcement

Mass-balance rules:

Outgoing quantity must not exceed available quantity (with tolerance)

Exit criteria

Trace backward works and shows evidence

Trace forward works and shows impacted shipments and quantities

Export to CSV/PDF

7) Phase 4: QA/QC controls (FAO GAP + HACCP / ISO 22000)
Goal

Build control points with automation levels for best ROI.

Control point automation levels

MUST automate (blocking, high risk, cheap ROI)

SHOULD semi-automate (system helps; humans execute/approve)

OK manual (structured checklist + evidence)

MUST automate in V1.1

Scale weight verification + mismatch flags

Certificate expiry checks (block dispatch if expired unless override)

High-risk season mycotoxin gating (block dispatch until passed)

Refrigerator temperature monitoring in stores (alert + corrective action record)

Recall initiation workflow (trace forward + evidence pack, approvals required)

SHOULD semi-automate

Auto-create QC tasks for new lots

Hotspot detection → Nonconformance + suggested action (approval required)

OK manual (still tracked)

Visual inspection checklists with photo attachments

Exit criteria

Shipment is blocked if required QC/cert missing for that product/season policy

CAPA workflow exists and is auditable

8) Phase 5: Integrations (Scales + Sensors)
Goal

Bring real evidence into the system.

ScaleConnector (start simple)

CSV import into ScaleTicket

Map ticket → Lot quantity

Flag mismatches → Nonconformance

IoT Gateway (universal observation model)

Observation supports:

Bins: temp, humidity, moisture, CO2

Stores: refrigerator temperature

Weather: rainfall, humidity

Irrigation telemetry: flow, valve state

Remote sensing derived indices: NDVI, flood risk

Rules:

Validate units

Range checks

Quarantine suspect data (quality_flag), don’t use it for automation

Exit criteria

Real scale ticket updates lot quantities

Real sensor reading attaches to correct bin/site and triggers alerts if out-of-range

9) Phase 6: Hybrid AI (assist only, safe by design)
Goal

Use cloud LLM without leaking data and without autonomy.

AI Gateway rules

Redact sensitive data (PII, pricing, customer IDs)

Send only minimal context

Log hashes + record references

Have fallback behavior (AI down = system still works)

AI functions allowed in V1.1

“What’s missing for compliance on this lot?”

Summarize nonconformance and draft corrective action checklist

Summarize evidence pack / audit narrative

Not allowed in V1.1

No automatic accept/reject lots

No automatic recalls

No customer communications without approval

Exit criteria

AI suggestions are always auditable and never execute actions

10) Staging (Kubernetes) - only after Dev works
Goal

Deploy a production-like stack on your new machine using k3s.

Why later?

Because Kubernetes adds complexity. We only do it once the app works in Compose.

Plan

Use k3s single node

Install Ingress (Traefik default is fine)

Persistent volumes for DB and files

Deploy Frappe stack first, then services

Exit criteria

kubectl shows node Ready

Frappe is reachable via ingress

UAT runs in staging without dev shortcuts

11) Acceptance tests (how YAM approves without coding)
Must-pass scenarios

Create Site + StorageBin + Lot

Create QCTest + attach Certificate

Transfer: split lot → shipment lot

Trace backward from shipment lot (shows QC/certs/bin history)

Trace forward from storage lot (blast radius)

Block shipment when mandatory QC/cert missing (season policy)

Import ScaleTicket CSV updates quantities + flags mismatch

Post sensor Observation; invalid data is quarantined

EvidencePack generated for a date range + site

Site isolation: Site A user can’t see Site B data

12) Work queue (GitHub Issues template)

Create issues in this order:

Dev runtime: infra/docker compose + init scripts

Create yam_agri_core app + install

Implement V1.1 DocTypes + site permissions

Trace backward/forward UI + export

QA/QC control points + CAPA workflow + evidence packs

Scale connector CSV import + reconciliation

IoT gateway observation ingest + validation/quarantine

Hybrid AI gateway (redaction + logs + fallback)

13) What you should NOT do (to avoid downtime)

Don’t start with Kubernetes before dev works

Don’t integrate 20 sensor vendors at once

Don’t let AI execute risky actions in V1.1

Don’t commit secrets to GitHub

14) Owner/operator responsibilities

YAM (Product Owner): approve workflows, policies, UAT results

Operator/Dev: run commands, fix environment issues, implement tasks

QA Manager: defines approvals, signs off on controls

End.

---

## What changed vs your earlier blueprint (so you don’t get lost)
- Explicit “**restart on new machine**” flow
- Dev = **Compose**, Staging = **k3s later**
- More “**beginner**” language and proof checks
- Adds “**what NOT to do**” and acceptance tests as your control mechanism
- Integrations explained using **universal observation model** (sensors + satellite + weather + irrigation)

---

## Next: add it to GitHub (quick)
1) Create file: `docs/BLUEPRINT_PLAYBOOK_BEGINNER.md`
2) Paste content
3) Commit message:
   - `docs: add beginner blueprint playbook`

No more planning documents required before building.
