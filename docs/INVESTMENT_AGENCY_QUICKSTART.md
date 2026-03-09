# Investment Promotion Agency - AI-Enhanced GTD Environment

> **Quick Setup for Investment Agencies**
>
> This guide helps CEOs and investment promotion agencies set up a local DevOps AI environment integrated with the Getting Things Done (GTD) methodology and ERPNext for comprehensive opportunity tracking, risk management, and build planning.

---

## 🎯 What This System Does

This platform combines:

1. **GTD Methodology** - Systematic approach to managing opportunities, risks, and tasks
2. **Local AI Environment** - Ollama-powered AI assistance for analysis and planning
3. **ERPNext Integration** - Enterprise-grade opportunity and project tracking
4. **DevOps Best Practices** - Docker-based reproducible environment
5. **Build Planning Tools** - AI-assisted project planning and resource allocation

### Key Features

| Feature | Description | Benefit |
|---------|-------------|---------|
| **GTD Capture** | AI-assisted categorization of incoming opportunities | Never miss an opportunity |
| **GTD Clarify** | Determine actionability and next steps | Clear decision-making |
| **GTD Organize** | Smart categorization into action lists | Efficient workflow |
| **Opportunity Analysis** | AI-powered investment feasibility assessment | Data-driven decisions |
| **Risk Assessment** | Comprehensive risk evaluation and mitigation | Proactive risk management |
| **Build Planning** | Project planning with timeline and resource optimization | Realistic execution plans |
| **ERPNext CRM** | Track opportunities, projects, and stakeholders | Centralized information |
| **Local AI** | Offline AI capabilities for sensitive data | Data sovereignty |

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites

Before starting, ensure you have:

- **Computer:** 8GB RAM minimum (16GB recommended)
- **Operating System:** Windows 10+, macOS 10.15+, or Linux
- **Internet:** Required for initial setup (can work offline after setup)
- **Time:** ~30 minutes for full setup

### One-Command Setup

```bash
# Clone the repository
git clone https://github.com/YasserAKareem/yam_agri_core.git
cd yam_agri_core/infra/docker

# Run the automated setup
bash setup-investment-agency.sh
```

The script will:
1. ✅ Check prerequisites (Docker, Ollama)
2. ✅ Configure environment (.env file)
3. ✅ Pull AI models (Ollama)
4. ✅ Pull Docker images
5. ✅ Start all services
6. ✅ Initialize ERPNext site
7. ✅ Create sample GTD opportunities (optional)

**After setup completes:**
- Access ERPNext: http://localhost:8000
- Access AI Gateway: http://localhost:8001
- Username: `Administrator`
- Password: (shown during setup)

---

## 📋 GTD Workflow for Investment Agencies

### The Five GTD Phases

#### 1. 📥 Capture
**Collect everything** - opportunities, risks, tasks from all sources.

**Sources:**
- Email inquiries from investors
- Meeting notes with stakeholders
- Phone calls from prospects
- Government announcements
- Market research reports
- Trade show contacts

**AI Assistance:**
```
Use: GTD Capture template
Input: Email, call notes, meeting summary
Output: Categorization, priority, stakeholders, next action
```

#### 2. 🔍 Clarify
**Process what it means** - Is it actionable? What's the outcome?

**Questions to Answer:**
- Is this a real investment opportunity?
- What's the successful outcome?
- What's the very next physical action?
- Who should own this?
- Is this a quick action or a project?

**AI Assistance:**
```
Use: GTD Clarify template
Input: Opportunity description
Output: Actionability assessment, outcome definition, next action, owner, timeline
```

#### 3. 🗂️ Organize
**Put it where it belongs** - categorize into appropriate lists.

**GTD Lists:**
- **Next Actions** - Specific tasks you can do now
- **Projects** - Multi-step outcomes (e.g., "Secure ABC Manufacturing Investment")
- **Waiting For** - Items you've delegated or are waiting on
- **Someday/Maybe** - Ideas to consider later
- **Reference** - Information with no action needed

**Context Tags:**
- `@office` - Requires office (meetings, document review)
- `@calls` - Phone calls to make
- `@computer` - Computer work (analysis, emails)
- `@field` - Site visits, inspections
- `@meetings` - Agenda items for specific meetings

**AI Assistance:**
```
Use: GTD Organize template
Input: Clarified item and next action
Output: Recommended list, context tags, time/energy required, dependencies
```

#### 4. ⚡ Engage
**Choose and do** - Pick actions based on context, time, energy, priority.

**Decision Factors:**
1. **Context** - Where are you? (@office, @field, @computer)
2. **Time Available** - 5 minutes? 2 hours? Full day?
3. **Energy Level** - High energy for strategic work, low for routine tasks
4. **Priority** - High-value opportunities first

**Example Daily Workflow:**
- **Morning (High Energy):** Strategic analysis, investor meetings
- **Midday:** Phone calls, quick actions
- **Afternoon:** Computer work, document review
- **End of Day:** Process inbox, plan tomorrow

#### 5. 🔄 Review
**Weekly review** - Keep system current and reliable.

**Weekly Review Checklist:**
- [ ] Process all inboxes to zero (email, voicemail, notes)
- [ ] Review previous week's calendar (missed opportunities?)
- [ ] Review upcoming week's calendar (prepare for meetings)
- [ ] Review Projects list (any stuck projects?)
- [ ] Review Waiting For list (follow up on delays)
- [ ] Review Someday/Maybe list (any ready to activate?)
- [ ] Capture new ideas and commitments
- [ ] Update priorities based on agency goals

**AI Assistance:**
```
Use: Weekly Review report
Input: Date range, focus areas
Output: Summary of actions, waiting items, projects, risks, recommendations
```

---

## 💼 Use Cases for Investment Agencies

### Use Case 1: New Investor Inquiry

**Scenario:** CEO receives email from potential investor interested in manufacturing.

**GTD Workflow:**

1. **Capture** (Email → Inbox)
   - Forward email to `opportunities@agency.gov`
   - Or manually create in ERPNext
   - AI categorizes: "Investment Opportunity - Manufacturing"

2. **Clarify**
   - AI analyzes email content
   - Identifies: Actionable, $5M investment, 200 jobs
   - Recommends: Schedule meeting as next action

3. **Organize**
   - List: Next Actions
   - Context: @calls
   - Owner: Manufacturing Sector Officer
   - Project: "ABC Manufacturing Investment"

4. **Engage**
   - Officer calls investor (15 min)
   - Schedules site visit (@field)
   - Requests proposal documents (@computer)

5. **Review**
   - Weekly: Check if proposal received
   - Monthly: Review project progress

### Use Case 2: Risk Assessment for Large Project

**Scenario:** $25M hotel development proposal needs risk evaluation.

**AI Workflow:**

1. Use **Risk Assessment** template
   - Input: Hotel project details
   - AI identifies: Market risk (tourism volatility), regulatory risk (permits), financial risk (currency fluctuation)

2. AI provides:
   - Likelihood × Impact scores
   - Mitigation strategies
   - Contingency plans
   - Monitoring indicators

3. Create Risk Register in ERPNext
   - Link to Investment Opportunity
   - Assign risk owners
   - Set review frequency

### Use Case 3: Build Planning for Technology Park

**Scenario:** Need to plan 36-month technology park development.

**AI Workflow:**

1. Use **Build Planning** template
   - Input: Project objectives, constraints, context
   - AI generates: WBS, critical path, milestones, resource requirements

2. Review AI Plan:
   - Phase 1: Feasibility (3 months)
   - Phase 2: Design (6 months)
   - Phase 3: Approvals (4 months)
   - Phase 4: Construction (20 months)
   - Phase 5: Operation (ongoing)

3. Import to ERPNext Project
   - Create tasks with dependencies
   - Assign team members
   - Track progress with Gantt chart

---

## 🛠️ Configuration and Customization

### Agency-Specific Settings

Edit `infra/docker/.env`:

```bash
# Your agency details
AGENCY_NAME=National Investment Promotion Agency
AGENCY_SHORT_NAME=NIPA
AGENCY_CONTACT_EMAIL=info@nipa.gov

# Priority sectors (affects AI scoring)
PRIORITY_SECTORS=Manufacturing,Technology,Renewable Energy,Agriculture,Tourism

# Investment thresholds (USD)
SMALL_INVESTMENT_MAX=1000000      # < $1M
MEDIUM_INVESTMENT_MAX=10000000    # $1M - $10M
LARGE_INVESTMENT_MIN=10000000     # > $10M

# Approval thresholds
REQUIRE_DIRECTOR_APPROVAL_THRESHOLD=5000000   # > $5M
REQUIRE_BOARD_APPROVAL_THRESHOLD=25000000     # > $25M

# GTD settings
GTD_CONTEXTS=@office,@calls,@computer,@field,@meetings,@travel
GTD_WEEKLY_REVIEW_DAY=Friday
```

### AI Model Selection

Choose based on your hardware:

| Model | RAM Required | Speed | Quality | Best For |
|-------|--------------|-------|---------|----------|
| `llama3.2:3b` | ~2GB | Fast | Good | Quick GTD assistance, categorization |
| `llama3.1:8b` | ~5GB | Medium | Excellent | Detailed analysis, build planning |
| `qwen2.5:7b` | ~4GB | Medium | Very Good | Structured output, risk assessment |
| `gemma2:9b` | ~6GB | Slower | Excellent | Comprehensive analysis, strategic planning |

**Install models:**
```bash
ollama pull llama3.2:3b       # Recommended for most users
ollama pull llama3.1:8b       # If you have 16GB+ RAM
ollama pull qwen2.5:7b        # Good balance
```

**Configure in .env:**
```bash
OLLAMA_MODEL=llama3.2:3b
OLLAMA_ALLOWED_MODELS=llama3.2:3b,llama3.1:8b,qwen2.5:7b
```

### ERPNext Customization

**Create Custom Fields:**
1. Log in to ERPNext
2. Go to: Customization > Customize Form
3. Select DocType: "Investment Opportunity"
4. Add fields specific to your agency

**Example Custom Fields:**
- Investment Sector (Select)
- Expected Jobs (Integer)
- Expected Exports (Currency)
- Timeline Months (Integer)
- Investor Country (Link to Country)
- Site Location (Geolocation)

**Create Custom Reports:**
1. Reports > Report Builder
2. Select: Investment Opportunity
3. Add columns: Opportunity Name, Sector, Investment Size, Stage, Priority
4. Add filters: GTD Status, Priority, Sector
5. Save as: "Active Opportunities Pipeline"

---

## 📊 Dashboard and Reports

### CEO Dashboard (Quick View)

**Key Metrics:**
- Total Opportunities in Pipeline
- Total Investment Value (USD)
- Expected Job Creation
- Opportunities by Stage (funnel chart)
- Opportunities by Sector (pie chart)
- GTD Next Actions (my tasks)
- High-Risk Items (attention needed)

**Access:** ERPNext > GTD Investment Desk > Dashboard

### Weekly Review Report

**Generated Every Friday:**
- Opportunities Captured this week
- Opportunities Moved to Implementation
- Projects Requiring Attention
- Waiting For items > 7 days
- High/Critical Risks
- AI Recommendations

**Access:** ERPNext > Reports > Weekly GTD Review

### Monthly Portfolio Report

**Generated 1st of each month:**
- Pipeline Summary by Sector
- Conversion Rates (Lead → Implementation)
- Average Processing Time
- Job Creation Projections
- Export Potential
- Risk Trends

**Export as:** PDF, Excel, CSV

---

## 🔧 DevOps Operations

### Daily Operations

**Start System:**
```bash
cd infra/docker
bash run.sh up
```

**Stop System:**
```bash
cd infra/docker
bash run.sh down
```

**View Logs:**
```bash
cd infra/docker
bash run.sh logs                    # All services
bash run.sh logs ai_gateway         # Specific service
```

**Check Status:**
```bash
cd infra/docker
bash run.sh status
```

### Backup and Recovery

**Create Backup:**
```bash
cd infra/docker
bash run.sh backup

# Backups stored in: ./backups/YYYYMMDD_HHMM/
```

**Restore Backup:**
```bash
cd infra/docker
bash run.sh restore                           # Latest backup
bash run.sh restore ./backups/20260309_1200/  # Specific backup
```

**Automated Backups:**
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /path/to/yam_agri_core/infra/docker && bash run.sh backup
```

### Offline Deployment

**Prepare for Offline:**
```bash
cd infra/docker
bash run.sh prefetch

# This creates: ./offline-images.tar (~3-4GB)
# Copy to USB drive
```

**Deploy Offline:**
```bash
# On offline machine
cd infra/docker
bash run.sh offline-init
bash run.sh init
```

### Multi-Office Deployment

For agencies with regional offices:

**1. Central Office:**
- Full installation with all features
- Master data management
- Consolidated reporting

**2. Regional Offices:**
- Lightweight installation
- Sync to central every 6 hours
- Offline-capable

**Configure Sync:**
```bash
# In regional office .env
SYNC_ENABLED=1
SYNC_CENTRAL_URL=https://central.agency.gov
SYNC_INTERVAL_HOURS=6
```

---

## 📚 Training and Adoption

### CEO Quick Start (30 Minutes)

1. **Introduction to GTD (10 min)**
   - Watch: [GTD in 15 minutes](https://www.youtube.com/watch?v=gCswMsONkwY)
   - Read: [GTD Overview](https://todoist.com/productivity-methods/getting-things-done)

2. **Platform Tour (10 min)**
   - Log in to ERPNext
   - Navigate: GTD Investment Desk
   - Create first opportunity
   - Try AI Capture assistant

3. **First Week Workflow (10 min)**
   - Process daily inbox
   - Use AI for clarification
   - Review weekly report
   - Plan next week

### Team Training (2 Hours)

**Session 1: GTD Fundamentals (1 hour)**
- 5 phases of GTD
- Lists and contexts
- Weekly review process
- Hands-on exercise

**Session 2: Platform Usage (1 hour)**
- Creating opportunities
- Using AI templates
- Reports and dashboards
- Collaboration features

**Materials:** `docs/DEVOPS_AI_GTD_SETUP.md`

### Best Practices

1. **Daily Review** (15 min)
   - Process email inbox
   - Update next actions
   - Review calendar

2. **Weekly Review** (1 hour, Friday PM)
   - Process all inboxes to zero
   - Review projects and waiting items
   - Plan next week's priorities
   - Run AI weekly review

3. **Monthly Review** (2 hours)
   - Review portfolio performance
   - Update strategic priorities
   - Analyze risk trends
   - Refine AI templates

4. **Quarterly Planning** (Half day)
   - Strategic goal setting
   - Resource allocation
   - Team capacity planning
   - System optimization

---

## 🆘 Troubleshooting

### Common Issues

**Problem:** AI Gateway not responding
```bash
# Solution 1: Check Ollama is running
ollama list

# Solution 2: Restart AI Gateway
docker compose restart ai_gateway

# Solution 3: Check logs
docker compose logs ai_gateway
```

**Problem:** Slow performance on 8GB laptop
```bash
# Solution 1: Use smaller AI model
ollama pull llama3.2:3b
# Update .env: OLLAMA_MODEL=llama3.2:3b

# Solution 2: Stop non-essential services
docker compose stop iot_gateway

# Solution 3: Limit resources in .env
DOCKER_MEMORY_LIMIT_DB=512m
DOCKER_MEMORY_LIMIT_FRAPPE=2g
```

**Problem:** Cannot access ERPNext at localhost:8000
```bash
# Solution 1: Check services are running
docker compose ps

# Solution 2: Check firewall
sudo ufw allow 8000/tcp

# Solution 3: Try 127.0.0.1:8000 instead
```

**Problem:** Forgot admin password
```bash
# Solution: Reset password
cd infra/docker
bash run.sh bench --site invest.localhost set-admin-password NewPassword123
```

### Getting Help

1. **Documentation:** `docs/DEVOPS_AI_GTD_SETUP.md`
2. **GitHub Issues:** https://github.com/YasserAKareem/yam_agri_core/issues
3. **Frappe Forum:** https://discuss.frappe.io
4. **ERPNext Docs:** https://docs.erpnext.com

---

## 🎓 Additional Resources

### GTD Resources
- **Book:** "Getting Things Done" by David Allen
- **Online Guide:** https://todoist.com/productivity-methods/getting-things-done
- **Video:** [GTD Workflow](https://www.youtube.com/watch?v=gCswMsONkwY)

### ERPNext Resources
- **Documentation:** https://docs.erpnext.com
- **User Manual:** https://docs.erpnext.com/docs/user/manual/en
- **Video Tutorials:** https://www.youtube.com/c/FrappeTech

### AI and Ollama
- **Ollama:** https://ollama.com
- **Models Library:** https://ollama.com/library
- **Best Practices:** https://github.com/ollama/ollama/blob/main/docs/faq.md

### DevOps
- **Docker Documentation:** https://docs.docker.com
- **Docker Compose:** https://docs.docker.com/compose/
- **Infrastructure as Code:** https://www.terraform.io/intro

---

## 🗺️ Roadmap

### Version 1.0 (Current)
- ✅ GTD methodology integration
- ✅ AI-assisted capture, clarify, organize
- ✅ Local Ollama AI environment
- ✅ ERPNext opportunity tracking
- ✅ Build planning templates
- ✅ Risk assessment framework

### Version 1.1 (Q2 2026)
- 📋 Email integration for auto-capture
- 📋 Calendar sync (Google/Outlook)
- 📋 Mobile app for field work
- 📋 Advanced analytics dashboard
- 📋 Multi-language support (Arabic, French, Spanish)

### Version 2.0 (Q3 2026)
- 📋 Multi-agent AI collaboration
- 📋 Predictive analytics (success probability)
- 📋 Automated reporting to government portals
- 📋 CRM integration (Salesforce, HubSpot)
- 📋 Advanced visualization (GIS mapping)

---

## 📝 License and Support

**License:** MIT License (see LICENSE file)

**Commercial Support:** Available for enterprise deployments

**Community Support:** GitHub Issues and Frappe Forum

---

**Last Updated:** 2026-03-09
**Version:** 1.0.0
**Authors:** YAM Agri Core Development Team

---

## 🚀 Ready to Get Started?

```bash
# One command to rule them all:
git clone https://github.com/YasserAKareem/yam_agri_core.git
cd yam_agri_core/infra/docker
bash setup-investment-agency.sh
```

**Questions?** Open an issue: https://github.com/YasserAKareem/yam_agri_core/issues

**Happy Investing! 🎯📊💼**
