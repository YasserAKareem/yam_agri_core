# arc42 §7 — Deployment View

> **arc42 Section:** 7  
> **Version:** 1.1  
> **Status:** ⚠️ Draft  
> **Date:** 2026-02-23  
> **Related SDLC doc:** [03_SYSTEM_ARCHITECTURE.md §4](../Docs%20v1.1/03_SYSTEM_ARCHITECTURE.md) | [08_DEPLOYMENT_GUIDE.md](../Docs%20v1.1/08_DEPLOYMENT_GUIDE.md)  
> **Related C4 docs:** [`docs/C4 model Architecture v1.1/08_DEPLOYMENT_DEV.md`](../C4%20model%20Architecture%20v1.1/08_DEPLOYMENT_DEV.md)

---

## 7.1 Deployment Environments

| Environment | Purpose | Technology | Access |
|-------------|---------|-----------|--------|
| **Dev** | Developer laptop — daily build and test | Docker Compose | localhost only |
| **Staging** | Pre-production validation — all acceptance tests | k3s (single-node) | WireGuard VPN |
| **Production** | Live business operations | k3s (multi-node, future) | WireGuard VPN + nginx |
| **Field Hub** | Per-site offline edge node | Raspberry Pi 4 + Docker | Site LAN only |

> **Rule:** Production is never deployed until all 10 acceptance tests pass on staging.

---

## 7.2 Development Environment (Docker Compose)

### Infrastructure Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                 Developer Laptop (8 GB RAM, macOS/Linux)          │
│                                                                    │
│  ┌──────────────── Docker Compose ─────────────────────────────┐  │
│  │                                                              │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │  │
│  │  │  frappe-web  │  │  frappe-     │  │  frappe-          │  │  │
│  │  │  (gunicorn)  │  │  worker      │  │  scheduler        │  │  │
│  │  │  :8000       │  │  (RQ)        │  │  (cron)           │  │  │
│  │  └──────┬───────┘  └──────┬───────┘  └─────────┬─────────┘  │  │
│  │         │                  │                     │            │  │
│  │  ┌──────▼──────────────────▼─────────────────────▼────────┐  │  │
│  │  │              MariaDB 10.6 (:3306)                       │  │  │
│  │  │              Volume: mariadb-data                       │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  │                                                                │  │
│  │  ┌────────────────────────────────────────────────────────┐   │  │
│  │  │  Redis Queue (:6379)   Redis Cache (:6380)             │   │  │
│  │  └────────────────────────────────────────────────────────┘   │  │
│  │                                                                │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐   │  │
│  │  │  nginx      │  │  socketio   │  │  ai-gateway          │   │  │
│  │  │  (:80)      │  │  (:9000)    │  │  (FastAPI, :8001)    │   │  │
│  │  └─────────────┘  └─────────────┘  └──────────────────────┘   │  │
│  │                                                                │  │
│  │  ┌─────────────┐  ┌─────────────┐                             │  │
│  │  │  MinIO      │  │  mosquitto  │                             │  │
│  │  │  (:9001)    │  │  (:1883)    │                             │  │
│  │  └─────────────┘  └─────────────┘                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  Frappe site data: ./sites/ (bind mount)                           │
│  Custom app: ./apps/yam_agri_core/ (bind mount)                    │
└──────────────────────────────────────────────────────────────────┘
```

### Memory Budget

| Service | Approximate RAM |
|---------|----------------|
| MariaDB 10.6 | ~400 MB |
| Redis (×2 instances) | ~50 MB each |
| Frappe web + workers (2×) | ~1.5–2 GB |
| nginx | ~50 MB |
| socketio | ~100 MB |
| ai-gateway (FastAPI) | ~200 MB |
| MinIO | ~100 MB |
| mosquitto | ~20 MB |
| **Total** | **~2.5–3.5 GB** ✅ within 6 GB limit |

### Key Files

| File | Purpose |
|------|---------|
| `infra/compose/docker-compose.yml` | Main compose definition |
| `infra/docker/run.sh` | Convenience wrapper: `up`, `down`, `logs`, `shell`, `init`, `reset`, `backup`, `prefetch` |
| `infra/.env.example` | Environment variable template (never commit `.env`) |
| `infra/frappe_docker/` | Frappe-specific Docker build context and entrypoint |

---

## 7.3 Staging Environment (k3s — Single Node)

### Infrastructure Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                Staging Server (VPS or on-premises)                │
│                                                                    │
│  ┌────────── WireGuard VPN ────────────────────────────────────┐  │
│  │  Only VPN peers can access staging                          │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌──────────────── k3s Single Node ───────────────────────────┐   │
│  │                                                              │   │
│  │  namespace: frappe                                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │   │
│  │  │ frappe-web   │  │ frappe-      │  │ frappe-          │  │   │
│  │  │ (Deployment) │  │ worker       │  │ scheduler        │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘  │   │
│  │  ┌────────────────────────────────────────────────────────┐  │   │
│  │  │  MariaDB (StatefulSet) — PV: mariadb-data (10 GB)     │  │   │
│  │  └────────────────────────────────────────────────────────┘  │   │
│  │  ┌────────────────────────────────────────────────────────┐  │   │
│  │  │  Redis (Deployment) — queue + cache                   │  │   │
│  │  └────────────────────────────────────────────────────────┘  │   │
│  │  ┌──────────────┐  ┌──────────────┐                         │   │
│  │  │  MinIO       │  │  ai-gateway  │                         │   │
│  │  │  (StatefulSet)│  │  (Deployment)│                        │   │
│  │  └──────────────┘  └──────────────┘                         │   │
│  │                                                              │   │
│  │  Traefik Ingress — TLS termination (Let's Encrypt)           │   │
│  │  Internal DNS: yam-staging.vpn.internal                     │   │
│  └──────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### Staging Deployment Procedure

1. All 10 acceptance tests pass on dev
2. `run.sh` generates a site backup and database dump
3. Docker images pushed to registry (or loaded from tar)
4. `kubectl apply -f k8s/staging/` deploys manifests
5. `bench migrate` run in frappe-web pod
6. All 10 acceptance tests re-run on staging
7. Owner reviews and approves staging sign-off

---

## 7.4 Production Architecture (Future — Post-V1.1)

> Production deployment is blocked until staging passes all acceptance tests. This section documents the intended production target.

```
┌─────────────────────────────────────────────────────────────────────┐
│                Production (Multi-node k3s)                           │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Frappe workers ×3 (replicated Deployment)                   │    │
│  │  MariaDB primary + read replica (StatefulSet)                │    │
│  │  Redis Sentinel (3 pods)                                     │    │
│  │  MinIO distributed (4 drives)                                │    │
│  │  Prometheus + Grafana (monitoring namespace)                 │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  Automated Restic backups → encrypted offsite S3 (daily)             │
│  WireGuard VPN — admin access only                                    │
│  HTTPS — HSTS enforced; HTTP → HTTPS redirect                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7.5 Field Hub Deployment (Per-Site Edge Node)

```
┌──────────────────────────────────────────────────────────────┐
│          Field Hub (Raspberry Pi 4, per site)                 │
│                                                               │
│  ┌──────────────────── Docker Compose ──────────────────────┐ │
│  │  frappe-web (minimal) (:8000)                            │ │
│  │  MariaDB 10.6                                            │ │
│  │  Redis                                                   │ │
│  │  Mosquitto MQTT Broker (:1883)                           │ │
│  │  IoT Gateway (Python subscriber)                        │ │
│  │  Ollama (llama3.2:3b Q4 — local LLM cache)              │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                               │
│  Solar PV + LiFePO₄ battery — primary power                  │
│  12 V DC input; fanless operation; IP54-rated enclosure      │
│  Offline-first: 7-day autonomous operation guaranteed         │
│  Sync: PouchDB/Frappe queue when WireGuard VPN available     │
└──────────────────────────────────────────────────────────────┘
```

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial section — V1.1 |
