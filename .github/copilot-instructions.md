# Copilot Instructions — YAM Agri Core

> **Read this file first. It is the single authoritative context for every AI
> coding session on this repository.**
>
> Specialised agents live in `.github/agents/`. Select the one that matches
> your role for deeper, role-specific guidance:
> - `developer.md` — Frappe app developer (Python / JavaScript)
> - `devops.md` — Infrastructure / DevOps engineer (Docker, CI, k3s)
> - `qa-manager.md` — QA / Food-safety compliance engineer
> - `owner.md` — Platform owner / product lead (Yasser)

---

## 1. What this Platform Does

**YAM Agri** is a cereal-crop supply chain **quality and traceability system**
for Yemen. It tracks grain lots from farm harvest through silo storage to
final shipment, enforces food safety standards (FAO GAP + HACCP/ISO 22000),
and supports donor/auditor evidence reporting.

### Nine Personas (Users)

| ID | Persona | Channel | Key action |
|----|---------|---------|-----------|
| U1 | Smallholder Farmer | 2G SMS (Nokia feature phone) | Register harvest lots; receive alerts |
| U2 | Farm Supervisor | Mobile PWA (Android, offline) | Create lots, capture GPS, crew scheduling |
| U3 | QA / Food Safety Inspector | Frappe Desk (tablet/laptop) | Record QC tests, approve high-risk actions |
| U4 | Silo / Store Operator | Frappe Desk (desktop, LAN) | Monitor bins, import scale tickets |
| U5 | Logistics Coordinator | Mobile PWA + maps | Manage shipment lots, dispatch trucks |
| U6 | Agri-Business Owner (Yasser) | Web dashboard | KPI dashboards, AI suggestions, final approval |
| U7 | System Admin / IT (Ibrahim) | Frappe Desk + CLI via WireGuard VPN | Docker/k3s, users, backups |
| U8 | External Auditor / Donor | Read-only web portal | Download evidence packs |
| U9 | AI Copilot (non-human) | Internal AI Gateway API | Suggest compliance checks, CAPA drafts (never autonomous) |

### Supply Chain Stages

A: Seed & Input Procurement → B: Land Prep & Planting → C: Crop Monitoring →
D: Harvest & Post-Harvest → **E: Storage & Quality** ← V1.1 primary focus →
F: Processing & Milling → G: Packaging & Labelling → H: Transport & Logistics →
**I: Sales & Customer** ← V1.1 secondary focus

---

## 2. Non-Negotiable Rules (apply to every code change)

1. **Every record must belong to a Site** — raise `frappe.ValidationError` if `site` is blank
2. **Site isolation is mandatory** — register BOTH `permission_query_conditions` AND `has_permission` in `hooks.py` for every DocType with a `site` field
3. **QA Manager approves high-risk transitions** — Lot accept/reject, Transfer approval, EvidencePack approval require the `QA Manager` role (enforced server-side via `frappe.has_role`, never client-side only)
4. **AI is assistive only** — AI components may only return suggestion text; they must never call any Frappe write API, submit workflows, or take autonomous action
5. **Never commit secrets** — `.env.example` only; real credentials via environment variables (`frappe.conf` or `os.environ`)
6. **Defence in depth** — every client-side check must be backed by server-side validation in the Python controller
7. **Arabic/RTL first** — all user-facing strings must be wrapped in `__("…")` (JS) or `_("…")` (Python)

---

## 3. Repository Layout

```
yam_agri_core/                        ← repo root
├── .github/
│   ├── copilot-instructions.md       ← THIS FILE
│   ├── agents/                       ← role-specific Copilot agents
│   │   ├── developer.md
│   │   ├── devops.md
│   │   ├── owner.md
│   │   └── qa-manager.md
│   └── workflows/                    ← CI/CD (ci.yml, pr_review.yml, …)
├── apps/
│   └── yam_agri_core/                ← Frappe app root
│       ├── pyproject.toml            ← flit_core packaging (bench pip install)
│       ├── setup.py
│       └── yam_agri_core/            ← Python package (app-level)
│           ├── hooks.py              ← ALL Frappe hooks live here
│           ├── modules.txt
│           ├── patches.txt
│           ├── fixtures/             ← lot_workflow.json (registered via fixtures=[…])
│           ├── translations/ar.csv   ← Arabic translations
│           └── yam_agri_core/        ← Module package (business logic)
│               ├── ai/               ← Pure-Python AI modules (no Frappe DB)
│               ├── api/              ← @frappe.whitelist() RPC endpoints
│               ├── doctype/          ← One folder per DocType
│               │   ├── lot/          ← lot.py, lot.json, lot.js, test_records.json
│               │   └── …
│               ├── seed/             ← Demo data (confirm=1 safety gate)
│               ├── tests/            ← pytest + Frappe unit tests
│               │   ├── test_agr_cereal_001.py   ← pure-Python (runs in CI)
│               │   └── test_doc_validations.py  ← requires bench run-tests
│               ├── workspace/        ← Frappe Workspace JSON definitions
│               ├── boot.py           ← extend_bootinfo / boot_session hooks
│               ├── install.py        ← after_install / after_migrate hooks
│               ├── site_permissions.py ← all site isolation functions
│               ├── uninstall.py
│               └── workflow_setup.py
├── docs/
│   ├── C4 model Architecture v1.1/   ← C4 L1–L3 diagrams (Mermaid)
│   ├── arc42 Architecture v1.1/      ← arc42 §1–13 (ADRs in §9)
│   ├── Docs v1.1/                    ← SDLC docs (data model, RBAC, test plan…)
│   ├── AGENTS_AND_MCP_BLUEPRINT.md
│   ├── PERSONA_JOURNEY_MAP.md
│   └── TOUCHPOINT_APP_BLUEPRINT.md
├── environments/
│   ├── dev/config.yaml
│   ├── staging/config.yaml + k3s-manifest.yaml
│   └── production/config.yaml
├── infra/
│   ├── docker/
│   │   ├── docker-compose.yml        ← dev stack definition
│   │   ├── run.sh                    ← dev ops script (see §7)
│   │   ├── preflight.sh
│   │   └── .env.example              ← copy → .env; never commit .env
│   └── frappe_docker/                ← git submodule (frappe/frappe_docker)
├── pyproject.toml                    ← ruff + pytest config for the monorepo
└── .pre-commit-config.yaml           ← ruff, pre-commit-hooks, prettier
```

**Important:** the Frappe app module is three directories deep:
`apps/yam_agri_core/yam_agri_core/yam_agri_core/`

Python import prefix: `yam_agri_core.yam_agri_core.<module>`
Example: `from yam_agri_core.yam_agri_core.site_permissions import assert_site_access`

---

## 4. Technology Stack (exact versions)

### Core Platform
| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | Frappe | v16 |
| ERP | ERPNext | v16 |
| Agriculture module | Frappe Agriculture | latest compatible |
| Custom app | yam_agri_core | 1.1.0-dev |
| Database | MariaDB (InnoDB — crash recovery) | 10.6 |
| App server | Gunicorn | 2 workers × 4 threads |
| Python | Python | 3.11 |

### Infrastructure (Docker Compose — dev)
| Service | Image | Purpose |
|---------|-------|---------|
| `db` | `mariadb:10.6` | Primary DB; `restart: always` |
| `redis-cache` | `redis:6.2-alpine` | Session + page cache |
| `redis-queue` | `redis:6.2-alpine` | RQ job broker |
| `redis-socketio` | `redis:6.2-alpine` | WebSocket pub/sub |
| `backend` | `frappe/erpnext:v16.5.0` | Gunicorn app server |
| `frontend` | `frappe/erpnext:v16.5.0` | nginx entrypoint |
| `websocket` | `frappe/erpnext:v16.5.0` | Node.js socketio |
| `queue-short` | `frappe/erpnext:v16.5.0` | RQ short worker |
| `queue-long` | `frappe/erpnext:v16.5.0` | RQ long worker |
| `scheduler` | `frappe/erpnext:v16.5.0` | bench schedule |

### Planned V1.2 Infrastructure
| Component | Technology | Notes |
|-----------|-----------|-------|
| Object storage | MinIO (self-hosted S3) | Certificate PDFs, EvidencePack ZIPs |
| Vector store | Qdrant OSS | RAG for AI (FAO GAP, HACCP docs) |
| AI Gateway | FastAPI | PII redaction + LLM routing |
| Local LLM | Ollama + Llama 3.2 3B Q4 | Offline inference (fits 4 GB RAM) |
| IoT Gateway | Python + Mosquitto MQTT | Sensor → Observation records |
| SMS Handler | Python + FastAPI | Africa's Talking webhook |
| Field Hub | Raspberry Pi 4 + frappe-bench (minimal) | Offline edge node per site |
| VPN | WireGuard | IT admin remote access |

### Tooling
| Tool | Version | Purpose |
|------|---------|---------|
| ruff | v0.11.2 | Lint + format (tabs, 110-char lines) |
| pytest | latest | Pure-Python unit tests |
| yamllint | latest | CI YAML lint |
| pre-commit | v4.6.0 hooks | Ruff, trailing-ws, check-yaml, prettier |
| docker compose | v2 | Dev stack |
| k3s | latest | Staging/production |

---

## 5. DocType Reference (V1.1)

All DocTypes are in `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/`.
All use `autoname: "naming_series:"` with series `YAM-[ABBREV]-.YYYY.-`.

### Naming Series Convention
| DocType | Series |
|---------|--------|
| Site | *(user-defined name — master)* |
| StorageBin | `YAM-SB-.YYYY.-` |
| Device | `YAM-DEV-.YYYY.-` |
| Lot | `YAM-LOT-.YYYY.-` |
| Transfer | `YAM-TRF-.YYYY.-` |
| ScaleTicket | `YAM-ST-.YYYY.-` |
| QCTest | `YAM-QCT-.YYYY.-` |
| Certificate | `YAM-CERT-.YYYY.-` |
| Nonconformance | `YAM-NC-.YYYY.-` |
| EvidencePack | `YAM-EP-.YYYY.-` |
| Complaint | `YAM-COMP-.YYYY.-` |
| Observation | `YAM-OBS-.YYYY.-` |

### DocType Field Summary

#### Site (master — user-defined name)
Fields: `site_name` (Data), `site_type` (Farm/Silo/Warehouse/Store/Market/Office), `description`, `geo_location` (Geolocation), `boundary_geojson` (Code/JSON).
The `geo_location` and `boundary_geojson` fields are added as Custom Fields by `install.py` if not already present.

#### StorageBin
Fields: `storage_bin_name`, `site` → Site, `warehouse` → Warehouse (ERPNext), `capacity_kg` (Float), `current_qty_kg` (Float), `status` (Active/Maintenance/Closed), `notes`.
Validation: `capacity_kg >= 0`, `current_qty_kg >= 0`, `current_qty_kg <= capacity_kg`.

#### Device
Fields: `device_name`, `site` → Site, `device_type` (Scale/Temperature Sensor/Humidity Sensor/Other), `serial_number`, `model`, `status` (Active/Inactive), `notes`.

#### Lot (primary traceability unit)
Fields: `lot_number`, `site` → Site, `crop` → Crop (Frappe Agriculture), `qty_kg` (Float), `status` (Draft/Accepted/Rejected/For Dispatch/Dispatched).
**Workflow**: `lot_workflow.json` — `Lot QA Approval`; states: Draft → Accepted → For Dispatch → Dispatched; Rejected at any stage.
Validation rules in `lot.py`:
- `site` required
- `crop` validated against existing Crop records (text alias lookup via `_resolve_crop_name`)
- Status → `Accepted` or `Rejected`: requires `QA Manager` role (server-side check)
- Status → `For Dispatch`: calls `check_certificates_for_dispatch()` — blocks if any linked Certificate is expired

#### Transfer
Fields: `site` → Site, `transfer_type` (Split/Merge/Blend/Move), `from_lot` → Lot, `to_lot` → Lot, `qty_kg`, `transfer_datetime`, `status` (Draft/Submitted/Approved/Rejected), `notes`.
Validation: `qty_kg > 0`; from/to lot site must match transfer site; `Approved`/`Rejected` requires QA Manager role.

#### ScaleTicket
Fields: `ticket_number`, `site` → Site, `device` → Device, `lot` → Lot, `ticket_datetime`, `gross_kg`, `tare_kg`, `net_kg` (computed = gross − tare), `vehicle`, `driver`, `notes`.
Validation: `net_kg >= 0`; device.site and lot.site must match ticket site.

#### QCTest
Fields: `lot` → Lot, `site` → Site, `test_type` (Select), `test_date`, `result_value` (Float), `pass_fail` (Pass/Fail), `notes`.
Methods: `days_since_test()` → int|None; `is_fresh_for_season(max_days)` → bool.

#### Certificate
Fields: `cert_type` (Data), `lot` → Lot, `site` → Site, `expiry_date` (Date).
Method: `is_expired()` → bool (expiry_date < today).

#### Nonconformance
Fields: `site` → Site, `lot` → Lot, `capa_description` (Small Text), `status` (Open/Under Review/Closed).
Validation: `status` defaults to `Open` via `before_insert` (not `on_update`).

#### EvidencePack
Fields: `title`, `site` → Site, `from_date`, `to_date`, `status` (Draft/Prepared/Approved/Rejected), `notes`.
Validation: `from_date <= to_date`; setting `Approved`/`Rejected` requires QA Manager role.

#### Complaint
Fields: `site` → Site, `complaint_date`, `customer_name`, `lot` → Lot, `description`, `status` (Open/Investigating/Closed/Escalated), `resolution`.
Validation: lot.site must match complaint.site.

#### Observation (universal sensor model)
Fields: `site` → Site, `device` → Device, `observed_at` (Datetime), `observation_type`, `value` (Float), `unit`, `quality_flag` (OK/Quarantine/Invalid), `raw_payload` (Long Text), `notes`.
Validation: `quality_flag` defaults to `OK` in `validate()` if not set; device.site must match observation.site.

#### YAM Plot, YAM Soil Test, YAM Plot Yield, YAM Crop Variety, YAM Crop Variety Recommendation
All: `site` → Site required. Plot has `area_ha`, `plot_name`. Soil Test has `organic_matter_pct`, `ph`. Yield has `season`, `crop`, `yield_kg_per_ha`. Crop Variety has `variety_name`, `maturity_days`, `drought_tolerance` (0–5). Recommendation has `season`, `crop`, `variety`, `plot` → YAM Plot.

---

## 6. Site Isolation — Implementation Pattern

Site isolation is enforced at **two independent layers**. Both must be
implemented for every DocType with a `site` field:

```python
# hooks.py — BOTH entries required for complete isolation:
permission_query_conditions = {
    "Lot": "yam_agri_core.yam_agri_core.site_permissions.lot_query_conditions",
    # … all site-bearing DocTypes
}
has_permission = {
    "Lot": "yam_agri_core.yam_agri_core.site_permissions.lot_has_permission",
    # … all site-bearing DocTypes
}
```

Layer 1 — `permission_query_conditions`: applied to SQL `WHERE` on every list query (prevents list-view leakage).
Layer 2 — `has_permission`: called on every direct document read (prevents single-record bypass by known name).

Standard helpers in `site_permissions.py`:
- `get_allowed_sites(user)` — returns list from User Permission records; `[]` for System Manager/Administrator (full access)
- `build_site_query_condition(doctype, user)` — returns `None` (full access) or `WHERE site IN (…)` or `"1=0"` (no sites)
- `assert_site_access(site)` — throws `PermissionError` if denied; call in every controller `validate()`
- `_doctype_has_site_permission(doc, user)` — standard `has_permission` implementation for all site-bearing DocTypes

All site isolation is bypassed for `Administrator` and users with `System Manager` role.

---

## 7. Hooks in `hooks.py`

The Frappe app's entry-point file. Complete list of active hooks:

```python
# App identity
app_name = "yam_agri_core"
app_title = "YAM Agri Core"
app_version = "1.1.0-dev"
required_apps = ["frappe/erpnext"]

# Apps screen + boot
add_to_apps_screen = [{ "name": "yam_agri_core", "route": "/app/lot", … }]
after_install = "yam_agri_core.yam_agri_core.install.after_install"
after_migrate = "yam_agri_core.yam_agri_core.install.after_migrate"
before_uninstall = "yam_agri_core.yam_agri_core.uninstall.before_uninstall"
fixtures = ["Workflow"]           # loads lot_workflow.json on bench migrate
extend_bootinfo = "…boot.extend_bootinfo"
boot_session   = "…boot.boot_session"   # compatibility alias

# Client-side JS per DocType
app_include_js = ["yam_agri_core.bundle.js"]
doctype_js = { "Lot": "…/lot.js", "Site": "…/site.js", "QCTest": "…/qc_test.js" }

# Site isolation (must be in sync — every DocType needs BOTH)
permission_query_conditions = { … }   # list filtering
has_permission = { … }                # direct-read guard

# Desk search
global_search_doctypes = { "Default": [{"doctype": "Lot"}, …] }
```

**Do not use `ignore_permissions=True`** unless the code is in a scheduled
background job and the reason is documented in a comment.

---

## 8. Python Controller Pattern

Every DocType controller must follow this pattern:

```python
# apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/my_doctype/my_doctype.py
import frappe
from frappe import _
from frappe.model.document import Document
from yam_agri_core.yam_agri_core.site_permissions import assert_site_access

class MyDoctype(Document):
    def before_insert(self):
        # Set default values that must be committed (NOT on_update)
        if not self.get("status"):
            self.status = "Open"

    def validate(self):
        # 1. Non-negotiable site check
        if not self.get("site"):
            frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)
        assert_site_access(self.get("site"))

        # 2. High-risk state transition guard
        new_status = (self.get("status") or "").strip()
        if new_status in ("Approved", "Rejected"):
            old_status = frappe.db.get_value("MyDoctype", self.name, "status") if self.name else None
            if old_status != new_status and not frappe.has_role("QA Manager"):
                frappe.throw(
                    _("Only a user with role 'QA Manager' may set status to {0}").format(new_status),
                    frappe.PermissionError,
                )

        # 3. Cross-site consistency checks
        linked_lot = self.get("lot")
        if linked_lot:
            lot_site = frappe.db.get_value("Lot", linked_lot, "site")
            if lot_site and lot_site != self.get("site"):
                frappe.throw(_("Lot site must match this record's site"), frappe.ValidationError)
```

**Critical:** Default values that must persist to the database belong in
`before_insert`, **not** `on_update` (which fires after the DB write).

---

## 9. JavaScript Client Pattern

```javascript
// apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/lot/lot.js
frappe.ui.form.on("Lot", {
    refresh(frm) {
        // Use __() for all user-visible strings (Arabic/RTL translation)
        if (frm.doc.status === "For Dispatch") {
            frm.add_custom_button(__("Verify Certificates"), () => {
                frappe.call({
                    method: "yam_agri_core.yam_agri_core.api.lot.check_dispatch_readiness",
                    args: { lot: frm.doc.name },
                    callback(r) {
                        if (r.message?.ok) {
                            frappe.show_alert({ message: __("All certificates valid"), indicator: "green" });
                        }
                    }
                });
            });
        }
    },
    site(frm) {
        // Auto-fill child records when site changes
        if (frm.doc.site) {
            frm.set_query("storage_bin", () => ({ filters: { site: frm.doc.site } }));
        }
    }
});
```

Business logic must live in the Python controller. JavaScript is **UX only**.

---

## 10. AI Module Pattern

The AI recommender (`ai/agr_cereal_001.py`) is **pure Python** — no Frappe
imports, no DB access. This allows it to run in CI without a live Frappe bench.

The API wrapper (`api/agr_cereal_001.py`) handles:
1. `@frappe.whitelist()` decoration
2. `assert_site_access(site)` check
3. Reads from DB (`frappe.get_all`)
4. Calls the pure AI function
5. Returns serialised JSON — **no writes to DB**

AI suggestions stored in DocType fields must be in **read-only** fields.
No AI code path may call `frappe.get_doc(…).save()` or `frappe.new_doc(…).insert()`.

Future AI Gateway (V1.2) must:
- Redact PII (names, phones, prices, GPS coords) before any external LLM call
- Log every interaction: `(timestamp, user, record_type, record_name, task, SHA-256(prompt), SHA-256(response))`
- Route to Ollama (local) first; fall back to cloud LLM only if local is unavailable
- Return suggestion text only — never DocType write instructions

---

## 11. RBAC — Roles and Role Profiles

Use **ERPNext standard roles** only. Do not create custom role names.
Map job functions to **Role Profiles** (bundles of standard roles):

| Role Profile | Standard roles | Personas |
|-------------|---------------|---------|
| YAM Farm Ops | `Agriculture Manager`, `Stock User` | U2 Farm Supervisor |
| YAM QA Manager | `Quality Manager` | U3 QA/Food Safety Inspector |
| YAM Warehouse | `Stock User`, `Stock Manager`* | U4 Silo/Store Operator |
| YAM Logistics | `Delivery User` | U5 Logistics Coordinator |
| YAM Owner | `System Manager` (prod: read-only dashboards) | U6 Owner (Yasser) |
| YAM IT Admin | `System Manager` | U7 IT Admin (Ibrahim) |
| YAM Auditor | `Auditor` (read-only) | U8 External Auditor |

*`Stock Manager` only when workflow step requires it.

**In Frappe controllers, check roles using `frappe.has_role("Quality Manager")` or
`frappe.has_role("QA Manager")` (where `QA Manager` is the role name used in
DocType permission rows).** Never hard-code role names as string literals in
business logic — use named constants.

---

## 12. Coding Standards

### Python
- **Indentation**: Tabs (Frappe convention — `ruff format` enforces this)
- **Line length**: 110 characters (ruff config in `pyproject.toml`)
- **Imports**: sorted by ruff (stdlib → third-party → frappe → yam_agri_core → local)
- **ORM**: always use `frappe.get_all`, `frappe.db.get_value`, `frappe.get_doc` — never `frappe.db.sql` with f-strings
- **Translations**: `_("…")` for Python user-facing strings
- **Secrets**: use `frappe.conf.get("key")` or `os.environ.get("KEY")` — never literals

### DocType JSON
- DocType names: **Title Case Singular** (e.g., `"Scale Ticket"`, not `"ScaleTickets"`)
- Transaction DocTypes: `"autoname": "naming_series:"` with series `YAM-[ABBREV]-.YYYY.-`
- Master DocTypes (Site, Device): user-defined name (no autoname)
- Must have `"title_field"` set to the most human-readable field
- Every record must have a `"site"` Link field → `"options": "Site"`

### JavaScript
- `camelCase` for variables and functions
- Wrap all user-visible strings in `__("…")`
- Never implement business logic in JS — server-side Python only

---

## 13. Testing

### Pure-Python tests (run in CI without bench)
Location: `apps/yam_agri_core/yam_agri_core/yam_agri_core/tests/test_agr_cereal_001.py`

```bash
# From repo root:
python -m pytest apps/yam_agri_core/yam_agri_core/yam_agri_core/tests/test_agr_cereal_001.py -v
```

### Frappe integration tests (require running bench)
Location: `apps/yam_agri_core/yam_agri_core/yam_agri_core/tests/test_doc_validations.py`
(Uses `monkeypatch` to stub `frappe.db`, `frappe.has_role`, etc.)

```bash
# Inside a running bench:
bench --site yam.localhost run-tests --app yam_agri_core
```

### CI test command (`.github/workflows/ci.yml`)
```bash
pytest apps/yam_agri_core/yam_agri_core/yam_agri_core/tests/ -v --tb=short \
  --ignore=…/test_doc_validations.py   # Frappe-db tests excluded from CI
```

### `test_records.json` (per DocType)
Frappe uses `test_records.json` to seed the test DB before `bench run-tests`.
File location: `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/<name>/test_records.json`

---

## 14. Dev Environment (`infra/docker/run.sh`)

```bash
cd infra/docker
cp .env.example .env          # fill in values (never commit .env)

bash run.sh up                 # start Docker Compose stack
bash run.sh init               # create site + install apps (first time only)
bash run.sh logs               # stream logs
bash run.sh shell              # bash shell inside frappe container
bash run.sh bench migrate      # run bench commands (any bench subcommand)
bash run.sh down               # stop stack
bash run.sh reset              # wipe volumes + rebuild (destructive)

# Yemen offline/resilience helpers:
bash run.sh prefetch           # pull + save all images to offline-images.tar
bash run.sh offline-init       # load images from tar + start (no internet)
bash run.sh backup             # backup site DB + files → ./backups/<timestamp>/
bash run.sh restore            # restore from latest backup
bash run.sh status             # show container health + recent logs
```

Inside the container, run `bench` commands directly:
```bash
bench --site localhost migrate
bench --site localhost run-tests --app yam_agri_core
bench --site localhost execute yam_agri_core.yam_agri_core.install.get_lot_crop_link_status
bench export-fixtures --app yam_agri_core          # exports fixtures = ["Workflow"]
```

---

## 15. CI / Lint / Pre-commit

```bash
# Lint (must pass before opening a PR):
pip install ruff
ruff check apps/yam_agri_core
ruff format apps/yam_agri_core --check

# YAML lint:
pip install yamllint
yamllint -d "{extends: relaxed, rules: {line-length: {max: 160}}}" $(git ls-files '*.yml' '*.yaml')

# Pre-commit (runs ruff, check-yaml, check-json, prettier on commit):
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

CI workflows (`.github/workflows/`):
- `ci.yml` — secret scan, YAML lint, Docker Compose validate, Python lint (ruff), env config check, pure-Python tests
- `pr_review.yml` — PR title format (Conventional Commits), size warning, auto-label
- `stale.yml` — stale issue/PR management
- `compose-validation.yml` — runs `preflight.sh` on infra changes

---

## 16. Key Architecture Decisions (from arc42 §9)

| ADR | Decision | Implication |
|-----|---------|------------|
| ADR-001 | Use Frappe + ERPNext as core platform | MariaDB-only; no raw SQL; Frappe ORM for everything |
| ADR-002 | All custom code in `yam_agri_core` app | Never patch `frappe`, `erpnext`, or `agriculture` source files |
| ADR-003 | AI is assistive only via AI Gateway | AI Gateway is mandatory; no Frappe write API exposed to AI |
| ADR-004 | Docker Compose dev → k3s staging/prod | Don't start k3s work until Docker Compose dev is stable |

---

## 17. Yemen-Specific Constraints

These constraints shape every design decision:

| Constraint | Impact |
|-----------|--------|
| **Daily power outages (2–8 h)** | All Docker services `restart: always`; MariaDB InnoDB for crash recovery; daily `bench backup` scheduled |
| **2G/3G only at farms** | SMS-based U1 interface (TP-01 FarmerSMS); offline PWA for U2 (7-day queue); Field Hub Raspberry Pi per site |
| **8 GB RAM laptops** | Docker Compose dev stack must use < 3 GB total |
| **Intermittent internet** | `run.sh prefetch` pre-pulls all images; `offline-init` restores offline; Ollama local LLM for offline AI |
| **Arabic/RTL users** | All Frappe Desk labels, messages, and custom JS must be in RTL-safe Arabic/English bilingual |
| **Field site connectivity** | Field Hub RPi4 runs minimal frappe-bench; syncs to central via Frappe REST API when online |

---

## 18. What NOT to Do

- **Do not** patch `frappe`, `erpnext`, or `agriculture` source files
- **Do not** create custom Frappe roles — use standard ERPNext roles via Role Profiles
- **Do not** add `permission_query_conditions` without also adding `has_permission` (both required)
- **Do not** put default values in `on_update` — use `before_insert` for new records
- **Do not** use `frappe.db.sql` with string interpolation — use Frappe ORM or parameterised queries
- **Do not** write AI code that calls `frappe.get_doc(…).save()` or submits workflows
- **Do not** commit `.env` files with real credentials — `.env.example` only
- **Do not** set `restart: no` on any database or cache service
- **Do not** expose MariaDB port 3306 externally in staging/production
- **Do not** start Kubernetes work before Docker Compose dev is stable and all ATs pass
- **Do not** modify `environments/production/` without QA Manager review and staging test evidence

---

## 19. Automated QC — Frappe Skill Agent

The repository includes an automated QC agent at `tools/frappe_skill_agent.py` that checks
all Python, JavaScript, and JSON source files for Frappe best-practice violations.
Full documentation: `docs/FRAPPE_SKILL_AGENT.md`.

### How to run

**VS Code (quickest):** Press **Ctrl+Shift+B** (Win/Linux) or **Cmd+Shift+B** (macOS) →
select **"Frappe Skill Agent: Run (text report)"**.

**Terminal (all options):**
```bash
python tools/frappe_skill_agent.py                              # text report (default)
python tools/frappe_skill_agent.py --verbose                    # include code pairs for each finding
python tools/frappe_skill_agent.py --format json                # machine-readable JSON
python tools/frappe_skill_agent.py --save-learned proposals.json   # export auto-learned rule proposals
python tools/frappe_skill_agent.py --export-training-data /tmp/training.jsonld.json
```

**Run before every PR** and fix all critical/high findings before opening.

**Exit codes:** `0` = passed (no critical or high findings); `1` = failed; `2` = configuration error.

### How to read the output

```
Result   : ❌ FAILED
Findings : 12 total  (critical:2  high:3  medium:5  low:2)
```

Each finding shows the Rule ID, file + line, and the exact problem. With `--verbose`, negative
and positive code examples are printed for every finding.

### Frappe Skill Rule Set (FS-001 – FS-020)

| Rule ID | Severity | File | Check |
|---------|----------|------|-------|
| FS-001 | Critical | `.py` | `frappe.throw()` called with raw string not wrapped in `_()` |
| FS-002 | High | `.js` | User-visible JS string not wrapped in `__()` |
| FS-003 | Medium | `.json` | DocType JSON: `site` field not marked `reqd: 1` |
| FS-004 | Low | `.json` | DocType JSON: missing `title_field` |
| FS-005 | Medium | `.json` | Transaction DocType missing `track_changes: 1` |
| FS-006 | High | `.py` | Hardcoded email address in non-test Python (extract to constant) |
| FS-007 | Medium | `.py` | Default field value set in `validate()` without a `before_insert()` |
| FS-008 | Medium | `.py` | Broad `except Exception: return []` that silently swallows errors |
| FS-009 | High | `.py` | DocType with `lot` field but no cross-site `lot.site` consistency check |
| FS-010 | Critical | `.py` | AI module (`ai/`) calls a Frappe write API (save/insert/submit) |
| FS-011 | Critical | `hooks.py` | DocType in `permission_query_conditions` but NOT in `has_permission` (or vice versa) |
| FS-012 | Critical | `.py` | Hardcoded password, API key, or token in source |
| FS-013 | High | `.py` | Hardcoded IP address, hostname, or URL |
| FS-014 | High | `.py` | Hardcoded database connection string or host |
| FS-015 | Medium | `.py` | Hardcoded business-rule value (tax rate, discount, trial period) |
| FS-016 | Medium | `.py` | Hardcoded cloud resource identifier (S3 bucket, region, ARN) |
| FS-017 | Medium | `.json` | Master DocType without `track_changes` (no `naming_series`) |
| FS-018 | Low | `.json` | Master DocType with `site` field but no `status` / `is_active` field |
| FS-019 | Medium | `.py` | Hardcoded feature flag or inline `frappe.session.user ==` check |
| FS-020 | High | `.py` | Auto-learned: suspicious pattern not covered by FS-001 to FS-019 |

### Quick-fix cheat sheet

| Rule | Problem | Fix |
|------|---------|-----|
| FS-001 | `frappe.throw("raw string")` | `frappe.throw(_("raw string"), frappe.ValidationError)` |
| FS-002 | `frappe.msgprint("text")` | `frappe.msgprint(__("text"))` |
| FS-003 | `site` field, `reqd` missing or `0` | Add `"reqd": 1` to the `site` field in the DocType JSON |
| FS-006 | Hardcoded email | Extract to a module-level constant |
| FS-009 | No `lot.site` check | Add `lot_site = frappe.db.get_value("Lot", self.lot, "site"); if lot_site != self.site: frappe.throw(…)` |
| FS-011 | PQC/has_permission out of sync | Add both entries to `hooks.py` for every site-bearing DocType |
| FS-012 | Hard-coded token/password | Move to `frappe.conf.get()` or `os.environ.get()` |

### QC Rules Derived from Bug Audit (2026-02-24)

These rules were codified after a full codebase audit. See `docs/BUG_AUDIT_REPORT.md` for the
original findings and how each was fixed.

1. **Always wrap `frappe.throw` messages in `_()`** — even in seed, smoke, and utility files.
   Violations break `bench update-translations` discovery and display untranslated text to Arabic users.

2. **Every DocType with a `lot` field must validate `lot.site == self.site`** in `validate()`.
   The pattern is used by Complaint, ScaleTicket, Transfer — it must be applied consistently.

3. **`before_insert()` for new-record defaults; `validate()` as fallback only.**
   Nonconformance correctly sets `status = "Open"` in `before_insert()`. Follow this for all
   new-record defaults (e.g. `quality_flag = "OK"` in Observation).

4. **Never hardcode test-user emails inline in non-test code.** Extract them to module-level
   constants so a single change propagates everywhere (see `smoke.py` `_AT10_USER_A/_B`).

5. **AI modules must have zero Frappe imports.** The `ai/` directory is pure Python. All DB reads
   and site-permission checks live in the `api/` wrapper.

6. **DocType JSONs must include `reqd: 1` on the `site` field.** Python validation is the
   security gate, but the JSON schema drives the Frappe form UX (red asterisk, client validation).

7. **Transaction DocTypes should set `track_changes: 1`.** For a HACCP/ISO 22000 platform, every
   field change on Lot, Transfer, EvidencePack, etc. must be journalled for audit evidence.

---

## 20. Bug Report Reference

The full bug catalogue is maintained at **`docs/BUG_AUDIT_REPORT.md`**.
All future bugs discovered by the Frappe Skill agent or code reviews should be appended there
following the same format: Category, Rule ID, File, Problem, Before/After, Status.
