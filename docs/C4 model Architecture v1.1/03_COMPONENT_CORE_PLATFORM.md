# C4 Level 3 — Component Diagram: Core Platform

> **C4 Level:** 3 — Component  
> **Container:** Frappe Backend (Python / Gunicorn / Frappe Framework v16 / ERPNext v16 / yam_agri_core)  
> **Version:** 1.1  
> **Date:** 2026-02-23  
> **Related:** [← Container Diagram](02_CONTAINER_DIAGRAM.md) | [Component: AI Layer →](04_COMPONENT_AI_LAYER.md)

---

## Purpose

This diagram zooms into the **Frappe Backend container** and shows its internal logical components — modules, DocTypes, hooks, and permission layers. It answers: **What are the logical pieces inside the core platform and how do they interact?**

---

## Diagram

```mermaid
C4Component
    title Component Diagram — Frappe Backend Container (Core Platform)

    %% ── External callers ───────────────────────────────────────────────────────
    Person(webuser,   "Web Users (U2–U6, U8)", "Browser or PWA")
    Container(nginx,  "nginx", "Reverse proxy", "Routes HTTP/HTTPS requests")
    Container(ai_gw,  "AI Gateway", "FastAPI", "Requests AI suggestions")
    Container(iot_gw, "IoT Gateway", "Python/MQTT", "Creates Observation records")
    Container(scale,  "Scale Connector", "Python", "Creates ScaleTicket records")
    ContainerDb(db,   "MariaDB 10.6", "MariaDB", "Persists all data")
    ContainerDb(redis,"Redis", "Redis", "Cache + job queue")
    ContainerDb(minio,"MinIO", "S3", "File attachments")

    System_Boundary(frappe_be, "Frappe Backend Container") {

        %% ── Frappe Framework Core ──────────────────────────────────────────────
        Component(frappe_core, "Frappe Framework Core",
            "Python — frappe package",
            "DocType engine, ORM, REST/RPC API router,\nWorkflow engine, Permission system,\nFile manager, Scheduler, Email/SMS,\nAudit log, WebSocket emit.")

        %% ── ERPNext Modules ────────────────────────────────────────────────────
        Component(erpnext, "ERPNext v16 Modules",
            "Python — erpnext package",
            "Purchase Management\nSales Management\nInventory / Stock\nFinance / Accounting\nHR / Payroll\nCRM\nStandard ERPNext roles and permissions.")

        %% ── Frappe Agriculture ─────────────────────────────────────────────────
        Component(agri_app, "Frappe Agriculture App",
            "Python — agriculture package",
            "Crop DocType\nCrop Cycle DocType\nWater Analysis DocType\nDisease Tracking\nFarm Activity Schedule\nProvides crop master data for yam_agri_core.")

        %% ── yam_agri_core — DocTypes ───────────────────────────────────────────
        Component(doctype_site, "Site DocType",
            "Python: doctype/site/site.py\nJSON: doctype/site/site.json",
            "Master record for farm, silo, store, office.\nFields: site_name, site_type, geo_location,\nboundary_geojson.\nPermissions: System Manager (CRUD), Agriculture Manager (RW),\nQA Manager (read-only).")

        Component(doctype_lot, "Lot DocType",
            "Python: doctype/lot/lot.py\nJSON: doctype/lot/lot.json",
            "Primary traceability unit.\nFields: lot_number, site, crop, qty_kg, status.\nStatus: Draft→Accepted→Rejected→For Dispatch→Dispatched.\nValidation: site required, QA Manager role for accept/reject,\ncertificate expiry check before dispatch.")

        Component(doctype_qctest, "QCTest DocType",
            "Python: doctype/qc_test/qc_test.py\nJSON: doctype/qc_test/qc_test.json",
            "Quality control test result.\nFields: lot, site, test_type, test_date,\nresult_value, pass_fail.\nLinked to Lot; site required.")

        Component(doctype_cert, "Certificate DocType",
            "Python: doctype/certificate/certificate.py\nJSON: doctype/certificate/certificate.json",
            "Compliance certificate with expiry.\nFields: cert_type, lot, site, expiry_date.\nis_expired() method used in dispatch validation.")

        Component(doctype_nc, "Nonconformance DocType",
            "Python: doctype/nonconformance/nonconformance.py\nJSON: doctype/nonconformance/nonconformance.json",
            "CAPA record.\nFields: site, status, description.\nStatus workflow: Open→Investigation→Action→Verification→Closed.\nAuto-set status=Open on creation.")

        Component(doctype_agr, "AGR-CEREAL DocTypes",
            "Python + JSON:\nyam_plot.py/json\nyam_soil_test.py/json\nyam_plot_yield.py/json\nyam_crop_variety.py/json\nyam_crop_variety_recommendation.py/json",
            "Agricultural planning DocTypes.\nYAM Plot: farm plot with GPS boundary.\nYAM Soil Test: pH, organic matter, nutrients.\nYAM Plot Yield: historical yield per season.\nYAM Crop Variety: local variety master.\nYAM Crop Variety Recommendation: AI proposal records.")

        %% ── yam_agri_core — API Layer ──────────────────────────────────────────
        Component(api_agr, "API: AGR-CEREAL-001",
            "Python: api/agr_cereal_001.py\n@frappe.whitelist()",
            "Whitelisted RPC method:\nget_variety_recommendations(site, season, crop, ...)\nAsserts site access, calls AI recommender,\nreturns ranked variety proposals.\nRead-only — no writes.")

        %% ── yam_agri_core — AI Module ──────────────────────────────────────────
        Component(ai_rec, "AI: Crop Recommender",
            "Python: ai/agr_cereal_001.py",
            "Deterministic, explainable recommender.\nInputs: plot, soil_test, yield_history, varieties.\nOutputs: ranked Recommendation dataclasses.\nNo external LLM — pure Python scoring.\nDesigned for auditability (every factor explained).")

        %% ── yam_agri_core — Report ─────────────────────────────────────────────
        Component(report, "Script Report: Crop Variety Recs",
            "Python: report/yam_crop_variety_recommendations/\nJS: yam_crop_variety_recommendations.js",
            "Frappe Script Report.\nCalls AGR-CEREAL-001 API.\nReturns tabular rows + chart payload.\nAccessible in Frappe Desk Insights.")

        %% ── yam_agri_core — Permissions ────────────────────────────────────────
        Component(perms, "Site Permission Layer",
            "Python: site_permissions.py\nhooks.py: permission_query_conditions",
            "Server-side site isolation.\nget_allowed_sites(user) — from User Permission records.\nbuild_site_query_condition(doctype) — SQL WHERE clause.\nApplied to: Site, YAM Plot, YAM Soil Test,\nYAM Plot Yield, YAM Crop Variety,\nYAM Crop Variety Recommendation.\nSystem Manager and Administrator bypass isolation.")

        %% ── yam_agri_core — Install/Migrate ────────────────────────────────────
        Component(install, "Install / Migration Hooks",
            "Python: install.py\nhooks.py: after_install, after_migrate",
            "Runs after app install and every migration:\ncreates default DocType fixtures,\nseed data, role profiles.")

        %% ── yam_agri_core — Seed Data ──────────────────────────────────────────
        Component(seed, "Seed / Demo Data",
            "Python: seed/agr_cereal_001_demo.py\nseed/agr_cereal_001_sample_data.py",
            "Creates demo Site, Plot, Soil Test,\nYield History, and Varieties.\nRequires confirm=1 safety gate.\nUsed for Desk demos and testing.")
    }

    %% ── Relationships ──────────────────────────────────────────────────────────
    Rel(nginx,    frappe_core, "HTTP requests\n(Frappe Desk, REST, RPC)", "HTTP :8000")
    Rel(ai_gw,    api_agr,    "Calls whitelisted RPC\n(variety recommendations)", "Frappe RPC")
    Rel(iot_gw,   frappe_core,"POST Observation record\nvia REST API", "Frappe REST API")
    Rel(scale,    frappe_core,"POST ScaleTicket + Lot update\nvia REST API", "Frappe REST API")

    Rel(frappe_core, doctype_site,   "Manages Site records", "Frappe DocType engine")
    Rel(frappe_core, doctype_lot,    "Manages Lot records", "Frappe DocType engine")
    Rel(frappe_core, doctype_qctest, "Manages QCTest records", "Frappe DocType engine")
    Rel(frappe_core, doctype_cert,   "Manages Certificate records", "Frappe DocType engine")
    Rel(frappe_core, doctype_nc,     "Manages Nonconformance records", "Frappe DocType engine")
    Rel(frappe_core, doctype_agr,    "Manages AGR-CEREAL DocTypes", "Frappe DocType engine")
    Rel(frappe_core, erpnext,        "Uses ERPNext standard\nDocTypes and roles", "Python import")
    Rel(frappe_core, agri_app,       "Uses Agriculture DocTypes\n(Crop, CropCycle)", "Python import")
    Rel(frappe_core, perms,          "Applies permission query\nconditions on every list query", "hooks.py")

    Rel(doctype_lot,  doctype_cert,  "Validates certificate expiry\nbefore dispatch", "Python: check_certificates_for_dispatch()")
    Rel(doctype_lot,  perms,         "Enforced by site isolation\nquery conditions", "SQL WHERE")
    Rel(api_agr,      ai_rec,        "Calls recommend() function", "Python function call")
    Rel(api_agr,      perms,         "Calls assert_site_access()", "Python function call")
    Rel(api_agr,      doctype_agr,   "Reads YAM Crop Variety records\nfrom DB", "frappe.get_all()")
    Rel(report,       api_agr,       "Calls get_variety_recommendations()", "Frappe RPC")

    Rel(frappe_core, db,    "All DocType data reads/writes", "SQL :3306")
    Rel(frappe_core, redis, "Cache and job queue", "Redis protocol")
    Rel(frappe_core, minio, "File attachments", "S3 API")
```

---

## Component Inventory

### Frappe Framework Core

| Capability | Description |
|-----------|-------------|
| **DocType Engine** | ORM layer that maps JSON schema → Python class → MariaDB table |
| **REST API Router** | Auto-generates `/api/resource/{DocType}` CRUD endpoints |
| **RPC Router** | Handles `/api/method/{path}` for `@frappe.whitelist()` functions |
| **Workflow Engine** | State machine transitions with role-based approvals |
| **Permission System** | Role-based + User Permission row-level security |
| **File Manager** | Stores attachments in MinIO (S3) or local filesystem |
| **Scheduler** | Cron-based job runner (`bench schedule`) |
| **Audit Log** | Immutable record of all document changes |
| **WebSocket Emit** | Sends real-time events to Frappe Desk via Redis pub/sub |

### yam_agri_core Custom App — DocTypes

| DocType | File | Key validation rules |
|---------|------|---------------------|
| **Site** | `doctype/site/` | `site_type`: Farm/Silo/Warehouse/Store/Market/Office; Geolocation field |
| **Lot** | `doctype/lot/` | `site` required; QA Manager role required for Accept/Reject; certificate expiry check before dispatch |
| **QCTest** | `doctype/qc_test/` | `site` required; linked to Lot |
| **Certificate** | `doctype/certificate/` | `site` required; `is_expired()` method; expiry check via `lot.py` |
| **Nonconformance** | `doctype/nonconformance/` | `site` required; auto-set `status=Open` on creation |
| **YAM Plot** | `doctype/yam_plot/` | `site` required; GPS boundary GeoJSON; linked to last Crop |
| **YAM Soil Test** | `doctype/yam_soil_test/` | `site` required; organic matter, pH fields |
| **YAM Plot Yield** | `doctype/yam_plot_yield/` | `site` required; historical yield per season |
| **YAM Crop Variety** | `doctype/yam_crop_variety/` | `site` required; maturity_days, drought_tolerance |
| **YAM Crop Variety Recommendation** | `doctype/yam_crop_variety_recommendation/` | Output of AI recommender; stored per site |

### yam_agri_core Custom App — API + AI

| Component | File | Description |
|-----------|------|-------------|
| **AGR-CEREAL-001 API** | `api/agr_cereal_001.py` | `@frappe.whitelist()` RPC; site access check; calls recommender |
| **Crop Recommender AI** | `ai/agr_cereal_001.py` | Pure Python deterministic scoring; no external LLM; returns `Recommendation` dataclasses |
| **Script Report** | `report/yam_crop_variety_recommendations/` | Frappe Script Report + JS chart; calls AGR-CEREAL-001 API |
| **Seed / Demo Data** | `seed/agr_cereal_001_*.py` | Demo data creation with `confirm=1` safety gate |

### Site Permission Layer

| Function | File | Description |
|----------|------|-------------|
| `get_allowed_sites(user)` | `site_permissions.py` | Returns list of sites from User Permission records |
| `build_site_query_condition(doctype)` | `site_permissions.py` | Returns SQL `WHERE site IN (...)` or `1=0` |
| `has_site_permission(site)` | `site_permissions.py` | Boolean check for a specific site |
| `assert_site_access(site)` | `site_permissions.py` | Throws `PermissionError` if access denied |
| `resolve_site(identifier)` | `site_permissions.py` | Resolves site name or site_name field to docname |
| `permission_query_conditions` | `hooks.py` | Frappe hook: applies site query to 6 DocTypes |

---

## Key Code Flows

### Flow 1: Lot Dispatch Validation

```
User sets Lot.status = "For Dispatch"
  → Frappe calls Lot.validate()
  → lot.py: check_certificates_for_dispatch(lot_name, status)
  → frappe.get_all("Certificate", filters={"lot": lot_name})
  → For each cert: is expiry_date < today?
  → If YES: frappe.throw(ValidationError) → dispatch blocked
  → If NO: validation passes → status saved
```

### Flow 2: QA Manager Accept/Reject

```
User sets Lot.status = "Accepted" or "Rejected"
  → Frappe calls Lot.validate()
  → lot.py: checks old_status ≠ new_status
  → frappe.has_role("QA Manager") → False for non-QA users
  → frappe.throw(PermissionError) → change blocked
  → Only if user has QA Manager role: status saved
```

### Flow 3: Site Isolation on List Query

```
GET /api/resource/Lot
  → Frappe calls permission_query_conditions["Lot"]? (not yet defined — proposed gap)
  → For DocTypes that have it (Site, YAM Plot, etc.):
     site_permissions.build_site_query_condition("YAM Plot", user)
     → get_allowed_sites(user)
     → Returns: `tabYAM Plot`.`site` IN ('SITE-001', 'SITE-002')
  → Frappe appends WHERE condition to SQL query
  → Only records for user's sites returned
```

### Flow 4: Variety Recommendation API

```
POST /api/method/yam_agri_core.yam_agri_core.api.agr_cereal_001.get_variety_recommendations
  → assert_site_access(site)
  → _get_varieties(site, crop) → frappe.get_all("YAM Crop Variety", ...)
  → recommend(plot, season, crop, varieties, soil_test, yield_history)
  → Pure Python scoring: base_yield × (1 + yield_adj)
  → Returns ranked list of Recommendation dataclasses
  → Serialised as JSON dict → no writes to DB
```

---

## Proposed Gap: Missing DocTypes in `hooks.py`

The current `permission_query_conditions` in `hooks.py` only covers AGR-CEREAL DocTypes. The following DocTypes also need site isolation query conditions added:

| DocType | Status |
|---------|--------|
| `Lot` | ❌ Missing from `permission_query_conditions` |
| `QCTest` | ❌ Missing |
| `Certificate` | ❌ Missing |
| `Nonconformance` | ❌ Missing |

See [11_PROPOSED_GAPS.md](11_PROPOSED_GAPS.md) for full gap analysis.

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial core platform component diagram — V1.1 |
