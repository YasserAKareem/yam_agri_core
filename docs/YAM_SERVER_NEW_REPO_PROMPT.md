# YAM Server - New Repository Creation Prompt

> **Purpose:** This document provides the exact prompt to use when creating a new GitHub repository for YAM Server or any of its component repositories.

---

## The Core Repository Prompt

When creating the **yam-server-core** repository (or any YAM Server family repository), use this prompt in the repository description and initial README:

### Repository Description (Short Form)

```
Compose-first AI platform for small teams. Local LLM gateway with Open WebUI, LiteLLM, vLLM, PostgreSQL+pgvector, Redis. Your gateway. Your models. Your rules.
```

### Initial README Prompt (Detailed Form)

```markdown
# YAM Server

A Compose-first AI platform designed for small teams who want to run serious local AI infrastructure without pretending every machine is a datacenter.

## What Problem Does This Solve?

Getting one model running locally is easy. Building a platform that survives real use is not.

YAM Server bridges the gap between "I have a chat window" and "I have a platform" by providing:

- **Identity and governance** through LiteLLM gateway (keys, teams, budgets, logs)
- **Clean user experience** via Open WebUI
- **Fast local inference** with vLLM
- **Document memory** using PostgreSQL + pgvector
- **Routing flexibility** through vLLM Semantic Router
- **Operational discipline** with Redis caching, observability, and backups

## The Core Stack

- **Traefik** - Front gate (TLS termination, stable URLs)
- **Open WebUI** - User interface
- **LiteLLM** - Gateway, auth, model catalog, usage tracking
- **vLLM Semantic Router** - Routing decisions
- **vLLM** - Local inference engine
- **PostgreSQL + pgvector** - Application state and document retrieval
- **Redis** - Caching and coordination
- **Tika** - Document extraction
- **Embeddings service** - Vector generation
- **Observability stack** - Logs, traces, metrics

## Getting Started

### One Command. Complete Platform.

```bash
./start.sh
```

That's the entire setup. No configuration files. No manual downloads. No credential management.

The bootstrap script automatically:
- **Detects your GPU** (NVIDIA, AMD, or CPU-only)
- **Picks the right model** for your VRAM (8GB → Llama 3.2 3B, 16GB → Llama 3.1 8B)
- **Generates secure credentials** (API keys, passwords, tokens)
- **Starts all services** (Open WebUI, LiteLLM, vLLM, PostgreSQL, Redis, Traefik)
- **Runs health checks** until everything is ready
- **Opens your browser** to http://localhost

From clone to working AI platform in under 5 minutes.

## Design Philosophy

1. **Honest about hardware limits** - An RTX 4060 (8GB VRAM) runs text and retrieval excellently. It doesn't run everything at once.
2. **Compose-first** - Built for a serious workstation, not a giant cluster on day one.
3. **Clean boundaries** - Gateway, inference, storage, and observability stay separate.
4. **Growth through modularity** - Add services when they solve real bottlenecks, not because they feel modern.

## Hardware Target

**Minimum useful configuration:**
- RTX 4060 with 8 GB VRAM
- 32 GB system RAM
- 500 GB NVMe storage
- Modern quad-core CPU

**Honest scope for 8 GB VRAM:**
- ✅ Text generation (fast)
- ✅ Embeddings and document retrieval
- ✅ Light voice work
- ⚠️ Multiple simultaneous large models (limited)
- ❌ Heavy video generation (needs separate worker)

## Repository Family

YAM Server is a family of repositories, not a monolith:

- **yam-server-core** - Platform (this repo)
- **yam-server-models** - Model profiles and routing policies
- **yam-server-observability** - Dashboards, alerts, SLO definitions
- **yam-server-agents** - A2A agents and tool wrappers
- **yam-server-workflows** - n8n flows and automation
- **yam-server-media** - STT, TTS, image/video workers
- **yam-server-docs** - Runbooks, ADRs, architecture
- **yam-server-apps** - Optional add-on services

Each repo owns a clean surface area and can evolve independently.

## What Makes This Different

Unlike typical "run AI locally" demos:

- **Gateway-first** - LiteLLM stays in front even for local inference
- **Multi-tenancy ready** - Teams, keys, and budgets from day one
- **Document-native** - Not just chat, but retrieval from your material
- **Operationally honest** - Backups, health checks, and observability are core, not optional
- **Modular growth** - Add services when you need them, not all at once

## Key Workflows

### Chat Request Flow
```
Browser → Open WebUI → LiteLLM → Semantic Router → vLLM → Response
```

### Document Upload Flow
```
Upload → Open WebUI → Tika → Embeddings → PostgreSQL+pgvector
Query → Retrieval → Prompt augmentation → LiteLLM → vLLM
```

## Add-ons (Install After Core)

**Soon after core:**
- Authentik (OIDC/SSO)
- Grafana LGTM (observability)
- n8n (automation)
- SearXNG (research)

**When document workflows grow:**
- Langfuse (prompt observability)
- Qdrant (only if pgvector isn't enough)

**When voice matters:**
- Local STT service
- Local TTS service

**When creative workflows matter:**
- Image worker (separate GPU budget)
- Video worker (separate machine recommended)

## Documentation

See `docs/YAM_SERVER_HOW_IT_WORKS.md` for the complete architecture explanation.

## Contributing

Contributions welcome. Follow the [CONTRIBUTING.md](CONTRIBUTING.md) guide.

## License

[Choose: MIT, Apache 2.0, or GPL-3.0]

---

**Your gateway. Your models. Your documents. Your routes. Your repos. Your rules.**
```

---

## Prompt Variations by Repository

When creating specific family repositories, adapt the description:

### yam-server-models
```
Model profiles, semantic-router policies, LiteLLM mappings, and hardware benchmarks for YAM Server. Quantization guidance and system-prompt defaults.
```

### yam-server-observability
```
Grafana dashboards, Prometheus rules, Loki/Tempo config, SLO definitions for YAM Server. The watchtower that makes the platform dependable.
```

### yam-server-agents
```
A2A agent definitions, tool wrappers, policy packs, and semantic-router rules for YAM Server agent platform.
```

### yam-server-workflows
```
n8n flows, event-driven jobs, ingest pipelines, and automation orchestration for YAM Server. Version-controlled workflow definitions.
```

### yam-server-media
```
Optional STT, TTS, image-generation, and video-worker infrastructure for YAM Server. Media expands faster than text; it deserves its own space.
```

### yam-server-docs
```
Architecture notes, runbooks, ADRs, onboarding guides, threat models, and operational playbooks for YAM Server. Docs as infrastructure.
```

### yam-server-business
```
Frappe/ERPNext business application layer for YAM Server. Custom DocTypes, workflows, reports, and AI-assisted business features. Where AI meets real operational workflows.
```

### yam-server-ui-kit
```
Vue 3 UI/UX design system for YAM Server based on frappe-ui. Reusable components, design tokens, accessibility patterns. Build once, use everywhere.
```

### yam-server-apps
```
Optional add-on services, research tools, admin helpers, and line-of-business apps for YAM Server. Experimentation without bloat.
```

---

## GitHub Repository Settings

When creating any YAM Server repository:

1. **Visibility**: Start private, go public when documented
2. **License**: Choose MIT, Apache 2.0, or GPL-3.0 (be consistent across the family)
3. **Default branch**: `main`
4. **Topics/Tags**: `ai`, `local-llm`, `docker-compose`, `vllm`, `litellm`, `open-webui`, `self-hosted`, `platform`, `yam-server`
5. **Issues**: Enable
6. **Projects**: Enable (link to YAM Server platform project)
7. **Wiki**: Disable (use docs repo instead)

### Initial Files

Every new YAM Server repo should start with:

- `README.md` (using the prompt above, adapted to the specific repo)
- `LICENSE`
- `.gitignore` (Docker, Python, Node, secrets)
- `CONTRIBUTING.md` (code of conduct, PR process)
- `.github/CODEOWNERS` (assign ownership)
- `.github/workflows/ci.yml` (basic CI)

---

## Quick Creation Checklist

- [ ] Create repo with descriptive name (`yam-server-*`)
- [ ] Add short description (see prompts above)
- [ ] Initialize with README using the detailed form
- [ ] Add LICENSE file
- [ ] Set up `.gitignore` for the repo type
- [ ] Configure topics/tags for discoverability
- [ ] Add CODEOWNERS file
- [ ] Set up branch protection for `main`
- [ ] Enable issues and projects
- [ ] Link to YAM Server platform project board
- [ ] Add initial CI workflow
- [ ] Document the repo's ownership boundary
- [ ] Cross-link to related repos in README

---

## Why This Matters

These prompts are not just boilerplate. They establish:

1. **Consistent philosophy** across all YAM Server repos
2. **Clear ownership boundaries** so teams can work independently
3. **Honest scope communication** that respects hardware limits
4. **Professional positioning** that distinguishes this from toy demos
5. **Discoverability** through proper topics and descriptions

Use these prompts exactly as written, or adapt them minimally to fit the specific repository's role in the YAM Server family.
