# Deployment Guide — YAM Agri Platform V1.1

> **SDLC Phase:** Deployment  
> **Version:** 1.1  
> **Status:** ⚠️ Draft  
> **Date:** 2026-02-23  
> **Related:** [System Architecture](03_SYSTEM_ARCHITECTURE.md) | [Operations Runbook](09_OPERATIONS_RUNBOOK.md)  
> **Deep reference:** `docs/AGENTS_AND_MCP_BLUEPRINT.md` §3

---

## 1. Environments Overview

| Environment | Infrastructure | Purpose | Access |
|-------------|---------------|---------|--------|
| **Dev** | Docker Compose on developer laptop | Development and acceptance testing | localhost:8000 |
| **Staging** | k3s on staging server | UAT and pre-production testing | WireGuard VPN |
| **Production** | k3s (multi-node, future V2.0+) | Live operations | WireGuard VPN |

**Rule:** Never deploy to production until staging passes all 10 acceptance tests.

---

## 2. Prerequisites

### 2.1 Developer Workstation

| Requirement | Version | Install command |
|-------------|---------|----------------|
| Docker Engine | 24+ | https://docs.docker.com/engine/install/ |
| Docker Compose | v2.x | Included with Docker Desktop or `apt install docker-compose-plugin` |
| Git | 2.x | `apt install git` or Homebrew |
| VS Code | Latest | https://code.visualstudio.com/ |
| Node.js (for Frappe build) | 18 LTS | `nvm install 18` |
| Python | 3.11+ | Frappe requirement |

### 2.2 Staging / Production Server

| Requirement | Version | Notes |
|-------------|---------|-------|
| Ubuntu | 22.04 LTS | Recommended; 20.04 also works |
| RAM | ≥ 8 GB | 16 GB recommended for staging |
| Disk | ≥ 50 GB SSD | For data, backups, Docker images |
| k3s | Latest stable | Installed via script (see §5) |
| WireGuard | Latest | For VPN access |

---

## 3. Dev Environment Setup (Docker Compose)

### 3.1 First-Time Setup (with internet)

```bash
# 1. Clone the repository
git clone https://github.com/YasserAKareem/yam_agri_core.git
cd yam_agri_core/infra/docker

# 2. Copy and configure environment
cp .env.example .env
# Edit .env: set SITE_NAME, ADMIN_PASSWORD, DB_ROOT_PASSWORD, etc.

# 3. Pull Docker images and save offline archive
bash run.sh prefetch
# Creates ./offline-images.tar (~2-4 GB)
# Copy to USB drive for offline use

# 4. Start the stack
bash run.sh up

# 5. Wait for stack to be healthy (~2-3 minutes)
bash run.sh logs
# Look for: "Starting development server..."

# 6. Initialize Frappe site (first time only)
bash run.sh init
# This creates the Frappe site, installs ERPNext + Agriculture + yam_agri_core
```

### 3.2 run.sh Command Reference

| Command | Description |
|---------|-------------|
| `bash run.sh up` | Start all Docker containers |
| `bash run.sh down` | Stop all containers |
| `bash run.sh logs` | Follow container logs |
| `bash run.sh shell` | Open a bash shell inside the Frappe container |
| `bash run.sh init` | Create Frappe site + install apps (first time only) |
| `bash run.sh reset` | Wipe all volumes + clean rebuild (data loss — dev only!) |
| `bash run.sh backup` | Create timestamped backup in `./backups/` |
| `bash run.sh restore` | Restore most recent backup |
| `bash run.sh restore ./backups/YYYYMMDD_HHMM/` | Restore specific backup |
| `bash run.sh prefetch` | Pull all Docker images and save to `offline-images.tar` |
| `bash run.sh offline-init` | Load images from `offline-images.tar` and start stack |
| `bash run.sh status` | Show container status and health |

### 3.3 Offline Setup (Field Site / No Internet)

```bash
# Ensure offline-images.tar is present (copy from USB)
ls -lh offline-images.tar

# Load images and start
bash run.sh offline-init

# Initialize site
bash run.sh init
```

### 3.4 After Power Outage Recovery

```bash
# Check container status
bash run.sh status

# Restart if containers stopped
bash run.sh up

# If MariaDB reports corruption:
bash run.sh down
docker compose -f docker-compose.yaml up db        # InnoDB crash recovery
# Wait for "ready for connections" in logs, then:
bash run.sh up
```

### 3.5 App Installation (Manual)

If `yam_agri_core` app is not yet installed:

```bash
# Open shell in Frappe container
bash run.sh shell

# Inside container:
bench --site ${SITE_NAME} install-app yam_agri_core
bench --site ${SITE_NAME} migrate
```

---

## 4. Installing and Updating Apps

### 4.1 Install a New Version of yam_agri_core

```bash
bash run.sh shell

# Inside container — pull latest app code
cd apps/yam_agri_core
git pull origin main

# Run migrations
cd /home/frappe/frappe-bench
bench --site ${SITE_NAME} migrate

# Clear cache
bench --site ${SITE_NAME} clear-cache
```

### 4.2 Run Frappe Migrations

Always run after pulling new DocType changes:

```bash
bash run.sh shell
bench --site ${SITE_NAME} migrate
bench --site ${SITE_NAME} build  # if JS/CSS assets changed
```

### 4.3 Import Fixtures (Seed Data)

```bash
bench --site ${SITE_NAME} import-fixtures
# or for specific app:
bench --site ${SITE_NAME} import-fixtures --app yam_agri_core
```

---

## 5. Staging Deployment (k3s)

> Complete this section only after Dev passes all 10 acceptance tests.

### 5.1 Install k3s on Staging Server

```bash
# From operator workstation (safe dry-run first)
DRY_RUN=1 ./scripts/provision_k3s.sh <staging_host> <ssh_user>

# Execute for real
DRY_RUN=0 ./scripts/provision_k3s.sh <staging_host> <ssh_user>
```

### 5.2 Deploy Frappe Stack

```bash
# Clone repo on staging server
git clone https://github.com/YasserAKareem/yam_agri_core.git
cd yam_agri_core/environments/staging

# Copy and edit environment config
cp .env.example .env
# Set all passwords and secrets for staging (different from dev!)

# WireGuard + k3s API restriction (dry-run then apply)
DRY_RUN=1 WG_ENDPOINT=<public_host_or_ip> ./scripts/setup_wireguard.sh <staging_host> <ssh_user>
DRY_RUN=1 VPN_SUBNET=10.88.0.0/24 ./scripts/restrict_k3s_api.sh <staging_host> <ssh_user>

# Validate tooling and required variables
./scripts/preflight.sh .env

# Generate secrets manifest from .env (do not commit generated file)
./scripts/generate-secrets.sh .env manifests/secrets.generated.yaml

# Apply k8s manifests
DRY_RUN_MODE=render ./scripts/apply_manifests.sh
./scripts/apply_manifests.sh

# Wait for pods to be ready
kubectl get pods -n yam-agri-staging -w
```

### 5.3 Data Migration (Dev -> Staging)

```bash
# Create backup evidence from dev
MODE=backup-only ./scripts/migrate_dev_to_staging.sh

# Full restore on staging
MODE=full STAGING_TARGET=<user@host> STAGING_SITE=<staging_site> ./scripts/migrate_dev_to_staging.sh
```

### 5.4 Staging Acceptance

Run all 10 acceptance tests (Section 4 of [07_TEST_PLAN.md](07_TEST_PLAN.md)) on staging before signing off.

```bash
./scripts/phase8_acceptance.sh localhost
```

---

## 6. Environment-Specific Configuration

| Config item | Dev value | Staging value | Production value |
|-------------|-----------|--------------|-----------------|
| `SITE_NAME` | `yam.localhost` | `yam-staging.vpn.internal` | `yam.yourdomain.com` |
| `ADMIN_PASSWORD` | Weak (dev use) | Strong (generated) | Strong (managed secret) |
| `DB_ROOT_PASSWORD` | Weak | Strong | Strong |
| `AI_GATEWAY_TOKEN` | Dev token | Staging token | Prod token |
| HTTPS | No (localhost) | Self-signed | Let's Encrypt |
| Backup destination | `./backups/` | MinIO on staging | Offsite S3 |
| WireGuard | Not required | Required | Required |

---

## 7. CI/CD Pipeline

### 7.1 GitHub Actions Workflow

The `.github/workflows/ci.yml` pipeline runs on every PR to `main` and `staging`:

| Job | What it checks |
|----|---------------|
| `Secret scan` | `gitleaks` — no secrets in diff |
| `YAML lint` | Docker Compose and k8s YAML validity |
| `Docker Compose validate` | `docker compose config` validates compose file |
| `PR title format` | Conventional commit title (feat/fix/chore/docs/infra) |

### 7.2 Deployment Workflow

```
Developer → feature branch → PR → CI checks → Review (1 approver)
→ Merge to main → Manual trigger: deploy to staging
→ Run acceptance tests on staging → Platform owner sign-off
→ Manual trigger: deploy to production (future)
```

---

## 8. Yemen-Specific Deployment Notes

| Constraint | Adaptation |
|-----------|-----------|
| Power outages | `restart: always` on all Docker/k3s services; InnoDB crash recovery configured |
| Slow internet | Pre-fetch images (`run.sh prefetch`) on fast connection; carry `offline-images.tar` on USB |
| Low RAM (8 GB laptop) | Total Docker stack < 3 GB; stop mock services when not testing |
| No internet at field | `run.sh offline-init` loads from local tar file |
| WireGuard at field sites | Each field developer has unique WireGuard peer; config from IT Admin |

### Low-Bandwidth Tips

| Situation | What to do |
|-----------|-----------|
| Slow Docker image pull | Pre-fetch with `run.sh prefetch` on fast connection |
| Large PR on 3G | Enable compression: `git config --global core.compression 9` |
| Slow initial clone | `git clone --depth 1 ...` then `git fetch --unshallow` later |
| GitHub Actions failing | Check CI logs via GitHub MCP server in Copilot Agent mode |

---

## 9. Rollback Procedure

### 9.1 Dev Rollback

```bash
# Restore last backup
bash run.sh restore

# Or restore specific backup
bash run.sh restore ./backups/20260222_0800/
```

### 9.2 Staging Rollback

```bash
# Revert to previous app version
cd apps/yam_agri_core
git checkout <previous_tag_or_commit>

# Re-run migrations
bench --site ${SITE_NAME} migrate

# If schema rollback needed — restore from backup
bash run.sh restore ./backups/pre-deploy/
```

### 9.3 Database-Level Rollback

```bash
# Stop Frappe
bash run.sh down

# Restore MariaDB from backup
bash run.sh restore ./backups/YYYYMMDD_HHMM/

# Restart
bash run.sh up
```

---

## 10. Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial deployment guide — V1.1 |
