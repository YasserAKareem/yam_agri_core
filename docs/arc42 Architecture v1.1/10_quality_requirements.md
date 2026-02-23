# arc42 §10 — Quality Requirements

> **arc42 Section:** 10  
> **Version:** 1.1  
> **Status:** ⚠️ Draft  
> **Date:** 2026-02-23  
> **Related SDLC doc:** [02_REQUIREMENTS_SPECIFICATION.md §4](../Docs%20v1.1/02_REQUIREMENTS_SPECIFICATION.md) | [07_TEST_PLAN.md](../Docs%20v1.1/07_TEST_PLAN.md)  
> **Standard:** ISO/IEC 25010 (SQuaRE) quality characteristics used as reference

---

## 10.1 Quality Tree

The quality tree shows the **priority-ordered hierarchy** of quality goals for the YAM Agri Platform V1.1:

```
YAM Agri Platform Quality
│
├── 1. FUNCTIONAL CORRECTNESS (highest priority)
│   ├── Data Integrity
│   │   ├── QS-01: Lot mass balance never violated
│   │   └── QS-02: Site field mandatory on all records
│   ├── Site Isolation
│   │   ├── QS-03: Cross-site data access blocked at API level
│   │   └── QS-04: Permission query conditions applied on all list queries
│   └── Season Policy Gating
│       ├── QS-05: Shipment blocked when mandatory QC test missing
│       └── QS-06: Shipment blocked when certificate expired
│
├── 2. SECURITY (critical)
│   ├── AI Safety
│   │   ├── QS-07: AI cannot write/submit any DocType record
│   │   └── QS-08: PII never sent to external LLM without redaction
│   └── Secrets
│       └── QS-09: No credentials committed to Git repository
│
├── 3. RELIABILITY / RESILIENCE
│   ├── Crash Recovery
│   │   ├── QS-10: InnoDB crash recovery after ungraceful power cut
│   │   └── QS-11: All services auto-restart after power restore
│   └── Offline Operation
│       └── QS-12: Field Hub operates 7 days without internet
│
├── 4. PERFORMANCE EFFICIENCY
│   ├── QS-13: Frappe Desk page load ≤ 3 seconds on site LAN
│   ├── QS-14: CSV import 500 rows ≤ 30 seconds
│   ├── QS-15: Trace-backward query ≤ 5 seconds (10 generations)
│   └── QS-16: Dev stack startup ≤ 5 minutes on 8 GB RAM laptop
│
├── 5. USABILITY
│   ├── QS-17: All end-user UI text available in Arabic (RTL)
│   └── QS-18: New user operational within 1 day with documentation
│
└── 6. MAINTAINABILITY
    ├── QS-19: Custom app upgrade survives `bench update`
    └── QS-20: New developer makes first DocType change within 1 working day
```

---

## 10.2 Quality Scenarios

Each scenario specifies: **stimulus → system → response** for an architecturally significant quality requirement.

### Functional Correctness

#### QS-01: Lot Mass Balance

| Element | Description |
|---------|-------------|
| **Source** | Logistics Coordinator (U5) |
| **Stimulus** | Attempts to split LOT-A (5000 kg) into two children totalling 6000 kg |
| **Environment** | Frappe Desk, Transfer form submit |
| **System** | Transfer `validate()` hook |
| **Response** | Server raises `ValidationError`: "Transfer quantity (6000 kg) exceeds source available quantity (5000 kg)" |
| **Measure** | No Transfer record is created; Lot quantities unchanged; user sees error message |

#### QS-03: Cross-site Data Access Blocked

| Element | Description |
|---------|-------------|
| **Source** | Operator user assigned to SITE-A only |
| **Stimulus** | Calls `GET /api/resource/Lot/LOT-SITE-B-001` directly (bypassing UI) |
| **Environment** | Any environment; user is authenticated |
| **System** | Frappe REST API + `permission_query_conditions` hook |
| **Response** | HTTP 403 `PermissionError`; no data returned |
| **Measure** | Zero records from SITE-B are ever accessible to SITE-A user |

#### QS-05: Season Policy Gate — Missing QC Test

| Element | Description |
|---------|-------------|
| **Source** | Logistics Coordinator (U5) |
| **Stimulus** | Submits Lot (type=Shipment) for wheat, season=2026-Spring, missing Protein QCTest |
| **Environment** | Season Policy `SP-WHEAT-2026-SPRING` has Protein as mandatory |
| **System** | Lot `on_submit()` hook → SeasonPolicy check |
| **Response** | Server raises `ValidationError`: "Season Policy requires Protein QCTest. Missing: [Protein]" |
| **Measure** | Lot.docstatus remains 0 (draft/saved); shipment not dispatched |

### Security

#### QS-07: AI Cannot Write DocType Records

| Element | Description |
|---------|-------------|
| **Source** | AI Gateway (external or compromised LLM response) |
| **Stimulus** | LLM response contains a JSON payload attempting to update Lot status |
| **Environment** | AI Gateway response processing |
| **System** | AI Gateway returns only `{ "suggestion": "..." }` text; `gateway_client.py` stores in read-only field |
| **Response** | Suggestion text stored in `ai_suggestion` field; no DocType record is written, submitted, or amended |
| **Measure** | No change in Frappe document state attributable to AI output alone |

#### QS-08: PII Redaction Before External LLM

| Element | Description |
|---------|-------------|
| **Source** | QA Inspector triggers compliance_check for LOT-001 |
| **Stimulus** | Lot context includes farmer name "Ahmed Al-Shaibani" and phone "+967xxxx" |
| **Environment** | Cloud LLM fallback (internet available) |
| **System** | AI Gateway redaction step |
| **Response** | Prompt sent to cloud LLM contains "[FARMER_ID:F-001]" and "[PHONE_REDACTED]"; original values never transmitted |
| **Measure** | AI Gateway redaction audit log confirms redaction_applied=true; prompt hash logged |

### Reliability

#### QS-10: InnoDB Crash Recovery

| Element | Description |
|---------|-------------|
| **Source** | Power cut during active DB write |
| **Stimulus** | Ungraceful shutdown of MariaDB container (simulated: `kill -9` on mysqld) |
| **Environment** | Dev or staging |
| **System** | MariaDB 10.6 InnoDB with `innodb_flush_log_at_trx_commit=1` |
| **Response** | Container restarts automatically; InnoDB runs crash recovery; database accessible within 60 seconds; committed transactions intact; uncommitted transaction rolled back |
| **Measure** | All committed Lot records present; no data corruption; recovery completed without manual intervention |

### Performance

#### QS-13: Frappe Desk Page Load

| Element | Description |
|---------|-------------|
| **Source** | Any authenticated Frappe user |
| **Stimulus** | Opens Lot list view with 1000 records |
| **Environment** | Site LAN (100 Mbps); dev or staging environment |
| **System** | Frappe web server + MariaDB |
| **Response** | List view renders with first 20 records |
| **Measure** | Response time ≤ 3 seconds from form submit to page render |

#### QS-16: Dev Stack Startup

| Element | Description |
|---------|-------------|
| **Source** | Developer on 8 GB RAM laptop |
| **Stimulus** | Runs `./infra/docker/run.sh up` from a cold start (images already cached) |
| **Environment** | Developer laptop; Docker Compose |
| **System** | All Docker Compose services |
| **Response** | Frappe Desk is accessible at `http://localhost:8000` and login works |
| **Measure** | Time from `run.sh up` to working login: ≤ 5 minutes |

### Maintainability

#### QS-19: Custom App Survives `bench update`

| Element | Description |
|---------|-------------|
| **Source** | DevOps (U7) runs `bench update --patch` |
| **Stimulus** | ERPNext or Frappe core is updated to a new patch version |
| **Environment** | Dev environment |
| **System** | `yam_agri_core` custom app |
| **Response** | All custom DocTypes, hooks, and business rules continue to work; no `yam_agri_core` files modified |
| **Measure** | All 10 acceptance tests still pass after `bench update` |

---

## 10.3 Acceptance Test Scenarios (Functional Quality Gate)

All 10 acceptance tests must pass before V1.1 is complete:

| AT# | Scenario | Quality goal |
|----|----------|-------------|
| AT-01 | Create Site → StorageBin → Lot | FR correctness — basic data entry |
| AT-02 | Create QCTest + attach Certificate to Lot | FR correctness — QC evidence |
| AT-03 | Transfer: split Lot into shipment Lot | FR correctness — mass balance |
| AT-04 | Trace backward from shipment Lot | FR correctness — traceability backward |
| AT-05 | Trace forward from storage Lot | FR correctness — traceability forward |
| AT-06 | Block shipment when QC/cert missing | FR correctness — season policy gate |
| AT-07 | Import ScaleTicket CSV → quantity + mismatch flag | FR correctness — scale integration |
| AT-08 | Post sensor Observation → quarantine invalid data | FR correctness — IoT data quality |
| AT-09 | Generate EvidencePack for date range + site | FR correctness — evidence bundling |
| AT-10 | Site A user cannot see Site B data | Security — site isolation |

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial section — V1.1 |
