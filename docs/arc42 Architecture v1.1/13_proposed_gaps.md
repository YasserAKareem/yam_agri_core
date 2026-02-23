# arc42 §13 — Proposed Gaps and Missing Data

> **arc42 Section:** 13 (extension — not a standard arc42 section)  
> **Version:** 1.1  
> **Status:** ⚠️ Draft — awaiting owner prioritisation  
> **Date:** 2026-02-23  
> **Audience:** Platform Owner (U6), QA Manager (U3), Lead Developer, DevOps (U7)

---

This section consolidates all **identified gaps** across the arc42 documentation set and the wider SDLC documentation. It cross-references gaps from `docs/Docs v1.1/00_INDEX.md` and adds architecture-specific gaps identified during this documentation review.

All items are proposed additions for V1.1 completion or V1.2. Priority ratings: **High** (blocks V1.1 go-live), **Medium** (important but not blocking), **Low** (desirable for completeness).

---

## 13.1 High-Priority Gaps (Blocking V1.1 Go-Live)

| Gap ID | Gap Description | Proposed Document / Section | Owner | Status |
|--------|----------------|---------------------------|-------|--------|
| G-01 | **Season Policy Matrix** — SeasonPolicy DocType exists but no initial data values defined for any crop/season combination. Without this, the season policy gate (AT-06) cannot enforce rules. | `docs/Docs v1.1/10_COMPLIANCE_AND_QUALITY.md §5` | QA Manager (U3) | ❌ Missing |
| G-02 | **FAO GAP Middle East — full checklist** — The control mapping table is a framework; the QA Manager must confirm applicable FAO GAP clauses for Yemen cereal crops and mark each as compliant or requiring action. | `docs/Docs v1.1/10_COMPLIANCE_AND_QUALITY.md §2` | QA Manager (U3) | ❌ Missing |
| G-03 | **HACCP Hazard Analysis worksheet** — Severity × Likelihood table for each of the 6 CCPs is required for ISO 22000:2018 §8.3 compliance. | `docs/Docs v1.1/10_COMPLIANCE_AND_QUALITY.md §3` | QA Manager (U3) | ❌ Missing |
| G-04 | **DocType field-level validation rules** — Validation logic in Python controllers is not systematically documented. Developers must read code to find rules. | `docs/Docs v1.1/04_DATA_MODEL.md §3` | Lead Developer | ❌ Missing |
| G-05 | **Workflow state machine Frappe fixtures** — Lot, QCTest, Transfer, Nonconformance, EvidencePack, Certificate workflows documented in text/markdown but not committed as Frappe Workflow JSON fixtures. Risk of configuration drift between environments. | `yam_agri_core/fixtures/` (repo) | Lead Developer | ❌ Missing |
| G-06 | **Frappe Permission fixtures** — DocType permission matrix documented in `06_SECURITY_AND_RBAC.md §3` but not committed as Frappe Custom Permission JSON fixtures. | `yam_agri_core/fixtures/` (repo) | Lead Developer | ❌ Missing |

---

## 13.2 Medium-Priority Gaps

| Gap ID | Gap Description | Proposed Document / Section | Owner | Status |
|--------|----------------|---------------------------|-------|--------|
| G-07 | **Disaster Recovery Plan (DRP)** — Step-by-step recovery procedure from catastrophic failure (full server loss, data corruption, ransomware). | New: `docs/Docs v1.1/13_DISASTER_RECOVERY.md` | DevOps (U7) | 🔲 Stub needed |
| G-08 | **Data Retention & Privacy Policy** — Formal data retention schedules, legal basis for each data category, deletion procedures, and privacy notice for farmers. Required by donor/NGO reporting. | New: `docs/Docs v1.1/14_DATA_PRIVACY.md` | Platform Owner (U6) | 🔲 Stub needed |
| G-09 | **SMS Command Grammar (full EBNF)** — Africa's Talking SMS integration is V1.2, but the command grammar should be defined now to avoid redesign. | `docs/Docs v1.1/05_API_SPECIFICATION.md §6` | Lead Developer | 🔲 Stub needed |
| G-10 | **Incident Response Playbook** — Detailed playbook for the 7-step incident response process (detect → contain → assess → notify → remediate → document → review). | `docs/Docs v1.1/09_OPERATIONS_RUNBOOK.md §7` | DevOps (U7) | ❌ Missing |
| G-11 | **AI Model Cards** — Per-model documentation: intended use, known limitations, ethical considerations, performance benchmarks on YAM compliance tasks, data retention policy of the model vendor. | New: `docs/Docs v1.1/15_AI_MODEL_CARDS.md` | Lead Developer + QA Manager | 🔲 Stub needed |
| G-12 | **Automated site isolation test** — AT-10 is tested manually. Should be an automated regression test to prevent future code changes from regressing site isolation. | `yam_agri_core/tests/test_site_isolation.py` | Lead Developer | ❌ Missing |
| G-13 | **EvidencePack PDF print format** — Current Frappe print format for EvidencePack is a basic template. A professionally branded PDF is needed for auditor and customer submissions. | Frappe print format in `yam_agri_core` | Lead Developer | ❌ Missing |

---

## 13.3 Low-Priority Gaps

| Gap ID | Gap Description | Proposed Document / Section | Owner | Status |
|--------|----------------|---------------------------|-------|--------|
| G-14 | **Capacity Planning Guide** — Resource usage projections per Lot/Site count; identifies when the platform will approach performance limits and what to do. | `docs/Docs v1.1/09_OPERATIONS_RUNBOOK.md §8` | DevOps (U7) | ❌ Missing |
| G-15 | **Org Chart diagram (visual)** — A Mermaid or PNG org chart showing the reporting structure and role assignments to complement the RBAC tables. | `docs/Docs v1.1/06_SECURITY_AND_RBAC.md §2` (or standalone) | Platform Owner (U6) | ❌ Missing |
| G-16 | **Monitoring & alerting runbook** — Prometheus metrics to watch; alert thresholds; on-call escalation. Required for staging/production operations. | `docs/Docs v1.1/09_OPERATIONS_RUNBOOK.md §6` | DevOps (U7) | ❌ Missing |
| G-17 | **Developer onboarding guide** — Step-by-step guide for a new developer to set up the environment, understand the DocTypes, and make a first code change. | New: `docs/Docs v1.1/16_DEVELOPER_ONBOARDING.md` | Lead Developer | 🔲 Stub needed |
| G-18 | **User training materials** — Role-specific quick-start guides (Arabic) for U2 Farm Supervisor, U3 QA Inspector, U4 Silo Operator. | New: `docs/training/` | Lead Developer + Owner | ❌ Missing |
| G-19 | **V1.2 architecture roadmap** — A brief document describing the planned architecture changes for V1.2 (Storage/Harvest AI, SMS, InfluxDB, PouchDB sync). Helps new developers understand the direction. | New: `docs/arc42 Architecture v1.1/14_roadmap_v1.2.md` (or separate) | Platform Owner (U6) | 🔲 Stub needed |
| G-20 | **k3s deployment manifests** — Kubernetes manifests for the staging environment are referenced but not yet written. | New: `infra/k8s/staging/` | DevOps (U7) | ❌ Missing |

---

## 13.4 Architecture-Specific Proposed Additions

These gaps were identified specifically during the arc42 architecture documentation review and were not previously listed in the SDLC index:

| Gap ID | Gap Description | Proposed Section | Priority |
|--------|----------------|-----------------|----------|
| A-01 | **Mass balance tolerance configuration** — The 2% tolerance for scale ticket mismatch and transfer balance is referenced but not documented as a configurable setting. Where is it set? What is the default? | `08_crosscutting_concepts.md §8.5` + data model | High |
| A-02 | **MQTT topic access control** — MQTT broker (Mosquitto) should authenticate devices per-topic. The ACL configuration for the MQTT broker is not documented. | `07_deployment_view.md §7.5` + ops runbook | Medium |
| A-03 | **AI Gateway service token rotation** — The AI Gateway uses a service bearer token. The rotation procedure and token format are not documented. | `08_crosscutting_concepts.md §8.1.4` | Medium |
| A-04 | **Field Hub sync conflict resolution policy** — The policy for resolving data conflicts when a Field Hub reconnects after extended offline operation is not formally defined. | `08_crosscutting_concepts.md §8.2.3` | Medium |
| A-05 | **MinIO bucket policy and IAM** — MinIO access keys and bucket policies for separating cert files from photos from EvidencePack exports are not documented. | `07_deployment_view.md` + security doc | Medium |
| A-06 | **Frappe scheduler job inventory** — All scheduled jobs (certificate expiry check, observation alerts, backup trigger) should be listed in one place for ops visibility. | New: `docs/arc42 Architecture v1.1/` or ops runbook | Low |
| A-07 | **Redis Sentinel / failover for production** — Redis HA configuration for production is mentioned but not detailed. | `07_deployment_view.md §7.4` | Low |

---

## 13.5 Summary by Owner

| Owner | High-priority gaps | Total gaps |
|-------|-------------------|-----------|
| QA Manager (U3) | G-01, G-02, G-03 | 3 |
| Lead Developer | G-04, G-05, G-06, G-12, G-13 + A-01..A-07 | 12 |
| DevOps (U7) | G-07, G-10, G-20 | 3 |
| Platform Owner (U6) | G-08, G-15 | 2 |
| Joint (Developer + QA Manager) | G-11 | 1 |

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial proposed gaps section — V1.1 |
