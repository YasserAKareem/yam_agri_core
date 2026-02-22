# Dev Docker helper — infra/docker

This folder contains scripts to run the Frappe/ERPNext dev stack locally.

Quick commands (use WSL / Git Bash on Windows):

```bash
cd infra/docker

# run preflight checks
bash preflight.sh

# start the stack (background)
bash run.sh up -d

# show logs
bash run.sh logs

# open a shell in the frappe container
bash run.sh shell

# use the helper to run bench commands inside the container
# example: reload app definitions and fixtures
bash bench.sh --site site1.local reload-doc yam_agri_core

# run tests (if configured)
bash bench.sh --site site1.local run-tests

# stop and remove containers
bash run.sh down
```

Notes:
- Ensure `infra/.env` exists (copy `infra/.env.example` and fill secrets).
- On Windows use WSL or Git Bash; `run.ps1` is available for PowerShell users that prefer a wrapper.
- `bench.sh` detects `FRAPPE_SERVICE` from `.env` (defaults to `backend`).

If you want I can add a small GitHub Actions job to run these checks automatically on PRs.
