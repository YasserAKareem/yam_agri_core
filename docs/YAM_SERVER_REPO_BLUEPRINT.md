# YAM Server - Repository Blueprint

> **Purpose:** This document defines the multi-repository strategy for YAM Server, explaining why the platform is split across multiple repositories, what each repo owns, and how they work together.

---

## Philosophy: Specialized Repos Over Monoliths

The temptation when building a platform is to put everything in one repository. It feels simple. It feels fast. And for the first week or two, it is.

Then reality arrives:

- Models change faster than docs
- Observability evolves faster than workflows
- Media services change faster than text services
- Agents evolve on a different cadence than the gateway
- One team wants to experiment without breaking production
- Different parts need different security/access controls

**YAM Server addresses this with a family of specialized repositories.**

Each repository:
- Owns a **clear surface area**
- Has **explicit ownership boundaries**
- Can **evolve independently**
- Reduces the **blast radius of change**
- Enables **parallel development** by different teams

This is not fragmentation. This is intentional architecture.

---

## The Repository Family

### 1. yam-server-core

**What it owns:**
- Docker Compose files for the core platform
- Service configuration (Traefik, Open WebUI, LiteLLM, vLLM, PostgreSQL, Redis, Tika, embeddings)
- Bootstrap logic (GPU detection, credential generation, first-run setup)
- Health checks and service dependencies
- Environment contracts (`.env` structure, required variables)
- Backup and restore scripts
- Core documentation (getting started, architecture overview)

**What it does NOT own:**
- Model profiles or routing policies → yam-server-models
- Monitoring dashboards → yam-server-observability
- Agent definitions → yam-server-agents
- n8n flows → yam-server-workflows

**Ownership:** Platform engineering, DevOps

**Release cadence:** Stable - changes only when platform contract changes

**Dependencies:**
- References model profiles from `yam-server-models`
- Pulls dashboards from `yam-server-observability`
- Optional: agent configs from `yam-server-agents`

---

### 2. yam-server-models

**What it owns:**
- Model profiles (which models, which quantizations, for which hardware)
- LiteLLM model catalog mappings
- vLLM Semantic Router route policies
- System prompt defaults
- Model alias definitions ("fast", "default", "coder")
- Hardware compatibility matrices
- Quantization guidance (Q4 vs Q8, when to use each)
- Benchmark results per model per GPU

**What it does NOT own:**
- How services deploy → yam-server-core
- Observability of models → yam-server-observability

**Ownership:** ML runtime engineering, inference optimization team

**Release cadence:** Frequent - new models, tuned policies, updated benchmarks

**Why separate:**
- Model landscape changes rapidly
- Routing policies evolve through experimentation
- Different people tune models vs platform infrastructure

---

### 3. yam-server-observability

**What it owns:**
- Grafana dashboards
- Prometheus scrape configs and alert rules
- Loki log aggregation setup
- Tempo trace collection
- SLO definitions (latency targets, error budgets)
- Alert thresholds and escalation policies
- Retention policies
- Operational runbooks (what to do when X fires)

**What it does NOT own:**
- The services being monitored → yam-server-core
- Application-specific metrics → respective app repos

**Ownership:** SRE, platform reliability engineering

**Release cadence:** Moderate - dashboards evolve as platform matures

**Why separate:**
- Observability is a cross-cutting concern
- Dashboards and alerts need fast iteration
- Different stakeholders (SRE vs developers)
- Keeps monitoring config out of core platform releases

---

### 4. yam-server-agents

**What it owns:**
- A2A (agent-to-agent) agent definitions
- Tool wrappers and function schemas
- Starter agent prompts and personalities
- Agent policy packs (allowed tools, constraints)
- Semantic-router route policies specific to agent classes
- Agent orchestration patterns

**What it does NOT own:**
- The inference engine → yam-server-core
- Workflow automation → yam-server-workflows

**Ownership:** Agent platform team, AI application developers

**Release cadence:** Frequent - agents are experimental and evolve rapidly

**Why separate:**
- Agents are high-velocity development
- Need room to experiment without platform stability concerns
- Clear separation between "run a model" and "coordinate agents"

---

### 5. yam-server-workflows

**What it owns:**
- n8n workflow definitions (exported JSON)
- Event-driven job configurations
- Ingest pipeline definitions
- Connector logic (how to pull from external systems)
- Scheduled task definitions
- Approval flow templates
- Integration test data

**What it does NOT own:**
- The n8n service itself → yam-server-core
- Core platform workflows like backups → yam-server-core

**Ownership:** Automation engineering, integration specialists

**Release cadence:** Frequent - workflows change as business needs change

**Why separate:**
- Workflows evolve independently of infrastructure
- Version control for what's usually trapped in a UI
- Different stakeholders (business analysts vs platform engineers)
- Enables workflow CI/CD (lint, test, deploy)

---

### 6. yam-server-media

**What it owns:**
- STT (speech-to-text) service definitions
- TTS (text-to-speech) service configurations
- Image generation worker setup
- Video generation worker setup (separate hardware profile)
- Media-specific model profiles
- Transcoding and format conversion logic
- Media storage and retrieval patterns

**What it does NOT own:**
- Core text inference → yam-server-core
- Observability → yam-server-observability

**Ownership:** Media and multimodal runtime team

**Release cadence:** Variable - STT/TTS stable, image/video experimental

**Why separate:**
- Media has different hardware requirements (more VRAM)
- Text platform should be stable before adding heavy media
- Media workers often run on separate machines
- Protects core platform from GPU-hungry experiments

---

### 7. yam-server-docs

**What it owns:**
- Architecture documentation (ADRs, C4 diagrams)
- Runbooks (incident response, recovery procedures)
- Onboarding guides
- Security and threat models
- Hardware selection guides
- Operational playbooks
- Glossary and terminology
- API documentation
- Troubleshooting guides

**What it does NOT own:**
- README files in component repos (each repo has its own)
- Code comments (those live with the code)

**Ownership:** Shared - curated like product infrastructure

**Release cadence:** Continuous - docs evolve with understanding

**Why separate:**
- Documentation deserves its own review process
- Searchable, linkable, citable architecture knowledge
- Prevents docs from being buried in code repos
- Enables docs-as-code workflow

---

### 8. yam-server-apps

**What it owns:**
- Optional add-on services
- Research tools (SearXNG, etc.)
- Admin helpers (custom dashboards, utilities)
- Internal line-of-business applications
- Customer-specific portals
- Experimental integrations
- Proof-of-concept services

**What it does NOT own:**
- Core platform services → yam-server-core

**Ownership:** Application teams, solution builders, experimental projects

**Release cadence:** Highly variable - each app at its own pace

**Why separate:**
- Keeps experimentation alive without bloating core
- Clear boundary between "platform" and "applications built on platform"
- Apps can have different licenses, ownership, maturity levels
- Fail-fast mentality without risking core stability

---

## How Repositories Work Together

### Reference Pattern

Core repository references other repos via:

1. **Git submodules** (for stable dependencies)
2. **Volume mounts** (for runtime configs)
3. **Package registries** (for versioned artifacts)

Example `docker-compose.yml` snippet:
```yaml
services:
  litellm:
    volumes:
      - ./models/catalog.yaml:/app/catalog.yaml:ro  # from yam-server-models
      - ./observability/litellm-config.json:/app/metrics.json:ro  # from yam-server-observability
```

### Version Pinning

Each repository:
- Tags releases with semantic versioning (`v1.2.3`)
- Core repo specifies compatible versions of dependencies
- CI validates cross-repo compatibility

Example in `yam-server-core` README:
```markdown
## Compatible Versions

- yam-server-models: v1.4.0+
- yam-server-observability: v1.2.0+
- yam-server-agents: v0.9.0+ (optional)
```

### Development Workflow

**For platform-wide changes:**
1. Open coordinated PRs across affected repos
2. Link PRs with "Depends on ORG/repo#123"
3. CI validates cross-repo compatibility
4. Merge in dependency order

**For isolated changes:**
1. Change only the relevant repo
2. Verify backward compatibility
3. Update core repo reference if needed

---

## Repository Boundaries - What Goes Where?

| If you're adding... | Put it in... |
|---------------------|--------------|
| A new core service (Redis, PostgreSQL, etc.) | `yam-server-core` |
| A new model or routing policy | `yam-server-models` |
| A Grafana dashboard or Prometheus alert | `yam-server-observability` |
| An A2A agent definition | `yam-server-agents` |
| An n8n workflow | `yam-server-workflows` |
| A TTS service or image worker | `yam-server-media` |
| An ADR, runbook, or architecture diagram | `yam-server-docs` |
| An optional tool or experiment | `yam-server-apps` |

**When in doubt:** Ask "Does the core platform stop working without this?" If yes → core. If no → appropriate specialized repo.

---

## Access Control by Repository

Different repos need different access policies:

| Repository | Who has write access | Why |
|------------|---------------------|-----|
| `yam-server-core` | Platform team only | Changes affect everyone |
| `yam-server-models` | ML engineers | Specialized knowledge required |
| `yam-server-observability` | SRE team | Operational discipline |
| `yam-server-agents` | Agent developers | Experimental velocity |
| `yam-server-workflows` | Automation team + analysts | Business logic owners |
| `yam-server-media` | Media team | Separate hardware expertise |
| `yam-server-docs` | All teams (with review) | Shared knowledge |
| `yam-server-apps` | Varies by app | Loose coupling |

This enables **parallel development** without stepping on each other.

---

## CI/CD Strategy Per Repository

### yam-server-core
- Validate Compose files
- Secret scanning
- Integration tests (can services reach each other?)
- Security scanning of base images

### yam-server-models
- Validate YAML/JSON schemas
- Lint model configs
- Test that referenced models exist
- Benchmark regressions

### yam-server-observability
- Dashboard JSON validation
- Prometheus rule linting
- Test queries against sample data

### yam-server-agents
- Agent schema validation
- Tool wrapper unit tests
- Policy conflict detection

### yam-server-workflows
- n8n workflow JSON validation
- Lint for secrets in workflows
- Dry-run tests

### yam-server-media
- Service definition validation
- Model availability checks

### yam-server-docs
- Markdown linting
- Link checking
- Spelling
- Diagram rendering

### yam-server-apps
- Varies per app
- At minimum: linting and secret scanning

---

## Anti-Patterns to Avoid

❌ **Don't:** Create a repo per minor feature
✅ **Do:** Group related concerns into meaningful repos

❌ **Don't:** Duplicate configs across repos
✅ **Do:** Reference from core or create a shared-configs repo

❌ **Don't:** Let repos drift without version coordination
✅ **Do:** Pin versions, test compatibility, document requirements

❌ **Don't:** Mix application code with infrastructure
✅ **Do:** Keep platform (core) separate from apps (apps repo)

❌ **Don't:** Put everything in core "just to be safe"
✅ **Do:** Trust the boundary definitions

---

## Migration Path: Monorepo → Family

If you already have a monorepo, migrate gradually:

1. **Phase 1:** Extract `yam-server-docs` (low risk, high value)
2. **Phase 2:** Extract `yam-server-models` (enables ML team independence)
3. **Phase 3:** Extract `yam-server-observability` (SRE ownership)
4. **Phase 4:** Extract `yam-server-apps` (clean up core)
5. **Phase 5+:** Extract agents, workflows, media as needed

Each extraction:
- Preserves git history (`git subtree split`)
- Updates references in core
- Tests end-to-end before declaring success

---

## Communication Between Teams

With multiple repos comes coordination overhead. Minimize with:

1. **Clear ownership** - CODEOWNERS file in each repo
2. **Explicit version dependencies** - Document in README
3. **Cross-repo PR linking** - GitHub "Depends on" conventions
4. **Slack channels per repo** - `#yam-server-core`, `#yam-server-models`, etc.
5. **Weekly sync meeting** - For cross-cutting changes
6. **Shared project board** - Links issues across repos

---

## The Payoff

This multi-repo strategy costs coordination overhead. What do you get in return?

✅ **Parallel development** - Teams don't block each other
✅ **Clear ownership** - No ambiguity about who maintains what
✅ **Reduced blast radius** - Changes stay local
✅ **Independent release cadences** - Fast-moving concerns don't destabilize stable ones
✅ **Specialized CI/CD** - Each repo tests what matters for its domain
✅ **Better security** - Granular access control
✅ **Easier onboarding** - New contributors can understand one repo without grokking the entire platform

The goal is not to create complexity. The goal is to **manage complexity through intentional boundaries**.

---

## Quick Reference

**Creating a new YAM Server repo?** See [YAM_SERVER_NEW_REPO_PROMPT.md](YAM_SERVER_NEW_REPO_PROMPT.md)

**Understanding the architecture?** See [YAM_SERVER_HOW_IT_WORKS.md](YAM_SERVER_HOW_IT_WORKS.md)

**Setting up development environment?** See `yam-server-core` README

**Proposing a new repo?** Open an issue in `yam-server-core` explaining:
- What problem it solves
- Why it can't fit in existing repos
- Who will own it
- Expected release cadence
- Compatibility with existing repos
