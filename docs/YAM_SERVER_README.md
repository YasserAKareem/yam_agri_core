# YAM Server Documentation - Quick Start Guide

> **What is this?** Documentation for creating and understanding YAM Server - a Compose-first AI platform for small teams with Frappe/ERPNext business integration.
>
> **Core Promise:** One command (`./start.sh`) detects your GPU, picks the right model, generates credentials, and launches everything. From clone to working platform in under 5 minutes.

---

## Core Documentation

This folder contains everything you need to create and integrate the YAM Server platform:

### 1. [YAM_SERVER_HOW_IT_WORKS.md](YAM_SERVER_HOW_IT_WORKS.md)
**Read this first** to understand the complete architecture, philosophy, and design decisions behind YAM Server.

**What's inside:**
- The problem YAM Server solves
- Core technology stack (including Frappe/ERPNext)
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
- Repository-specific prompt variations (for models, observability, agents, business, ui-kit, etc.)
- GitHub settings checklist
- Initial files checklist
- Topics/tags for discoverability

**Who should read this:** Anyone creating a new YAM Server repository on GitHub right now.

---

### 3. [YAM_SERVER_REPO_BLUEPRINT.md](YAM_SERVER_REPO_BLUEPRINT.md)
**Consult this** to understand the multi-repository strategy and boundaries.

**What's inside:**
- Why YAM Server is split across multiple repos (not a monolith)
- Detailed description of each repository's responsibility (including yam-server-business and yam-server-ui-kit)
- What goes where (decision matrix)
- How repositories reference each other
- Access control strategy per repo
- CI/CD approach per repo
- Migration path from monorepo

**Who should read this:** Team leads, architects, and anyone making decisions about where new functionality should live.

---

## Integration Documentation

### 4. [YAM_SERVER_FRAPPE_INTEGRATION.md](YAM_SERVER_FRAPPE_INTEGRATION.md)
**Read this** to understand how Frappe/ERPNext integrates with YAM Server AI infrastructure.

**What's inside:**
- Integration architecture (side-by-side, not nested)
- Three key integration patterns (document processing, recommendations, report generation)
- Deployment options (separate containers vs. integrated)
- Security considerations (API keys, PII redaction, rate limiting)
- Testing strategy
- Example: YAM Agri use cases

**Who should read this:** Business application developers, Frappe developers, integration engineers.

---

### 5. [YAM_SERVER_UI_DESIGN_SYSTEM.md](YAM_SERVER_UI_DESIGN_SYSTEM.md)
**Read this** to understand the UI/UX design system based on Frappe UI.

**What's inside:**
- Design philosophy and principles
- Technology foundation (Vue 3, Tailwind CSS, Frappe UI)
- Design tokens (colors, typography, spacing)
- Component library (base + YAM-specific components)
- Layout patterns (desktop, mobile PWA)
- Accessibility guidelines (WCAG 2.1 AA)
- RTL support for Arabic
- Dark mode support
- Storybook documentation

**Who should read this:** UI/UX designers, frontend developers, anyone building YAM Server user interfaces.

---

## Quick Answer to Common Questions

### "I want to create the main YAM Server repo. What do I do?"

**See the complete guide:** [YAM_SERVER_GITHUB_REPO_FORM_GUIDE.md](YAM_SERVER_GITHUB_REPO_FORM_GUIDE.md)

**Quick summary:**
1. Create repo named `yam-server-core`
2. Description: `One command to launch your AI platform. Local LLM with Open WebUI, LiteLLM, vLLM. Detects GPU, picks model, generates credentials automatically.`
3. Use the README template from [YAM_SERVER_NEW_REPO_PROMPT.md](YAM_SERVER_NEW_REPO_PROMPT.md)
4. Add topics: `local-llm`, `self-hosted`, `docker-compose`, `one-command-setup`, `ai-platform`
5. License: MIT or Apache 2.0

**Time required:** 10 minutes for repo setup, then start building `./start.sh`

---

### "What do I write in the GitHub repo form?"

**Three critical fields:**

1. **Repository name:** `yam-server-core`

2. **Description (160 char max):**
   ```
   One command to launch your AI platform. Local LLM with Open WebUI, LiteLLM, vLLM. Detects GPU, picks model, generates credentials automatically.
   ```

3. **Topics (keywords):**
   - `local-llm`
   - `self-hosted`
   - `docker-compose`
   - `one-command-setup`
   - `ai-platform`

**Full details:** See [YAM_SERVER_GITHUB_REPO_FORM_GUIDE.md](YAM_SERVER_GITHUB_REPO_FORM_GUIDE.md) for complete form field instructions, README template, and first commit message.

---

### "How do I emphasize the 'one command' promise?"

**In every document:**
- Lead with `./start.sh` as the first code example
- Show the automatic detection and configuration
- Emphasize "5 minutes from clone to working platform"
- List what the script does automatically (GPU detection, model selection, credential generation)
- Contrast with "most AI demos" that require manual setup

**Example opening:**
```bash
./start.sh
# That's it. No config files. No manual downloads.
# GPU detected → Model selected → Credentials generated → Platform launched
```

See [YAM_SERVER_GITHUB_REPO_FORM_GUIDE.md](YAM_SERVER_GITHUB_REPO_FORM_GUIDE.md) for the complete README template that emphasizes this promise.

---

### "Should I use a GitHub template?"

**No.** Select "No template" when creating the repository.

**Why:** YAM Server has custom Docker Compose structure and bootstrap logic that doesn't fit standard templates. The one-command promise requires a custom setup approach.

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

When complete, the YAM Server ecosystem will consist of 10 specialized repositories, each owning a clear surface area:

| Repository | Purpose | Owner | First Question |
|------------|---------|-------|----------------|
| `yam-server-core` | Platform (Compose files, `./start.sh`, bootstrap) | Platform engineering | Does it break the one-command promise? |
| `yam-server-models` | Model profiles, routing policies | ML runtime team | Which model for which GPU? |
| `yam-server-observability` | Dashboards, alerts, SLO definitions | SRE | How do we know it's working? |
| `yam-server-agents` | A2A agents, tool wrappers | Agent platform team | Can an agent do this? |
| `yam-server-workflows` | n8n flows, automation | Automation team | Should this be automated? |
| `yam-server-media` | STT, TTS, image/video workers | Media team | Does this need a separate GPU? |
| `yam-server-docs` | Runbooks, ADRs, architecture | Shared (curated) | Is this documented? |
| `yam-server-business` | Frappe/ERPNext business apps, AI-assisted features | Business developers | How does AI help the business? |
| `yam-server-ui-kit` | Vue 3 design system (frappe-ui based) | UI/UX team | Is this reusable? |
| `yam-server-apps` | Optional add-ons, experiments | App teams | Does this belong in core? |

**Key principle:** `yam-server-core` must maintain the "one command" promise. Everything else is optional and can fail without breaking the basic platform.

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
- [Frappe Framework](https://frappeframework.com/docs) - Business application framework
- [Frappe UI](https://github.com/frappe/frappe-ui) - Vue 3 component library
- [ERPNext](https://docs.erpnext.com/) - Open source ERP

---

## Version History

- **2026-03-17**: Initial documentation created based on architecture analysis
  - Created HOW_IT_WORKS.md (23K)
  - Created NEW_REPO_PROMPT.md (8K)
  - Created REPO_BLUEPRINT.md (14K)
  - Created this README
- **2026-03-17**: Added Frappe/ERPNext integration and UI design system
  - Updated HOW_IT_WORKS.md with Frappe integration section
  - Updated REPO_BLUEPRINT.md with yam-server-business and yam-server-ui-kit repos
  - Created FRAPPE_INTEGRATION.md (25K) - Complete integration guide
  - Created UI_DESIGN_SYSTEM.md (18K) - UI/UX design system based on frappe-ui
  - Updated NEW_REPO_PROMPT.md with new repo prompts
  - Updated this README with new documentation links
- **2026-03-17**: Emphasized "one command" promise throughout documentation
  - Created GITHUB_REPO_FORM_GUIDE.md (15K) - Complete guide for repo creation
  - Updated README with quick answers about repo form fields
  - Enhanced NEW_REPO_PROMPT.md to highlight `./start.sh` as primary entry point
  - Added "Core Promise" to README header
  - Updated repository family table with "First Question" column to guide decisions

---

**Your gateway. Your models. Your documents. Your routes. Your repos. Your rules.**
