# DevOps AI Environment for GTD-Driven Investment Promotion

> **Purpose:** This guide configures a local DevOps AI environment for investment promotion agencies using the Getting Things Done (GTD) methodology, integrated with ERPNext for comprehensive opportunity and risk management.

---

## Table of Contents

1. [Overview](#overview)
2. [GTD Methodology Integration](#gtd-methodology-integration)
3. [AI Gateway Configuration](#ai-gateway-configuration)
4. [ERPNext Integration](#erpnext-integration)
5. [DevOps Environment Setup](#devops-environment-setup)
6. [Build Planning with AI](#build-planning-with-ai)
7. [Templates and Tools](#templates-and-tools)
8. [Usage Examples](#usage-examples)
9. [Troubleshooting](#troubleshooting)

---

## Overview

This environment combines:
- **Local AI Gateway** with Ollama (offline LLM support)
- **GTD-focused AI templates** for capture, clarify, organize, engage, review
- **ERPNext integration** for opportunity and risk tracking
- **Docker-based DevOps stack** for reproducible environments
- **Build planning AI** for project timeline and resource optimization

### Key Capabilities

| Capability | Description | AI Template |
|-----------|-------------|-------------|
| **Capture** | Intake opportunities/risks from multiple sources | `gtd_capture` |
| **Clarify** | Determine actionability and next steps | `gtd_clarify` |
| **Organize** | Categorize into GTD lists and contexts | `gtd_organize` |
| **Opportunity Analysis** | Assess investment feasibility and impact | `opportunity_analysis` |
| **Risk Assessment** | Comprehensive risk evaluation and mitigation | `risk_assessment` |
| **Build Planning** | Project planning with WBS and critical path | `build_planning` |

---

## GTD Methodology Integration

### The Five GTD Phases

#### 1. Capture
**Collect everything** that has your attention into trusted inboxes.

**AI Support:**
```python
# API endpoint: POST /api/method/yam_agri_core.yam_agri_core.api.ai_assist.gtd_capture_assist
{
  "item_type": "email|meeting|call|document",
  "source": "investor@example.com",
  "content": "New manufacturing facility proposal - $5M investment",
  "context": "Sector: Manufacturing, Timeline: Q3 2026, Contact: John Smith"
}
```

**AI Response Includes:**
- Item categorization (opportunity/risk/task/reference)
- Priority suggestion (High/Medium/Low)
- Stakeholder identification
- Recommended next action

#### 2. Clarify
**Process what it means** - is it actionable? What's the desired outcome?

**AI Support:**
```python
# API endpoint: POST /api/method/yam_agri_core.yam_agri_core.api.ai_assist.gtd_clarify_assist
{
  "item_name": "Manufacturing Facility Proposal",
  "item_type": "Investment Opportunity",
  "description": "$5M facility for auto parts manufacturing",
  "context": "Jobs: 200+, Export potential: High, Timeline: 24 months"
}
```

**AI Response Analyzes:**
1. Is this actionable? (Yes/No)
2. Successful outcome definition
3. Very next physical action
4. Owner recommendation
5. Project vs. single action
6. Effort and timeline estimate

#### 3. Organize
**Put it where it belongs** - categorize into appropriate lists.

**GTD Lists:**
- **Next Actions** - specific, physical, visible activities
- **Projects** - multi-step outcomes requiring >1 action
- **Waiting For** - items delegated or pending from others
- **Someday/Maybe** - ideas to review later
- **Reference** - information with no action needed

**Context Tags:**
- `@office` - requires office presence
- `@calls` - phone calls to make
- `@computer` - computer-based work
- `@field` - site visits required
- `@meetings` - agenda items for specific meetings

**AI Support:**
```python
# API endpoint: POST /api/method/yam_agri_core.yam_agri_core.api.ai_assist.gtd_organize_assist
{
  "item_name": "Manufacturing Facility - Site Visit",
  "item_type": "Next Action",
  "next_action": "Schedule site inspection with engineering team",
  "context": "Related to $5M manufacturing opportunity"
}
```

**AI Response Suggests:**
- GTD list assignment
- Context tags
- Time required estimate
- Energy level needed
- Related projects
- Dependencies

#### 4. Engage
**Choose and do** - select actions based on context, time, energy, priority.

**Weekly Review Checklist:**
- [ ] Process all inboxes to zero
- [ ] Review previous week's calendar
- [ ] Review upcoming week's calendar
- [ ] Review Projects list
- [ ] Review Waiting For list
- [ ] Review Someday/Maybe list
- [ ] Capture new ideas/commitments

#### 5. Review
**Weekly review** to keep system current and reliable.

**AI Support for Review:**
```python
# Generate weekly review report
# API endpoint: POST /api/method/yam_agri_core.yam_agri_core.api.ai_assist.gtd_weekly_review
{
  "user": "ceo@agency.gov",
  "week_start": "2026-03-03",
  "week_end": "2026-03-09"
}
```

---

## AI Gateway Configuration

### Local Setup (Ollama)

**1. Install Ollama:**
```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama

# Windows
# Download from https://ollama.com/download
```

**2. Pull Recommended Models:**
```bash
# Lightweight model for GTD assistance (3B parameters, ~2GB RAM)
ollama pull llama3.2:3b

# More capable model for detailed analysis (8B parameters, ~5GB RAM)
ollama pull llama3.1:8b

# Specialized for structured output
ollama pull qwen2.5:7b
```

**3. Configure Environment:**
```bash
cd infra/docker
cp .env.example .env

# Edit .env - add AI Gateway configuration:
# ENABLE_OLLAMA=1
# OLLAMA_URL=http://host.docker.internal:11434/api/generate
# OLLAMA_MODEL=llama3.2:3b
# OLLAMA_ALLOWED_MODELS=llama3.2:3b,llama3.1:8b,qwen2.5:7b
```

**4. Start Ollama Service:**
```bash
# Terminal 1: Start Ollama server
ollama serve

# Terminal 2: Test connectivity
curl http://localhost:11434/api/tags
```

### Docker Compose Integration

The AI Gateway is included in the Docker Compose stack:

```yaml
# infra/docker/docker-compose.yml (already configured)
services:
  ai_gateway:
    build:
      context: ../../tools/ai_gateway
    ports:
      - "8001:8000"
    environment:
      - OLLAMA_URL=${OLLAMA_URL}
      - OLLAMA_MODEL=${OLLAMA_MODEL}
      - ENABLE_OLLAMA=${ENABLE_OLLAMA}
      - OLLAMA_ALLOWED_MODELS=${OLLAMA_ALLOWED_MODELS}
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Start the full stack:**
```bash
cd infra/docker
bash run.sh up
```

**Verify AI Gateway:**
```bash
# Check health
curl http://localhost:8001/health

# List available templates
curl http://localhost:8001/templates

# Test suggestion endpoint
curl -X POST http://localhost:8001/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "task": "gtd-capture",
    "site": "HQ",
    "record_type": "Opportunity",
    "record_name": "TEST-001",
    "template_id": "gtd_capture",
    "template_vars": {
      "item_type": "email",
      "source": "investor@example.com",
      "content": "New factory proposal",
      "context": "Manufacturing sector"
    }
  }'
```

---

## ERPNext Integration

### Creating GTD-Compatible DocTypes

The platform includes custom DocTypes for investment promotion:

#### Investment Opportunity DocType

**Fields:**
- `opportunity_name` (Data, required)
- `site` (Link to Site, required) - for multi-office agencies
- `sector` (Select: Manufacturing/Services/Agriculture/Technology/Tourism/Other)
- `investment_size` (Currency)
- `investor_name` (Data)
- `investor_contact` (Data)
- `description` (Text)
- `gtd_status` (Select: Captured/Clarified/Next Action/Waiting For/Project/Someday-Maybe)
- `gtd_context` (Multi-Select: @office/@calls/@computer/@field/@meetings)
- `next_action` (Small Text)
- `next_action_owner` (Link to User)
- `priority` (Select: High/Medium/Low)
- `stage` (Select: Lead/Qualification/Feasibility/Approval/Implementation/Operational)
- `expected_jobs` (Int)
- `expected_exports` (Currency)
- `timeline_months` (Int)
- `risk_level` (Select: Low/Medium/High/Critical)
- `ai_analysis_summary` (Long Text, Read Only)
- `last_reviewed_date` (Date)

**Permissions:**
- Create: Investment Officer, Manager
- Read: All agency staff (site-isolated)
- Write/Submit: Investment Officer, Manager
- Approve: Agency Director

#### Risk Register DocType

**Fields:**
- `risk_name` (Data, required)
- `site` (Link to Site, required)
- `related_opportunity` (Link to Investment Opportunity)
- `risk_category` (Select: Political/Market/Financial/Technical/Environmental/Social)
- `description` (Text)
- `likelihood` (Select: Very Low/Low/Medium/High/Very High)
- `impact` (Select: Very Low/Low/Medium/High/Very High)
- `risk_score` (Float, computed: likelihood × impact)
- `mitigation_strategy` (Text)
- `contingency_plan` (Text)
- `owner` (Link to User)
- `status` (Select: Identified/Assessed/Mitigating/Monitoring/Closed)
- `review_frequency` (Select: Weekly/Monthly/Quarterly)
- `ai_mitigation_suggestions` (Long Text, Read Only)

### Workspace Configuration

Create a **GTD Investment Desk** workspace:

```json
{
  "name": "GTD Investment Desk",
  "title": "GTD Investment Desk",
  "category": "Modules",
  "icon": "list",
  "is_standard": 0,
  "charts": [
    {
      "chart_name": "Opportunities by Stage",
      "label": "Pipeline Overview"
    },
    {
      "chart_name": "Tasks by GTD Status",
      "label": "GTD Dashboard"
    }
  ],
  "shortcuts": [
    {
      "type": "DocType",
      "link_to": "Investment Opportunity",
      "label": "New Opportunity",
      "color": "Green"
    },
    {
      "type": "DocType",
      "link_to": "Risk Register",
      "label": "New Risk",
      "color": "Red"
    },
    {
      "type": "Page",
      "link_to": "gtd-inbox",
      "label": "GTD Inbox",
      "color": "Blue"
    }
  ],
  "links": [
    {
      "type": "Link",
      "label": "Capture",
      "links": [
        {
          "type": "DocType",
          "link_to": "Investment Opportunity",
          "label": "Opportunities",
          "filters": "[[\"gtd_status\", \"=\", \"Captured\"]]"
        }
      ]
    },
    {
      "type": "Link",
      "label": "Next Actions",
      "links": [
        {
          "type": "DocType",
          "link_to": "Investment Opportunity",
          "label": "My Actions",
          "filters": "[[\"gtd_status\", \"=\", \"Next Action\"], [\"next_action_owner\", \"=\", \"__user__\"]]"
        }
      ]
    },
    {
      "type": "Link",
      "label": "Projects",
      "links": [
        {
          "type": "DocType",
          "link_to": "Investment Opportunity",
          "label": "Active Projects",
          "filters": "[[\"gtd_status\", \"=\", \"Project\"]]"
        }
      ]
    },
    {
      "type": "Link",
      "label": "Waiting For",
      "links": [
        {
          "type": "DocType",
          "link_to": "Investment Opportunity",
          "label": "Pending Items",
          "filters": "[[\"gtd_status\", \"=\", \"Waiting For\"]]"
        }
      ]
    }
  ]
}
```

---

## DevOps Environment Setup

### Prerequisites

- Docker Desktop or Docker + Docker Compose
- 8GB RAM minimum (16GB recommended)
- Ollama installed (for local AI)
- Git

### Quick Start

**1. Clone and Configure:**
```bash
git clone https://github.com/YasserAKareem/yam_agri_core.git
cd yam_agri_core/infra/docker

# Copy and configure environment
cp .env.example .env

# Edit .env with your values:
# - FRAPPE_SITE=invest.localhost
# - ADMIN_PASSWORD=secure_password_here
# - ENABLE_OLLAMA=1
# - OLLAMA_URL=http://host.docker.internal:11434/api/generate
```

**2. Pull Images (for offline capability):**
```bash
# Pull and save all images
bash run.sh prefetch

# This creates ./offline-images.tar (~3-4GB)
# Copy to USB for offline use
```

**3. Start Stack:**
```bash
# Online start
bash run.sh up

# OR offline start (uses saved images)
bash run.sh offline-init
```

**4. Initialize Site:**
```bash
# First time only
bash run.sh init

# This will:
# - Create Frappe site
# - Install ERPNext
# - Install yam_agri_core app
# - Configure AI Gateway integration
```

**5. Access Platform:**
- **ERPNext Desk:** http://localhost:8000
- **AI Gateway:** http://localhost:8001
- **API Docs:** http://localhost:8001/docs

**Default Credentials:**
- Username: `Administrator`
- Password: (value from `.env` `ADMIN_PASSWORD`)

### Environment Variables Reference

```bash
# Core Configuration
FRAPPE_SITE=invest.localhost           # Site name
ADMIN_PASSWORD=ChangeMeInProduction    # Admin password
DB_ROOT_PASSWORD=ChangeMeInProduction  # MariaDB root password

# AI Gateway
ENABLE_OLLAMA=1                        # Enable local LLM
OLLAMA_URL=http://host.docker.internal:11434/api/generate
OLLAMA_MODEL=llama3.2:3b              # Default model
OLLAMA_ALLOWED_MODELS=llama3.2:3b,llama3.1:8b,qwen2.5:7b

# Service Ports (default, can override)
FRAPPE_HTTP_PORT=8000
FRAPPE_WEBSOCKET_PORT=9000
AI_GATEWAY_PORT=8001
IOT_GATEWAY_PORT=8002

# Resource Limits (for 8GB RAM systems)
MARIADB_MAX_CONNECTIONS=50
GUNICORN_WORKERS=2
GUNICORN_THREADS=4
```

### Directory Structure

```
yam_agri_core/
├── infra/docker/
│   ├── docker-compose.yml          # Main orchestration
│   ├── .env                        # YOUR config (never commit)
│   ├── .env.example                # Template
│   ├── run.sh                      # Ops script
│   ├── preflight.sh                # Pre-start checks
│   ├── backups/                    # Auto backups
│   └── offline-images.tar          # Offline image cache
├── tools/
│   ├── ai_gateway/                 # AI Gateway service
│   ├── iot_gateway/                # IoT integration
│   └── evidence_capture/           # Test data
└── apps/yam_agri_core/             # Frappe app
```

### Resource Management (8GB Laptop)

**Service Memory Budget:**
| Service | Allocated RAM |
|---------|---------------|
| MariaDB | ~400 MB |
| Redis (×3) | ~150 MB |
| Frappe Backend | ~1.5-2 GB |
| AI Gateway | ~500 MB |
| Ollama (external) | ~2-5 GB (model dependent) |
| **Total** | **~4.5-6 GB** |

**Optimization Tips:**
```bash
# Stop non-essential services if RAM is tight
docker compose stop iot_gateway

# Use smaller AI model
# In .env: OLLAMA_MODEL=llama3.2:3b  (instead of 8b)

# Limit Ollama concurrent requests
# In .env: OLLAMA_MAX_CONCURRENT=1
```

---

## Build Planning with AI

### Project Planning Workflow

**1. Define Project:**
```python
# API: POST /api/method/yam_agri_core.yam_agri_core.api.ai_assist.build_planning_assist
{
  "project_name": "Technology Park Development",
  "objectives": "Develop 50-acre technology park with 10 buildings, infrastructure, attracting 50+ tech companies",
  "constraints": "Budget: $100M, Timeline: 36 months, Regulatory approvals required",
  "context": "Greenfield site, utilities available, zoning approved"
}
```

**2. AI-Generated Plan Includes:**
- Work Breakdown Structure (WBS)
- Critical path analysis
- Resource requirements (team, budget, tools)
- Timeline with milestones
- Dependency mapping
- Risk mitigation strategies
- Success criteria and KPIs
- Stakeholder communication plan
- Quality gates

**3. Integrate with ERPNext Project:**
```python
# Create ERPNext Project from AI plan
import frappe

def create_project_from_ai_plan(ai_plan_json):
    project = frappe.new_doc("Project")
    project.project_name = ai_plan_json["project_name"]
    project.status = "Open"
    project.project_type = "External"

    # Add tasks from WBS
    for task_data in ai_plan_json["wbs_tasks"]:
        project.append("tasks", {
            "title": task_data["title"],
            "description": task_data["description"],
            "start": task_data["start_date"],
            "end": task_data["end_date"],
            "depends_on": task_data["dependencies"]
        })

    project.insert()
    return project
```

---

## Templates and Tools

### AI Prompt Templates

All templates available at: `http://localhost:8001/templates`

**Quick Reference:**

| Template ID | Use Case | Required Variables |
|-------------|----------|-------------------|
| `gtd_capture` | Capture inbox items | item_type, source, content, context |
| `gtd_clarify` | Clarify actionability | item_name, item_type, description, context |
| `gtd_organize` | Organize into lists | item_name, item_type, next_action, context |
| `opportunity_analysis` | Investment analysis | opportunity_name, sector, investment_size, description, context |
| `risk_assessment` | Risk evaluation | initiative_name, risk_areas, context |
| `build_planning` | Project planning | project_name, objectives, constraints, context |

### Command Line Tools

**Run Bench Commands:**
```bash
# Inside frappe container
cd infra/docker
bash run.sh bench migrate
bash run.sh bench console

# From host via run.sh
bash run.sh bench --site invest.localhost list-apps
bash run.sh bench --site invest.localhost execute yam_agri_core.setup.create_sample_opportunities
```

**Backup and Restore:**
```bash
# Create backup
bash run.sh backup

# List backups
ls -lt infra/docker/backups/

# Restore latest
bash run.sh restore

# Restore specific backup
bash run.sh restore ./backups/20260309_1200/
```

**Health Checks:**
```bash
# Check all services
bash run.sh status

# View logs
bash run.sh logs

# View specific service logs
docker compose -f infra/docker/docker-compose.yml logs -f ai_gateway
```

---

## Usage Examples

### Example 1: Capture New Opportunity

**Scenario:** CEO receives email about new manufacturing investment.

**1. Capture via API:**
```bash
curl -X POST http://localhost:8001/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "task": "gtd-capture",
    "site": "HQ",
    "record_type": "Email",
    "record_name": "investor-inquiry-2026-03-09",
    "template_id": "gtd_capture",
    "template_vars": {
      "item_type": "email",
      "source": "investor@globalcorp.com",
      "content": "Interested in establishing automotive parts manufacturing facility, $8M investment, 300 jobs, exports to GCC markets",
      "context": "Previous contact at trade show, strong financial backing, timeline flexible"
    }
  }'
```

**2. AI Response:**
```json
{
  "ok": true,
  "suggestion": "CATEGORIZATION:\n- Type: Investment Opportunity (High Priority)\n- Sector: Manufacturing (Automotive)\n- Stakeholders: Investor (GlobalCorp), Ministry of Industry, Free Zone Authority\n- Priority: HIGH - significant job creation, export potential\n- Next Action: Schedule initial meeting with investor to discuss requirements and site options\n- Owner: Investment Officer - Manufacturing Sector\n- Estimated Timeline: 18-24 months development\n- Dependencies: Site selection, regulatory approvals, infrastructure assessment"
}
```

**3. Create Investment Opportunity Record:**
```python
# In ERPNext
opportunity = frappe.new_doc("Investment Opportunity")
opportunity.opportunity_name = "GlobalCorp Automotive Parts Manufacturing"
opportunity.site = "HQ"
opportunity.sector = "Manufacturing"
opportunity.investment_size = 8000000
opportunity.investor_name = "GlobalCorp Industries"
opportunity.investor_contact = "investor@globalcorp.com"
opportunity.description = "Automotive parts manufacturing for GCC export"
opportunity.gtd_status = "Captured"
opportunity.priority = "High"
opportunity.expected_jobs = 300
opportunity.timeline_months = 18
opportunity.ai_analysis_summary = "... (paste AI response)"
opportunity.insert()
```

### Example 2: Clarify and Organize

**Scenario:** Processing captured opportunity.

**1. Clarify:**
```bash
curl -X POST http://localhost:8001/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "task": "gtd-clarify",
    "site": "HQ",
    "record_type": "Investment Opportunity",
    "record_name": "GlobalCorp Automotive Parts Manufacturing",
    "template_id": "gtd_clarify",
    "template_vars": {
      "item_name": "GlobalCorp Automotive Parts Manufacturing",
      "item_type": "Investment Opportunity",
      "description": "$8M automotive parts facility, 300 jobs, GCC exports",
      "context": "Timeline: 18-24 months, Investor: financially sound, sector: manufacturing"
    }
  }'
```

**AI Clarification Output:**
```
1. Is this actionable? YES - requires multi-step project approach
2. Successful outcome: Fully operational manufacturing facility with regulatory approvals and initial customer contracts
3. Very next physical action: Call investor to schedule site visit and preliminary meeting
4. Owner: Manufacturing Sector Investment Officer
5. Type: PROJECT (multi-step, >6 months)
6. Estimated effort: 150+ person-hours over 18 months
```

**2. Organize:**
```bash
curl -X POST http://localhost:8001/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "task": "gtd-organize",
    "site": "HQ",
    "record_type": "Investment Opportunity",
    "record_name": "GlobalCorp Automotive Parts Manufacturing",
    "template_id": "gtd_organize",
    "template_vars": {
      "item_name": "Schedule GlobalCorp site visit",
      "item_type": "Next Action",
      "next_action": "Call investor to coordinate initial site inspection",
      "context": "Project: GlobalCorp Manufacturing, Priority: High"
    }
  }'
```

**AI Organization Output:**
```
1. GTD List: Next Actions
2. Context: @calls (requires phone call)
3. Time required: <15 minutes (quick call)
4. Energy level: Medium
5. Related project: GlobalCorp Automotive Parts Manufacturing
6. Dependencies: None (can do immediately)
7. Suggested follow-up: After call, create calendar event for site visit (@office task)
```

**3. Update ERPNext:**
```python
# Update opportunity
opportunity = frappe.get_doc("Investment Opportunity", "OPP-2026-00001")
opportunity.gtd_status = "Next Action"
opportunity.gtd_context = "@calls"
opportunity.next_action = "Call investor@globalcorp.com to schedule site visit and preliminary meeting"
opportunity.next_action_owner = "investment.officer@agency.gov"
opportunity.save()

# Create task/project in ERPNext Project module
project = frappe.new_doc("Project")
project.project_name = "GlobalCorp Automotive Parts - Development"
project.status = "Open"
project.priority = "High"
project.save()
```

### Example 3: Weekly Review with AI

**Scenario:** CEO prepares for weekly review.

```bash
curl -X POST http://localhost:8001/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "task": "chat",
    "site": "HQ",
    "record_type": "Weekly Review",
    "record_name": "2026-W10",
    "context": "Review all opportunities and tasks for week ending 2026-03-09",
    "template_id": "general_assistant",
    "template_vars": {
      "task": "Generate weekly review summary",
      "site": "HQ",
      "record_type": "Weekly Review",
      "record_name": "2026-W10",
      "message": "Summarize: (1) Opportunities in Next Actions status, (2) Items in Waiting For > 7 days, (3) Projects requiring attention, (4) Risks rated High/Critical",
      "context": "User: CEO, Date: 2026-03-09, Focus: Manufacturing and Technology sectors"
    }
  }'
```

**AI Review Summary:**
```
WEEKLY REVIEW - Week 10 (Mar 3-9, 2026)

NEXT ACTIONS REQUIRING ATTENTION (7 items):
1. [HIGH] Call GlobalCorp - site visit scheduling (@calls)
2. [MEDIUM] Review TechPark feasibility study (@computer)
3. [HIGH] Ministry meeting prep - regulatory changes (@office)
...

WAITING FOR (items > 7 days):
1. Environmental impact assessment - ABC Consultants (14 days overdue)
2. Investor visa approval - Immigration Dept (9 days)
...

PROJECTS REQUIRING ATTENTION:
1. GlobalCorp Manufacturing - NEW, needs initial meeting
2. TechPark Phase 1 - feasibility review deadline this week
...

HIGH/CRITICAL RISKS:
1. CRITICAL - Regulatory delay risk on Port Expansion project
2. HIGH - Market demand uncertainty for Hotel Development
...

RECOMMENDATIONS:
- Escalate environmental assessment delay
- Schedule TechPark feasibility review meeting
- Update risk mitigation for Port Expansion regulatory issues
```

---

## Troubleshooting

### AI Gateway Issues

**Problem:** AI Gateway not responding
```bash
# Check service status
docker compose ps ai_gateway

# View logs
docker compose logs ai_gateway

# Restart service
docker compose restart ai_gateway
```

**Problem:** Ollama connection failed
```bash
# Check Ollama is running
ollama list

# Test Ollama API
curl http://localhost:11434/api/tags

# Verify Docker can reach host
# On Linux: use http://172.17.0.1:11434
# On Mac/Win: use http://host.docker.internal:11434
```

**Problem:** Model not found
```bash
# Pull missing model
ollama pull llama3.2:3b

# Verify in .env
grep OLLAMA_MODEL infra/docker/.env
```

### ERPNext Integration Issues

**Problem:** Cannot create Investment Opportunity
```bash
# Check app is installed
bash run.sh bench --site invest.localhost list-apps

# Migrate if needed
bash run.sh bench --site invest.localhost migrate

# Check permissions
# In ERPNext: Setup > Users and Permissions > Role Permission Manager
# Ensure user has Create permission for Investment Opportunity
```

**Problem:** Site isolation not working
```bash
# Verify site permissions are configured
bash run.sh bench --site invest.localhost execute \
  yam_agri_core.yam_agri_core.install.verify_site_permissions
```

### Performance Issues

**Problem:** System slow with 8GB RAM
```bash
# Check memory usage
docker stats

# Stop non-essential services
docker compose stop iot_gateway

# Use smaller AI model
# In .env: OLLAMA_MODEL=llama3.2:3b
ollama pull llama3.2:3b
docker compose restart ai_gateway
```

**Problem:** AI responses too slow
```bash
# Check Ollama resource allocation
# Increase VRAM allocation if GPU available

# Use faster model
ollama pull qwen2.5:3b  # Faster than llama

# Reduce max_tokens in requests
# In API call: "max_tokens": 300 (instead of 800)
```

### Backup and Recovery

**Problem:** Need to restore to previous state
```bash
# List available backups
ls -lt infra/docker/backups/

# Stop services
bash run.sh down

# Restore backup
bash run.sh restore ./backups/20260309_1000/

# Restart
bash run.sh up
```

**Problem:** Backup failed
```bash
# Check disk space
df -h

# Check backup directory permissions
ls -ld infra/docker/backups/

# Manual backup
docker compose exec backend bench --site invest.localhost backup \
  --with-files --backup-path /workspace/backups
```

---

## Next Steps

1. **Customize DocTypes:** Add fields specific to your agency's workflow
2. **Create Reports:** Build custom reports for weekly/monthly reviews
3. **Automate Workflows:** Set up email rules to auto-capture opportunities
4. **Train Staff:** Conduct GTD training sessions with AI assistance demos
5. **Integrate Systems:** Connect existing CRM/email/calendar systems
6. **Monitor Usage:** Track AI usage and refine templates based on feedback

---

## Support and Resources

- **GTD Methodology:** https://todoist.com/productivity-methods/getting-things-done
- **ERPNext Documentation:** https://docs.erpnext.com
- **Frappe Framework:** https://frappeframework.com/docs
- **Ollama Models:** https://ollama.com/library
- **Repository Issues:** https://github.com/YasserAKareem/yam_agri_core/issues

---

**Last Updated:** 2026-03-09
**Version:** 1.0
**Author:** YAM Agri Core Development Team
