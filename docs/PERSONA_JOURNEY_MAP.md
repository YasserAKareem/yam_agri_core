# User Persona & Customer Journey Map — YAM Agri Platform

> **Purpose:** Deep-detail profiles and end-to-end customer journey maps for all 9 YAM Agri platform personas. Use as the authoritative reference for UX design, acceptance testing, and team alignment.  
> **Context:** Yemen — conflict-affected, connectivity-constrained, water-scarce, solar-powered  
> **Related docs:**  
> - `docs/SMART_FARM_ARCHITECTURE.md` — 11-layer stack (Layer 11: this layer)  
> - `docs/TOUCHPOINT_APP_BLUEPRINT.md` — Touchpoint app build blueprints  
> - `docs/BLUEPRINT_PLAYBOOK_BEGINNER.md` — Overall platform playbook

---

## How to Read This Document

For each persona you will find:

1. **Profile card** — who they are, background, tech literacy, device, goals, frustrations
2. **Customer journey map** — stages from first awareness to daily expert use
3. **Key touchpoints** — which apps they use and when
4. **Pain points & delight moments** — what makes their day worse or better
5. **Yemen-specific context** — real-world constraints that shape their experience
6. **Acceptance test scenarios** — pass/fail criteria tied to their journey stages

---

---

# U1 — Smallholder Farmer (الفلاح الصغير)

## Profile Card

| Field | Detail |
|-------|--------|
| **Name (sample)** | Ahmed Al-Shaibani (أحمد الشيباني) |
| **Age** | 42 |
| **Location** | Rural highland farm, Taiz governorate |
| **Crops** | Sorghum (دُخن), wheat (قمح) — rain-fed |
| **Farm size** | 2–5 feddan (0.8–2 ha) |
| **Literacy** | Arabic only; functional literacy (can read SMS) |
| **Tech literacy** | Low — uses feature phone for calls and SMS |
| **Device** | Nokia 105 (2G SMS); no smartphone |
| **Connectivity** | 2G SMS only; no mobile internet; no Wi-Fi |
| **Power** | Solar panel for phone charging; no grid |
| **Language** | Arabic primary; no English |
| **YAM Agri role** | Supplies grain lots to YAM from his farm |
| **Income** | ~$200–400/month (seasonal) |
| **Primary goal** | Get fair price for his grain; know when to sell |
| **Key frustration** | No visibility into prices; delayed payment; crop losses from poor storage |

## Customer Journey Map

### Stage 1: Awareness (Pre-registration)
- **Trigger:** YAM Agri field agent visits village, explains SMS-based lot system
- **Emotion:** Curious but skeptical — "will this actually pay me more?"
- **Touchpoint:** Face-to-face from YAM field agent; paper flyer with SMS number
- **Action:** Ahmed keeps the SMS number on paper

### Stage 2: Onboarding (First use)
- **Trigger:** Field agent sends Ahmed a test SMS; helps him respond
- **Emotion:** Anxious — worried about making mistakes
- **Touchpoint:** TP-01 FarmerSMS; field agent present as guide
- **Action:** Ahmed sends `مساعدة` → receives Arabic menu
- **Success criteria:** Help menu delivered in < 10 seconds, fully in Arabic
- **Pain point:** Arabic character encoding must work on basic Nokia phone

### Stage 3: First Harvest Lot (Learning)
- **Trigger:** Sorghum harvest begins; Ahmed wants to register his grain
- **Emotion:** Hopeful but uncertain about syntax
- **Touchpoint:** TP-01 FarmerSMS
- **Action:** Ahmed sends `حصاد دخن 800 كيلو` → receives lot confirmation SMS with lot number
- **Success criteria:** Lot created in Frappe with status=Draft, crop=Sorghum, qty=800 kg
- **Pain point:** If confirmation SMS is delayed > 3 minutes, Ahmed assumes it failed and sends again

### Stage 4: Weight Confirmation
- **Trigger:** YAM scale operator weighs Ahmed's grain at the silo
- **Emotion:** Uncertain — trusts the scale? Did the weight match his estimate?
- **Touchpoint:** TP-01 (alert to Ahmed) + TP-04 SiloDashboard (operator)
- **Action:** System sends Ahmed SMS: `تأكيد: تم وزن الدفعة رقم LOT-001 وزن 795 كيلو`
- **Success criteria:** Ahmed receives weight confirmation within 5 minutes of scale ticket creation

### Stage 5: Alert Response
- **Trigger:** Stored grain moisture rises above 14% → alert sent to Ahmed
- **Emotion:** Worried — stored grain at risk
- **Touchpoint:** TP-01 FarmerSMS (inbound alert)
- **Action:** Ahmed forwards alert to field supervisor; system suggests aeration
- **Success criteria:** Alert in Arabic; aeration recommendation in simple language (reading level grade 6)

### Stage 6: Regular Use (Expert farmer)
- **Trigger:** Ahmed now registers every harvest via SMS without help
- **Emotion:** Confident; feels more in control of his income
- **Action:** Sends `حالة` each week to see his lot statuses; receives payment confirmation SMS
- **Delight moment:** Receives SMS: `تهانينا: تم قبول دفعتك وسيتم الدفع خلال 3 أيام` (congratulations, payment in 3 days)

## Pain Points & Delight Moments

| # | Pain point | Delight moment |
|---|-----------|----------------|
| 1 | SMS commands with typos fail silently | Fuzzy matching: `دخن` accepted even with common misspelling |
| 2 | Delayed payment — no visibility | SMS payment confirmation with exact date |
| 3 | Doesn't know if stored grain is at risk | Proactive soil moisture / temperature alert |
| 4 | Arabic SMS encoding broken on old phones | All messages use GSM 7-bit Arabic safe encoding |
| 5 | Can't track which lot was rejected and why | Rejection SMS includes brief reason in simple Arabic |

## Yemen-Specific Context
- **Connectivity:** 2G SMS is the only reliable channel in highland Taiz — no internet
- **Power:** Nokia phone charged via small solar panel; no grid; must send < 5 SMS to conserve
- **Language:** Exclusively Arabic; any English in SMS is confusing
- **Trust:** Ahmed trusts the YAM field agent who onboarded him; system must maintain that trust
- **Payment:** Hawala system used; SMS confirms that payment instruction issued

## Acceptance Test Scenarios

| ID | Scenario | Expected result | Pass criteria |
|----|---------|----------------|---------------|
| U1-T01 | Ahmed sends `حصاد دخن 800 كيلو` | Lot created, confirmation SMS sent | SMS delivered < 60s; lot in Frappe |
| U1-T02 | Ahmed sends `وزن 500 كيلو` | ScaleTicket draft created | Confirmation SMS with ticket number |
| U1-T03 | Ahmed sends `حالة` | Summary of last 3 lots | SMS with statuses in Arabic |
| U1-T04 | Moisture alert triggers | Ahmed receives Arabic SMS alert | Alert sent < 5 min of threshold breach |
| U1-T05 | Ahmed sends unrecognised text | Help menu returned in Arabic | Help menu in < 10s |
| U1-T06 | Ahmed sends message with typo `دخين` instead of `دُخن` | System fuzzy-matches to sorghum | Lot created correctly |

---

---

# U2 — Farm Supervisor (مشرف المزرعة)

## Profile Card

| Field | Detail |
|-------|--------|
| **Name (sample)** | Fatima Al-Omari (فاطمة العمري) |
| **Age** | 31 |
| **Location** | Farm site, Lahj governorate (coastal plain) |
| **Role** | Manages day-to-day farm operations for YAM Agri |
| **Team size** | 5–15 seasonal workers |
| **Tech literacy** | Medium — comfortable with Android; uses WhatsApp daily |
| **Device** | Samsung Android tablet (8-inch) + personal smartphone |
| **Connectivity** | Site Wi-Fi (from Field Hub); 3G occasionally; offline 2–4 days/week |
| **Power** | Solar + battery at farm; charges tablet daily |
| **Language** | Arabic primary; basic English (enough to read field labels) |
| **Primary goal** | Accurate lot records, crew coordination, no surprises at harvest |
| **Key frustration** | Data entry when offline; lot mistakes that take hours to fix |

## Customer Journey Map

### Stage 1: Onboarding
- **Trigger:** YAM IT admin creates her account; field agent walks through FieldPWA
- **Emotion:** Eager but wants to know "what do I do every morning?"
- **Touchpoint:** TP-02 FieldPWA (onboarding flow) + field agent guidance
- **Action:** Fatima completes onboarding checklist: creates a test Lot, takes a photo, records weight
- **Success criteria:** Onboarding < 30 minutes; no errors on first lot creation

### Stage 2: Daily Morning Routine
- **Trigger:** Fatima arrives at farm at 6 AM; opens FieldPWA on tablet
- **Emotion:** Focused; wants today's task list immediately
- **Touchpoint:** TP-02 FieldPWA — Home Dashboard (FP-01)
- **Action:** Views today's alerts, pending lot statuses, crew assignments
- **Success criteria:** Home screen loads in < 3 seconds even on cached data (offline)

### Stage 3: Harvest Lot Creation
- **Trigger:** Harvesting begins; Fatima needs to create lots for each batch
- **Touchpoint:** TP-02 FieldPWA — New Lot (FP-04)
- **Action:** Takes photo of grain, GPS auto-fills location, enters crop type + estimated weight
- **Success criteria:** Lot saved locally in < 2 seconds; GPS capture < 5 seconds

### Stage 4: Offline Work (2-day no-network period)
- **Trigger:** 4G goes down; site Wi-Fi also down due to power cut
- **Emotion:** Frustrated but accustomed; knows the app will queue
- **Touchpoint:** TP-02 FieldPWA (offline) — Sync Status (FP-11)
- **Action:** Continues creating lots, entering weights; sees "47 changes queued" in sync status
- **Success criteria:** All actions queue without error; no data loss; sync icon clearly visible

### Stage 5: Sync Recovery
- **Trigger:** 4G restored after 2 days; PouchDB syncs in background
- **Emotion:** Relieved; checks sync status
- **Touchpoint:** TP-02 FieldPWA — Sync Status (FP-11)
- **Action:** Sees "Syncing 47 changes… complete"; no conflicts
- **Success criteria:** Full sync completes in < 2 minutes for 47 records; zero data loss

### Stage 6: AI-Assisted Suggestion
- **Trigger:** New lot has incomplete data — AI flags it
- **Touchpoint:** TP-02 FieldPWA — AI Suggestion Panel (FP-10)
- **Action:** Sees Arabic suggestion: "الدفعة تفتقر إلى قيمة الرطوبة. أضفها قبل الإرسال."
- **Action:** Clicks Approve → moisture field highlighted; enters value
- **Delight moment:** "The system reminded me before I sent it — saved me a rejection"

## Pain Points & Delight Moments

| # | Pain point | Delight moment |
|---|-----------|----------------|
| 1 | Offline for days with no confirmation data saved | Sync status screen shows exactly what's queued |
| 2 | GPS inaccurate or slow on cloudy days | Map shows approximate position with accuracy radius |
| 3 | Photo too large → slow upload on 3G | Auto-compress photos to < 500 KB before upload |
| 4 | Lot conflicts after sync with office | Diff view: side-by-side field vs office version |
| 5 | Crew assignments lost when tablet restarts | Crew schedule cached in PouchDB; survives restart |

## Yemen-Specific Context
- **Power:** Tablet charged at farm from solar; must last full 8-hour shift
- **Dust:** Tablet in a ruggedized case; touchscreen must work with gloves
- **Language:** UI fully in Arabic; Hijri dates in crew schedule view

## Acceptance Test Scenarios

| ID | Scenario | Expected result | Pass criteria |
|----|---------|----------------|---------------|
| U2-T01 | Create lot offline (airplane mode) | Lot in local cache immediately | PouchDB record exists; no error |
| U2-T02 | 7-day offline then sync | All 7 days of changes sync correctly | Zero data loss; < 5 min sync time |
| U2-T03 | GPS capture | Lot location within 50m of actual field | GPS accuracy indicator shown |
| U2-T04 | AI suggestion on incomplete lot | Suggestion shown in Arabic with approve/reject | Interaction logged in AIInteraction DocType |
| U2-T05 | Conflict on sync | Diff view shown; user resolves | No silent data overwrite |

---

---

# U3 — QA / Food Safety Inspector (مفتش الجودة وسلامة الغذاء)

## Profile Card

| Field | Detail |
|-------|--------|
| **Name (sample)** | Dr. Khalid Al-Yemeni (د. خالد اليمني) |
| **Age** | 38 |
| **Location** | Travels between farm sites, silos, and main office |
| **Qualifications** | BSc Food Science; HACCP Level 3 certificate |
| **Tech literacy** | High — uses laptop and tablet; familiar with digital forms |
| **Device** | Lenovo laptop + Android tablet (field use) |
| **Connectivity** | 4G + site Wi-Fi; sometimes offline at remote farms |
| **Language** | Arabic and English (professional level) |
| **Primary goal** | Zero non-conformances reaching customers; defensible audit trail |
| **Key frustration** | Evidence scattered across paper + spreadsheet + WhatsApp; hard to compile for audits |

## Customer Journey Map

### Stage 1: Onboarding
- **Trigger:** Khalid joins YAM Agri; IT admin configures QA Manager role
- **Touchpoint:** TP-03 InspectorApp + TP-07 AdminPanel (role assignment)
- **Action:** Completes training on HACCP checklist DocType, certificate workflow
- **Success criteria:** Khalid can create a QCTest, pass/fail a checklist, issue a certificate in < 15 minutes

### Stage 2: Receiving Inspection (New Lot Arrives)
- **Trigger:** New wheat lot arrives at Hodeidah/Hudaydah silo
- **Touchpoint:** TP-03 InspectorApp — QCTest Form (IA-01)
- **Action:** Enters moisture (10.2%), protein (13.5%), aflatoxin (< 2 ppb); marks Pass
- **Success criteria:** QCTest linked to Lot; Certificate auto-draft created

### Stage 3: HACCP Control Point Check
- **Trigger:** Monthly HACCP audit at Taiz storage facility
- **Touchpoint:** TP-03 InspectorApp — HACCP Checklist (IA-02)
- **Action:** Steps through 8 control points; takes photos for 3 of them; marks CCP4 as Fail
- **Action:** Nonconformance auto-created for CCP4 failure with corrective action field
- **Success criteria:** Checklist saved with photos; nonconformance linked; audit trail timestamped

### Stage 4: AI Compliance Check
- **Trigger:** Khalid reviews a lot before dispatch
- **Touchpoint:** TP-03 InspectorApp — AI Compliance Check (IA-06)
- **Action:** Asks AI: "What's missing for lot LOT-2026-00456?"
- **AI response:** "Lot is missing a valid phytosanitary certificate (expired 3 days ago). Aflatoxin test result > 7 days old — retest recommended under Season Policy 2."
- **Success criteria:** AI response in < 5 seconds; source citations include Certificate #34 and Policy doc

### Stage 5: Evidence Pack Generation
- **Trigger:** UNDP donor requests compliance evidence for Q1 2026
- **Touchpoint:** TP-03 InspectorApp — Evidence Pack (IA-05)
- **Action:** Selects date range Jan–Mar 2026, site = Taiz; clicks Generate
- **AI summary agent** drafts a 3-paragraph narrative in Arabic and English
- **Success criteria:** Pack includes all QCTests, Certificates, Nonconformances for period; PDF in < 30s

### Stage 6: Certificate Expiry Management
- **Trigger:** Weekly: Khalid reviews certificates expiring in 30 days
- **Touchpoint:** TP-03 InspectorApp — Certificate Expiry Dashboard (IA-08)
- **Action:** Sees 3 certificates expiring this month; triggers re-inspection workflow
- **Delight moment:** System auto-creates re-inspection tasks before Khalid has to ask

## Pain Points & Delight Moments

| # | Pain point | Delight moment |
|---|-----------|----------------|
| 1 | Compiling evidence for audits takes a full day | Evidence Pack generated in < 30 seconds |
| 2 | Certificate expiry discovered day of dispatch | 30-day expiry dashboard + automated re-inspection task |
| 3 | HACCP checklist on paper — photos scattered in WhatsApp | All photos attached to checklist items; timestamped |
| 4 | AI doesn't explain why it flagged something | Source citations on every AI suggestion |
| 5 | Hard to trace which lot caused a customer complaint | Lot trace backward shows full history from complaint to farm |

## Acceptance Test Scenarios

| ID | Scenario | Expected result | Pass criteria |
|----|---------|----------------|---------------|
| U3-T01 | QCTest aflatoxin > limit | Nonconformance auto-created | NC linked to lot; CAPA field empty (requires human action) |
| U3-T02 | AI compliance check | Missing items listed with sources | Response < 5s; citations shown |
| U3-T03 | Evidence pack generation | PDF with all items for date range | Completes < 30s; all records included |
| U3-T04 | Certificate expired → dispatch attempt | Dispatch blocked | Workflow throws validation error; reason shown in Arabic |
| U3-T05 | HACCP photo attach | Photo saved to MinIO; linked to checklist item | Photo accessible offline after cache |

---

---

# U4 — Silo / Store Operator (مشغل الصومعة / المستودع)

## Profile Card

| Field | Detail |
|-------|--------|
| **Name (sample)** | Mahmoud Al-Zubayri (محمود الزبيري) |
| **Age** | 35 |
| **Location** | On-premise at Aden silo (main storage facility) |
| **Tech literacy** | Medium — uses desktop PC daily; comfortable with spreadsheets |
| **Device** | Desktop PC on-premise; on-site LAN (no internet required for daily work) |
| **Connectivity** | On-premise LAN; internet when syncing with central; offline capable |
| **Language** | Arabic primary; basic English for technical terms |
| **Primary goal** | Keep grain safe (temperature, humidity, pests); accurate stock records |
| **Key frustration** | Too many sensor alerts — alert fatigue; manual CSV weight entry is slow |

## Customer Journey Map

### Stage 1: Morning Start
- **Trigger:** Mahmoud arrives at silo at 7 AM; opens SiloDashboard on desktop
- **Touchpoint:** TP-04 SiloDashboard — Bin Monitor (SD-01)
- **Action:** Scans bin colour map — all green except Bin-07 (yellow: temp 32°C)
- **Action:** Checks Bin-07 detail; AI suggests aeration schedule
- **Success criteria:** Dashboard loads in < 3 seconds on LAN; Bin-07 highlighted yellow

### Stage 2: Scale Ticket Import
- **Trigger:** Truck arrives with 3 tons of sorghum; weighbridge operator hands Mahmoud a CSV
- **Touchpoint:** TP-04 SiloDashboard — Scale Ticket Import (SD-02)
- **Action:** Drags CSV onto import widget → 4 tickets created; 1 flagged as mismatch (declared vs actual > 2%)
- **Action:** Mahmoud reviews mismatch → creates Nonconformance for the discrepant ticket
- **Success criteria:** Import completes in < 10 seconds for 10 tickets; mismatch flagged automatically

### Stage 3: Alert Triage
- **Trigger:** 3 new alerts appear in Alert Centre: temp, humidity, and CO₂
- **Touchpoint:** TP-04 SiloDashboard — Alert Centre (SD-04)
- **Action:** AI Anomaly Panel ranks alerts: CO₂ spike in Bin-12 is #1 priority
- **Action:** Mahmoud clicks on CO₂ alert → opens Bin-12 detail → triggers inspection
- **Delight moment:** Alert ranked by AI; Mahmoud doesn't have to guess which is most critical
- **Success criteria:** Alert ranking loads in < 2 seconds; AI rank shown with confidence

### Stage 4: Stock Reconciliation
- **Trigger:** End of month; physical count vs ERP must match
- **Touchpoint:** TP-04 SiloDashboard — Stock Reconciliation (SD-03)
- **Action:** Runs reconciliation report; sees 50 kg difference in Bin-03 wheat
- **Action:** AI suggests possible cause: weight measurement tolerance or moisture loss
- **Success criteria:** Reconciliation report in < 10 seconds; discrepancy highlighted with tolerance band

### Stage 5: Aeration Control (Execute-with-approval)
- **Trigger:** AI suggests activating aeration for Bin-07 (rising temp)
- **Touchpoint:** TP-04 SiloDashboard — Aeration Control (SD-07)
- **Action:** AI suggests schedule; Mahmoud clicks "Request Aeration" → approval request sent to QA Manager
- **Action:** QA Manager approves → aeration starts automatically
- **Success criteria:** Approval workflow completes; aeration logged with approval record

## Pain Points & Delight Moments

| # | Pain point | Delight moment |
|---|-----------|----------------|
| 1 | Alert fatigue — 50+ alerts per day, most unimportant | AI alert ranking: top 3 critical issues surfaced immediately |
| 2 | Manual CSV import takes 30 minutes | Drag-drop CSV import in < 30 seconds |
| 3 | Shrinkage discovered at end of month — too late | Daily mini-reconciliation with trend alert |
| 4 | Can't tell if sensor is faulty or grain is actually bad | Data quality guardrail: quarantined readings labelled differently |
| 5 | Hard to explain to manager what happened with Bin-07 last week | Time-series chart shows full 7-day history per bin |

## Acceptance Test Scenarios

| ID | Scenario | Expected result | Pass criteria |
|----|---------|----------------|---------------|
| U4-T01 | Bin temperature exceeds 35°C | Red alert on bin map | Alert shown < 60s; bin turns red |
| U4-T02 | CSV import 10 tickets, 1 mismatch | 10 tickets created; 1 flagged | Import < 30s; mismatch NC auto-created |
| U4-T03 | Aeration approval workflow | Approval sent to QA Manager | Cannot execute without approval; logged |
| U4-T04 | Sensor reading out of range | Quarantine flag set; not used in automation | `quality_flag = quarantined` in Observation |
| U4-T05 | Stock reconciliation | Discrepancy shown with tolerance | Report < 10s; colour-coded diff |

---

---

# U5 — Logistics Coordinator (منسق اللوجستيات)

## Profile Card

| Field | Detail |
|-------|--------|
| **Name (sample)** | Omar Al-Hamdani (عمر الحمداني) |
| **Age** | 29 |
| **Location** | Mobile between office (Aden) and truck routes |
| **Tech literacy** | High — uses smartphone as primary work device; comfortable with apps |
| **Device** | Samsung Galaxy smartphone (5G); laptop at office |
| **Connectivity** | 4G in cities; patchy rural; offline on long routes |
| **Language** | Arabic and basic English |
| **Primary goal** | On-time shipments; minimal customs delays; zero cargo losses |
| **Key frustration** | Export document preparation is manual and error-prone; no live cargo tracking |

## Customer Journey Map

### Stage 1: Shipment Planning
- **Trigger:** Sales order from customer requires 20 tons wheat by specific date
- **Touchpoint:** TP-05 LogisticsApp — New Shipment (LA-04)
- **Action:** Selects lot(s), assigns truck, routes via AI suggestion
- **AI route suggestion:** Omar sees proposed route with estimated time + toll costs
- **Success criteria:** Route shown on map with waypoints; AI suggestion marked "Propose-only"

### Stage 2: Document Generation
- **Trigger:** Shipment confirmed; customs documentation needed
- **Touchpoint:** TP-05 LogisticsApp — Document Pack (LA-05)
- **Action:** Clicks "Generate Documents" → BOL + Certificate of Origin + Phytosanitary Cert drafted
- **AI agent** pre-fills fields from lot data (crop, origin, quantity, certificates)
- **Success criteria:** All 3 documents drafted in < 30 seconds; pre-filled from Frappe data

### Stage 3: In-Transit Tracking
- **Trigger:** Truck departs silo
- **Touchpoint:** TP-05 LogisticsApp — Route Map (LA-03)
- **Action:** Omar sees truck GPS position updating every 5 minutes on Leaflet map
- **Alert:** Temperature sensor in reefer truck spikes → alert sent to Omar
- **Success criteria:** GPS update every 5 min; temperature alert delivered < 5 min of breach

### Stage 4: Delivery Confirmation
- **Trigger:** Truck arrives at customer warehouse
- **Touchpoint:** TP-05 LogisticsApp — Shipment Detail (LA-02)
- **Action:** Driver sends SMS confirmation → lot status updates to "Delivered"
- **Carbon report** auto-generated for this shipment
- **Success criteria:** Delivery confirmation within 10 minutes; carbon report attached

## Pain Points & Delight Moments

| # | Pain point | Delight moment |
|---|-----------|----------------|
| 1 | Manual BOL preparation takes 2 hours | AI pre-fills all fields in < 30 seconds |
| 2 | Doesn't know where truck is | Live GPS map updated every 5 minutes |
| 3 | Cargo theft discovered at destination | Alert within minutes of deviation from route |
| 4 | Carbon reporting for donors manually calculated | Auto-generated per shipment |
| 5 | Customs rejection for missing certificate | AI pre-check catches missing certs before dispatch |

## Acceptance Test Scenarios

| ID | Scenario | Expected result | Pass criteria |
|----|---------|----------------|---------------|
| U5-T01 | Generate BOL from lot | BOL pre-filled and downloadable | < 30s; all mandatory fields populated |
| U5-T02 | GPS track truck | Position on map | Update every 5 min; latency < 30s |
| U5-T03 | In-transit temp alert | Omar receives push notification | Alert < 5 min of threshold breach |
| U5-T04 | Route AI suggestion | Route shown; approved by Omar | Cannot dispatch without approval action |
| U5-T05 | Carbon report | Per-shipment tonne-km × emission factor | Calculation verifiable against published factors |

---

---

# U6 — Agri-Business Owner (صاحب العمل الزراعي)

## Profile Card

| Field | Detail |
|-------|--------|
| **Name (sample)** | Yasser Al-Kareem (ياسر الكريم) |
| **Age** | 48 |
| **Location** | Aden main office; travels regionally |
| **Tech literacy** | Medium-high — uses laptop and smartphone; comfortable with dashboards |
| **Device** | MacBook Pro + iPhone; also uses Frappe on a desktop at office |
| **Connectivity** | Broadband at office; 4G when travelling |
| **Language** | Arabic and English (business level) |
| **Primary goal** | Grow business margins; prove food safety compliance to win contracts; build donor trust |
| **Key frustration** | No single view of the business; compliance status unknown until crisis; AI adds confusion not clarity |

## Customer Journey Map

### Stage 1: Daily Business Review (Morning)
- **Trigger:** Arrives at office; opens OwnerPortal on laptop
- **Touchpoint:** TP-06 OwnerPortal — Operations Dashboard (OP-01)
- **Action:** Sees: 12 active lots, 3 in transit, 2 compliance issues flagged, margin at 8.3%
- **Success criteria:** Dashboard loads in < 5 seconds; all KPIs current (< 1 hour old)

### Stage 2: AI Margin Copilot
- **Trigger:** End-of-month margin review
- **Touchpoint:** TP-06 OwnerPortal — Margin Copilot (OP-02)
- **Action:** AI (AGR-CEREAL-080): "Margin is 2% below target. Main driver: 15% higher drying cost at Taiz vs Hodeidah. Suggest moving 200 tons to Hodeidah storage."
- **Action:** Yasser reviews → clicks "Create action item" → task assigned to Logistics
- **Success criteria:** AI suggestion is Read-only; Yasser creates action manually; source data cited

### Stage 3: Compliance Status Review
- **Trigger:** Potential new export contract; buyer demands HACCP certificate proof
- **Touchpoint:** TP-06 OwnerPortal — Compliance Status (OP-03)
- **Action:** Sees all sites Green except Abyan (1 open CAPA)
- **Action:** Drills into Abyan → reviews CAPA → assigns QA Manager to close
- **Success criteria:** Compliance view shows per-site status; drilldown to CAPA in 1 click

### Stage 4: Donor / Audit Preparation
- **Trigger:** UNDP field visit in 2 weeks
- **Touchpoint:** TP-06 OwnerPortal → triggers TP-03 InspectorApp
- **Action:** Generates evidence pack; reviews AI narrative; approves for sharing
- **Delight moment:** 2-week evidence compilation reduced to 30 minutes

## Acceptance Test Scenarios

| ID | Scenario | Expected result | Pass criteria |
|----|---------|----------------|---------------|
| U6-T01 | Open dashboard | KPIs loaded | < 5s; data < 1 hour old |
| U6-T02 | AI Margin Copilot | Suggestion shown as Read-only | Cannot auto-execute; action item created manually |
| U6-T03 | Compliance drilldown | CAPA visible and assignable | 1-click from dashboard to CAPA |
| U6-T04 | Evidence pack for donor | Pack generated and approved | < 30 min total; AI narrative in AR and EN |

---

---

# U7 — System Admin / IT (مسؤول النظام)

## Profile Card

| Field | Detail |
|-------|--------|
| **Name (sample)** | Ibrahim Al-Sana'ani (إبراهيم الصنعاني) |
| **Age** | 26 |
| **Location** | Aden main office + remote (via VPN) |
| **Tech literacy** | Very high — Linux admin; Docker/k3s experience; Python scripting |
| **Device** | Laptop (Ubuntu 22.04); SSH access to servers |
| **Connectivity** | Broadband + WireGuard VPN to all sites |
| **Language** | Arabic and English (technical) |
| **Primary goal** | Zero downtime; successful backups; clean user management |
| **Key frustration** | Can't see health of all field hubs from one place; backup verification is manual |

## Customer Journey Map

### Stage 1: Morning Health Check
- **Trigger:** Ibrahim opens AdminPanel and Grafana
- **Touchpoint:** TP-07 AdminPanel — System Health (AP-01)
- **Action:** Checks CPU, RAM, disk per node; all green except Taiz hub (disk 87% full)
- **Action:** Runs `bench --site yam.local backup` on Taiz hub remotely via WireGuard
- **Success criteria:** System health loaded in < 5s; disk alert auto-generated at 80% threshold

### Stage 2: Field Hub Sync Status
- **Trigger:** Lahj field hub not synced for 48 hours
- **Touchpoint:** TP-07 AdminPanel — Sync Status (AP-05)
- **Action:** Sees 128 pending changes on Lahj hub; connectivity offline (4G down)
- **Action:** Calls Fatima (U2); confirms 4G is down; plans satellite uplink test
- **Success criteria:** Sync status shows last-sync time and pending count per hub

### Stage 3: Backup Verification
- **Trigger:** Daily automated backup job completes
- **Touchpoint:** TP-07 AdminPanel — Backup Status (AP-03)
- **Action:** Sees: Aden central ✅ (22:00); Taiz hub ✅ (23:00); Hodeidah hub ⚠️ (failed — disk full)
- **Action:** Manually triggers Hodeidah backup after clearing disk
- **Success criteria:** Backup status shows last success time + failure reason per node

### Stage 4: User Management
- **Trigger:** New inspector joins the team
- **Touchpoint:** TP-07 AdminPanel — User Management (AP-02)
- **Action:** Creates account with QA Inspector role; assigns to Taiz site only
- **Success criteria:** User can only see Taiz site data (site isolation enforced)

## Acceptance Test Scenarios

| ID | Scenario | Expected result | Pass criteria |
|----|---------|----------------|---------------|
| U7-T01 | Disk > 80% | Alert generated | Admin notified; shown in AP-01 |
| U7-T02 | Backup failure | Failure shown in AP-03 | Admin notified within 1 hour |
| U7-T03 | New user assigned to Taiz | Cannot see Lahj data | Frappe site isolation verified |
| U7-T04 | Field hub 48h offline | Shown in sync status | Last-sync time and pending count visible |

---

---

# U8 — External Auditor / Donor (المدقق الخارجي / المانح)

## Profile Card

| Field | Detail |
|-------|--------|
| **Name (sample)** | Dr. Sarah Mitchell (from FAO/UNDP) |
| **Age** | 44 |
| **Location** | Amman (remote); occasional Yemen site visit |
| **Tech literacy** | High — uses web portals; familiar with compliance documentation |
| **Device** | Laptop; web browser only (no app install) |
| **Connectivity** | Broadband (Amman office) |
| **Language** | English primary; Arabic reading ability (basic) |
| **Primary goal** | Verify that grant funds are being used properly; confirm food safety compliance |
| **Key frustration** | Evidence arrives in PDF dumps; hard to verify authenticity; no self-service |

## Customer Journey Map

### Stage 1: Portal Access
- **Trigger:** YAM Admin provides API key for UNDP portal access
- **Touchpoint:** TP-08 AuditorPortal
- **Action:** Logs in with API key (no Frappe account required); sees evidence pack browser
- **Success criteria:** Login via API key in < 30 seconds; sees only UNDP-entitled data

### Stage 2: Evidence Review
- **Trigger:** Quarterly review of UNDP-funded grain storage project
- **Touchpoint:** TP-08 AuditorPortal — Evidence Pack Browser (AU-01)
- **Action:** Filters by site=Taiz, date=Q1 2026; downloads 1 evidence pack
- **Action:** Verifies watermark "UNDP CONFIDENTIAL" on PDF; checks hash matches
- **Success criteria:** Pack downloadable; watermark present; SHA-256 hash listed

### Stage 3: Compliance Verification
- **Trigger:** FAO requires HACCP compliance status for food security report
- **Touchpoint:** TP-08 AuditorPortal — Compliance Summary (AU-03)
- **Action:** Views aggregated QC pass rates (94%), CAPA closure rate (88%), cert status
- **Success criteria:** Summary is current (< 24 hours old); methodology explained

### Stage 4: IATI Export
- **Trigger:** Donor reporting deadline; IATI XML needed for publication
- **Touchpoint:** TP-08 AuditorPortal — IATI Export (AU-05)
- **Action:** Selects date range; downloads IATI XML
- **Success criteria:** IATI XML validates against IATI schema; activity IDs match grant codes

## Acceptance Test Scenarios

| ID | Scenario | Expected result | Pass criteria |
|----|---------|----------------|---------------|
| U8-T01 | API key login | Access granted | Only UNDP-scoped data visible |
| U8-T02 | Evidence pack download | PDF with watermark + hash | Watermark correct org name; hash matches |
| U8-T03 | Compliance summary | Aggregated stats | < 24h old; methodology in footer |
| U8-T04 | IATI XML export | Valid IATI XML | Validates against IATI 2.03 schema |

---

---

# U9 — AI Copilot (غير بشري — كيان الذكاء الاصطناعي)

## Profile Card

| Field | Detail |
|-------|--------|
| **Agent name** | Various (ComplianceAgent, AnomalyAgent, SummaryAgent, CopilotAgent) |
| **Type** | Non-human AI agent built with OpenJiuwen SDK |
| **Location** | AI Gateway service (Layer 6) + local Ollama (Field Hub) |
| **Language output** | Arabic + English (bilingual) |
| **Input** | Frappe DocType data (redacted); user trigger text; sensor readings |
| **Output** | Structured suggestion with confidence + sources + redaction preview |
| **Autonomy level** | ZERO — never executes actions; always propose-only or execute-with-approval |
| **Primary goal** | Surface the right suggestion to the right person at the right time |
| **Key constraint** | Must degrade gracefully when offline; must never hallucinate silently |

## Agent Journey Map (Lifecycle)

### Stage 1: Model Activation (by Admin/QA Manager)
- **Trigger:** New agent model version ready for deployment
- **Touchpoint:** TP-07 AdminPanel — AI Model Registry (AP-04)
- **Pre-checks:** Trust & safety scan (#361), security scan (#365), evaluation attestation (#387)
- **Action:** QA Manager reviews model card; approves activation
- **Success criteria:** Model activated only after all pre-checks pass; activation logged

### Stage 2: Agent Invocation (by user action)
- **Trigger:** User opens AI Suggestion Panel in any touchpoint
- **Touchpoint:** TP-09 AICopilotPanel (embedded)
- **Action:** OpenJiuwen WorkflowAgent executes:
  1. Receive doctype + docname + user_locale
  2. Fetch redacted context from Frappe API
  3. Retrieve relevant docs from Qdrant vector store (RAG)
  4. Call LLM (local Ollama or cloud)
  5. Return structured suggestion with confidence + sources + redacted fields
- **Success criteria:** Response in < 5s (local) or < 10s (cloud); confidence score included

### Stage 3: Suggestion Review (by human)
- **Trigger:** User sees AI Suggestion Panel
- **Action:** User reads suggestion; sees source citations; sees redaction preview
- **Action:** User clicks [Approve], [Reject], [Escalate], or [Do manually]
- **Success criteria:** All actions logged in AIInteraction DocType with hash

### Stage 4: Fallback Mode (Ollama offline)
- **Trigger:** Local Ollama unavailable; no internet for cloud LLM
- **Action:** AI Panel shows: "AI غير متاح حالياً — يرجى المتابعة يدوياً" (AI unavailable — proceed manually)
- **Success criteria:** System continues to work fully without AI; no crash or blocking

### Stage 5: Model Retirement
- **Trigger:** New model version outperforms current; deprecation policy triggers
- **Touchpoint:** TP-07 AdminPanel — AI Model Registry (AP-04)
- **Action:** Admin sets deprecation date; users notified 7 days in advance
- **Success criteria:** Old model disabled cleanly; all past suggestions still traceable via AIInteraction log

## Agent Design Principles

| Principle | Implementation |
|-----------|---------------|
| No autonomy | All agent output types: Read-only, Propose-only, Execute-with-approval (never auto-execute) |
| PII safety | Presidio redaction before any LLM call; redacted fields shown in UI |
| Auditability | Every interaction logged: hash, user, action, timestamp, model version |
| Graceful degradation | Offline → local Ollama → static rules → manual mode |
| Confidence signalling | Colour-coded: green >80%, yellow 50–80%, red <50%; low-confidence triggers escalation suggestion |
| Bilingual | All outputs in Arabic + English simultaneously |
| Explainability | Source citations: 2–5 specific DocType records that informed the suggestion |

## Acceptance Test Scenarios

| ID | Scenario | Expected result | Pass criteria |
|----|---------|----------------|---------------|
| U9-T01 | ComplianceAgent on complete lot | "All compliance items present" | Confidence > 80%; correct sources |
| U9-T02 | ComplianceAgent on incomplete lot | Missing items listed | Correct items flagged; no false positives |
| U9-T03 | AnomalyAgent on normal sensor data | No alert | No false positives for 24h of normal data |
| U9-T04 | AnomalyAgent on hotspot bin | Alert flagged | Bin identified within 5 min of threshold breach |
| U9-T05 | Ollama offline | "AI unavailable" message shown | System fully functional without AI |
| U9-T06 | PII in context | PII redacted before LLM call | Presidio logs show redaction; LLM never sees raw PII |
| U9-T07 | Approval action | Logged in AIInteraction | Hash, user, timestamp, action_taken all present |

---

---

## Summary: Persona vs Touchpoint Matrix

| Persona | TP-01 SMS | TP-02 Field | TP-03 Inspector | TP-04 Silo | TP-05 Logistics | TP-06 Owner | TP-07 Admin | TP-08 Auditor | TP-09 AI |
|---------|-----------|-------------|----------------|------------|----------------|-------------|-------------|---------------|---------|
| U1 Farmer | **Primary** | — | — | — | — | — | — | — | Receives |
| U2 Supervisor | Secondary | **Primary** | — | — | — | — | — | — | Receives |
| U3 QA Inspector | — | Secondary | **Primary** | — | — | — | — | — | Receives |
| U4 Silo Operator | — | — | — | **Primary** | — | — | — | — | Receives |
| U5 Logistics | — | — | — | — | **Primary** | — | — | — | Receives |
| U6 Owner | — | — | — | — | — | **Primary** | — | — | Receives |
| U7 Admin | — | — | — | — | — | — | **Primary** | — | Manages |
| U8 Auditor | — | — | — | — | — | — | — | **Primary** | Read-only |
| U9 AI | — | — | — | — | — | — | — | — | **Primary** |

---

## Cross-Persona Journey: A Grain Lot Through the Full System

This shows how a single grain lot flows through all personas and touchpoints:

```
1. [U1 Ahmed] sends SMS: حصاد قمح 800 كيلو
        ↓ TP-01 FarmerSMS
2. [System] creates Lot draft in Frappe

3. [U2 Fatima] opens FieldPWA; sees new lot; adds GPS + photo
        ↓ TP-02 FieldPWA (offline)
4. [System] queues lot data; syncs when 4G returns

5. [U4 Mahmoud] imports weighbridge CSV; 795 kg confirmed
        ↓ TP-04 SiloDashboard
6. [System] creates ScaleTicket; mismatch 0.6% (within tolerance)

7. [U3 Khalid] runs QCTest; moisture 9.8%, aflatoxin < 2 ppb → PASS
        ↓ TP-03 InspectorApp
8. [U9 AI ComplianceAgent] checks lot → "Certificate of Origin missing"
9. [U3 Khalid] adds Certificate; AI re-checks → "All items present"

10. [U5 Omar] creates shipment from lot
         ↓ TP-05 LogisticsApp
11. [U9 AI RouteAgent] suggests optimal route → Omar approves
12. [System] generates BOL + Phytosanitary cert (pre-filled)

13. [U6 Yasser] sees shipment on OwnerPortal; 8.1% margin confirmed
         ↓ TP-06 OwnerPortal

14. [U8 Sarah] downloads evidence pack 3 months later
         ↓ TP-08 AuditorPortal
15. [System] serves pack with watermark + IATI export

16. [U7 Ibrahim] verifies all backups and syncs succeeded
         ↓ TP-07 AdminPanel
```

---

## Test Reference Matrix

Use this table as the master acceptance test reference for the entire platform:

| Test ID | Persona | Touchpoint | Stage | Type | Priority |
|---------|---------|-----------|-------|------|---------|
| U1-T01–T06 | U1 Farmer | TP-01 | All stages | Functional | P0 |
| U2-T01–T05 | U2 Supervisor | TP-02 | Offline + sync | Functional | P0 |
| U3-T01–T05 | U3 Inspector | TP-03 | QC + AI + evidence | Functional | P0 |
| U4-T01–T05 | U4 Silo Operator | TP-04 | Sensors + scale | Functional | P1 |
| U5-T01–T05 | U5 Logistics | TP-05 | Shipment + docs | Functional | P1 |
| U6-T01–T04 | U6 Owner | TP-06 | Dashboard + AI | Functional | P1 |
| U7-T01–T04 | U7 Admin | TP-07 | Ops | Functional | P1 |
| U8-T01–T04 | U8 Auditor | TP-08 | Read-only portal | Functional | P2 |
| U9-T01–T07 | U9 AI Copilot | TP-09 | All apps | AI safety | P0 |

**P0 tests must pass before V1.1 release.**  
**All tests must pass before V1.2 release.**

---

## References

- `docs/TOUCHPOINT_APP_BLUEPRINT.md` — Build blueprint for each touchpoint app
- `docs/SMART_FARM_ARCHITECTURE.md` — Full 11-layer technology stack
- `docs/BLUEPRINT_PLAYBOOK_BEGINNER.md` — Platform playbook and release plan
- `docs/Integration Feature Inventory.csv` — UX patterns and AI marketplace features
- `docs/20260222 YAM_AGRI_BACKLOG v1.csv` — 80-item feature backlog (Stage A–I)
