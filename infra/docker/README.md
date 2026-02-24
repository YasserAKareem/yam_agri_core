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

# deterministic Phase 0/1 acceptance (setup + restart + build smoke)
bash accept_phase01.sh

# stop and remove containers
bash run.sh down

# if the UI looks unstyled / missing assets
bash run.sh bench build
```

Notes:

- Ensure `infra/docker/.env` exists (copy `infra/docker/.env.example` and fill secrets).
- On Windows use WSL or Git Bash; `run.ps1` is available for PowerShell users that prefer a wrapper.
- `run.sh` detects `FRAPPE_SERVICE` from `.env` (defaults to `backend`).
- `accept_phase01.sh` writes `phase01_acceptance_report.json` with pass/fail per check.

## Offline init (exact steps)

Use this flow for low-connectivity deployments (field/offline laptop).

1. On a machine with internet, prefetch and archive all required images:

```bash
cd infra/docker
cp .env.example .env   # if not present
bash run.sh prefetch
```

Expected output:

- pulls all images from compose
- writes archive at `./offline-images.tar` (default)

1. Transfer archive to target machine (USB/network share):

```bash
# copy this file to target machine under infra/docker/
infra/docker/offline-images.tar
```

1. On target machine (no internet), load images and start services:

```bash
cd infra/docker
cp .env.example .env   # if not present
bash run.sh offline-init
```

Expected output:

- `docker load` completes from archive
- stack starts without pull/build

1. Initialize site/apps (first run on that machine):

```bash
bash run.sh init
```

1. Verify health and logs:

```bash
bash run.sh status
bash run.sh logs
```

1. Create a local recovery point:

```bash
bash run.sh backup
```

### Optional: custom archive path

Override archive location with `OFFLINE_IMAGES_ARCHIVE`:

```bash
OFFLINE_IMAGES_ARCHIVE=/mnt/usb/yam/offline-images.tar bash run.sh prefetch
OFFLINE_IMAGES_ARCHIVE=/mnt/usb/yam/offline-images.tar bash run.sh offline-init
```

Default archive path (when not overridden):

- `./offline-images.tar`

Windows note:

- Do not publish HTTP on host port `80` (often reserved by HTTP.sys). This stack publishes on `HTTP_PUBLISH_PORT` (default `8000`).

If you want I can add a small GitHub Actions job to run these checks automatically on PRs.
