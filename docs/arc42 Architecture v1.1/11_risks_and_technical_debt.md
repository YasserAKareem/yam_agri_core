# arc42 §11 — Risks and Technical Debt

> **arc42 Section:** 11  
> **Version:** 1.1  
> **Status:** ⚠️ Draft  
> **Date:** 2026-02-23  
> **Related SDLC doc:** [01_PROJECT_CHARTER.md §7](../Docs%20v1.1/01_PROJECT_CHARTER.md)

---

## 11.1 Architecture Risks

Risks that could affect architectural quality goals or project delivery:

| Risk ID | Risk | Likelihood | Impact | Architectural concern | Mitigation |
|---------|------|-----------|--------|----------------------|-----------|
| AR-01 | **Power outage causes data corruption** — MariaDB crash during write | High | High | Reliability (QS-10) | InnoDB crash recovery; `restart: always`; daily backups; UPS/solar recommended |
| AR-02 | **Internet unavailable during Docker image pull** — blocks dev environment setup | High | Medium | Dev onboarding | `run.sh prefetch` to cache images; `offline-images.tar` distribution |
| AR-03 | **Site isolation breach** — user sees records from another site | Low | Critical | Security (QS-03, QS-04) | Dual-layer: User Permissions + `permission_query_conditions`; AT-10 acceptance test mandatory |
| AR-04 | **AI suggestion executed as action without approval** — autonomous AI action | Low | Critical | AI safety (QS-07) | Architectural enforcement: AI Gateway returns text only; no write API exposed; read-only `ai_suggestion` field |
| AR-05 | **Secret committed to Git** — API key or DB password in repository | Low | Critical | Security (QS-09) | Pre-commit gitleaks scan; `.gitignore` for `.env`; CI secret scan on every PR |
| AR-06 | **MariaDB crash recovery fails after extended power outage** | Medium | High | Reliability | `innodb_force_recovery` documented in ops runbook; tested recovery procedure |
| AR-07 | **Knowledge loss if lead developer leaves** | Low | Medium | Maintainability | This architecture documentation set; SDLC docs; `.github/agents/` instruction files |
| AR-08 | **k3s staging setup blocks V1.1 release** | Medium | Medium | Deployment | Dev must pass all 10 ATs first; staging is optional for V1.1 if dev passes; phased rule |
| AR-09 | **Frappe major version upgrade breaks custom app** | Low | High | Maintainability (QS-19) | Custom app in `yam_agri_core`; no core patches; `bench update` tested on dev first |
| AR-10 | **Local LLM (Llama 3.2 3B Q4) insufficient quality for AI tasks** | Medium | Low | AI quality | Cloud LLM fallback configured; AI is assistive only so lower quality is tolerable |
| AR-11 | **Yemen connectivity degradation prevents cloud LLM access** | High | Low | AI quality | Ollama local fallback is primary; cloud LLM is optional fallback |
| AR-12 | **Frappe Agriculture app compatibility break** | Low | Medium | FR correctness | App pinned to tested version; upgrade only after testing in dev |

---

## 11.2 Technical Debt

Known technical debt items that are deliberately deferred for pragmatic reasons:

| TD ID | Item | Category | Impact | Planned resolution |
|-------|------|----------|--------|-------------------|
| TD-01 | **No automated tests (unit/integration)** — no test suite in `yam_agri_core` | Test coverage | Low in V1.1 (acceptance tests manual); grows over time | V1.2: add pytest-based Frappe tests for critical hooks |
| TD-02 | **InfluxDB deferred** — high-frequency sensor data stored in MariaDB (Observation DocType) | Scalability | Acceptable for V1.1 sensor volume; MariaDB will slow at high frequency | V1.2: add InfluxDB for time-series; keep MariaDB for key alerts |
| TD-03 | **No field-level validation rules documented** — DocType validators in code but not in data model doc | Maintainability | Developer must read code to find validation rules | V1.1 gap: add validation rules to `04_DATA_MODEL.md §3` |
| TD-04 | **PouchDB offline sync not implemented** — Field Hub syncs only when VPN is active | Offline resilience | Field data captured manually; sync on VPN reconnect | V1.2: implement PouchDB offline sync for browser-based field entry |
| TD-05 | **AI Gateway is a stub** — placeholder FastAPI service without production hardening | AI reliability | Sufficient for V1.1 (assistive only; low criticality) | V1.2: add rate limiting, circuit breaker, retry logic |
| TD-06 | **No monitoring stack** — no Prometheus/Grafana in V1.1 | Observability | Issues may go undetected between check-ins | V1.2: add Prometheus + Grafana for staging/production |
| TD-07 | **Workflow diagrams not in code** — state machines documented in text/markdown, not in Frappe Workflow JSON fixtures | Maintainability | Frappe Workflow must be configured manually; can drift from docs | V1.1 gap: export Frappe Workflow fixtures and commit to repo |
| TD-08 | **Season Policy Matrix not populated** — SeasonPolicy DocType exists but no initial data | Business readiness | Season policy gate cannot enforce rules without data | QA Manager must fill Season Policy Matrix before V1.1 go-live |
| TD-09 | **No capacity planning baseline** — no documented resource usage per Lot/Site count | Scalability | Unknown when the system will hit performance limits | V1.2: run load tests; document capacity planning baselines |
| TD-10 | **SMS integration deferred (V1.2)** — Farmer (U1) cannot register lots via SMS | Feature gap | U1 must use Frappe Desk or ask a supervisor to enter data | V1.2: implement Africa's Talking SMS webhook + command parser |
| TD-11 | **Evidence Pack PDF export not styled** — Frappe print format is a basic template | Audit quality | PDF will be functional but not professionally formatted | V1.2: design branded PDF print format |
| TD-12 | **No RBAC tests** — site isolation tested manually (AT-10) but not automated | Security regression | Site isolation could regress after a future code change | V1.2: add automated site isolation test using Frappe test framework |

---

## 11.3 Proposed Missing Data (Architecture View)

The following architecture elements are **identified as needed but not yet fully specified**. They are proposed for completion during V1.1 finalisation or V1.2 planning:

| Gap | Description | Priority | Proposed owner |
|-----|-------------|----------|---------------|
| Season Policy Matrix (initial data) | The SeasonPolicy DocType exists but no initial policy values are defined for wheat/sorghum/barley × spring/autumn | High | QA Manager (U3) |
| DocType field-level validation rules | Validation logic in Python controllers is not documented in the data model | High | Lead Developer |
| Workflow state machine fixtures | Frappe Workflow JSON fixtures should be committed to the repo (not just documented in markdown) | High | Lead Developer |
| HACCP Hazard Analysis worksheet | Full severity × likelihood matrix for each CCP | High | QA Manager (U3) |
| Disaster Recovery Plan (DRP) | Step-by-step recovery from catastrophic failure | Medium | DevOps (U7) |
| AI Model Cards | Per-model cards documenting intended use, limitations, performance on YAM tasks | Medium | Lead Developer + QA Manager |
| Capacity Planning Guide | Resource usage projections per site/lot count | Low | DevOps (U7) |
| Organisation Chart (visual) | Visual org chart diagram (Mermaid) to complement RBAC tables | Low | Owner (U6) |

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial section — V1.1 |
