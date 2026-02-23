# Security & RBAC — YAM Agri Platform V1.1

> **SDLC Phase:** Design  
> **Version:** 1.1  
> **Status:** ⚠️ Draft  
> **Date:** 2026-02-23  
> **Related:** [Requirements Specification](02_REQUIREMENTS_SPECIFICATION.md) | [System Architecture](03_SYSTEM_ARCHITECTURE.md)  
> **Deep reference:** `docs/planning/RBAC_AND_ORG_CHART.md`

---

## 1. Security Principles

| Principle | Implementation |
|-----------|---------------|
| **Least privilege** | Users get the minimum roles needed for their job function |
| **Site isolation** | Users see only data for their assigned Sites |
| **Secrets out of Git** | All credentials via `.env` (never committed); `.env.example` only |
| **Approval gates** | High-risk actions require QA Manager workflow approval |
| **AI safety** | AI never executes actions; Gateway redacts PII before any LLM call |
| **Audit trail** | All changes logged in Frappe document version history |
| **Defence in depth** | Server-side validation backs every client-side check |

---

## 2. Org Chart & Role Mapping

### 2.1 Human Roles → ERPNext Role Profiles

YAM Agri maps job functions to **Role Profiles** (bundles of ERPNext standard roles). Do not create custom roles — use the ERPNext standard set.

| Job function | Role Profile name | ERPNext standard roles included |
|-------------|------------------|--------------------------------|
| Farm Supervisor (U2) | YAM Farm Ops | `Agriculture Manager`, `Stock User` |
| QA / Food Safety Inspector (U3) | YAM QA Manager | `Quality Manager` (+ minimal read roles) |
| Silo / Store Operator (U4) | YAM Warehouse | `Stock User` (+ `Stock Manager` when needed) |
| Logistics Coordinator (U5) | YAM Logistics | `Delivery User` |
| Agri-Business Owner (U6) | YAM Owner | `System Manager` (prod: read-only dashboards) |
| System Admin / IT (U7) | YAM IT Admin | `System Manager` |
| Application Developer | YAM Developer | `System Manager` (dev only; never production) |
| External Auditor (U8) | YAM Auditor | `Auditor` (read-only) |

**Design rule:** Start with the **smallest** subset of ERPNext roles that enables the job. Add roles only when a specific workflow step requires it.

### 2.2 ERPNext Standard Roles Reference

The following standard roles are available and should be used as-is:

```
Accounts Manager · Accounts User · Administrator
Agriculture Manager · Auditor
Delivery Manager · Delivery User
Employee · Employee Self Service
HR User · Item Manager
Maintenance Manager · Maintenance User
Manufacturing Manager · Manufacturing User
Projects Manager · Projects User
Purchase Manager · Purchase Master Manager · Purchase User
Quality Manager
Sales Manager · Sales Master Manager · Sales User
Stock Manager · Stock User
Supplier · Support Team · System Manager · Website Manager
```

> **Never duplicate these roles.** Create Role Profiles that compose them.

---

## 3. Permission Matrix (DocType × Role)

| DocType | YAM Farm Ops | YAM QA Manager | YAM Warehouse | YAM Logistics | YAM Owner | YAM IT Admin | YAM Auditor |
|---------|:-----------:|:--------------:|:-------------:|:-------------:|:---------:|:------------:|:-----------:|
| Site | R | R | R | R | R | R/W | R |
| StorageBin | R/W | R | R/W | R | R | R/W | R |
| Device | R | R | R/W | — | R | R/W | R |
| Lot | R/W/S | R/W/S | R/W/S | R/W | R | R | R |
| Transfer | R/W/S | R/W/S/A | R/W | R | R | R | R |
| ScaleTicket | R/W | R | R/W/S | R | R | R | R |
| QCTest | R | R/W/S/A | R | R | R | R | R |
| Certificate | R | R/W/S | R | R | R | R | R |
| Nonconformance | R | R/W/S/A | R/W | R | R | R | R |
| EvidencePack | R | R/W/S | R | R | R/W | R | R |
| Complaint | R | R/W | R | R/W | R | R | R |
| Observation | R | R | R/W | — | R | R | R |
| SeasonPolicy | — | R/W | — | — | R | R/W | R |

**Legend:** R = Read · W = Write · S = Submit · A = Approve (via Workflow) · — = No access

> This matrix is the **target** permission design. Individual DocType permissions must be configured in Frappe Desk → DocType → Permissions.

---

## 4. Site Isolation

### 4.1 Implementation

Site isolation is **non-negotiable** and enforced at two levels:

**Level 1 — User Permissions (Frappe built-in):**
- Create a `User Permission` record for each user → Site link
- Default: new users have **zero** Site access until explicitly assigned
- Example: `User Permission: User=ahmed@yam.com, Allow=Site, For Value=SITE-FARM-001`

**Level 2 — Permission Query Conditions (server-side):**
- Add a `get_permission_query_conditions` hook in `yam_agri_core/hooks.py`
- All list views and API list queries automatically filtered by user's assigned Sites
- No client-side bypass possible

```python
# hooks.py example
permission_query_conditions = {
    "Lot": "yam_agri_core.permissions.lot_permission_query",
    "QCTest": "yam_agri_core.permissions.qctest_permission_query",
    # ... all DocTypes with site field
}
```

### 4.2 Acceptance Test for Site Isolation

1. Create two sites: `SITE-A` and `SITE-B`
2. Create user `operator-a` with User Permission for `SITE-A` only
3. Create records in both sites
4. Login as `operator-a` → verify: Lot list shows only `SITE-A` records
5. Attempt direct API call: `GET /api/resource/Lot/LOT-SITE-B-001` → expect `403 PermissionError`

---

## 5. High-Risk Action Approvals

The following actions **require workflow approval** before they execute:

| Action | DocType | Required approver role |
|--------|---------|----------------------|
| Accept / Reject a Lot | Lot | Quality Manager (U3) |
| Override certificate expiry | Certificate | Quality Manager (U3) |
| Close a Critical Nonconformance | Nonconformance | Quality Manager (U3) |
| Release Lot for shipment | Lot | Quality Manager (U3) |
| Approve a Lot Transfer (Shipment) | Transfer | Quality Manager (U3) |
| Initiate a Recall | EvidencePack | Quality Manager (U3) + Owner (U6) |
| Activate new AI model | — | Quality Manager (U3) + Owner (U6) |

**Implementation:** Frappe Workflow with transition conditions. Server-side `validate` hooks reject state changes without the workflow approval flag.

---

## 6. Secrets Management

### 6.1 Rules

| Rule | Detail |
|------|--------|
| Never commit `.env` | Only `.env.example` is in Git |
| Use `${env:VARIABLE}` in configs | VS Code MCP config, compose files |
| Rotate after any suspected exposure | Immediately revoke and regenerate API keys |
| Separate secrets per environment | Dev, staging, and production use different credentials |

### 6.2 Required Environment Variables

```bash
# .env.example — copy to .env and fill in real values; never commit .env

# MariaDB
DB_ROOT_PASSWORD=<change_me>
DB_NAME=frappe_db
DB_USER=frappe
DB_PASSWORD=<change_me>

# Frappe Site
SITE_NAME=yam.localhost
ADMIN_PASSWORD=<change_me>

# AI Gateway
AI_GATEWAY_TOKEN=<change_me>
OPENAI_API_KEY=<change_me>          # optional: cloud LLM
ANTHROPIC_API_KEY=<change_me>       # optional: cloud LLM

# SMS
SMS_API_KEY=<change_me>             # Africa's Talking
SMS_USERNAME=<change_me>

# Backup
RESTIC_PASSWORD=<change_me>
BACKUP_S3_BUCKET=<your_bucket>
AWS_ACCESS_KEY_ID=<change_me>
AWS_SECRET_ACCESS_KEY=<change_me>
```

### 6.3 CI Secret Scanning

GitHub Actions workflow `CI / Secret scan` runs `gitleaks` on every PR to detect accidentally committed secrets. PRs fail if secrets are detected.

---

## 7. Network Security

### 7.1 Development

- Frappe Dev server accessible only at `localhost:8000`
- No external exposure; Docker network is isolated

### 7.2 Staging

- Access via **WireGuard VPN only**
- Each developer has a unique WireGuard peer (private key never shared)
- Frappe accessible at `yam-staging.vpn.internal` (internal DNS)
- HTTPS via self-signed cert or Let's Encrypt via Traefik

### 7.3 Production (Future)

- HTTPS enforced; HTTP redirects to HTTPS
- HSTS header enabled
- Frappe behind nginx reverse proxy
- Database accessible only from Frappe containers (not exposed to host network)
- Admin panel accessible only via VPN

---

## 8. AI Security

### 8.1 Redaction Policy (AI Gateway)

Before any data is sent to an external LLM, the AI Gateway **must** redact:

| Data type | Redaction action |
|-----------|-----------------|
| Farmer names and phone numbers | Replace with `[FARMER]` |
| Customer names and IDs | Replace with `[CUSTOMER]` |
| Pricing, margin, financial data | Replace with `[PRICE]` |
| GPS coordinates (exact) | Round to 3 decimal places or replace with region name |
| Employee names | Replace with role only (e.g., `[QA_INSPECTOR]`) |

**Validation:** AI Gateway logs a redaction audit record before every external LLM call. If redaction fails, the call is blocked.

### 8.2 AI Action Prohibition

Server-side enforcement (hooks.py + workflow) ensures:
- No AI call can submit, cancel, or amend any DocType without human action
- AI Gateway returns suggestions only (text responses)
- All AI suggestions are stored as `ai_suggestion` field (read-only; not a workflow action)
- User must explicitly click "Apply Suggestion" which creates a human-authored record

### 8.3 AI Interaction Audit Log

Every AI interaction is logged with:
- `timestamp`
- `user` (who triggered it)
- `record_type` and `record_name` (e.g., `Lot LOT-2026-001`)
- `task` (compliance_check / capa_draft / evidence_narrative)
- `prompt_hash` (SHA-256)
- `response_hash` (SHA-256)
- `model_used`
- `redaction_applied` (boolean)
- `suggestion_accepted` (boolean — updated when user accepts/dismisses)

---

## 9. Data Privacy

### 9.1 Personal Data Inventory

| Data category | DocType/field | Legal basis | Retention |
|---------------|--------------|-------------|----------|
| Farmer mobile number | Lot → farmer → Supplier.mobile | Business necessity | 7 years |
| Employee name | User, Transfer.operator | Employment contract | Duration + 3 years |
| GPS coordinates (lot capture) | Lot.gps_lat/lng | Business necessity | 7 years |
| Customer complaint details | Complaint.description | Customer contract | 7 years |

> ⚠️ **Proposed addition:** A full Data Retention & Privacy Policy document (`14_DATA_PRIVACY.md`) is identified as a gap. See `00_INDEX.md`.

---

## 10. Incident Response (Security)

| Step | Action |
|------|--------|
| 1 | Detect: CI alert, user report, or monitoring alert |
| 2 | Contain: revoke suspected API keys; disable affected user accounts |
| 3 | Assess: determine scope (which sites, records, period affected) |
| 4 | Notify: Platform Owner (U6) and IT Admin (U7) immediately |
| 5 | Remediate: rotate secrets; patch vulnerability; restore from backup if needed |
| 6 | Document: create Nonconformance record of type "Security Incident" |
| 7 | Review: post-incident review within 5 business days |

---

## 11. Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial security & RBAC document — V1.1 |
