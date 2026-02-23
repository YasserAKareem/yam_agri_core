# arc42 §6 — Runtime View

> **arc42 Section:** 6  
> **Version:** 1.1  
> **Status:** ⚠️ Draft  
> **Date:** 2026-02-23  
> **Related SDLC doc:** [03_SYSTEM_ARCHITECTURE.md §5](../Docs%20v1.1/03_SYSTEM_ARCHITECTURE.md)  
> **Related C4 docs:** [`docs/C4 model Architecture v1.1/06_DYNAMIC_LOT_LIFECYCLE.md`](../C4%20model%20Architecture%20v1.1/06_DYNAMIC_LOT_LIFECYCLE.md)

---

The runtime view describes **how the building blocks interact at runtime** through key scenarios.

---

## 6.1 Scenario: Harvest Lot Creation and QC Evidence Flow

**Trigger:** Farm Supervisor (U2) records a new grain harvest.

```
U2 (Farm Supervisor)
  │  [Frappe Desk — Lot form]
  │  Fill: lot_type=Harvest, crop=Wheat, season=2026-Spring,
  │        declared_qty_kg=5000, site=SITE-FARM-001,
  │        storage_bin=BIN-A12, harvest_date=2026-02-20
  │
  ▼
Frappe Web (yam_agri_core/lot/lot.py — validate hook)
  │  Check: site is set ✅
  │  Check: available_qty_kg ≤ declared_qty_kg ✅
  │  Check: no Season Policy violation for Draft status (not yet)
  │
  ▼
MariaDB — INSERT tabLot (status=Draft)
  │
  ▼
Scale Connector (scale/importer.py)
  │  QA team uploads CSV scale tickets for LOT-2026-001
  │  Per row: create ScaleTicket; compare net_weight to declared_qty_kg
  │  If |net_weight - declared_qty| > tolerance (2%):
  │      CREATE Nonconformance (type=Weight Mismatch, lot=LOT-2026-001)
  │
  ▼
QA Inspector (U3)
  │  [Frappe Desk — QCTest form]
  │  Create QCTest: test_type=Mycotoxin, result=3.2 ppb → Pass
  │  Create QCTest: test_type=Moisture, result=12.8% → Pass
  │  Attach Certificate (FAO GAP, expiry=2027-01-01) to Lot
  │
  ▼
Logistics Coordinator (U5)
  │  Set Lot status → Released (triggers Season Policy check)
  │  [lot.py — on_submit hook]
  │  SeasonPolicy: crop=Wheat, season=2026-Spring
  │    Mandatory tests: Moisture ✅, Protein ✗ (missing!)
  │    → BLOCK: "Protein QCTest missing for Season Policy SP-WHEAT-2026-SPRING"
  │    Lot remains In Storage; coordinator notified
  │
  ▼  (after protein test added)
  │  Season Policy check passes → Lot.status = Released
  │
  ▼
Transfer (Split)
  │  Logistics Coordinator creates Transfer (type=Split)
  │  Source: LOT-2026-001 (500 kg)
  │  Destination: LOT-2026-002 (type=Shipment)
  │  Transfer.validate: source available_qty ≥ 500 ✅
  │  Transfer.on_submit: LOT-2026-001.available_qty_kg -= 500
  │                      LOT-2026-002.declared_qty_kg = 500
```

---

## 6.2 Scenario: Sensor Observation — Alert and Quarantine

**Trigger:** IoT temperature sensor in BIN-A12 reports a high reading.

```
IoT Sensor (DEV-TEMP-001)
  │  MQTT publish: topic = yam/SITE-FARM-001/DEV-TEMP-001/observation
  │  Payload: { "metric": "temperature", "value": 36.2, "unit": "C", "ts": "..." }
  │
  ▼
Mosquitto MQTT Broker (Field Hub)
  │
  ▼
iot/gateway.py (paho-mqtt subscriber)
  │  Lookup Device: DEV-TEMP-001 → site=SITE-FARM-001, storage_bin=BIN-A12
  │  Validate range: threshold_max = 35°C
  │  value (36.2) > threshold_max (35) → quality_flag = Quarantine
  │
  ▼
Frappe REST API — POST /api/resource/Observation
  │  Creates: Observation (quality_flag=Quarantine, alert_sent=0)
  │
  ▼
Frappe Scheduler / Event hook
  │  Observation.after_insert hook:
  │  quality_flag == Quarantine AND metric_type == Temperature →
  │    Send Frappe Notification to YAM QA Manager, YAM Warehouse roles
  │    Notification: "ALERT: BIN-A12 temperature 36.2°C exceeds 35°C threshold"
  │    Set alert_sent = 1
  │
  ▼
Silo Operator (U4) / QA Inspector (U3) receives alert in Frappe Desk
  │  Reviews observation; investigates bin
  │  Creates Nonconformance (type=Sensor Alert, severity=Major)
  │  CAPA workflow begins
```

---

## 6.3 Scenario: AI Compliance Check

**Trigger:** QA Inspector (U3) clicks "AI: Check Compliance" on LOT-2026-001.

```
QA Inspector (U3)
  │  [Frappe Desk — Lot form, AI Suggest button]
  │
  ▼
Frappe JavaScript (lot.js)
  │  POST /api/method/yam_agri_core.ai.gateway_client.compliance_check
  │  payload: { lot_name: "LOT-2026-001" }
  │
  ▼
yam_agri_core/ai/gateway_client.py (server-side Python)
  │  Gather lot data: status, season, QCTests[], Certificates[], Nonconformances[]
  │  Build context dict (NO PII, NO pricing)
  │  POST http://ai-gateway:8001/suggest
  │    { "lot": "LOT-2026-001", "task": "compliance_check",
  │      "context": { "season_policy": "...", "tests": [...], "certs": [...] } }
  │
  ▼
AI Gateway (FastAPI — ai-gateway service)
  │  1. Authenticate service token ✅
  │  2. Validate task: "compliance_check" ∈ permitted list ✅
  │  3. REDACT: scan context for PII/pricing → none found (pre-filtered)
  │  4. Build prompt: "Given this lot context, list missing QC requirements..."
  │  5. POST http://ollama:11434/api/generate (llama3.2:3b)
  │  6. Receive response: "Lot LOT-2026-001 is missing: Pesticide Residue test.
  │                        Certificate CERT-2025-012 expires in 14 days."
  │  7. Log: { timestamp, user, record="LOT-2026-001", prompt_hash, response_hash,
  │             model="llama3.2:3b", redaction_applied=true, tokens_used=312 }
  │  8. Return: { "suggestion": "...", "log_hash": "sha256:..." }
  │
  ▼
Frappe — gateway_client.py receives suggestion
  │  Saves suggestion to Lot.ai_suggestion field (read-only; NOT submitted)
  │  Returns suggestion text to JavaScript
  │
  ▼
Frappe Desk — AI Suggestion Panel
  │  Displays: "AI Suggestion — Review Required: [suggestion text]"
  │  Shows: [Accept] [Dismiss] buttons
  │
  ▼  User clicks [Accept]
  │
QA Inspector (U3) reviews and accepts
  │  Creates QCTest (type=Pesticide Residue) manually
  │  Sets AI Interaction Log: suggestion_accepted=true
```

---

## 6.4 Scenario: EvidencePack Generation

**Trigger:** Platform Owner (U6) requests an evidence pack for an upcoming donor audit.

```
Platform Owner (U6)
  │  [Frappe Desk — EvidencePack form]
  │  Fill: site=SITE-FARM-001, from_date=2026-01-01, to_date=2026-02-23
  │  Click "Generate Pack"
  │
  ▼
evidence_pack.py — generate() method
  │  Query: QCTests WHERE site=SITE-FARM-001 AND test_date BETWEEN dates
  │  Query: Certificates WHERE site=SITE-FARM-001 AND issue_date BETWEEN dates
  │  Query: ScaleTickets WHERE site=SITE-FARM-001 AND date BETWEEN dates
  │  Query: Observations WHERE site=SITE-FARM-001 AND timestamp BETWEEN dates (key alerts only)
  │  Query: Nonconformances WHERE site=SITE-FARM-001 AND date BETWEEN dates
  │  Populate child tables: qc_tests, certificates, scale_tickets, observations, nonconformances
  │
  ▼  (Optional: AI narrative)
  │  POST AI Gateway: task=evidence_narrative, context={pack summary}
  │  AI drafts narrative → stored in EvidencePack.narrative
  │  Owner must review and approve before sending
  │
  ▼
Print Format / PDF export
  │  EvidencePack PDF generated via Frappe print format
  │  Stored in MinIO (linked as EvidencePack.export_pdf attachment)
  │
  ▼
EvidencePack.status = Finalised
  │  (Changed to "Sent to Auditor" when owner shares the PDF)
```

---

## 6.5 Scenario: Lot Transfer — Split with Approval

**Trigger:** Logistics Coordinator (U5) initiates a split to create a shipment lot.

```
Logistics Coordinator (U5)
  │  [Frappe Desk — Transfer form]
  │  Fill: transfer_type=Split, source_lots=[{lot=LOT-2026-001, qty=500}],
  │         destination_lots=[{lot=LOT-2026-002 (new Shipment), qty=500}]
  │  Click Save → [Draft]
  │
  ▼
Transfer.validate (transfer.py)
  │  source_lots total qty == destination_lots total qty ✅
  │  LOT-2026-001.available_qty_kg (5000) ≥ 500 ✅
  │  destination is Shipment type → requires QA Manager approval (if configured)
  │
  ▼  Frappe Workflow: Submit → "Pending QA Approval"
  │
QA Manager (U3) receives workflow notification
  │  Reviews transfer; approves → Transfer.docstatus = 1 (Submitted)
  │
  ▼
Transfer.on_submit (transfer.py)
  │  LOT-2026-001.available_qty_kg -= 500  (now 4500)
  │  LOT-2026-002.declared_qty_kg = 500; LOT-2026-002.status = Received
  │  MariaDB COMMIT (within Frappe transaction)
```

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial section — V1.1 |
