# C4 Level 3 — Component Diagram: Service Adapters

> **C4 Level:** 3 — Component  
> **Containers:** Scale Connector · IoT Gateway · SMS Handler (V1.2)  
> **Version:** 1.1  
> **Date:** 2026-02-23  
> **Related:** [← Component: AI Layer](04_COMPONENT_AI_LAYER.md) | [Dynamic: Lot Lifecycle →](06_DYNAMIC_LOT_LIFECYCLE.md)

---

## Purpose

This diagram zooms into the **Service Adapter** containers — the lightweight integration bridges between the physical world (sensors, scales, SMS) and the Frappe platform. Each adapter follows the same pattern: ingest raw data → validate → normalize → write to Frappe via REST API.

---

## Diagram

```mermaid
C4Component
    title Component Diagram — Service Adapters

    %% ── External inputs ────────────────────────────────────────────────────────
    System_Ext(iot_hw,   "IoT Sensors",         "Temperature, humidity, CO₂,\nmoisture sensors — MQTT publish")
    System_Ext(scale_hw, "Scales / Weighbridges","CSV export or serial port output")
    System_Ext(sms_gw,   "SMS Gateway\n(Africa's Talking)", "Inbound SMS webhook callbacks")

    %% ── Target system ──────────────────────────────────────────────────────────
    Container(frappe, "Frappe Backend", "Python / Gunicorn",
        "Core platform — receives\nObservation, ScaleTicket, Lot records\nvia REST API")

    System_Boundary(adapters, "Service Adapter Containers") {

        %% ════════════════════════════════════════════════════════════════════════
        %% IoT GATEWAY
        %% ════════════════════════════════════════════════════════════════════════
        System_Boundary(iot_gw_box, "IoT Gateway Container (Python)") {

            Component(mqtt_sub, "MQTT Subscriber",
                "Python — paho-mqtt client\nTopics: yam/{site}/{device}/observation",
                "Subscribes to all sensor topics.\nReconnects automatically after network loss.\nBuffers unprocessed messages in local queue\nduring Frappe outages.")

            Component(obs_validator, "Observation Validator",
                "Python — validator.py",
                "Validates incoming sensor readings:\n• Unit check: metric → expected unit\n• Range check: value within threshold bounds\n• Type check: value is numeric\n• Device registration check: device exists in Frappe\nSets quality_flag:\n  Valid → passes all checks\n  Warning → minor deviation\n  Quarantine → out of range or unknown device")

            Component(obs_writer, "Observation Writer",
                "Python — frappe_client.py\nFrappe REST API",
                "Creates Observation DocType records:\nPOST /api/resource/Observation\n{device, site, metric_type, value, unit,\n timestamp, quality_flag}\nTriggers alert if quality_flag = Quarantine\nand threshold_max exceeded.")

            Component(alert_dispatcher, "Alert Dispatcher",
                "Python — alerts.py",
                "Sends Frappe notification when\nObservation exceeds critical threshold:\n• Bin temperature > 35°C\n• Moisture > 14%\n• CO₂ anomaly detected\nCalls Frappe notification API.\nDoes NOT create Nonconformance automatically\n(human decision required).")
        }

        %% ════════════════════════════════════════════════════════════════════════
        %% SCALE CONNECTOR
        %% ════════════════════════════════════════════════════════════════════════
        System_Boundary(scale_box, "Scale Connector Container (Python)") {

            Component(csv_importer, "CSV Importer",
                "Python — csv_import.py\nTriggered by file drop or schedule",
                "Watches import directory for CSV files.\nParses scale ticket CSV:\n  ticket_no, date, operator,\n  gross_weight_kg, tare_weight_kg,\n  net_weight_kg, lot, device\nValidates: required fields present,\ndate parseable, weights numeric.\nRejects rows with errors → error report.")

            Component(lot_matcher, "Lot Matcher",
                "Python — lot_match.py\nFrappe REST API",
                "Resolves lot identifier from CSV to\nFrappe Lot DocType name.\nSupports: lot_number field match,\nLot.name direct match.\nRaises error if Lot not found.\nChecks Lot site matches import site.")

            Component(mismatch_detector, "Mismatch Detector",
                "Python — mismatch.py\nConfigurable tolerance (default 2%)",
                "Compares CSV net_weight_kg against\nLot.qty_kg (declared quantity).\nMismatch = abs(net_weight - declared) / declared > tolerance\nSets ScaleTicket.mismatch_flag = True\nif mismatch detected.")

            Component(ticket_writer, "Scale Ticket Writer",
                "Python — frappe_client.py\nFrappe REST API",
                "Creates ScaleTicket DocType records:\nPOST /api/resource/ScaleTicket\n{ticket_no, lot, site, device, date,\n gross_weight_kg, tare_weight_kg,\n net_weight_kg, mismatch_flag}\nUpdates Lot.qty_kg if net_weight valid.\nReturns import summary: imported/failed/mismatches.")

            Component(nc_creator, "Nonconformance Creator",
                "Python — nc.py\nFrappe REST API",
                "Creates Nonconformance record when\nmismatch_flag = True:\nPOST /api/resource/Nonconformance\n{site, lot, nc_type='Weight Mismatch',\n description, status='Open'}\nLinks to ScaleTicket.\nDoes NOT auto-close or auto-resolve.")
        }

        %% ════════════════════════════════════════════════════════════════════════
        %% SMS HANDLER (V1.2 — Planned)
        %% ════════════════════════════════════════════════════════════════════════
        System_Boundary(sms_box, "SMS Handler Container (FastAPI) — V1.2 Planned") {

            Component(sms_webhook, "SMS Webhook Receiver",
                "FastAPI — POST /inbound\nAfrica's Talking callback",
                "[V1.2 Planned]\nReceives inbound SMS from Africa's Talking.\nValidates HMAC signature.\nExtracts: from_number, text, timestamp.")

            Component(sms_parser, "SMS Command Parser",
                "Python — parser.py\nArabic + English keywords",
                "[V1.2 Planned]\nParses structured SMS commands:\n  حصاد {crop} {qty} {unit} → Harvest Lot\n  وزن {qty} {unit} → ScaleTicket draft\n  حالة / STATUS → lot status query\n  مساعدة / HELP → help menu\nFuzzy matching for common Arabic typos.\nMaps from_number to Frappe farmer/Supplier.")

            Component(sms_action, "SMS Action Handler",
                "Python — actions.py\nFrappe REST API",
                "[V1.2 Planned]\nExecutes parsed SMS command:\n• Create Lot → POST /api/resource/Lot\n• Create ScaleTicket → POST /api/resource/ScaleTicket\n• Lot status query → GET /api/resource/Lot\nEnforces: site access for the farmer.\nReturns confirmation SMS payload.")

            Component(sms_sender, "SMS Response Sender",
                "Python — sender.py\nAfrica's Talking API",
                "[V1.2 Planned]\nSends Arabic confirmation/alert SMS:\n  تأكيد: تم تسجيل الدفعة رقم LOT-001\n  وزن 2000 كيلو\nGSM 7-bit Arabic-safe encoding.\nMax 160 chars per SMS.\nTemplated responses — not AI-generated.")
        }
    }

    %% ── Relationships ──────────────────────────────────────────────────────────
    Rel(iot_hw,   mqtt_sub,      "Publishes sensor readings", "MQTT :8883 (TLS)")
    Rel(mqtt_sub, obs_validator, "Raw reading message", "Python queue")
    Rel(obs_validator, obs_writer, "Validated observation\nwith quality_flag", "Python function call")
    Rel(obs_writer, frappe,      "POST Observation record", "Frappe REST API (HTTPS)")
    Rel(obs_writer, alert_dispatcher, "Trigger alert if\nquality_flag=Quarantine", "Python call")
    Rel(alert_dispatcher, frappe,"Send Frappe notification", "Frappe REST API (HTTPS)")

    Rel(scale_hw,   csv_importer,    "Drops CSV file", "File system / SFTP")
    Rel(csv_importer, lot_matcher,   "Pass parsed rows", "Python function call")
    Rel(lot_matcher, frappe,         "Resolve Lot name", "Frappe REST API (GET)")
    Rel(lot_matcher, mismatch_detector, "Matched lot + weights", "Python function call")
    Rel(mismatch_detector, ticket_writer, "Rows with mismatch_flag set", "Python function call")
    Rel(ticket_writer, frappe,       "POST ScaleTicket, update Lot qty", "Frappe REST API (HTTPS)")
    Rel(mismatch_detector, nc_creator, "Mismatched rows", "Python function call")
    Rel(nc_creator, frappe,          "POST Nonconformance record", "Frappe REST API (HTTPS)")

    Rel(sms_gw,    sms_webhook,   "POST inbound SMS", "HTTPS webhook")
    Rel(sms_webhook, sms_parser,  "Raw SMS text + from_number", "Python function call")
    Rel(sms_parser,  sms_action,  "Parsed command + farmer", "Python function call")
    Rel(sms_action, frappe,       "Create/query Lot or ScaleTicket", "Frappe REST API (HTTPS)")
    Rel(sms_action, sms_sender,   "Confirmation payload", "Python function call")
    Rel(sms_sender, sms_gw,       "Send confirmation SMS to farmer", "HTTPS REST")
```

---

## Component Inventory

### IoT Gateway

| Component | Responsibility |
|-----------|---------------|
| **MQTT Subscriber** | Subscribe to `yam/{site}/{device}/observation` topics; buffer during outages |
| **Observation Validator** | Check units, range, device registration; set `quality_flag` |
| **Observation Writer** | POST Observation to Frappe REST API |
| **Alert Dispatcher** | Send Frappe notification for critical threshold breaches |

**MQTT Topic Schema:**
```
Topic:   yam/{site_code}/{device_id}/observation
Payload: {
  "metric": "temperature",
  "value":  28.5,
  "unit":   "C",
  "ts":     "2026-02-23T10:00:00Z"
}
```

**Validation Thresholds (configurable per device):**

| Metric | Safe range | Warning | Quarantine |
|--------|-----------|---------|-----------|
| Temperature (bin) | 10–30 °C | 30–35 °C | > 35 °C or < 5 °C |
| Humidity (bin) | 50–70 % | 70–80 % | > 80 % |
| Moisture (grain) | 8–14 % | 14–16 % | > 16 % |
| CO₂ | 400–1000 ppm | 1000–2000 ppm | > 2000 ppm |
| Temperature (refrigerator) | 1–5 °C | 5–8 °C | > 8 °C or < 0 °C |

### Scale Connector

| Component | Responsibility |
|-----------|---------------|
| **CSV Importer** | Watch directory or receive upload; parse CSV rows; validate fields |
| **Lot Matcher** | Resolve CSV lot reference to Frappe Lot name |
| **Mismatch Detector** | Compare net_weight_kg vs Lot.qty_kg with configurable tolerance |
| **Scale Ticket Writer** | POST ScaleTicket, update Lot quantity |
| **Nonconformance Creator** | Auto-create NC record for weight mismatches |

**CSV Column Specification:**
```
ticket_no         string   required
date              ISO-8601 required
operator          string   required
gross_weight_kg   float    required
tare_weight_kg    float    required
net_weight_kg     float    computed (gross − tare)
lot               string   required (Lot.name or lot_number)
device            string   optional (Device.name)
```

### SMS Handler (V1.2 — Planned)

| Component | Responsibility |
|-----------|---------------|
| **SMS Webhook Receiver** | Receive Africa's Talking callback; validate HMAC |
| **SMS Command Parser** | Parse Arabic/English commands with fuzzy matching |
| **SMS Action Handler** | Create/query Frappe records; site access check |
| **SMS Response Sender** | Send Arabic confirmation SMS via Africa's Talking |

---

## Proposed Gap: Field Hub Data Sync

The Field Hub (offline Raspberry Pi node) currently acts as an isolated local Frappe instance. A **Field Hub Sync Adapter** is needed to:

1. Queue writes made offline on the Field Hub
2. Detect connectivity restoration
3. Push queued records to central Frappe via REST API
4. Handle conflict resolution (last-write-wins for low-risk fields; manual for Lot status)

See [11_PROPOSED_GAPS.md](11_PROPOSED_GAPS.md) for full gap analysis.

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial service adapters component diagram — V1.1 |
