# Metadata Exports

This folder holds **versioned snapshots** of the live Frappe site metadata (DocTypes, fields, permissions, workflows, reports, workspaces).

## Why
- Prevent duplicate DocTypes / roles / fields.
- Align DocTypes to Agriculture E2E processes using *real installed state* (ERPNext + installed apps).
- Enable AI agents to validate architecture consistency.

## How to export (Docker dev stack)
From repo root:

1) Ensure stack is up:
- `cd infra/docker`
- `bash run.sh up`

Note: the dev compose must mount the repo `docs/` into the backend container at `/home/frappe/frappe-bench/docs` (see `infra/docker/docker-compose.yml`).

2) Run export (writes to `docs/metadata_exports/<timestamp>/`):
- `bash run.sh bench --site localhost execute yam_agri_core.yam_agri_core.metadata_export.run`

Optional kwargs:
- `bash run.sh bench --site localhost execute yam_agri_core.yam_agri_core.metadata_export.run --kwargs '{"output_dir":"docs/metadata_exports/manual"}'`

## Outputs
- `doctypes.csv`
- `docfields.csv`
- `docperms.csv`
- `workflows.csv`
- `workflow_states.csv`
- `workflow_transitions.csv`
- `reports.csv`
- `workspaces.csv`
- `workspace_links.csv` (best-effort; depends on installed schema)
