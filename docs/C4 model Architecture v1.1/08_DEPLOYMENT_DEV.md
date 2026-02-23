# C4 Deployment Diagram — Dev Environment (Docker Compose)

> **C4 Type:** Deployment Diagram  
> **Environment:** Development (Docker Compose on developer laptop)  
> **Version:** 1.1  
> **Date:** 2026-02-23  
> **Source files:** `infra/docker/docker-compose.yml` · `environments/dev/docker-compose.yaml`  
> **Related:** [← Dynamic: AI Assist](07_DYNAMIC_AI_ASSIST.md) | [Deployment: Staging →](09_DEPLOYMENT_STAGING.md)

---

## Purpose

This deployment diagram shows how the YAM Agri Platform **containers are mapped to infrastructure** in the development environment. It reflects the actual `docker-compose.yml` files in the repository, showing which services exist, how they communicate, and which volumes they share.

---

## Diagram

```mermaid
C4Deployment
    title Deployment Diagram — Dev Environment (Docker Compose)

    Deployment_Node(laptop, "Developer Laptop", "Ubuntu 22.04 / macOS / Windows + WSL2\n8 GB RAM minimum\nDocker Desktop or Docker Engine 24+") {

        Deployment_Node(docker_network, "Docker Network: frappe-net", "Docker bridge network\nAll services on same virtual network\nHostname = service name") {

            Deployment_Node(frontend_svc, "frontend service", "frappe/erpnext:v16.5.0\nnginx-entrypoint.sh\nPort: :8080 → HOST :8000") {
                Container(nginx_c, "nginx", "nginx (bundled in ERPNext image)",
                    "Reverse proxy for HTTP :8080.\nProxy to backend:8000 (Frappe API)\nProxy to websocket:9000 (WebSocket).\nServes static JS/CSS assets.\nHost port: HTTP_PUBLISH_PORT (default 8000)")
            }

            Deployment_Node(websocket_svc, "websocket service", "frappe/erpnext:v16.5.0\nnode socketio.js\nPort: :9000 (internal only)") {
                Container(ws_c, "WebSocket Server", "Node.js / frappe socketio.js",
                    "Real-time push to Frappe Desk.\nConnects to redis-cache :6379\nand redis-queue :6380.")
            }

            Deployment_Node(backend_svc, "backend service", "frappe/erpnext:v16.5.0\ngunicorn --workers=2 --threads=4\nPort: :8000 (internal only)") {
                Container(frappe_c, "Frappe Backend", "Python 3.11 / Gunicorn / Frappe v16 / ERPNext v16",
                    "Core platform — all DocTypes, REST/RPC API.\nInstalls: erpnext, agriculture, yam_agri_core,\nyam_agri_qms_trace.\nPYTHONPATH includes all 3 custom apps.")
            }

            Deployment_Node(worker_short_svc, "queue-short service", "frappe/erpnext:v16.5.0\nbench worker --queue short,default") {
                Container(ws_short_c, "Worker: Short Queue", "Python / RQ",
                    "Processes short background jobs.")
            }

            Deployment_Node(worker_long_svc, "queue-long service", "frappe/erpnext:v16.5.0\nbench worker --queue long,default,short") {
                Container(ws_long_c, "Worker: Long Queue", "Python / RQ",
                    "Processes long-running jobs\n(CSV imports, evidence packs).")
            }

            Deployment_Node(scheduler_svc, "scheduler service", "frappe/erpnext:v16.5.0\nbench schedule") {
                Container(sched_c, "Scheduler", "Python / Frappe bench schedule",
                    "Cron-triggered jobs: certificate expiry,\nbackup triggers, sensor threshold checks.")
            }

            Deployment_Node(db_svc, "db service", "mariadb:10.6\nPort: :3306 (internal only)\nrestart: always") {
                ContainerDb(db_c, "MariaDB 10.6", "mariadb:10.6\nInnoDB engine",
                    "Primary relational DB.\nVolume: db_data (Docker named volume).\nCrash recovery: InnoDB auto-repair on restart.\nhealthcheck: mysqladmin ping every 5s.")
            }

            Deployment_Node(redis_cache_svc, "redis-cache service", "redis:6.2-alpine\nPort: :6379 (internal only)\nrestart: always") {
                ContainerDb(rc_c, "Redis Cache", "redis:6.2-alpine",
                    "Session and page cache.")
            }

            Deployment_Node(redis_queue_svc, "redis-queue service", "redis:6.2-alpine\nPort: :6380 (internal only)\nrestart: always") {
                ContainerDb(rq_c, "Redis Queue", "redis:6.2-alpine",
                    "RQ job broker.")
            }

            Deployment_Node(redis_ws_svc, "redis-socketio service", "redis:6.2-alpine\nPort: :6381 (internal only)\nrestart: always") {
                ContainerDb(rws_c, "Redis WebSocket", "redis:6.2-alpine",
                    "WebSocket pub/sub.")
            }
        }

        Deployment_Node(volumes, "Docker Named Volumes", "Persistent storage on host filesystem") {
            ContainerDb(db_vol, "db_data volume", "Docker named volume",
                "MariaDB data directory.\nPersists across container restarts.\nSurvives: docker compose down\nLost on: docker compose down --volumes")
            ContainerDb(sites_vol, "sites-vol volume", "Docker named volume",
                "Frappe site files: config, private files,\npublic files, logs, cache.\nShared between: backend, frontend,\nwebsocket, queue-short, queue-long, scheduler.")
        }

        Deployment_Node(bind_mounts, "Bind Mounts (Host ↔ Container)", "Host directories mounted into containers") {
            ContainerDb(apps_mount, "App source code", "../../apps/ → /home/frappe/frappe-bench/apps/",
                "Live code mounts for development:\n• apps/agriculture → apps/agriculture\n• apps/yam_agri_core → apps/yam_agri_core\n• apps/yam_agri_qms_trace → apps/yam_agri_qms_trace\n• docs/ → docs/\nChanges on host instantly visible in containers.")
        }
    }

    %% ── Relationships ──────────────────────────────────────────────────────────
    Rel(nginx_c,    frappe_c,   "Proxy HTTP → backend:8000", "HTTP")
    Rel(nginx_c,    ws_c,       "Proxy WS → websocket:9000", "WebSocket")
    Rel(frappe_c,   db_c,       "SQL queries", "MySQL :3306")
    Rel(frappe_c,   rc_c,       "Cache reads/writes", "Redis :6379")
    Rel(frappe_c,   rq_c,       "Enqueue jobs", "Redis :6380")
    Rel(ws_short_c, rq_c,       "Poll short queue", "Redis :6380")
    Rel(ws_long_c,  rq_c,       "Poll long queue", "Redis :6380")
    Rel(ws_c,       rc_c,       "Subscribe events", "Redis :6379")
    Rel(ws_c,       rws_c,      "Pub/sub events", "Redis :6381")
    Rel(frappe_c,   sites_vol,  "Read/write site files", "Filesystem")
    Rel(frappe_c,   apps_mount, "Load app Python code", "Filesystem (bind mount)")
    Rel(db_c,       db_vol,     "Persist data", "Filesystem")
```

---

## ASCII Fallback — Docker Compose Service Map

```
HOST: Developer Laptop (port 8000 exposed)
│
│  HTTP :8000 → container port :8080
│
└──► Docker Network: frappe-net
     │
     ├──[frontend]─────────────────── frappe/erpnext:v16.5.0
     │   nginx-entrypoint.sh          HOST :8000 → :8080
     │   ├── proxy → backend:8000
     │   └── proxy → websocket:9000
     │
     ├──[backend]──────────────────── frappe/erpnext:v16.5.0
     │   gunicorn :8000                Internal only
     │   Frappe v16 + ERPNext v16
     │   + agriculture app
     │   + yam_agri_core              PYTHONPATH: all 3 custom apps
     │   + yam_agri_qms_trace
     │   ├── reads/writes → db:3306
     │   ├── cache → redis-cache:6379
     │   └── jobs → redis-queue:6380
     │
     ├──[websocket]────────────────── frappe/erpnext:v16.5.0
     │   node socketio.js              Port :9000 internal
     │   ├── subscribe → redis-cache:6379
     │   └── pub/sub → redis-socketio:6381
     │
     ├──[queue-short]─────────────── frappe/erpnext:v16.5.0
     │   bench worker --queue short   Polls redis-queue:6380
     │
     ├──[queue-long]──────────────── frappe/erpnext:v16.5.0
     │   bench worker --queue long    Polls redis-queue:6380
     │
     ├──[scheduler]───────────────── frappe/erpnext:v16.5.0
     │   bench schedule               Triggers cron jobs
     │
     ├──[db]──────────────────────── mariadb:10.6
     │   InnoDB storage               Port :3306 internal
     │   restart: always              Volume: db_data
     │   healthcheck: mysqladmin ping
     │
     ├──[redis-cache]─────────────── redis:6.2-alpine
     │   Port :6379 internal          restart: always
     │
     ├──[redis-queue]─────────────── redis:6.2-alpine
     │   Port :6380 internal          restart: always
     │
     └──[redis-socketio]───────────── redis:6.2-alpine
         Port :6381 internal          restart: always

DOCKER VOLUMES:
  db_data    → MariaDB data directory
  sites-vol  → Frappe bench/sites/ (shared across 6 services)

BIND MOUNTS (host path → container path):
  ../../apps/agriculture        → .../apps/agriculture
  ../../apps/yam_agri_core      → .../apps/yam_agri_core
  ../../apps/yam_agri_qms_trace → .../apps/yam_agri_qms_trace
  ../../docs                    → .../docs
```

---

## Service Dependency Graph

```
frontend → backend (service_started)
         → websocket (service_started)

websocket → backend (service_started)
          → redis-cache (service_started)
          → redis-queue (service_started)

backend → db (service_healthy via mysqladmin ping)
        → redis-cache (service_started)
        → redis-queue (service_started)
        → redis-socketio (service_started)

queue-short → backend (service_started)
            → redis-cache (service_started)
            → redis-queue (service_started)

queue-long → backend (service_started)
           → redis-cache (service_started)
           → redis-queue (service_started)

scheduler → backend (service_started)
          → redis-cache (service_started)
          → redis-queue (service_started)
```

---

## Memory Budget (8 GB RAM Laptop)

| Service | Approximate RAM |
|---------|----------------|
| MariaDB 10.6 | ~400 MB |
| redis-cache | ~30 MB |
| redis-queue | ~30 MB |
| redis-socketio | ~30 MB |
| backend (gunicorn 2 workers × 4 threads) | ~900 MB |
| frontend (nginx) | ~30 MB |
| websocket (Node.js) | ~100 MB |
| queue-short | ~300 MB |
| queue-long | ~300 MB |
| scheduler | ~200 MB |
| **Total** | **~2.3 GB** |
| OS + browser + IDE overhead | ~2–4 GB |
| **Available headroom (8 GB)** | **~1.5–3.5 GB** |

---

## Yemen-Resilient Deployment Configuration

| Concern | Configuration |
|---------|--------------|
| **Power cut** | `restart: always` on all services; InnoDB auto-recovery; sites-vol preserves session state |
| **Offline startup** | `run.sh offline-init` loads images from `offline-images.tar`; no internet required |
| **Database corruption** | `healthcheck` ensures backend only starts when MariaDB is ready; InnoDB crash recovery on restart |
| **Code changes** | Bind mounts: edit code on host → instant effect in container (no rebuild needed) |
| **Backup** | `run.sh backup` → timestamped dump to `./backups/`; copy to USB drive |

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial dev deployment diagram — V1.1 |
