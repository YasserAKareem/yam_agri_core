# Phase 7 Execution Log (2026-02-27)

## 1) Scope for this pass

- Implement Phase 7 (WBS 7.1 to 7.5) end-to-end.
- Add EvidencePack builder, linked-document model, PDF/ZIP exports, and auditor portal stub.
- Add AT-09 acceptance automation and Phase 7 smoke alias.
- Run migration + test/acceptance verification in bench container.

## 2) WBS coverage status

| WBS | Scope | Status |
|-----|-------|--------|
| 7.1 | EvidencePack builder controller | Completed |
| 7.1.1 | Collect scoped QC/Cert/Scale/Observation/NC records | Completed |
| 7.1.2 | Link scoped records to EvidencePack child table | Completed |
| 7.1.3 | Status flow `Draft -> Ready -> Sent` (server-enforced) | Completed |
| 7.2 | PDF export | Completed |
| 7.2.1 | Jinja2 print format for EvidencePack | Completed |
| 7.2.2 | Include approved AI narrative only | Completed |
| 7.3 | ZIP export | Completed |
| 7.3.1 | Bundle linked attachments into ZIP + manifest | Completed |
| 7.3.2 | Downloadable export from Desk | Completed |
| 7.4 | Auditor read-only portal view stub | Completed |
| 7.5 | AT-09 acceptance automation | Completed |

## 3) Implementation details

### 3.1 EvidencePack data model + controller hardening

- Updated `EvidencePack` DocType schema:
  - required scope range (`from_date`, `to_date`), optional `lot`.
  - lifecycle/status support: `Draft`, `Ready`, `Sent`, `Prepared`, `Approved`, `Rejected`.
  - generation/export metadata: `generated_at`, `generated_by`, `record_count`, `pdf_file`, `zip_file`, `approved_ai_narrative`.
  - linked records table field: `linked_documents`.
- Added child table DocType `EvidencePack Linked Document` with dynamic source link:
  - `source_doctype`, `source_name`, `site`, `document_date`, `status`, `attachment_count`, `summary`.
- Strengthened server validation in EvidencePack controller:
  - date-range checks,
  - canonical transitions for `Draft -> Ready -> Sent`,
  - QA/System/Admin gate for terminal states,
  - site/lot consistency checks.

### 3.2 Backend API (Phase 7)

Added `yam_agri_core.api.evidence_pack` with whitelisted methods:

- `generate_evidence_pack_links`
- `export_evidence_pack_pdf`
- `export_evidence_pack_zip`
- `mark_evidence_pack_sent`
- `get_auditor_evidence_pack_stub` (`allow_guest=True`)

Behavior implemented:

- role gate (`QA Manager`, `System Manager`, `Administrator`),
- site access enforcement,
- scoped record collection by site/date/(optional lot),
- linked row generation with attachment counts,
- PDF render from Jinja include + attachment save,
- ZIP assembly with path-safe filenames + `manifest.json`,
- state progression to `Ready` after build/export,
- optional AI narrative inclusion only when accepted interaction evidence exists.

### 3.3 Desk + portal wiring

- Updated EvidencePack form script actions:
  - `Generate Linked Evidence`, `Export PDF`, `Export ZIP`, `Mark Sent`, `Auditor Portal Stub`, `AI Narrative Summary`.
- AI Narrative flow kept assistive-only with explicit accept/reject logging path.
- Added portal stub page:
  - `/evidence-pack-auditor` Python controller + HTML template.

### 3.4 Health checks + tests

- Added AT-09 automation in health checks:
  - `run_at09_automated_check()`
  - `run_phase7_smoke()` alias
- Added Phase 7 test files:
  - `test_evidence_pack_phase7_api.py`
  - `test_phase7_health_checks.py`

## 4) Defects found and fixed during validation

1. ZIP export manifest serialization failure (`date` not JSON serializable).
   - Fix: `json.dumps(..., default=str)` in ZIP manifest writer.

2. Scope collector regression causing invalid Observation link rows.
   - Symptom: `Could not find Row #N: Source Record: YAM-ST-...` during AT-09.
   - Root cause: accidental indentation made source query run only when `lot` field exists, reusing stale rows for doctypes without `lot`.
   - Fix: corrected query block indentation in `_collect_scope_rows`.

3. Query API compatibility cleanup.
   - Updated new API query calls from deprecated `limit_page_length` to `limit`.

## 5) Verification commands executed

1. `docker exec docker-backend-1 bash -lc 'cd /home/frappe/frappe-bench && ./env/bin/python -m pytest -q apps/yam_agri_core/yam_agri_core/yam_agri_core/tests/test_evidence_pack_phase7_api.py apps/yam_agri_core/yam_agri_core/yam_agri_core/tests/test_phase7_health_checks.py'`
2. `docker exec docker-backend-1 bash -lc 'cd /home/frappe/frappe-bench && bench --site localhost migrate'`
3. `docker exec docker-backend-1 bash -lc 'cd /home/frappe/frappe-bench && bench --site localhost execute yam_agri_core.yam_agri_core.health.checks.run_at09_automated_check'`
4. `docker exec docker-backend-1 bash -lc 'cd /home/frappe/frappe-bench && bench --site localhost execute yam_agri_core.yam_agri_core.health.checks.run_phase7_smoke'`
5. `docker exec docker-backend-1 bash -lc 'cd /home/frappe/frappe-bench && bench --site localhost run-tests --app yam_agri_core'`

## 6) Verification results

- Targeted Phase 7 pytest: `6 passed`.
- AT-09 automated check: `pass`.
- Phase 7 smoke alias: `pass`.
- Full app bench tests: `pass`.
- Migration: completed successfully on `localhost`.

## 7) Files touched in this phase

- `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/evidence_pack/evidence_pack.json`
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/evidence_pack/evidence_pack.py`
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/evidence_pack/evidence_pack.js`
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/evidence_pack_linked_document/evidence_pack_linked_document.json`
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/evidence_pack_linked_document/evidence_pack_linked_document.py`
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/doctype/evidence_pack_linked_document/__init__.py`
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/api/evidence_pack.py`
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/templates/includes/evidence_pack_pdf.html`
- `apps/yam_agri_core/yam_agri_core/www/evidence-pack-auditor.py`
- `apps/yam_agri_core/yam_agri_core/www/evidence-pack-auditor.html`
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/health/checks.py`
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/tests/test_evidence_pack_phase7_api.py`
- `apps/yam_agri_core/yam_agri_core/yam_agri_core/tests/test_phase7_health_checks.py`
