# YAM Server Observability - Repository Creation Guide

> **Repository:** `yam-server-observability`
> **Purpose:** Grafana dashboards, Prometheus alerts, SLO definitions, operational runbooks
> **Owner:** SRE Team, Platform Reliability Engineering
> **Release Cadence:** Moderate - dashboards evolve as platform matures

---

## GitHub Repository Form

### Repository Name
```
yam-server-observability
```

### Description (160 characters)
```
Grafana dashboards, Prometheus rules, Loki/Tempo configs, and SLO definitions for YAM Server. The watchtower that makes the platform dependable.
```

### Topics
```
observability, grafana, prometheus, loki, tempo, slo, dashboards,
alerting, monitoring, yam-server
```

---

## File Structure

```
yam-server-observability/
├── dashboards/
│   ├── grafana/
│   │   ├── platform-overview.json
│   │   ├── model-performance.json
│   │   ├── resource-usage.json
│   │   ├── api-gateway.json
│   │   └── user-experience.json
│   └── provisioning/
│       └── dashboards.yaml
├── alerts/
│   ├── prometheus/
│   │   ├── platform-health.yml
│   │   ├── model-performance.yml
│   │   ├── resource-limits.yml
│   │   └── slo-violations.yml
│   └── alertmanager/
│       ├── config.yml
│       └── templates/
├── slos/
│   ├── availability.yaml
│   ├── latency.yaml
│   ├── error-rate.yaml
│   └── throughput.yaml
├── queries/
│   ├── promql/
│   │   ├── model-tokens-per-second.promql
│   │   ├── api-latency-p95.promql
│   │   └── gpu-utilization.promql
│   └── logql/
│       ├── error-patterns.logql
│       └── slow-queries.logql
├── runbooks/
│   ├── high-gpu-temperature.md
│   ├── api-gateway-down.md
│   ├── slow-inference.md
│   └── disk-space-low.md
├── config/
│   ├── prometheus.yml
│   ├── loki.yaml
│   ├── tempo.yaml
│   └── retention-policies.yaml
└── docs/
    ├── METRICS_CATALOG.md
    ├── DASHBOARD_GUIDE.md
    └── ALERTING_PHILOSOPHY.md
```

---

## Key Components

### Platform Overview Dashboard

Tracks overall health:
- Active users
- Requests per minute
- P50/P95/P99 latency
- Error rate
- GPU utilization
- Model tokens/second

### Model Performance Dashboard

Inference metrics:
- Time to first token
- Tokens per second
- VRAM usage
- Batch size distribution
- Model routing decisions

### SLO Definitions

```yaml
# slos/latency.yaml
availability_target: 99.5%   # 43 minutes downtime per month
latency_p95_ms: 500
latency_p99_ms: 1000
error_budget:
  monthly: 0.5%
  alert_threshold: 50%  # Alert when 50% of error budget consumed
```

### Critical Alerts

- GPU temperature > 85°C
- VRAM utilization > 95%
- API gateway down > 1 minute
- P95 latency > 2x SLO
- Error rate > 5%

---

## README Template

```markdown
# YAM Server Observability

> The watchtower that makes the platform dependable.

## What You Get

- **5 Grafana Dashboards:** Platform, models, resources, gateway, UX
- **12 Alert Rules:** Critical, warning, and informational
- **4 SLO Definitions:** Availability, latency, errors, throughput
- **8 Runbooks:** What to do when alerts fire

## Quick Start

Import dashboards:
```bash
# From yam-server-core
docker compose up grafana
# Navigate to http://localhost:3001
# Import from dashboards/grafana/*.json
```

## Dashboard Catalog

| Dashboard | Purpose | Key Metrics |
|-----------|---------|-------------|
| **Platform Overview** | Health at a glance | Uptime, requests, errors |
| **Model Performance** | Inference quality | Tokens/sec, latency, VRAM |
| **Resource Usage** | Hardware monitoring | GPU, CPU, memory, disk |
| **API Gateway** | LiteLLM metrics | Auth, routing, rate limits |
| **User Experience** | End-user perspective | P95 latency, success rate |

## Alert Philosophy

We follow **symptom-based alerting**:
- Alert on user impact, not internal metrics
- Actionable alerts only (always has a runbook)
- Three severity levels: critical, warning, info
- Pages wake humans only for critical alerts

## SLO Targets (v1.0)

- **Availability:** 99.5% (43 min downtime/month)
- **Latency P95:** < 500ms
- **Latency P99:** < 1000ms
- **Error Rate:** < 0.5%

## Integration

Works with yam-server-core:
```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ../observability/config/prometheus.yml:/etc/prometheus/prometheus.yml
      - ../observability/alerts:/etc/prometheus/alerts

  grafana:
    image: grafana/grafana
    volumes:
      - ../observability/dashboards:/etc/grafana/provisioning/dashboards
```
```

---

## Copilot Instructions Highlights

```markdown
## Critical Rules

1. **Alerts Must Be Actionable** - Every alert must have a runbook
2. **SLOs Must Be Realistic** - Based on actual hardware capabilities
3. **Dashboards Must Load Fast** - Optimize queries, use recording rules
4. **No Alert Fatigue** - Warning alerts must not page humans

## Dashboard Design Principles

- Overview first, details on demand
- Time ranges: 1h, 6h, 24h, 7d
- Consistent color scheme (green=good, yellow=warning, red=critical)
- Always show error budget burn rate
```

---

**Status:** Ready for creation
