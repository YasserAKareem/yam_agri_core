# API Specification — YAM Agri Platform V1.1

> **SDLC Phase:** Design  
> **Version:** 1.1  
> **Status:** ⚠️ Draft  
> **Date:** 2026-02-23  
> **Related:** [Data Model](04_DATA_MODEL.md) | [System Architecture](03_SYSTEM_ARCHITECTURE.md)

---

## 1. API Overview

The YAM Agri Platform exposes APIs through three mechanisms:

| Mechanism | Base URL | Auth | Notes |
|-----------|----------|------|-------|
| **Frappe REST API** | `/api/resource/{DocType}` | Session cookie or API key+secret | CRUD on all DocTypes |
| **Frappe RPC (whitelisted)** | `/api/method/{method_path}` | Session cookie or API key+secret | Custom business logic |
| **AI Gateway (internal)** | `http://ai-gateway:8001` | Internal service token | AI suggestions only; not exposed externally |

---

## 2. Authentication

### 2.1 API Key + Secret (recommended for integrations)

```http
GET /api/resource/Lot/LOT-2026-001
Authorization: token {api_key}:{api_secret}
Content-Type: application/json
```

**How to generate:** In Frappe Desk → User → API Access → Generate Keys

### 2.2 Session Cookie (Desk / PWA)

```http
POST /api/method/frappe.auth.get_logged_user
Content-Type: application/json

{ "usr": "user@example.com", "pwd": "password" }
```

Response sets `sid` cookie used for subsequent requests.

### 2.3 Permission Enforcement

All API calls are subject to:
- **Role-based permissions** (read/write/submit/cancel per DocType per role)
- **Site isolation** (User Permissions on `Site` field — server-side; no client-side bypass)

---

## 3. Frappe REST API Reference

### 3.1 Standard CRUD Patterns

**List records:**
```http
GET /api/resource/{DocType}?filters=[["site","=","SITE-001"]]&fields=["name","status","lot_type"]&limit=50
Authorization: token {api_key}:{api_secret}
```

**Get single record:**
```http
GET /api/resource/{DocType}/{name}
```

**Create:**
```http
POST /api/resource/{DocType}
Content-Type: application/json

{ "lot_type": "Storage", "crop": "Wheat", "season": "2026-Spring", "site": "SITE-001", "declared_qty_kg": 5000 }
```

**Update:**
```http
PUT /api/resource/{DocType}/{name}
Content-Type: application/json

{ "status": "In Storage", "storage_bin": "BIN-012" }
```

**Delete:**
```http
DELETE /api/resource/{DocType}/{name}
```

### 3.2 DocType Endpoints Summary

| DocType | Endpoint | Key filters |
|---------|----------|------------|
| Site | `/api/resource/Site` | `is_active`, `site_type` |
| StorageBin | `/api/resource/StorageBin` | `site`, `status`, `bin_type` |
| Device | `/api/resource/Device` | `site`, `device_type`, `is_active` |
| Lot | `/api/resource/Lot` | `site`, `status`, `lot_type`, `crop`, `season` |
| Transfer | `/api/resource/Transfer` | `site`, `transfer_type`, `transfer_date` |
| ScaleTicket | `/api/resource/ScaleTicket` | `site`, `lot`, `mismatch_flag` |
| QCTest | `/api/resource/QCTest` | `lot`, `site`, `test_type`, `overall_result` |
| Certificate | `/api/resource/Certificate` | `site`, `cert_type`, `is_expired`, `status` |
| Nonconformance | `/api/resource/Nonconformance` | `site`, `status`, `severity`, `nc_type` |
| EvidencePack | `/api/resource/EvidencePack` | `site`, `from_date`, `to_date`, `lot` |
| Observation | `/api/resource/Observation` | `site`, `device`, `metric_type`, `quality_flag` |

---

## 4. Custom RPC Methods (Whitelisted)

### 4.1 Lot Traceability

#### Trace Backward
Returns the full upstream trace for a Lot (all ancestor Lots, QC tests, certificates, storage bin history).

```http
GET /api/method/yam_agri_core.api.traceability.trace_backward?lot=LOT-2026-001
Authorization: token {api_key}:{api_secret}
```

**Response:**
```json
{
  "message": {
    "lot": "LOT-2026-001",
    "ancestors": [
      {
        "lot": "LOT-2026-000",
        "transfer": "TRF-2026-001",
        "transfer_type": "Split",
        "qty_kg": 2000
      }
    ],
    "qc_tests": [
      { "name": "QCT-2026-001", "test_type": "Moisture", "overall_result": "Pass", "test_date": "2026-02-01" }
    ],
    "certificates": [
      { "name": "CERT-2026-001", "cert_type": "FAO GAP", "expiry_date": "2027-01-01", "status": "Active" }
    ],
    "storage_bins": ["BIN-012", "BIN-005"]
  }
}
```

#### Trace Forward
Returns all downstream Lots derived from the given Lot, with impacted shipment quantities.

```http
GET /api/method/yam_agri_core.api.traceability.trace_forward?lot=LOT-2026-000
```

**Response:**
```json
{
  "message": {
    "lot": "LOT-2026-000",
    "descendants": [
      {
        "lot": "LOT-2026-001",
        "transfer": "TRF-2026-001",
        "lot_type": "Shipment",
        "qty_kg": 2000,
        "status": "Shipped"
      }
    ],
    "total_impacted_kg": 2000
  }
}
```

### 4.2 Compliance Check

Returns missing QC tests, expired/missing certificates, and open nonconformances for a Lot.

```http
GET /api/method/yam_agri_core.api.compliance.check_lot?lot=LOT-2026-001
```

**Response:**
```json
{
  "message": {
    "lot": "LOT-2026-001",
    "season_policy": "SP-Wheat-2026-Spring",
    "missing_tests": ["Mycotoxin"],
    "expired_certs": [],
    "missing_certs": ["Export"],
    "open_nonconformances": 1,
    "can_ship": false,
    "blocking_reasons": ["Mycotoxin test required by season policy", "Export certificate missing"]
  }
}
```

### 4.3 Scale Ticket CSV Import

```http
POST /api/method/yam_agri_core.api.scale.import_csv
Authorization: token {api_key}:{api_secret}
Content-Type: multipart/form-data

file: <scale_tickets.csv>
site: SITE-001
tolerance_pct: 2.0
```

**Response:**
```json
{
  "message": {
    "imported": 48,
    "failed": 2,
    "mismatches": 3,
    "nonconformances_created": 3,
    "errors": [
      { "row": 12, "reason": "Lot LOT-2026-099 not found" },
      { "row": 37, "reason": "Missing net_weight_kg" }
    ]
  }
}
```

### 4.4 Evidence Pack Generation

```http
POST /api/method/yam_agri_core.api.evidence.generate_pack
Content-Type: application/json

{
  "site": "SITE-001",
  "from_date": "2026-01-01",
  "to_date": "2026-02-28",
  "lot": null
}
```

**Response:**
```json
{
  "message": {
    "evidence_pack": "EP-2026-001",
    "qc_tests_count": 12,
    "certificates_count": 3,
    "scale_tickets_count": 48,
    "observations_count": 120,
    "nonconformances_count": 2
  }
}
```

### 4.5 Crop/Variety Recommendations (AGR-CEREAL-001)

```http
POST /api/method/yam_agri_core.yam_agri_core.api.agr_cereal_001.get_variety_recommendations
Content-Type: application/json

{
  "site": "SITE-001",
  "season": "2026",
  "crop": "Wheat",
  "plot": { "last_crop": "Barley", "area_ha": 10 },
  "soil_test": { "organic_matter_pct": 2.7, "ph": 7.4 },
  "yield_history": [
    { "season": "2024", "crop": "Wheat", "yield_kg_per_ha": 2600 }
  ],
  "varieties": [
    { "variety_name": "WHT-Prime", "maturity_days": 115, "drought_tolerance": 4.2 }
  ]
}
```

---

## 5. AI Gateway API (Internal)

> The AI Gateway is an **internal service** only — not exposed to the internet. Frappe calls it from the server side only.

### Base URL
`http://ai-gateway:8001`

### Authentication
Internal service token via environment variable `AI_GATEWAY_TOKEN`.

### 5.1 POST /suggest

Request compliance check, CAPA draft, or evidence pack narrative.

**Request:**
```json
{
  "task": "compliance_check",
  "lot": "LOT-2026-001",
  "context": {
    "crop": "Wheat",
    "season": "2026-Spring",
    "missing_tests": ["Mycotoxin"],
    "open_nc_count": 1
  }
}
```

**Supported tasks:**
| `task` | Description |
|--------|-------------|
| `compliance_check` | List what's missing for compliance on this Lot |
| `capa_draft` | Draft a corrective action plan for a Nonconformance |
| `evidence_narrative` | Draft a human-readable narrative for an EvidencePack |

**Response:**
```json
{
  "suggestion": "Based on the 2026-Spring season policy for Wheat, the following actions are required before shipment: 1) Complete mycotoxin test (aflatoxin B1 < 5 ppb for EU export). 2) Resolve open nonconformance NC-2026-003 (weight mismatch). Estimated time: 2–3 business days.",
  "log_hash": "sha256:abc123...",
  "model": "ollama/llama3.2:3b",
  "tokens_used": 412,
  "redaction_applied": true
}
```

**Security guarantees:**
- PII (farmer names, phone numbers, customer IDs) redacted before sending to any LLM
- Pricing and financial data redacted
- All calls logged with: timestamp, user, lot reference, prompt hash, response hash, model used

---

## 6. SMS Command API (TP-01 FarmerSMS — V1.2)

> ⚠️ This section is **proposed / V1.2 scope**. Not implemented in V1.1.

### Inbound SMS Webhook

```http
POST /api/method/yam_agri_core.sms.handle_inbound
Content-Type: application/json

{
  "from": "+967xxxxxxxxx",
  "text": "حصاد قمح 2000 كيلو",
  "shortcode": "YAM",
  "timestamp": "2026-02-23T10:00:00Z"
}
```

### Supported SMS Commands

| Command (Arabic) | English alias | Action |
|-----------------|---------------|--------|
| `حصاد {crop} {qty} {unit}` | `LOT {crop} {qty} {unit}` | Create Harvest Lot (Draft) |
| `وزن {qty} {unit}` | `WEIGHT {qty} {unit}` | Create ScaleTicket draft |
| `حالة` | `STATUS` | Return status summary of farmer's lots |
| `مساعدة` | `HELP` | Return Arabic help menu |

### SMS Response Format Rules
- Maximum 160 characters per SMS (GSM 7-bit)
- Arabic-safe encoding (no extended characters not in GSM 7-bit Arabic table)
- Lot numbers and dates in numerals only (universal)

---

## 7. Error Codes

| HTTP code | Frappe error key | Meaning |
|-----------|-----------------|---------|
| 200 | — | Success |
| 400 | `ValidationError` | Invalid field value or missing required field |
| 401 | `AuthenticationError` | Missing or invalid API credentials |
| 403 | `PermissionError` | User does not have permission for this record/action |
| 404 | `DoesNotExistError` | Record not found |
| 409 | `DuplicateEntryError` | Duplicate naming series |
| 417 | `ValidationError` | Business rule violation (e.g., season policy not met) |
| 500 | `InternalError` | Unexpected server error — check `frappe.log` |

---

## 8. Rate Limits

| API caller | Limit | Notes |
|------------|-------|-------|
| Internal Frappe Desk | None | Trusted |
| Integration (API key) | 100 requests/minute | Per API key |
| AI Gateway | 20 requests/minute | Per lot; rate-limited to control LLM costs |
| SMS Gateway webhook | 10 requests/second | Africa's Talking callback |

---

## 9. Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial API specification — V1.1 |
