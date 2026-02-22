# Touchpoint App Blueprint — YAM Agri Platform

> **Purpose:** Define every app surface (touchpoint) that a user interacts with in the YAM Agri platform, including the build blueprint, screen inventory, offline rules, and OSS alternatives for each.  
> **Context:** Yemen — solar-powered, offline-first, Arabic/RTL-first, assistive-AI only  
> **Related docs:**  
> - `docs/SMART_FARM_ARCHITECTURE.md` — 11-layer technology stack (this file covers Layer 10)  
> - `docs/PERSONA_JOURNEY_MAP.md` — deep persona profiles and journey maps  
> - `docs/BLUEPRINT_PLAYBOOK_BEGINNER.md` — overall platform playbook

---

## 0) What is a Touchpoint App?

A **touchpoint app** is the UI surface through which a specific persona interacts with the YAM Agri platform. Each touchpoint:

- Is built for **one primary persona** (but may serve secondary personas)
- Uses the **Frappe REST/RPC API** as its data backbone
- Must have an **offline fallback** mode appropriate to its persona's connectivity
- Must display AI suggestions using the **standard AI Suggestion Panel** (Section 18.3 of the Blueprint)
- Must support **Arabic/RTL and English** bilingual display

There are **9 touchpoint apps** corresponding to the 9 platform personas.

---

## 1) Touchpoint App Overview

| App ID | App name | Primary persona | Channel | Offline support | Arabic |
|--------|---------|----------------|---------|----------------|--------|
| **TP-01** | **FarmerSMS** | U1 Smallholder Farmer | SMS / USSD | ✅ 100% offline | ✅ Required |
| **TP-02** | **FieldPWA** | U2 Farm Supervisor | Mobile PWA | ✅ 7-day queue | ✅ Required |
| **TP-03** | **InspectorApp** | U3 QA / Food Safety Inspector | Tablet PWA + Frappe Desk | ⚠️ Partial (Wi-Fi) | ✅ Required |
| **TP-04** | **SiloDashboard** | U4 Silo / Store Operator | Desktop Frappe Desk | ⚠️ On-premise LAN | ✅ Required |
| **TP-05** | **LogisticsApp** | U5 Logistics Coordinator | Mobile PWA + map | ⚠️ 4G for maps | ✅ Required |
| **TP-06** | **OwnerPortal** | U6 Agri-Business Owner | Web dashboard | ❌ Broadband | ✅ Required |
| **TP-07** | **AdminPanel** | U7 System Admin | Frappe Desk + CLI | ❌ Server access | EN primary |
| **TP-08** | **AuditorPortal** | U8 External Auditor / Donor | Read-only web | ❌ Internet | EN/AR toggle |
| **TP-09** | **AICopilotPanel** | U9 AI Copilot (embedded) | Embedded in all apps | ✅ Local fallback | ✅ Required |

---

## 2) TP-01 — FarmerSMS (Smallholder Farmer Touchpoint)

### Purpose
Allow U1 farmers with only a feature phone to report lot data, receive alerts, and get basic guidance — all via SMS without any app installation.

### Technology
| Component | Primary | OSS alternative |
|-----------|---------|----------------|
| SMS API | Africa's Talking | RapidPro (OSS), Gammu |
| Message parser | Python keyword parser (FastAPI webhook) | RapidPro flow engine |
| Data storage | Frappe Lot / ScaleTicket DocTypes via REST | Same |
| Alert delivery | Africa's Talking outbound SMS | Twilio (more expensive) |
| AI suggestions | Pre-generated SMS-length Arabic text from CopilotAgent | Static rule-based texts |

### SMS Command Design
All commands use Arabic-first keywords with English aliases:

```
INCOMING SMS COMMANDS (farmer → system):
  وزن [رقم_الكمية] [وحدة]     → create ScaleTicket draft
  وزن 500 كيلو                 → weight 500 kg
  LOT [crop] [quantity] [unit] → create Lot (English alias)
  حصاد قمح 2000 كيلو           → harvest lot: wheat 2000 kg
  حالة                         → request status summary of my lots
  STATUS                       → same (English alias)
  مساعدة                        → send help menu
  HELP                         → same (English alias)

OUTGOING SMS ALERTS (system → farmer):
  تحذير: رطوبة التربة منخفضة [الموقع]  → soil moisture alert
  تنبيه: موعد الري [الموقع]             → irrigation reminder
  تأكيد: تم تسجيل الوزن [الرقم]         → weight confirmation
  طلب: مراجعة الشحنة [الرقم] مطلوبة    → approval request
```

### Screens / Flows
Since SMS has no "screens", the touchpoint is a **conversation flow**:

```
Farmer sends SMS
      │
      ▼
[Africa's Talking webhook → FastAPI]
      │
      ▼
[Keyword parser]
      ├── Recognised → Create/update Frappe DocType → Confirm SMS
      └── Unrecognised → Send help menu in Arabic
```

### Build checklist (GitHub Issues)
- [ ] `SMS-01` Setup Africa's Talking webhook in FastAPI
- [ ] `SMS-02` Implement Arabic keyword parser (weight, lot, status, help)
- [ ] `SMS-03` Frappe REST integration: create ScaleTicket from SMS
- [ ] `SMS-04` Frappe REST integration: create Lot draft from SMS
- [ ] `SMS-05` Outbound alerts: soil moisture, irrigation reminder, approval request
- [ ] `SMS-06` Arabic message templates (bilingual AR/EN)
- [ ] `SMS-07` Rate limiting + fraud prevention (max 20 SMS/day per sender)
- [ ] `SMS-08` Test with actual Africa's Talking sandbox in Yemen numbers

### Acceptance tests
1. Farmer sends `وزن 500 كيلو` → ScaleTicket created with quantity=500, unit=kg, status=Draft
2. Farmer sends `حالة` → receives Arabic SMS listing their last 3 lots
3. Unrecognised message → Arabic help menu returned within 10 seconds
4. Soil moisture drops below 25% → farmer receives Arabic alert SMS within 5 minutes

---

## 3) TP-02 — FieldPWA (Farm Supervisor Touchpoint)

### Purpose
Allow U2 farm supervisors to manage lots, crew, field tasks, and sensor data from an Android tablet — even when offline for up to 7 days.

### Technology
| Component | Primary | OSS alternative |
|-----------|---------|----------------|
| App shell | Frappe PWA (built-in) + custom Frappe app pages | React Native, Flutter |
| Offline storage | PouchDB (browser IndexedDB) | Service Worker Cache API |
| Sync engine | Frappe offline queue + PouchDB → MariaDB sync | CouchDB replication |
| Maps (offline) | Leaflet.js + offline OSM tiles (MBTiles) | Google Maps (no offline) |
| Camera | Browser getUserMedia → photo attachment | Native Android camera |
| Barcode scanner | ZXing-js (browser) | Native Android scanner |
| AI suggestions | CopilotAgent via local Ollama (Field Hub) | Static rule-based |
| Push notifications | Web Push API (ntfy.sh self-hosted) | Firebase FCM |

### Screen Inventory

| Screen ID | Screen name | Purpose | Offline? |
|-----------|------------|---------|---------|
| FP-01 | **Home / Dashboard** | Today's tasks, alerts, lot summary | ✅ |
| FP-02 | **Lot List** | Browse, filter, search lots | ✅ |
| FP-03 | **Lot Detail** | View lot: crop, qty, location, QC, transfers | ✅ |
| FP-04 | **New Lot** | Create harvest/storage lot with photo + GPS | ✅ |
| FP-05 | **Weight Entry** | Enter scale ticket (manual or CSV) | ✅ |
| FP-06 | **Transfer** | Split / merge / blend lots | ✅ queue |
| FP-07 | **Field Map** | Lot locations on OSM offline map | ✅ (cached tiles) |
| FP-08 | **Crew Schedule** | View/assign crew to tasks | ✅ |
| FP-09 | **Sensor Readings** | Latest bin/field sensor values | ✅ (last cached) |
| FP-10 | **AI Suggestion Panel** | Embedded CopilotAgent suggestions | ✅ (local Ollama) |
| FP-11 | **Sync Status** | Show pending changes, last sync time | ✅ |

### Offline rules
1. All screens FP-01 to FP-09 must work with **zero network** using cached data
2. Create/edit actions queue in PouchDB; sync automatically when Wi-Fi or 4G available
3. Conflict detection: if server has newer version, show diff and ask user to resolve
4. AI suggestions use local Ollama on the Field Hub via LAN; fallback to static rules if Ollama unavailable

### Build checklist
- [ ] `FP-01` Bootstrap Frappe PWA with offline manifest and Service Worker
- [ ] `FP-02` PouchDB integration: sync Lot, ScaleTicket, Transfer, Observation DocTypes
- [ ] `FP-03` Offline map: download OSM tiles for Yemen governorates as MBTiles
- [ ] `FP-04` GPS capture on Lot create (browser Geolocation API)
- [ ] `FP-05` Photo attachment (base64 → MinIO upload when online)
- [ ] `FP-06` Barcode scan for lot ID (ZXing-js)
- [ ] `FP-07` AI Suggestion Panel component (Arabic/English toggle)
- [ ] `FP-08` Push notification subscription (ntfy.sh)
- [ ] `FP-09` Arabic RTL layout + Hijri date toggle
- [ ] `FP-10` End-to-end offline test: 7-day no-network scenario

### Acceptance tests
1. Create a Lot with photo + GPS while airplane mode is on → lot appears in list immediately
2. After 7 days offline, reconnect → all 7 days of queued changes sync to server without data loss
3. Soil moisture alert arrives as push notification while app is in background
4. Map shows all farm lots with offline OSM tiles when no internet

---

## 4) TP-03 — InspectorApp (QA / Food Safety Inspector Touchpoint)

### Purpose
Allow U3 inspectors to conduct QC tests, complete HACCP checklists, issue certificates, and generate evidence packs — on tablet or laptop with partial offline support.

### Technology
| Component | Primary | OSS alternative |
|-----------|---------|----------------|
| App shell | Frappe Desk (mobile-responsive) + custom page | React-based custom UI |
| Checklist engine | Custom Frappe DocType: `HACCPChecklist` | Google Forms (no audit trail) |
| Photo evidence | Camera + MinIO upload | Local SD card + sync |
| Certificate PDF | Frappe Print Format (Jinja2 + WeasyPrint) | Puppeteer headless Chrome |
| Digital signature | Frappe Sign / canvas signature widget | DocuSign (costly) |
| AI assist | ComplianceAgent: "What's missing for this lot?" | Static checklist review |
| Barcode / QR | ZXing-js (browser) | Honeywell scanner (hardware) |

### Screen Inventory

| Screen ID | Screen name | Purpose | Offline? |
|-----------|------------|---------|---------|
| IA-01 | **QCTest Form** | Enter test results (moisture, protein, aflatoxin…) | ⚠️ Wi-Fi |
| IA-02 | **HACCP Checklist** | Step-by-step control point checklist + photo | ⚠️ Wi-Fi |
| IA-03 | **Certificate Issue** | Generate + sign certificate for a lot | ⚠️ Wi-Fi |
| IA-04 | **Nonconformance** | Log CAPA + corrective action | ⚠️ Wi-Fi |
| IA-05 | **Evidence Pack** | Assemble pack for a date range + site | ⚠️ Wi-Fi |
| IA-06 | **AI Compliance Check** | "What's missing?" AI suggestion panel | ⚠️ Wi-Fi; local fallback |
| IA-07 | **Lot Trace View** | Trace backward/forward from a lot | ⚠️ Wi-Fi |
| IA-08 | **Certificate Expiry Dashboard** | List expiring certs by crop/site | ⚠️ Wi-Fi |

### HACCP Checklist DocType design
```
HACCPChecklist
├── lot (Link → Lot)
├── site (Link → Site)
├── inspector (Link → User)
├── inspection_date (Date)
├── items (Table → HACCPChecklistItem)
│     ├── control_point (Select: CCP1..CCP8)
│     ├── parameter (Data)
│     ├── measured_value (Float)
│     ├── limit_min (Float)
│     ├── limit_max (Float)
│     ├── status (Select: Pass / Fail / N/A)
│     ├── corrective_action (Text)
│     └── photo (Attach)
└── ai_summary (Text — AI-generated narrative, read-only)
```

### Build checklist
- [ ] `IA-01` HACCPChecklist DocType + form with photo attach
- [ ] `IA-02` ComplianceAgent integration: suggest missing items after QC save
- [ ] `IA-03` Certificate Print Format (bilingual AR/EN, WeasyPrint)
- [ ] `IA-04` Digital signature widget on Certificate DocType
- [ ] `IA-05` EvidencePack generator: bundle QCTests + Certificates + Observations → PDF
- [ ] `IA-06` Lot trace backward/forward UI with visual graph
- [ ] `IA-07` Certificate expiry alert + dashboard widget
- [ ] `IA-08` AI summary auto-populate on EvidencePack (SummaryAgent)

### Acceptance tests
1. Create QCTest with aflatoxin value above limit → Nonconformance auto-created
2. AI Compliance Check returns missing items for an incomplete lot in < 5 seconds
3. Certificate PDF renders correctly in Arabic RTL layout
4. Evidence pack generates and downloads within 30 seconds for a 1-month date range

---

## 5) TP-04 — SiloDashboard (Silo / Store Operator Touchpoint)

### Purpose
Allow U4 operators to monitor bin sensors, manage scale tickets, reconcile stock, and respond to alerts from a desktop workstation on the local site LAN.

### Technology
| Component | Primary | OSS alternative |
|-----------|---------|----------------|
| App shell | Frappe Desk (desktop) | Custom React dashboard |
| Real-time sensor | Frappe WebSocket + InfluxDB live feed | Node-RED dashboard |
| Scale ticket import | CSV drag-and-drop + bulk import | Barcode scanner integration |
| Alerts | Frappe Notification + ntfy.sh | PagerDuty (costly) |
| Bin visualisation | SVG bin map (custom Frappe page) | Grafana dashboard |
| AI alerts | AnomalyAgent: hotspot detection | Static threshold rules |

### Screen Inventory

| Screen ID | Screen name | Purpose | Offline? |
|-----------|------------|---------|---------|
| SD-01 | **Bin Monitor** | Real-time sensor grid for all bins | ⚠️ LAN (InfluxDB) |
| SD-02 | **Scale Ticket Import** | Drag-drop CSV → bulk ScaleTicket create | ⚠️ LAN |
| SD-03 | **Stock Reconciliation** | Compare physical vs ERP stock | ⚠️ LAN |
| SD-04 | **Alert Centre** | All active alerts ranked by severity | ⚠️ LAN |
| SD-05 | **Lot Movement Log** | In/out lot transfers for today | ⚠️ LAN |
| SD-06 | **AI Anomaly Panel** | Sensor hotspot suggestions from AnomalyAgent | ⚠️ LAN; local fallback |
| SD-07 | **Aeration Control** | Manual/auto aeration schedule (approval required) | ⚠️ LAN |

### Bin Monitor SVG Design
Each storage bin is represented as a colour-coded SVG rectangle:
- 🟢 Green: all sensors within normal range
- 🟡 Yellow: one parameter near threshold (warn)
- 🔴 Red: one parameter out of range (alert)
- ⬜ Grey: sensor offline / no reading for >1 hour

Click on bin → drill-down panel with time-series chart (InfluxDB → Frappe page)

### Build checklist
- [ ] `SD-01` InfluxDB → Frappe WebSocket bridge for live sensor feed
- [ ] `SD-02` SVG bin visualisation page (custom Frappe Web Page or Desk page)
- [ ] `SD-03` CSV bulk import for ScaleTickets with mismatch flagging
- [ ] `SD-04` Stock reconciliation report: physical vs ERP with diff highlighting
- [ ] `SD-05` Alert ranking page using AnomalyAgent output
- [ ] `SD-06` Aeration control DocType with approval workflow
- [ ] `SD-07` ntfy.sh push + browser notification for critical alerts
- [ ] `SD-08` Grafana dashboard embed (iframe in Frappe) for historical trends

### Acceptance tests
1. Bin temperature exceeds 35°C → red alert appears on bin map within 60 seconds
2. CSV import of 100 scale tickets completes in < 30 seconds with mismatch report
3. Aeration control button → approval request sent to QA Manager before execution
4. AI anomaly panel correctly identifies the hotspot bin from synthetic test data

---

## 6) TP-05 — LogisticsApp (Logistics Coordinator Touchpoint)

### Purpose
Allow U5 coordinators to plan shipments, dispatch trucks, track in-transit cargo, and manage customs documents from a mobile device.

### Technology
| Component | Primary | OSS alternative |
|-----------|---------|----------------|
| App shell | Mobile PWA (Frappe + custom pages) | React Native |
| Maps | Leaflet.js + OpenStreetMap (offline tiles) | Google Maps |
| Route optimisation | AI agent (AGR-CEREAL-056) → propose | OR-Tools (OSS) |
| Document automation | AI agent (AGR-CEREAL-057) → draft BOL/invoice | Pandoc + Jinja2 templates |
| GPS tracking | Browser Geolocation API + Frappe Observation | Traccar (OSS) |
| Carbon calc | OpenGHG formulae in Python service | Scope 3 spreadsheet |

### Screen Inventory

| Screen ID | Screen name | Purpose | Offline? |
|-----------|------------|---------|---------|
| LA-01 | **Shipment List** | All active shipments with status | ⚠️ 4G |
| LA-02 | **Shipment Detail** | Lot, quantity, documents, ETA | ⚠️ 4G |
| LA-03 | **Route Map** | Live truck position + planned route | ❌ Live 4G |
| LA-04 | **New Shipment** | Create dispatch from lot selection | ⚠️ 4G |
| LA-05 | **Document Pack** | Generate BOL, COO, phytosanitary cert | ⚠️ 4G |
| LA-06 | **Carbon Report** | Per-shipment carbon estimate | ⚠️ 4G |
| LA-07 | **AI Route Suggestion** | Optimised route with constraints | ⚠️ 4G; local fallback |

### Build checklist
- [ ] `LA-01` Mobile-responsive shipment list with offline cache
- [ ] `LA-02` Route map page with Leaflet + OSM offline tiles
- [ ] `LA-03` GPS position update via Observation DocType (truck as Device)
- [ ] `LA-04` BOL/invoice document template (Jinja2 → WeasyPrint PDF)
- [ ] `LA-05` Carbon calculation service (distance × emission factor)
- [ ] `LA-06` Route optimisation AI agent integration (AGR-CEREAL-056, Execute-with-approval)

### Acceptance tests
1. Create shipment from lot selection → BOL draft generated automatically
2. AI route suggestion accounts for road restrictions → shown as propose-only before dispatch
3. In-transit temperature alert (from reefer sensor) sent to coordinator within 5 minutes
4. Carbon report generated for a 500 km shipment with correct tonne-km calculation

---

## 7) TP-06 — OwnerPortal (Agri-Business Owner Touchpoint)

### Purpose
Give U6 the business owner a single-pane view of the whole operation: margins, compliance status, AI insights, and strategic KPIs.

### Technology
| Component | Primary | OSS alternative |
|-----------|---------|----------------|
| App shell | Frappe Insights (embedded) + custom Workspace | Apache Superset, Metabase |
| Charts | Frappe Charts.js (built-in) | Plotly, ECharts |
| AI insights | EndToEndMarginCopilot (AGR-CEREAL-080) | Static reports |
| Alerts | Frappe Email Digest + ntfy.sh | PagerDuty |
| Export | Excel/CSV + PDF report | Same |

### Screen Inventory

| Screen ID | Screen name | Purpose |
|-----------|------------|---------|
| OP-01 | **Operations Dashboard** | Sites, lots, active shipments, compliance status |
| OP-02 | **Margin Copilot** | End-to-end margin analysis with AI narrative |
| OP-03 | **Compliance Status** | Certificate expiry, QC pass rates, open CAPA |
| OP-04 | **AI Insights Feed** | Chronological AI suggestions across all agents |
| OP-05 | **Backlog Progress** | Which backlog features are live, in-progress, planned |
| OP-06 | **Alert Summary** | Critical + warning alerts across all sites |

### Build checklist
- [ ] `OP-01` Frappe Workspace with business-owner Insights dashboard
- [ ] `OP-02` End-to-End Margin Copilot (AGR-CEREAL-080, Read-only AI)
- [ ] `OP-03` Compliance status report (certs expiring in 30/60/90 days)
- [ ] `OP-04` AI insights feed DocType: log all AI suggestions + approvals
- [ ] `OP-05` Weekly email digest (Frappe scheduler + Jinja2 template)

---

## 8) TP-07 — AdminPanel (System Admin Touchpoint)

### Purpose
Allow U7 system admins to configure the platform, manage users, run backups, and monitor system health.

### Technology
| Component | Primary | OSS alternative |
|-----------|---------|----------------|
| App shell | Frappe Desk (full) + bench CLI | Ansible playbooks |
| Monitoring | Prometheus + Grafana | Netdata (OSS) |
| Backup management | Restic + Rclone dashboard | Duplicati Web UI |
| Log viewer | Loki + Grafana Explore | GoAccess (web logs) |
| AI model mgmt | MLflow Model Registry | BentoML |

### Screen Inventory

| Screen ID | Screen name | Purpose |
|-----------|------------|---------|
| AP-01 | **System Health** | CPU, RAM, disk, DB size per node |
| AP-02 | **User Management** | Create/disable users, assign roles, site access |
| AP-03 | **Backup Status** | Last backup time, size, off-site replication status |
| AP-04 | **AI Model Registry** | Active models, versions, attestations, cost |
| AP-05 | **Sync Status** | Field hub last sync, pending items, conflicts |
| AP-06 | **Logs & Alerts** | Error logs, security events, Frappe scheduler log |

### Build checklist
- [ ] `AP-01` Grafana dashboard import for Frappe + k3s metrics
- [ ] `AP-02` Restic backup status webhook → Frappe Notification
- [ ] `AP-03` Field hub sync status API endpoint + dashboard widget
- [ ] `AP-04` MLflow Model Registry embed or Frappe DocType mirror

---

## 9) TP-08 — AuditorPortal (External Auditor / Donor Touchpoint)

### Purpose
Give U8 external auditors and donor organisations read-only, self-service access to evidence packs, compliance certificates, and audit trails.

### Technology
| Component | Primary | OSS alternative |
|-----------|---------|----------------|
| App shell | Frappe Web + custom read-only portal pages | Nextcloud (file-based) |
| Authentication | Frappe guest role + API key per organisation | OAuth 2.0 |
| Evidence export | EvidencePack PDF + ZIP download | Same |
| IATI export | Custom Frappe script → IATI XML | Direct API call |
| Watermarking | WeasyPrint CSS watermark | Ghostscript |

### Screen Inventory

| Screen ID | Screen name | Purpose |
|-----------|------------|---------|
| AU-01 | **Evidence Pack Browser** | List + download evidence packs by site/date |
| AU-02 | **Certificate Status** | Live certificate validity per lot/crop |
| AU-03 | **Compliance Summary** | Aggregated QC pass rates, CAPA closure rates |
| AU-04 | **Lot Trace View** | Read-only trace backward/forward for a lot |
| AU-05 | **IATI Export** | Download IATI-compatible XML for donor reporting |

### Build checklist
- [ ] `AU-01` Guest role with read-only access to EvidencePack, Certificate, QCTest
- [ ] `AU-02` Per-organisation API key management in Frappe
- [ ] `AU-03` IATI XML export script (FAO/UNDP fields)
- [ ] `AU-04` Evidence pack watermark ("CONFIDENTIAL — [Organisation name]")
- [ ] `AU-05` Compliance summary auto-generated report (scheduler weekly)

---

## 10) TP-09 — AICopilotPanel (Embedded AI Touchpoint)

### Purpose
Provide a **consistent, safe AI suggestion experience** embedded in every other touchpoint app. This is not a standalone app; it is a reusable UI component.

### Design specification

```
┌──────────────────────────────────────────────────────────────┐
│  🤖  AI Suggestion  [confidence: 87%]  [source: QCTest #1234] │
│                                                              │
│  Arabic text: "الشحنة تفتقر إلى شهادة أفلاتوكسين صالحة.    │
│               الرجاء إضافة الشهادة قبل الإرسال."            │
│                                                              │
│  English: "Shipment is missing a valid aflatoxin certificate.│
│            Please add the certificate before dispatch."      │
│                                                              │
│  Based on: [Certificate #45] [QCTest #88] [Policy: Season-2] │
│  Redacted: [customer_id, price] hidden from AI              │
│                                                              │
│  [✅ Approve]  [❌ Reject]  [🔼 Escalate to QA Manager]       │
│                             [📝 Do manually]                  │
└──────────────────────────────────────────────────────────────┘
```

### Mandatory rules (from Integration Feature Inventory §18.1)
1. **#413 Human-in-the-loop** — every suggestion requires Approve / Reject / Escalate
2. **#421 Source citations** — always show which DocTypes / records the AI used
3. **#438 Privacy-first** — show redaction preview (what was hidden)
4. **#439 Audit trail** — every interaction logged with hash to MLflow + Frappe Activity
5. **#467 Permission consent** — first time a new AI tool is used, show consent dialog

### Technology
| Component | Primary | OSS alternative |
|-----------|---------|----------------|
| Panel component | Frappe Form script (JavaScript + Vue micro-component) | React component |
| Confidence score | OpenJiuwen output field `confidence` | LLM logprob calc |
| Source citations | Frappe linked document titles | Custom API endpoint |
| Redaction preview | Presidio response metadata | spaCy NER labels |
| Audit logging | MLflow + Frappe Activity Log | Custom DB table |
| Approval recording | Frappe Workflow state change | Custom DocType |
| Bilingual text | Side-by-side AR/EN in panel | AR-only with EN toggle |

### Build checklist
- [ ] `AI-01` AICopilotPanel Vue/JS component with AR/EN bilingual display
- [ ] `AI-02` Confidence score visual indicator (colour-coded: green >80%, yellow 50–80%, red <50%)
- [ ] `AI-03` Source citation links (click → open linked DocType in new tab)
- [ ] `AI-04` Redaction preview section (collapsed by default, expandable)
- [ ] `AI-05` Approve/Reject/Escalate/Manual button handlers
- [ ] `AI-06` Audit log: POST to Frappe AI Interaction log + MLflow on every action
- [ ] `AI-07` Permission consent dialog for first use of each AI tool
- [ ] `AI-08` Offline fallback: show "AI unavailable — do manually" when Ollama down
- [ ] `AI-09` Embed AICopilotPanel in: FP-10, IA-06, SD-06, LA-07, OP-04

---

## 11) Cross-Touchpoint Standards

### Standard API contract
Every touchpoint app communicates with Frappe via a **standard REST envelope**:

```json
POST /api/method/yam_agri_core.ai.suggest
{
  "doctype": "Lot",
  "docname": "LOT-2026-00123",
  "agent": "ComplianceAgent",
  "context_fields": ["status", "crop", "site", "certificate"],
  "user_locale": "ar"
}

Response:
{
  "suggestion": "...",
  "confidence": 0.87,
  "sources": [{"doctype": "Certificate", "name": "CERT-0045"}],
  "redacted_fields": ["customer_id", "price"],
  "interaction_id": "uuid-xxxx"
}
```

### Standard AI Interaction DocType
```
AIInteraction
├── interaction_id (Data, unique)
├── agent (Select: ComplianceAgent | AnomalyAgent | SummaryAgent | CopilotAgent)
├── doctype_ref (Data)
├── docname_ref (Data)
├── user (Link → User)
├── timestamp (Datetime)
├── suggestion_hash (Data — SHA-256 of suggestion text)
├── confidence (Float)
├── action_taken (Select: Approved | Rejected | Escalated | Manual)
├── action_by (Link → User)
├── action_timestamp (Datetime)
└── sources (Table → AIInteractionSource)
      ├── doctype_ref (Data)
      └── docname_ref (Data)
```

### Offline-first degradation ladder
When connectivity or AI is unavailable, each touchpoint degrades gracefully:

```
FULL ONLINE (4G/broadband + cloud LLM)
  → All features available; cloud LLM for best suggestions

PARTIAL ONLINE (LAN only + Field Hub Ollama)
  → All Frappe features; AI suggestions from local Ollama 3B model

FIELD HUB OFFLINE (no WAN, but Field Hub LAN active)
  → Frappe forms cached; AI suggestions from local Ollama; queue changes in PouchDB

FULL OFFLINE (no network at all)
  → SMS only (TP-01); PWA reads from local cache; no AI suggestions; queue changes
  → Show "Offline mode — changes queued" banner on all PWA screens
```

---

## 12) Touchpoint Release Plan

| Touchpoint | V1.1 | V1.2 | V1.3 | V2.0 |
|-----------|------|------|------|------|
| TP-01 FarmerSMS | ✅ Core (lot + weight SMS) | Enhanced alerts | Irrigation advisor | — |
| TP-02 FieldPWA | ✅ Core (offline lot + weight) | AI suggestions | Maps + crew | Advanced analytics |
| TP-03 InspectorApp | ✅ Core (QCTest + cert) | AI compliance | HACCP full | Evidence pack AI |
| TP-04 SiloDashboard | ✅ Core (bins + scale) | AI anomaly | Aeration control | Full reconciliation |
| TP-05 LogisticsApp | — | Basic shipment | Route AI | Full docs + carbon |
| TP-06 OwnerPortal | ✅ Basic dashboard | Compliance KPIs | Margin copilot | Full AI insights |
| TP-07 AdminPanel | ✅ Frappe Desk | Backup status | Model registry | Full observability |
| TP-08 AuditorPortal | — | Basic evidence | IATI export | Full compliance |
| TP-09 AICopilotPanel | — | ✅ V1.2 embedded | Expanded agents | Full agent suite |

---

## 13) References

- `docs/SMART_FARM_ARCHITECTURE.md` — Layer 10: Touchpoints, Layer 11: Persona/Journey Map
- `docs/PERSONA_JOURNEY_MAP.md` — Deep persona profiles and customer journey maps
- `docs/BLUEPRINT_PLAYBOOK_BEGINNER.md` — Section 18: Human-AI UX Standards
- `docs/Integration Feature Inventory.csv` — Mandatory UX patterns (#413, #421, #438, #439, #467)
- [Frappe PWA offline docs](https://frappeframework.com/docs/user/en/pwa)
- [PouchDB offline sync](https://pouchdb.com/)
- [Africa's Talking SMS API](https://africastalking.com/)
- [Leaflet.js offline tiles](https://github.com/allartk/leaflet.offline)
- [WeasyPrint — Python PDF from HTML/CSS](https://weasyprint.org/)
- [ntfy.sh — self-hosted push notifications](https://ntfy.sh/)
