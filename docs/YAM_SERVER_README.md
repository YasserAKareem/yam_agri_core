# YAM Server Documentation - Quick Start Guide

> **What is this?** Documentation for creating and understanding YAM Server - a Compose-first AI platform for small teams.

---

## Three Essential Documents

This folder contains everything you need to create a new YAM Server repository family:

### 1. [YAM_SERVER_HOW_IT_WORKS.md](YAM_SERVER_HOW_IT_WORKS.md)
**Read this first** to understand the complete architecture, philosophy, and design decisions behind YAM Server.

**What's inside:**
- The problem YAM Server solves
- Core technology stack
- The "team in the building" metaphor (each service's role)
- Request flow diagrams (chat, document upload)
- Hardware expectations and honest scope
- Philosophy and design principles

**Who should read this:** Anyone who wants to understand why YAM Server exists and how it's architected differently from typical "run AI locally" demos.

---

### 2. [YAM_SERVER_NEW_REPO_PROMPT.md](YAM_SERVER_NEW_REPO_PROMPT.md)
**Use this** when actually creating a new GitHub repository for YAM Server or any of its components.

**What's inside:**
- Exact repository description text (short form)
- Complete README template (detailed form)
- Repository-specific prompt variations (for models, observability, agents, etc.)
- GitHub settings checklist
- Initial files checklist
- Topics/tags for discoverability

**Who should read this:** Anyone creating a new YAM Server repository on GitHub right now.

---

### 3. [YAM_SERVER_REPO_BLUEPRINT.md](YAM_SERVER_REPO_BLUEPRINT.md)
**Consult this** to understand the multi-repository strategy and boundaries.

**What's inside:**
- Why YAM Server is split across multiple repos (not a monolith)
- Detailed description of each repository's responsibility
- What goes where (decision matrix)
- How repositories reference each other
- Access control strategy per repo
- CI/CD approach per repo
- Migration path from monorepo

**Who should read this:** Team leads, architects, and anyone making decisions about where new functionality should live.

---

## Quick Answer to Common Questions

### "I want to create the main YAM Server repo. What do I do?"

1. Read [YAM_SERVER_HOW_IT_WORKS.md](YAM_SERVER_HOW_IT_WORKS.md) to understand the platform (30 min)
2. Open [YAM_SERVER_NEW_REPO_PROMPT.md](YAM_SERVER_NEW_REPO_PROMPT.md)
3. Copy the "Initial README Prompt (Detailed Form)" section
4. Create a new GitHub repo named `yam-server-core`
5. Use the short description for the GitHub repo description field
6. Paste the detailed README as your initial `README.md`
7. Follow the "Initial Files" and "GitHub Repository Settings" checklists

**Time required:** 15-20 minutes for initial setup

---

### "I want to add model profiles. Which repo?"

`yam-server-models` - See the repository family in [YAM_SERVER_REPO_BLUEPRINT.md](YAM_SERVER_REPO_BLUEPRINT.md#2-yam-server-models)

---

### "I want to add a Grafana dashboard. Which repo?"

`yam-server-observability` - See [YAM_SERVER_REPO_BLUEPRINT.md](YAM_SERVER_REPO_BLUEPRINT.md#3-yam-server-observability)

---

### "Should I create a new repo or add to an existing one?"

Consult the "Repository Boundaries - What Goes Where?" table in [YAM_SERVER_REPO_BLUEPRINT.md](YAM_SERVER_REPO_BLUEPRINT.md#repository-boundaries---what-goes-where)

**Rule of thumb:** If the core platform stops working without it → `yam-server-core`. Otherwise → specialized repo.

---

### "What's the difference between YAM Server and YAM Agri?"

- **YAM Agri Core** (this repo): Frappe-based agricultural supply chain platform for Yemen's cereal sector
- **YAM Server**: Compose-first local AI platform (Open WebUI + LiteLLM + vLLM + PostgreSQL)

They are separate projects with different purposes. YAM Server could potentially be used as the AI infrastructure layer for YAM Agri in the future.

---

## Repository Family Overview

When complete, the YAM Server ecosystem will consist of:

| Repository | Purpose | Owner |
|------------|---------|-------|
| `yam-server-core` | Platform (Compose files, services, bootstrap) | Platform engineering |
| `yam-server-models` | Model profiles, routing policies | ML runtime team |
| `yam-server-observability` | Dashboards, alerts, SLO definitions | SRE |
| `yam-server-agents` | A2A agents, tool wrappers | Agent platform team |
| `yam-server-workflows` | n8n flows, automation | Automation team |
| `yam-server-media` | STT, TTS, image/video workers | Media team |
| `yam-server-docs` | Runbooks, ADRs, architecture | Shared (curated) |
| `yam-server-apps` | Optional add-ons, experiments | App teams |

See [YAM_SERVER_REPO_BLUEPRINT.md](YAM_SERVER_REPO_BLUEPRINT.md) for complete details.

---

## Document Relationships

```
YAM_SERVER_HOW_IT_WORKS.md (architecture & philosophy)
         ↓
         ├─→ YAM_SERVER_NEW_REPO_PROMPT.md (practical creation guide)
         │              ↓
         │         [Create repos on GitHub]
         │
         └─→ YAM_SERVER_REPO_BLUEPRINT.md (multi-repo strategy)
                    ↓
              [Organize work across repos]
```

**Read order:**
1. How It Works (understand)
2. Repo Blueprint (strategy)
3. New Repo Prompt (execute)

---

## Contributing

If you're improving these documents:

1. **How It Works** changes require architectural discussion (open an issue first)
2. **Repo Blueprint** changes need consensus on boundaries (discuss in team meeting)
3. **New Repo Prompt** improvements welcome (keep prompts practical and tested)

All changes should be validated against the existing YAM Server installations (if any exist).

---

## References

These documents reference:

- [Dream Server](https://github.com/Light-Heart-Labs/DreamServer) - Inspiration for clear infrastructure explanation
- [vLLM Semantic Router](https://vllm-semantic-router.com/) - Routing layer
- [LiteLLM](https://docs.litellm.ai/) - Gateway and model catalog
- [Open WebUI](https://docs.openwebui.com/) - User interface

---

## Version History

- **2026-03-17**: Initial documentation created based on architecture analysis
  - Created HOW_IT_WORKS.md (23K)
  - Created NEW_REPO_PROMPT.md (8K)
  - Created REPO_BLUEPRINT.md (14K)
  - Created this README

---

**Your gateway. Your models. Your documents. Your routes. Your repos. Your rules.**
