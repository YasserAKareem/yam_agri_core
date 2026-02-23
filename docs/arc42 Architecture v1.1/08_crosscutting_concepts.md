# arc42 §8 — Cross-cutting Concepts

> **arc42 Section:** 8  
> **Version:** 1.1  
> **Status:** ⚠️ Draft  
> **Date:** 2026-02-23  
> **Related SDLC docs:** [06_SECURITY_AND_RBAC.md](../Docs%20v1.1/06_SECURITY_AND_RBAC.md) | [11_AI_GOVERNANCE.md](../Docs%20v1.1/11_AI_GOVERNANCE.md) | [10_COMPLIANCE_AND_QUALITY.md](../Docs%20v1.1/10_COMPLIANCE_AND_QUALITY.md)

---

Cross-cutting concepts are **design decisions and patterns that apply across multiple building blocks** and cannot be attributed to a single component.

---

## 8.1 Security and Access Control

### 8.1.1 Authentication

- **Mechanism:** Frappe built-in authentication (username + password)
- **2FA:** Optional TOTP via Frappe 2FA module (recommended for QA Manager and IT Admin)
- **Session:** Frappe session cookies (HTTP-only; Secure flag on HTTPS)
- **API access:** Frappe API keys for service-to-service (AI Gateway → Frappe; Scale importer)

### 8.1.2 Authorisation — Role-Based Access Control (RBAC)

Frappe's standard Role/Permission system is used exclusively. No custom authorisation framework.

| Level | Mechanism |
|-------|-----------|
| DocType read/write/submit | Frappe DocPerm table (per DocType per Role) |
| Workflow transitions | Frappe Workflow transition conditions (role-based) |
| High-risk actions | Workflow approval gates (QA Manager role required) |

**Role Profiles** (bundles of ERPNext roles) map job functions to permissions:

| Role Profile | Roles included | Job function |
|-------------|---------------|-------------|
| YAM Farm Ops | Agriculture Manager, Stock User | Farm Supervisor (U2) |
| YAM QA Manager | Quality Manager | QA/Food Safety Inspector (U3) |
| YAM Warehouse | Stock User | Silo/Store Operator (U4) |
| YAM Logistics | Delivery User | Logistics Coordinator (U5) |
| YAM Owner | System Manager | Agri-Business Owner (U6) |
| YAM IT Admin | System Manager | System Admin/IT (U7) |
| YAM Auditor | Auditor (read-only) | External Auditor (U8) |

Full permission matrix: [06_SECURITY_AND_RBAC.md §3](../Docs%20v1.1/06_SECURITY_AND_RBAC.md).

### 8.1.3 Site Isolation

Site isolation is the most critical security property of the system.

**Implementation — two layers:**

```python
# Layer 1: User Permission record (Frappe built-in)
# Admin creates: User Permission → user=ahmed@yam.com, Allow=Site, For Value=SITE-FARM-001

# Layer 2: Permission Query Conditions (hooks.py)
permission_query_conditions = {
    "Lot":             "yam_agri_core.permissions.lot_permission_query",
    "QCTest":          "yam_agri_core.permissions.qctest_permission_query",
    "Certificate":     "yam_agri_core.permissions.certificate_permission_query",
    "Nonconformance":  "yam_agri_core.permissions.nonconformance_permission_query",
    "Observation":     "yam_agri_core.permissions.observation_permission_query",
    # ... all DocTypes with `site` field
}

# permissions.py example:
def lot_permission_query(user):
    sites = get_user_sites(user)  # reads User Permission records
    return f"`tabLot`.`site` IN ({', '.join(frappe.db.escape(s) for s in sites)})"
```

**Test:** AT-10 (acceptance test 10) must pass before V1.1 release.

### 8.1.4 Secrets Management

| Rule | Implementation |
|------|---------------|
| No secrets in Git | Only `.env.example` committed; `.gitignore` excludes `.env` |
| Runtime injection | All secrets injected as environment variables at container start |
| CI scanning | `gitleaks` runs on every PR via GitHub Actions |
| Secret rotation | Rotate immediately on suspected exposure; dev/staging/production use separate values |

---

## 8.2 Resilience and Availability

### 8.2.1 Crash Recovery

| Risk | Mitigation |
|------|-----------|
| Power cut during DB write | InnoDB crash recovery; `innodb_flush_log_at_trx_commit=1` |
| Container crash | `restart: always` on all Docker services |
| MariaDB corruption | Daily Restic backup to local path; optional offsite S3 |
| Network partition | Frappe offline queue; Field Hub operates autonomously for 7 days |

### 8.2.2 Backup Strategy

```
Daily (automated, 02:00 local time):
  1. bench backup --with-files → /backups/{site}/{date}/
  2. Restic backup /backups → encrypted local repo
  3. Optional: Restic copy → offsite S3 bucket

Recovery:
  1. restore from Restic repo
  2. bench restore --with-private-files
  3. bench migrate (if schema change)
```

### 8.2.3 Offline Operation (Field Hub)

- Field Hub maintains a full local Frappe instance
- All data entered offline is queued for sync
- Sync occurs automatically when WireGuard VPN connects
- Conflict resolution: last-write-wins with manual review for conflicts on critical DocTypes (Lot, Transfer)

---

## 8.3 Internationalisation (i18n) and Localisation

| Requirement | Implementation |
|------------|---------------|
| Arabic/RTL UI | Frappe built-in i18n; Arabic translations in `yam_agri_core/translations/ar.csv` |
| RTL layout | Frappe Desk supports RTL natively when locale = Arabic |
| SMS encoding | GSM 7-bit Arabic-safe encoding in Africa's Talking integration (V1.2) |
| Date format | ISO 8601 for data storage; localised display via Frappe date formatting |
| Number format | Thousand separators per local standard (optional Frappe setting) |
| Currency | Yemeni Rial (YER) + USD for export pricing (ERPNext multi-currency) |

---

## 8.4 AI Governance (Cross-cutting)

All AI interactions are governed by the same rules regardless of which building block initiates them.

### 8.4.1 The Three Mandatory Gates

Every AI call must pass through all three gates:

```
Gate 1: AUTHENTICATE
  Caller must present valid service bearer token to AI Gateway.
  Unauthenticated callers are rejected (HTTP 401).

Gate 2: WHITELIST CHECK
  Task must be in permitted list:
    - compliance_check
    - capa_draft
    - evidence_narrative
  Unknown tasks are rejected (HTTP 403).

Gate 3: REDACT
  Context is scanned for and stripped of:
    - Farmer names / phones → [FARMER_ID] / [PHONE_REDACTED]
    - Customer names / IDs → [CUSTOMER_ID]
    - Pricing / margin data → [PRICE_REDACTED]
    - GPS exact coords → rounded to 2 decimal places
    - Employee names → [ROLE] token
  If redaction cannot be confirmed, call is BLOCKED.
```

### 8.4.2 AI Non-Action Principle

**Structurally enforced** (not just policy):

- AI Gateway returns only `{ "suggestion": "..." }` — no DocType names, no API endpoints
- `gateway_client.py` stores suggestion in a **read-only** field (`ai_suggestion` on Lot/Nonconformance)
- The AI Suggestion Panel in Frappe Desk shows suggestion text + Accept/Dismiss buttons
- "Accept" button creates a **human-authored** record (e.g., a new QCTest or Nonconformance task); the AI suggestion is never directly submitted
- Server-side: no hook in `yam_agri_core` allows the AI Gateway service account to submit, cancel, or amend any DocType

### 8.4.3 AI Interaction Audit Log

Every interaction logged with: `timestamp`, `user`, `record_type`, `record_name`, `task`, `model_used`, `prompt_hash`, `response_hash`, `redaction_applied`, `tokens_used`, `suggestion_accepted`.  
Log is **immutable** — no delete permission on AI Interaction Log DocType.

Full AI governance policy: [11_AI_GOVERNANCE.md](../Docs%20v1.1/11_AI_GOVERNANCE.md).

---

## 8.5 Data Quality and Validation

All data validation follows the **server-side enforcement principle**: client-side validation is UX only; correctness is always guaranteed by server-side hooks.

| Validation type | Implementation |
|----------------|---------------|
| Mandatory fields | `reqd=1` in DocType definition + server `validate()` hook |
| Mass balance | Transfer `validate()`: sum(source qty) == sum(destination qty) ± tolerance |
| Site mandatory | All DocTypes: `validate()` raises if `site` field is empty |
| Sensor range | Observation `validate()`: value vs threshold → quality_flag |
| Certificate expiry | Scheduled daily job + Lot submit validator |
| Season policy gate | Lot `on_submit()`: mandatory tests and certs checked before status=Released |

---

## 8.6 Logging and Monitoring

| Log type | Implementation | Retention |
|----------|---------------|-----------|
| Application errors | Frappe bench log (`logs/frappe.log`, `logs/worker.log`) | 30 days rolling |
| Document change history | Frappe built-in version history (per DocType record) | Indefinite |
| Admin actions | Frappe activity log | 7 years (compliance) |
| AI interactions | AI Interaction Log DocType (immutable) | 7 years (compliance) |
| Access log | nginx `access.log` | 90 days |
| Sensor observations | Observation DocType (MariaDB) | 7 years |

**Monitoring (V1.2+):** Prometheus + Grafana stack for metrics; Frappe Health Check endpoint for k3s liveness/readiness probes.

---

## 8.7 Persistence

| Data category | Storage technology | Notes |
|--------------|-------------------|-------|
| All DocType records | MariaDB 10.6 (InnoDB) | Primary system of record |
| File attachments (PDFs, photos) | MinIO (S3-compatible) | Certificate files, EvidencePack exports |
| Session data | Redis 7 | Ephemeral; lost on Redis restart |
| Job queue | Redis 7 | RQ (Redis Queue) for background workers |
| Real-time (WebSocket) | Redis 7 PubSub | Frappe socketio real-time desk updates |
| Vector embeddings (V1.2+) | Qdrant | For RAG-based AI agents |
| Time-series sensor data (V1.2+) | InfluxDB | High-frequency IoT observations |

---

## 8.8 Error Handling and CAPA Integration

Business errors are treated as system events that **create evidence**, not just exception messages:

| Error condition | System response |
|----------------|----------------|
| Scale ticket weight mismatch | Auto-create Nonconformance (type=Weight Mismatch) |
| Sensor value out of range | Set quality_flag=Quarantine + send alert notification |
| Season policy gate fail | Block Lot submission; display missing items |
| Certificate expired | Block Lot submission; flag certificate as Expired |
| AI Gateway unreachable | Graceful degradation — AI Suggest button shows "AI unavailable"; all other functions continue |
| MariaDB unavailable | HTTP 503 with retry instruction; data persisted in Field Hub queue |

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial section — V1.1 |
