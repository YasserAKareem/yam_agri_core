# YAM Server Docs - Repository Creation Guide

> **Repository:** `yam-server-docs`
> **Purpose:** Architecture documentation, runbooks, ADRs, onboarding, troubleshooting
> **Owner:** Shared - curated like product infrastructure
> **Release Cadence:** Continuous - docs evolve with understanding

---

## GitHub Repository Form

### Repository Name
```
yam-server-docs
```

### Description
```
Architecture, runbooks, ADRs, and operational playbooks for YAM Server. Docs as infrastructure - searchable, linkable, citable.
```

### Topics
```
documentation, architecture, adrs, runbooks, operations,
troubleshooting, yam-server, docs-as-code
```

---

## File Structure

```
yam-server-docs/
├── architecture/
│   ├── c4-model/
│   │   ├── level-1-context.md
│   │   ├── level-2-container.md
│   │   ├── level-3-component.md
│   │   └── diagrams/
│   ├── adr/
│   │   ├── 0001-use-docker-compose.md
│   │   ├── 0002-litellm-as-gateway.md
│   │   ├── 0003-one-command-bootstrap.md
│   │   └── template.md
│   ├── design-principles.md
│   ├── integration-patterns.md
│   └── scalability-model.md
├── runbooks/
│   ├── incidents/
│   │   ├── gpu-overheat.md
│   │   ├── api-gateway-down.md
│   │   ├── out-of-vram.md
│   │   └── slow-inference.md
│   ├── operations/
│   │   ├── backup-restore.md
│   │   ├── upgrade-process.md
│   │   ├── scaling-up.md
│   │   └── disaster-recovery.md
│   └── maintenance/
│       ├── log-rotation.md
│       ├── certificate-renewal.md
│       └── database-cleanup.md
├── onboarding/
│   ├── new-developers.md
│   ├── platform-team.md
│   ├── ml-engineers.md
│   ├── sre-team.md
│   └── contributors.md
├── guides/
│   ├── hardware-selection.md
│   ├── model-selection.md
│   ├── production-checklist.md
│   ├── security-hardening.md
│   └── performance-tuning.md
├── troubleshooting/
│   ├── common-errors.md
│   ├── gpu-issues.md
│   ├── network-problems.md
│   ├── storage-issues.md
│   └── faq.md
├── security/
│   ├── threat-model.md
│   ├── security-controls.md
│   ├── vulnerability-management.md
│   └── incident-response.md
├── api/
│   ├── litellm-api.md
│   ├── open-webui-api.md
│   ├── vllm-api.md
│   └── agent-api.md
├── glossary/
│   ├── terms.md
│   └── acronyms.md
└── README.md
```

---

## ADR Template

```markdown
# ADR-NNNN: [Short Title]

**Status:** [Proposed | Accepted | Deprecated | Superseded by ADR-XXXX]
**Date:** YYYY-MM-DD
**Deciders:** [Names or roles]
**Context:** [What is the issue we're seeing that motivates this decision?]

## Decision

[What is the change we're proposing and/or doing?]

## Rationale

[Why are we doing this? What were the alternatives?]

## Consequences

### Positive
- [What becomes easier or better?]

### Negative
- [What becomes harder or worse?]

### Neutral
- [What changes but isn't clearly better or worse?]

## Implementation Notes

[How will this be implemented? Any migration needed?]

## Related Decisions

- [ADR-XXXX: Related decision]
- [Link to related docs]
```

---

## Runbook Template

```markdown
# Runbook: [Operation or Incident Name]

**Purpose:** [One-line description]
**Severity:** [P0-Critical | P1-High | P2-Medium | P3-Low]
**SLA:** [Response time / Resolution time]
**On-Call:** [Team or role responsible]

## Symptoms

What you'll observe when this issue occurs:
- [Symptom 1]
- [Symptom 2]
- [Metric threshold that triggers alert]

## Impact

- **Users Affected:** [All | Specific subset]
- **Business Impact:** [Revenue | Reputation | Operations]
- **Severity Rationale:** [Why this severity level?]

## Diagnosis

### Quick Check

```bash
# Command to verify the issue
./scripts/health-check.sh

# Check specific service
docker compose ps service-name
docker compose logs service-name --tail=100
```

### Root Cause Investigation

1. **Check [component]:**
   ```bash
   # Commands to investigate
   ```
   Expected: [What you should see]
   If not: [What it means]

2. **Verify [dependency]:**
   [Investigation steps]

### Common Causes

- **Cause 1:** [Description]
  - Probability: High/Medium/Low
  - Fix: [Quick reference to solution below]

- **Cause 2:** [Description]

## Resolution

### Immediate Mitigation

Steps to restore service quickly:

```bash
# 1. Stop affected service
docker compose stop service-name

# 2. Clear problematic state
rm -rf /data/temp/*

# 3. Restart
docker compose up -d service-name

# 4. Verify health
./scripts/health-check.sh service-name
```

### Complete Fix

Permanent resolution:

1. **Step 1:** [Description]
   ```bash
   # Commands
   ```

2. **Step 2:** [Description]

### Verification

Confirm resolution:
- [ ] Service health check passes
- [ ] Metrics return to normal
- [ ] No errors in logs for 5 minutes
- [ ] End-to-end test passes

## Rollback

If resolution fails:

```bash
# Restore to previous state
./scripts/restore.sh backups/last-known-good/
```

## Prevention

How to prevent this in the future:
- [ ] Add monitoring for [metric]
- [ ] Implement [guardrail]
- [ ] Update [configuration]

## Post-Incident

- [ ] Update runbook with lessons learned
- [ ] Create preventive ticket if needed
- [ ] Update monitoring/alerting
- [ ] Share incident report with team

## Related

- Alert: [Link to alert definition]
- Dashboard: [Link to Grafana dashboard]
- ADR: [Related architectural decision]
- Past Incidents: [Links to previous occurrences]

## History

| Date | Action | Person |
|------|--------|---------|
| YYYY-MM-DD | Created | Name |
| YYYY-MM-DD | Updated after incident #123 | Name |
```

---

## README

```markdown
# YAM Server Documentation

> Docs as infrastructure - searchable, linkable, citable.

## What's Here

### Architecture
Deep technical documentation:
- C4 model diagrams (Context, Container, Component)
- ADRs (Architecture Decision Records)
- Design principles and patterns
- Integration guides

### Runbooks
Operational procedures:
- Incident response (P0-P3)
- Routine operations (backups, upgrades)
- Maintenance tasks

### Onboarding
Get started quickly:
- New developer onboarding
- Role-specific guides (platform, ML, SRE)
- Contribution guidelines

### Guides
How-to documentation:
- Hardware selection
- Model selection
- Production deployment
- Security hardening
- Performance tuning

### Troubleshooting
Problem resolution:
- Common errors and solutions
- Component-specific issues
- FAQ

### Security
Security documentation:
- Threat model
- Security controls
- Incident response
- Vulnerability management

### API
API references:
- LiteLLM gateway
- Open WebUI
- vLLM inference
- Agent platform

## Documentation Principles

1. **Searchable** - Use consistent terminology, comprehensive glossary
2. **Linkable** - Deep links to specific sections
3. **Citable** - Reference from code, issues, discussions
4. **Current** - Update with code changes
5. **Honest** - Document limitations and known issues
6. **Actionable** - Every page should enable action

## How to Use

### For Incidents

1. Identify symptoms
2. Find matching runbook in `runbooks/incidents/`
3. Follow diagnosis steps
4. Execute resolution
5. Verify fix
6. Update runbook with learnings

### For Architecture Questions

1. Start with C4 Level 1 (context)
2. Drill down to specific component
3. Check relevant ADRs for rationale
4. Review integration patterns if crossing boundaries

### For Onboarding

1. Start with `onboarding/new-developers.md`
2. Follow role-specific guide
3. Complete hands-on labs
4. Review architecture docs
5. Read ADRs for key decisions

## Contributing

All contributions welcome:
- Clarifications
- Examples
- Corrections
- New runbooks after incidents
- ADRs for new decisions

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Documentation Standards

### Markdown

- Use GitHub-flavored markdown
- Headers: # for title, ## for sections, ### for subsections
- Code blocks: ` ``` ` with language identifier
- Links: Relative for internal, absolute for external

### Diagrams

- Use Mermaid for diagrams (renders in GitHub)
- Store source in markdown, not separate files
- Include alt text for accessibility

### ADRs

- One ADR per decision
- Sequential numbering: ADR-0001, ADR-0002...
- Never delete, only deprecate
- Use template in `architecture/adr/template.md`

### Runbooks

- One runbook per incident type or operation
- Test runbooks during incident simulation
- Update after every real incident
- Use template in `runbooks/template.md`

## Search

GitHub's built-in search works well:
- In-repo: Use GitHub search bar
- Specific term: `grep -r "term" .`
- By category: Browse directory structure

## Recently Updated

| Document | Last Updated | By |
|----------|-------------|-----|
| ADR-0003: One Command Bootstrap | 2026-03-17 | Platform Team |
| Runbook: GPU Overheat | 2026-03-15 | SRE |
| Guide: Model Selection | 2026-03-10 | ML Team |

## Roadmap

- [ ] Video walkthrough for onboarding
- [ ] Interactive architecture diagrams
- [ ] Automated runbook testing
- [ ] Multi-language support (Arabic, Spanish)
```

---

## Example ADR

```markdown
# ADR-0003: One Command Bootstrap

**Status:** Accepted
**Date:** 2026-03-17
**Deciders:** Platform Team, Product Lead
**Context:** Users struggle with multi-step setup processes. Configuration errors are common. GPU detection and model selection require expertise.

## Decision

The entire YAM Server platform will start with a single command: `./start.sh`

This script will:
1. Detect GPU type and available VRAM
2. Select appropriate model automatically
3. Generate all credentials securely
4. Start all services in correct order
5. Wait for health checks
6. Open browser to working UI

## Rationale

**Why:** Manual configuration is error-prone and intimidating.

**Alternatives considered:**
1. **Multi-command setup** (docker compose up + manual config)
   - Rejected: Too many steps, too many failure points
2. **Interactive wizard** (prompt for each choice)
   - Rejected: Slows down experienced users
3. **Zero-config with defaults** (no customization)
   - Rejected: Can't adapt to different hardware

**Why this approach:**
- Eliminates configuration errors
- Works for novices and experts
- Adapts to hardware automatically
- Maintains "advanced mode" option (manual .env)

## Consequences

### Positive
- Dramatic reduction in setup support requests
- Faster time to "first successful inference"
- Clear marketing differentiation
- Confidence in platform reliability

### Negative
- Bootstrap script becomes complex (must handle edge cases)
- GPU detection failures affect everyone
- Harder to debug (more magic)
- Must maintain compatibility across platforms (Linux, WSL, macOS)

### Neutral
- Advanced users can still use manual .env
- Script must be maintained alongside core platform

## Implementation Notes

- Script location: `scripts/start.sh`
- Required capabilities:
  - GPU detection (nvidia-smi, rocm-smi, fallback to CPU)
  - VRAM measurement
  - Model selection from compatibility matrix
  - Secure random credential generation
  - Docker health check monitoring
- Exit codes: 0=success, 1=user error, 2=system error
- Idempotent: Safe to re-run

## Related Decisions

- ADR-0001: Use Docker Compose (enables single-command start)
- ADR-0002: LiteLLM as Gateway (simplifies service orchestration)
```

---

## Copilot Instructions

```markdown
## Critical Rules

1. **Docs are Code** - Review, test, version control
2. **Runbooks Must Work** - Test during incident simulation
3. **ADRs are Permanent** - Never delete, only deprecate
4. **Links Must be Relative** - Survive repo moves
5. **Examples Required** - Every concept needs example

## Documentation Checklist

Before merging:
- [ ] Tested all commands in document
- [ ] Links work (no 404s)
- [ ] Diagrams render correctly
- [ ] Follows template (if applicable)
- [ ] Added to appropriate index
- [ ] Glossary updated if new terms

## Never Do This

- ❌ Copy docs without updating context
- ❌ Leave commands untested
- ❌ Delete ADRs (deprecate instead)
- ❌ Use absolute GitHub URLs
- ❌ Skip runbook testing
```

---

**Status:** Ready for creation
