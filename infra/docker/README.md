# Dev Docker helper — infra/docker

This folder contains scripts to run the Frappe/ERPNext dev stack locally.

Dev URL (Windows-friendly):

- [http://localhost:8000/desk](http://localhost:8000/desk)

Quick commands (use WSL / Git Bash on Windows):

```bash
cd infra/docker

# first time only
cp .env.example .env

# start the stack (background)
bash run.sh up

# create the site and install apps (one-time, after 'up')
bash run.sh init

# show logs
bash run.sh logs

# open a shell in the frappe container
bash run.sh shell

# use the helper to run bench commands inside the container
# example: reload app definitions and fixtures
bash run.sh bench --site localhost reload-doc yam_agri_core

# run tests (if configured)
bash run.sh bench --site localhost run-tests

# stop and remove containers
bash run.sh down

# if the UI looks unstyled / missing assets
bash run.sh bench build
```

Notes:

- Ensure `infra/docker/.env` exists (copy `infra/docker/.env.example` and fill secrets).
- On Windows use WSL or Git Bash; `run.ps1` is available for PowerShell users that prefer a wrapper.
- `run.sh` detects `FRAPPE_SERVICE` from `.env` (defaults to `backend`).

Windows note:

- Do not publish HTTP on host port `80` (often reserved by HTTP.sys). This stack publishes on `HTTP_PUBLISH_PORT` (default `8000`).

If you want I can add a small GitHub Actions job to run these checks automatically on PRs.
