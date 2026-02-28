# YAM Agri Core

> Infrastructure and configuration layer for the **YAM Agri Platform** — a cereal-crop supply chain quality and traceability system built on [Frappe](https://frappeframework.com/) and [ERPNext](https://erpnext.com/).

[![CI](https://github.com/YasserAKareem/yam_agri_core/actions/workflows/ci.yml/badge.svg)](https://github.com/YasserAKareem/yam_agri_core/actions/workflows/ci.yml)

---

## Overview

YAM Agri Core provides:

- **Lot traceability** — splits, merges, and blends across the cereal supply chain
- **QA/QC tests and certificates** — FAO GAP Middle East + HACCP/ISO 22000
- **Scale tickets** — weight measurements linked to devices and lots
- **Sensor observations** — universal model for bins, refrigerators, weather, irrigation, and remote sensing
- **Evidence packs** — audit-ready bundles for a date range and site
- **Site isolation** — users only see data for their permitted sites
- **Hybrid AI assistance** — assistive only; AI never executes risky actions automatically

## Requirements

| Component | Version |
|-----------|---------|
| Frappe    | v16     |
| ERPNext   | v16     |
| MariaDB   | 10.6+   |
| Redis     | 6+      |
| Docker    | 24+     |

## Quick Start (Dev)

```bash
# Clone with submodules
git clone --recurse-submodules https://github.com/YasserAKareem/yam_agri_core.git
cd yam_agri_core

# Copy and configure environment
cp environments/dev/.env.example environments/dev/.env
# Edit environments/dev/.env with your values

# Start the stack
bash infra/docker/run.sh up

# Initialise site + install apps
bash infra/docker/run.sh init
```

## Runtime Contract (Canonical)

- Use `infra/docker/run.sh` as the primary entrypoint for dev runtime operations.
- Treat `infra/docker/docker-compose.yml` as the canonical compose file for local operations.
- Use WSL or Git Bash on Windows for shell workflows to avoid path translation drift.
- For MCP stdio servers, use `.vscode/mcp.json` with `tools/mcp/launch_mcp.py` (not direct `npx`).

## Core DocTypes (V1.1)

| DocType | Purpose |
|---------|---------|
| Site | Farm, silo, store, or office location |
| Storage Bin | Physical bin within a site |
| Device | IoT sensor or scale device |
| Lot | Harvest, storage, or shipment lot |
| Transfer | Split, merge, or blend between lots |
| Scale Ticket | Weight measurement record |
| QC Test | Quality control test result |
| Certificate | Compliance certificate (expiry-checked) |
| Nonconformance | CAPA record |
| Evidence Pack | Audit evidence bundle |
| Complaint | Customer complaint record |
| Observation | Universal sensor/derived signal model |

## Development

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run pure-Python tests (fast, no DB)
cd apps/yam_agri_core && python -m pytest yam_agri_core/yam_agri_core/tests/ -v

# Run Frappe integration tests (requires Docker stack)
bash infra/docker/run.sh bench --site localhost run-tests --app yam_agri_core

# Lint
cd apps/yam_agri_core && ruff check .
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contribution guide.

## Non-Negotiable Business Rules

1. Every record **must** belong to a Site.
2. Users **do not** see other sites' data by default (site isolation via User Permissions).
3. High-risk actions (Lot accept/reject, Transfer approval) **require QA Manager role**.
4. AI is **assistive only** — no automatic lot accept/reject, recalls, or unsupervised customer communications.
5. **Never commit secrets** — use `.env.example` only; never commit `.env` with real credentials.

## License

[MIT](LICENSE)