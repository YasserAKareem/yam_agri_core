# C4 Deployment Diagram — Staging Environment (k3s)

> **C4 Type:** Deployment Diagram  
> **Environment:** Staging (k3s single-node on staging server)  
> **Version:** 1.1  
> **Date:** 2026-02-23  
> **Source file:** `environments/staging/k3s-manifest.yaml`  
> **Related:** [← Deployment: Dev](08_DEPLOYMENT_DEV.md) | [System Landscape →](10_SYSTEM_LANDSCAPE.md)

---

## Purpose

This deployment diagram shows how the YAM Agri Platform **containers are deployed on the k3s staging environment**. It reflects the `environments/staging/k3s-manifest.yaml` manifest and the architecture decisions made for staging — single-node k3s, Traefik ingress, PVC persistent storage, and WireGuard VPN access.

**Rule:** Staging is only deployed after Dev passes all 10 acceptance tests.

---

## Diagram

```mermaid
C4Deployment
    title Deployment Diagram — Staging (k3s Single-Node)

    Deployment_Node(vpn_access, "Developer / Admin Access", "WireGuard VPN\nRequired for all staging access\nUnique peer per developer") {
        Person(dev, "Developer / IT Admin (U7)", "Accesses staging via VPN only")
    }

    Deployment_Node(staging_server, "Staging Server", "Ubuntu 22.04 LTS\n8–16 GB RAM\nSSD storage\nk3s v1.x (single-node)\nTraefik ingress (bundled with k3s)") {

        Deployment_Node(k3s_node, "k3s Node", "Single-node k3s cluster\nNamespace: yam-agri-staging") {

            Deployment_Node(ingress_layer, "Ingress Layer", "Traefik IngressController\n(bundled with k3s)\nEntry point: web (HTTP :80)") {
                Container(traefik, "Traefik Ingress", "Traefik v2\nAnnotation: traefik.ingress.kubernetes.io/router.entrypoints: web",
                    "Routes external HTTP traffic.\nHost: staging.local\nPath: / → frappe service :8000\nTerminates TLS (staging: self-signed)")
            }

            Deployment_Node(frappe_deploy, "frappe Deployment", "Replicas: 1\nImage: frappe/erpnext\nNamespace: yam-agri-staging") {
                Container(frappe_pod, "Frappe Pod", "frappe/erpnext\nENV: SITE_NAME=staging.local\nENV: INSTALL_APPS=erpnext,agriculture",
                    "Core Frappe + ERPNext platform.\nMounts frappe-sites PVC.\nPort :8000 → Service frappe:8000")
            }

            Deployment_Node(agri_deploy, "agriculture-app Deployment", "Replicas: 1\nImage: yam_agri_core/agriculture_app:latest") {
                Container(agri_pod, "Agriculture App Pod", "yam_agri_core/agriculture_app:latest\nENV: FRAPPE_URL=http://frappe:8000",
                    "Frappe Agriculture app.\nConnects to Frappe at cluster-internal URL.")
            }

            Deployment_Node(yam_deploy, "yam-agri-core Deployment", "Replicas: 1\nImage: yam_agri_core/yam_agri_core:latest") {
                Container(yam_pod, "yam_agri_core Pod", "yam_agri_core/yam_agri_core:latest\nENV: FRAPPE_URL=http://frappe:8000",
                    "yam_agri_core custom app.\nConnects to Frappe at cluster-internal URL.")
            }

            Deployment_Node(db_deploy, "db Deployment", "Replicas: 1\nImage: postgres:15\nNamespace: yam-agri-staging") {
                ContainerDb(db_pod, "Database Pod", "postgres:15\nNote: staging manifest uses PostgreSQL\n(differs from dev MariaDB)",
                    "Database for staging.\nMounts db-data PVC.\nPort :5432 → Service db:5432\n⚠️ Note: Frappe requires MariaDB;\nstaging should use mariadb:10.6 (proposed fix)")
            }

            Deployment_Node(pvc_storage, "Persistent Volume Claims", "StorageClass: default (local-path in k3s)") {
                ContainerDb(frappe_pvc, "frappe-sites-pvc", "PVC — ReadWriteOnce — 1 Gi",
                    "Persistent storage for Frappe sites/.\nMounted in: frappe Deployment")
                ContainerDb(db_pvc, "db-data-pvc", "PVC — ReadWriteOnce — 1 Gi",
                    "Persistent storage for database data.\nMounted in: db Deployment")
            }

            Deployment_Node(services, "Kubernetes Services", "ClusterIP services for internal routing") {
                Container(svc_frappe,  "Service: frappe",          "ClusterIP :8000", "Routes to frappe Deployment pods")
                Container(svc_agri,    "Service: agriculture-app", "ClusterIP :80",   "Routes to agriculture-app pods")
                Container(svc_yam,     "Service: yam-agri-core",   "ClusterIP :80",   "Routes to yam-agri-core pods")
                Container(svc_db,      "Service: db",              "ClusterIP :5432", "Routes to db pods")
            }
        }
    }

    %% ── Relationships ──────────────────────────────────────────────────────────
    Rel(dev,       traefik,   "HTTPS via WireGuard VPN\nstaging.local", "HTTPS (TLS)")
    Rel(traefik,   svc_frappe, "Route HTTP /", "HTTP :8000")
    Rel(svc_frappe, frappe_pod, "Forward to pod", "HTTP :8000")
    Rel(frappe_pod, svc_db,    "Database queries", "TCP :5432")
    Rel(svc_db,    db_pod,     "Forward to pod", "TCP :5432")
    Rel(agri_pod,  svc_frappe, "FRAPPE_URL = http://frappe:8000", "HTTP :8000")
    Rel(yam_pod,   svc_frappe, "FRAPPE_URL = http://frappe:8000", "HTTP :8000")
    Rel(frappe_pod, frappe_pvc, "Mount /home/frappe/frappe-bench/sites", "Filesystem")
    Rel(db_pod,    db_pvc,     "Mount /var/lib/postgresql/data", "Filesystem")
```

---

## ASCII Fallback — k3s Staging Architecture

```
  Internet / Developer (WireGuard VPN required)
         │
         │ HTTPS :443 → :80
         ▼
  ┌───────────────────────────────────────────────────────────────────┐
  │  k3s Node (Ubuntu 22.04, 8–16 GB RAM)                             │
  │  Namespace: yam-agri-staging                                       │
  │                                                                    │
  │  ┌────────────────────────────────────────────────────────────┐   │
  │  │  Ingress Layer                                              │   │
  │  │  Traefik (bundled k3s ingress controller)                   │   │
  │  │  Host: staging.local → Service: frappe :8000               │   │
  │  └──────────────────────────────┬──────────────────────────── ┘   │
  │                                 │                                  │
  │  ┌──────────────────────────────▼──────────────────────────────┐  │
  │  │  Deployments                                                  │  │
  │  │                                                               │  │
  │  │  [frappe] ─── Deployment (1 replica)                         │  │
  │  │   frappe/erpnext image                                        │  │
  │  │   SITE_NAME=staging.local                                     │  │
  │  │   Mounts frappe-sites-pvc ──────────────────────▶ [PVC 1Gi]  │  │
  │  │                                                               │  │
  │  │  [agriculture-app] ─── Deployment (1 replica)                │  │
  │  │   yam_agri_core/agriculture_app:latest                       │  │
  │  │   FRAPPE_URL=http://frappe:8000                               │  │
  │  │                                                               │  │
  │  │  [yam-agri-core] ─── Deployment (1 replica)                  │  │
  │  │   yam_agri_core/yam_agri_core:latest                         │  │
  │  │   FRAPPE_URL=http://frappe:8000                               │  │
  │  │                                                               │  │
  │  │  [db] ─── Deployment (1 replica)                             │  │
  │  │   postgres:15  ⚠️ Should be mariadb:10.6 (see gaps)          │  │
  │  │   Mounts db-data-pvc ────────────────────────────▶ [PVC 1Gi] │  │
  │  └────────────────────────────────────────────────────────────  ┘  │
  │                                                                    │
  │  ┌────────────────────────────────────────────────────────────┐   │
  │  │  Services (ClusterIP)                                        │   │
  │  │  frappe :8000 | agriculture-app :80 | yam-agri-core :80    │   │
  │  │  db :5432                                                    │   │
  │  └────────────────────────────────────────────────────────────┘   │
  └───────────────────────────────────────────────────────────────────┘
```

---

## Staging vs Dev Differences

| Aspect | Dev (Docker Compose) | Staging (k3s) |
|--------|---------------------|--------------|
| Orchestrator | Docker Compose | k3s (single-node Kubernetes) |
| Image strategy | Bind mount source code | Built images pushed to registry |
| Database image | `mariadb:10.6` | `postgres:15` ⚠️ (should be mariadb:10.6) |
| Ingress | nginx bundled in ERPNext image | Traefik (k3s default) |
| Storage | Docker named volumes | Kubernetes PVCs (local-path StorageClass) |
| Network | Docker bridge `frappe-net` | k3s cluster network |
| Access | localhost:8000 | WireGuard VPN → staging.local |
| TLS | None (dev) | Self-signed cert (staging) |
| Redis | Separate containers | Not yet in staging manifest ⚠️ |

---

## Identified Issues in Current Staging Manifest

> These issues were found by comparing `environments/staging/k3s-manifest.yaml` against the system requirements. See [11_PROPOSED_GAPS.md](11_PROPOSED_GAPS.md) for full details.

| Issue | Severity | Detail |
|-------|---------|--------|
| Database is `postgres:15` | **Critical** | Frappe Framework requires MariaDB; staging must use `mariadb:10.6` |
| Redis services missing | **High** | No Redis Cache, Queue, or WebSocket containers in staging manifest |
| Frappe workers missing | **High** | No `queue-short`, `queue-long`, or `scheduler` deployments |
| WebSocket server missing | **Medium** | No WebSocket/socketio service; real-time features will not work |
| INSTALL_APPS incomplete | **High** | Staging only installs `erpnext,agriculture`; missing `yam_agri_core` |
| Secrets in plain text | **High** | DB passwords hardcoded in manifest; must use k8s Secrets |
| TLS not configured | **Medium** | No cert-manager or TLS secret; Traefik entry point should be websecure |
| PVC sizes too small | **Medium** | 1 Gi PVCs for Frappe sites and DB are insufficient for production-like data |

---

## Production Architecture (Future — V2.0+)

The production deployment target (not yet implemented) will add:

| Component | Production change |
|-----------|-----------------|
| MariaDB | MariaDB primary + replica (read replicas) |
| Redis | Redis Sentinel for HA |
| Frappe workers | Multiple replicas with HPA |
| Storage | MinIO distributed mode (multi-node) |
| Ingress | Traefik + cert-manager (Let's Encrypt) |
| Monitoring | Prometheus + Grafana + AlertManager |
| Backup | Automated Restic → offsite S3 |
| VPN | WireGuard (same as staging) |
| k3s | Multi-node cluster (3+ nodes) |

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial staging deployment diagram — V1.1 |
