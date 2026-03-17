# YAM Server Workflows - Repository Creation Guide

> **Repository:** `yam-server-workflows`
> **Purpose:** n8n workflow definitions, event-driven jobs, ingest pipelines, automation orchestration
> **Owner:** Automation Engineering, Integration Specialists
> **Release Cadence:** Frequent - workflows change as business needs change

---

## GitHub Repository Form

### Repository Name
```
yam-server-workflows
```

### Description
```
n8n flows, event-driven automation, and integration pipelines for YAM Server. Version-controlled workflow definitions.
```

### Topics
```
n8n, workflows, automation, event-driven, integration,
orchestration, yam-server, low-code
```

---

## File Structure

```
yam-server-workflows/
├── workflows/
│   ├── ingestion/
│   │   ├── document-processing.json
│   │   ├── email-monitoring.json
│   │   └── api-webhook-handler.json
│   ├── notifications/
│   │   ├── alert-dispatcher.json
│   │   └── digest-generator.json
│   ├── business/
│   │   ├── approval-flow.json
│   │   ├── report-scheduler.json
│   │   └── data-sync.json
│   └── maintenance/
│       ├── backup-scheduler.json
│       └── cleanup-old-data.json
├── triggers/
│   ├── cron/
│   │   └── schedules.yaml
│   ├── webhooks/
│   │   └── endpoints.yaml
│   └── events/
│       └── event-types.yaml
├── connectors/
│   ├── slack/
│   │   └── slack-connector.json
│   ├── email/
│   │   ├── smtp.json
│   │   └── imap.json
│   ├── databases/
│   │   ├── postgres.json
│   │   └── redis.json
│   └── apis/
│       ├── rest-client.json
│       └── graphql-client.json
├── templates/
│   ├── data-transformation.json
│   ├── error-handling.json
│   ├── retry-logic.json
│   └── conditional-routing.json
├── tests/
│   ├── workflow-validation/
│   │   └── test_workflow_schema.py
│   └── integration/
│       └── test_end_to_end.py
└── docs/
    ├── WORKFLOW_PATTERNS.md
    ├── TESTING_GUIDE.md
    └── DEPLOYMENT.md
```

---

## Example Workflows

### Document Processing Pipeline

```json
{
  "name": "Document Processing Pipeline",
  "nodes": [
    {
      "name": "Watch Folder",
      "type": "n8n-nodes-base.trigger",
      "parameters": {
        "path": "/data/uploads",
        "event": "add"
      }
    },
    {
      "name": "Extract Text (Tika)",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://tika:9998/tika",
        "method": "PUT"
      }
    },
    {
      "name": "Generate Embeddings",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://embeddings:8080/embed",
        "method": "POST"
      }
    },
    {
      "name": "Store in PostgreSQL",
      "type": "n8n-nodes-base.postgres"
    },
    {
      "name": "Notify User",
      "type": "n8n-nodes-base.slack",
      "parameters": {
        "text": "Document processed: {{$node['Watch Folder'].json['filename']}}"
      }
    }
  ],
  "connections": {
    "Watch Folder": {"main": [[{"node": "Extract Text (Tika)"}]]},
    "Extract Text (Tika)": {"main": [[{"node": "Generate Embeddings"}]]},
    "Generate Embeddings": {"main": [[{"node": "Store in PostgreSQL"}]]},
    "Store in PostgreSQL": {"main": [[{"node": "Notify User"}]]}
  }
}
```

### Alert Dispatcher

```json
{
  "name": "Alert Dispatcher",
  "nodes": [
    {
      "name": "Webhook Trigger",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "alerts",
        "method": "POST"
      }
    },
    {
      "name": "Determine Severity",
      "type": "n8n-nodes-base.switch",
      "parameters": {
        "rules": [
          {"value": "critical"},
          {"value": "warning"},
          {"value": "info"}
        ]
      }
    },
    {
      "name": "Page On-Call (Critical)",
      "type": "n8n-nodes-base.pagerduty"
    },
    {
      "name": "Send to Slack (Warning)",
      "type": "n8n-nodes-base.slack"
    },
    {
      "name": "Log Only (Info)",
      "type": "n8n-nodes-base.postgres"
    }
  ]
}
```

---

## README

```markdown
# YAM Server Workflows

> Automation that scales your platform beyond what humans can manually orchestrate.

## What's Inside

- **15+ Production Workflows:** Document processing, notifications, integrations
- **Reusable Templates:** Error handling, retries, transformations
- **Connector Library:** Slack, email, databases, APIs
- **Testing Framework:** Validate workflows before deployment

## Workflow Categories

### Ingestion Pipelines
- Document upload → processing → storage
- Email monitoring → extraction → routing
- API webhooks → validation → action

### Notifications
- Alert routing by severity
- Daily/weekly digest generation
- User notification preferences

### Business Automation
- Approval workflows
- Report scheduling
- Data synchronization

### Maintenance
- Scheduled backups
- Log rotation
- Resource cleanup

## Quick Start

```bash
# Import workflow into n8n
n8n import:workflow --input=workflows/ingestion/document-processing.json

# Test workflow
n8n execute --id=<workflow-id>

# Export modified workflow
n8n export:workflow --id=<workflow-id> --output=workflows/ingestion/
```

## Best Practices

1. **Version Control:** Every workflow in git, not just in n8n UI
2. **Error Handling:** Always include error branches
3. **Idempotency:** Design workflows to be safely re-run
4. **Secrets Management:** Use n8n credentials, never hardcode
5. **Testing:** Validate with test data before production

## Integration with Core

n8n runs as part of yam-server-core:

```yaml
# docker-compose.yml
services:
  n8n:
    image: n8nio/n8n
    volumes:
      - ../workflows:/workflows:ro
    environment:
      - N8N_WORKFLOWS_FOLDER=/workflows
```

## Common Patterns

### Data Transformation

Use Function nodes for complex logic:
```javascript
// Transform API response to database format
return items.map(item => ({
  json: {
    id: item.json.user_id,
    name: item.json.full_name,
    email: item.json.contact.email,
    created_at: new Date().toISOString()
  }
}));
```

### Error Handling

Every workflow should have error branches:
```
Main Flow → [Success] → Continue
         → [Error] → Log Error → Notify Admin → Store for Retry
```

### Retry Logic

For flaky APIs, use exponential backoff:
```
Attempt 1 → Wait 1s → Attempt 2 → Wait 2s → Attempt 3 → Wait 4s → Fail
```
```

---

## Copilot Instructions

```markdown
## Critical Rules

1. **Workflows Must Be Exportable** - All workflows must export cleanly to JSON
2. **No Secrets in Workflows** - Use n8n credentials manager
3. **Error Branches Required** - Every workflow must handle errors
4. **Testing Before Merge** - Test workflows with representative data
5. **Documentation Required** - Each workflow needs purpose, triggers, outputs

## Workflow Design Principles

- **Single Responsibility:** One workflow = one job
- **Composability:** Build from reusable sub-workflows
- **Observability:** Log inputs, outputs, errors
- **Idempotency:** Safe to re-run without side effects

## Never Do This

- ❌ Hardcode API keys or passwords
- ❌ Create workflows without error handling
- ❌ Deploy without testing
- ❌ Leave workflows undocumented
```

---

**Status:** Ready for creation
