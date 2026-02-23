# Operations Runbook — YAM Agri Platform V1.1

> **SDLC Phase:** Operations & Maintenance  
> **Version:** 1.1  
> **Status:** ⚠️ Draft  
> **Date:** 2026-02-23  
> **Audience:** IT Admin (U7 — Ibrahim Al-Sana'ani), DevOps  
> **Related:** [Deployment Guide](08_DEPLOYMENT_GUIDE.md) | [System Architecture](03_SYSTEM_ARCHITECTURE.md)

---

## 1. Daily Operations Checklist

| Task | Frequency | How |
|------|-----------|-----|
| Check container health | Daily | `bash run.sh status` |
| Review Frappe error log | Daily | Frappe Desk → Error Log |
| Check backup ran successfully | Daily | `ls -lt ./backups/` |
| Review open Critical Nonconformances | Daily | Frappe Desk → Nonconformance list, filter: status=Open, severity=Critical |
| Check certificate expiry alerts | Weekly | Frappe Desk → Certificate list, filter: status=Active, expiry_date < 30 days |
| Review sensor Quarantine observations | Daily | Frappe Desk → Observation list, filter: quality_flag=Quarantine |
| User access audit | Monthly | Frappe Desk → User Permissions list — verify no unexpected access |

---

## 2. Service Management

### 2.1 Start / Stop Services

```bash
# Start all services
bash run.sh up

# Stop all services
bash run.sh down

# View logs (follow)
bash run.sh logs

# View logs for specific service
docker compose -f docker-compose.yaml logs -f frappe

# Open shell in Frappe container
bash run.sh shell

# Restart a single service
docker compose -f docker-compose.yaml restart frappe
```

### 2.2 Service Health Check

```bash
# Show running containers and health status
bash run.sh status
# or
docker compose -f docker-compose.yaml ps

# Check Frappe is responding
curl -s http://localhost:8000/api/method/frappe.ping | python3 -m json.tool
# Expected: {"message": "pong"}
```

### 2.3 Memory Management

```bash
# Check Docker memory usage
docker stats --no-stream

# If memory is low, stop non-essential mock services
docker compose -f docker-compose.yaml stop mock_iot mock_scale

# Check MariaDB memory
docker exec -it <mariadb_container> mysql -u root -p -e "SHOW STATUS LIKE 'Innodb_buffer_pool%';"
```

---

## 3. Backup & Restore

### 3.1 Create a Backup

```bash
# Automated timestamped backup to ./backups/
bash run.sh backup

# Backup files created:
#   ./backups/YYYYMMDD_HHMM/
#     frappe-backup.sql.gz   (MariaDB dump)
#     files.tar.gz           (Frappe site files)
#     backup.log

# List available backups
ls -lt ./backups/
```

### 3.2 Restore from Backup

```bash
# Restore most recent backup
bash run.sh restore

# Restore specific backup
bash run.sh restore ./backups/20260222_0800/

# Manual restore (advanced)
bash run.sh shell
bench --site ${SITE_NAME} restore \
  --mariadb-root-password ${DB_ROOT_PASSWORD} \
  /home/frappe/frappe-bench/sites/${SITE_NAME}/private/backups/YYYYMMDD_HHMM-frappe-backup.sql.gz
```

### 3.3 Offsite Backup (Recommended)

After each backup, copy to external drive:

```bash
# Copy to USB drive (replace /media/usb with your mount point)
cp -r ./backups/$(ls -t ./backups/ | head -1) /media/usb/yam-backup/

# Or sync to S3 with rclone
rclone copy ./backups/ s3:${BACKUP_S3_BUCKET}/yam-backups/ --progress
```

### 3.4 Backup Schedule

| Backup type | Frequency | Retention |
|-------------|-----------|----------|
| Full DB + files | Daily (automated) | 7 days local |
| Pre-deployment backup | Before every migration | 30 days |
| Offsite copy (USB or S3) | Weekly | 90 days |
| Pre-travel backup | Before transporting laptop to field | Until return |

---

## 4. User Management

### 4.1 Create a New User

1. Frappe Desk → Users → New User
2. Fill: Email, Full Name, Mobile (optional), Send Welcome Email = Yes
3. Assign Role Profile (from `docs/Docs v1.1/06_SECURITY_AND_RBAC.md §2`)
4. Add User Permissions: Frappe Desk → User Permissions → New → User = new user, Allow = Site, For Value = their assigned site
5. Test: login as new user → confirm they see only their site's data

### 4.2 Deactivate a User

```bash
# In Frappe Desk → User → set "Enabled" = 0
# Or via bench:
bash run.sh shell
bench --site ${SITE_NAME} set-config disable_user <email>
```

### 4.3 Reset a User Password

```bash
bash run.sh shell
bench --site ${SITE_NAME} set-admin-password <email> --new-password <new_password>
```

---

## 5. Database Maintenance

### 5.1 Check Database Size

```bash
bash run.sh shell
bench --site ${SITE_NAME} console
# In Python console:
import frappe
frappe.db.sql("SELECT table_schema AS 'Database', ROUND(SUM(data_length + index_length) / 1024 / 1024, 1) AS 'Size (MB)' FROM information_schema.TABLES GROUP BY table_schema;")
```

### 5.2 Clear Frappe Cache

```bash
bash run.sh shell
bench --site ${SITE_NAME} clear-cache
bench --site ${SITE_NAME} clear-website-cache
```

### 5.3 Rebuild Assets

```bash
bash run.sh shell
bench --site ${SITE_NAME} build --app yam_agri_core
```

### 5.4 Run Pending Migrations

```bash
bash run.sh shell
bench --site ${SITE_NAME} migrate
```

### 5.5 InnoDB Crash Recovery (After Power Cut)

```bash
# 1. Stop all services
bash run.sh down

# 2. Start only MariaDB to let InnoDB recovery run
docker compose -f docker-compose.yaml up db

# 3. Watch logs for recovery messages
docker compose -f docker-compose.yaml logs -f db
# Look for: "InnoDB: Recovery complete"
# And then: "ready for connections"

# 4. After recovery, start everything
bash run.sh up
```

---

## 6. Monitoring & Alerts

### 6.1 Built-in Frappe Monitoring

| Monitor | How to access |
|---------|--------------|
| Error log | Frappe Desk → Error Log |
| Scheduled jobs | Frappe Desk → Scheduled Job Log |
| Email queue | Frappe Desk → Email Queue |
| Background jobs | Frappe Desk → RQ Job |
| System health | Frappe Desk → System Health Report |

### 6.2 Key Alerts to Configure

| Alert | Trigger | Action |
|-------|---------|--------|
| Certificate expiry (30 days) | Certificate `expiry_date < today + 30` | Email to QA Manager |
| Sensor quarantine | Observation `quality_flag = Quarantine` | Email to Site Operator + QA Manager |
| Scale ticket mismatch | `ScaleTicket.mismatch_flag = 1` | Email to QA Manager |
| Critical nonconformance opened | `Nonconformance.severity = Critical` | Email to QA Manager + Owner |
| Low disk space | Docker volume > 80% full | Email to IT Admin |
| Backup failure | Daily backup script exit code ≠ 0 | Email to IT Admin |

### 6.3 Prometheus + Grafana (Staging/Production — V1.2+)

For staging and production, add Prometheus + Grafana for infrastructure metrics:
- MariaDB query latency
- Redis memory usage
- Frappe worker queue depth
- Container restart count

---

## 7. Incident Response

### 7.1 Severity Levels

| Level | Definition | Response time |
|-------|-----------|--------------|
| P1 — Critical | System unavailable; data loss; security breach | Immediate (< 1 hour) |
| P2 — Major | Core feature broken; operations impacted | < 4 hours |
| P3 — Minor | Non-critical issue; workaround available | Next business day |

### 7.2 P1 Incident Procedure

1. **Detect:** user report, alert email, or `bash run.sh status` shows container(s) down
2. **Contain:** `bash run.sh down` to stop all services if data corruption suspected
3. **Assess:** check Frappe error log; check MariaDB status
4. **Notify:** call/message Platform Owner (U6) and IT Admin (U7) immediately
5. **Restore:** `bash run.sh restore` from last known-good backup
6. **Validate:** run AT-01 (create Site → Lot) to confirm system is functional
7. **Document:** create Nonconformance record; record root cause + corrective action
8. **Review:** post-incident review within 5 business days

### 7.3 Common Issues & Solutions

| Symptom | Likely cause | Solution |
|---------|-------------|---------|
| Frappe login page not loading | Container crashed or never started | `bash run.sh status` → `bash run.sh up` |
| "Database connection failed" | MariaDB not ready | `bash run.sh status` → wait 60s → retry |
| Slow page loads | Redis cache full or MariaDB slow query | `bench clear-cache`; check `SHOW PROCESSLIST` |
| "Permission denied" on record | User Permissions not set | Check User Permissions for that user + Site |
| CSV import fails | Malformed CSV or missing columns | Check error report; validate CSV headers |
| AI suggestion not returning | AI Gateway down | Check `docker logs ai-gateway`; restart if needed |
| Worker queue stuck | Redis connection dropped | `docker restart <redis_container>` |

---

## 8. Capacity Planning

### 8.1 Current Estimates (Dev / Small Deployment)

| Component | Current | Warning threshold | Action |
|-----------|---------|------------------|--------|
| MariaDB data | < 5 GB | 80% of volume | Extend volume or archive old data |
| Frappe file storage | < 10 GB | 80% of volume | Add MinIO or expand volume |
| Redis memory | < 200 MB | 80% of container limit | Increase Redis `maxmemory` |
| Docker volumes total | < 20 GB | 80% of disk | Clean up old images + volumes |

### 8.2 Scaling Triggers

| Trigger | Action |
|---------|--------|
| > 50 concurrent users | Upgrade to multi-worker Frappe setup; consider staging k3s |
| > 500 MB/day data ingest | Review InfluxDB retention policy; archive to DuckDB |
| Response time > 5 seconds | Profile MariaDB queries; add indexes; increase worker count |
| AI Gateway latency > 15 seconds | Switch local Ollama model to smaller quantization or add GPU |

---

## 9. Scheduled Maintenance Windows

| Task | Schedule | Duration | Notes |
|------|----------|----------|-------|
| Weekly backup + cleanup | Sunday 02:00 local | 30 min | Before business week |
| Monthly user access audit | 1st of month | 1 hour | IT Admin reviews all User Permissions |
| Quarterly certificate audit | 1st of quarter | 2 hours | QA Manager reviews all active certificates |
| MariaDB index optimization | Monthly | 15 min | `ANALYZE TABLE` on high-traffic DocTypes |
| OS + Docker security updates | Monthly | 1 hour | Stage maintenance window; backup first |

---

## 10. Contact Directory

| Role | Person | Responsibility |
|------|--------|---------------|
| Platform Owner | Yasser (U6) | Final escalation; approvals; go/no-go |
| IT Admin / DevOps | Ibrahim Al-Sana'ani (U7) | Infrastructure, backups, user management |
| QA Manager (U3) | TBD | Compliance, QC approvals, CAPA |
| Emergency backup IT | TBD | If primary IT Admin unavailable |

---

## 11. Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial operations runbook — V1.1 |
