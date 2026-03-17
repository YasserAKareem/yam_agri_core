# YAM Server - GitHub Repository Form Guide

> **Purpose:** This document provides exact text for creating the YAM Server GitHub repository, emphasizing the "one command" promise that makes setup effortless.

---

## Repository Form Fields

### Repository Name
```
yam-server-core
```

### Description (160 character limit)
**Option 1 (Emphasis on simplicity):**
```
One command to launch your AI platform. Local LLM with Open WebUI, LiteLLM, vLLM. Detects GPU, picks model, generates credentials automatically.
```

**Option 2 (Emphasis on completeness):**
```
Compose-first AI platform for small teams. One command starts Open WebUI, LiteLLM gateway, vLLM inference, PostgreSQL+pgvector. Auto-detects hardware.
```

**Option 3 (Emphasis on control):**
```
Self-hosted AI platform that starts with one command. Detects your GPU, picks the right model, launches everything. Your gateway. Your models. Your rules.
```

**Recommended:** Option 1 - It best captures the "easy start" promise while remaining concise.

---

## GitHub Template Selection

### Start with a template?

**Select:** `❌ No template`

**Reason:** YAM Server has a specific Docker Compose structure and bootstrap logic that doesn't align with standard GitHub templates. The initial setup will be customized for the one-command promise.

---

## Initial Repository Setup Prompt

When GitHub asks "How would you like to set up your repository?", use this approach:

### Initialize with README

**Select:** `✅ Yes, add a README file`

Then immediately edit it with the content below.

### Add .gitignore

**Select:** `✅ Yes, select .gitignore template`

**Template to choose:** `Python` (or `Docker` if Python isn't listed)

### Choose a license

**Select:** `MIT License` (or `Apache 2.0` for enterprise-friendly choice)

**Reasoning:** Open source is critical for trust in self-hosted AI platforms. MIT is most permissive; Apache 2.0 includes patent protections.

---

## README.md Content (Initial Commit)

This is the content that should go in the initial README.md, emphasizing the "one command" promise:

```markdown
# YAM Server

> One command to launch your complete local AI platform.

## The Promise

```bash
./start.sh
```

That's it. No configuration files to edit. No models to download manually. No credentials to generate.

The bootstrap script:
- **Detects your GPU** (NVIDIA, AMD, or CPU-only)
- **Picks the right model** for your hardware (8GB VRAM → Llama 3.2 3B, 16GB → Llama 3.1 8B, etc.)
- **Generates secure credentials** (API keys, passwords, tokens)
- **Starts everything** (Open WebUI, LiteLLM, vLLM, PostgreSQL, Redis)
- **Health checks** until ready
- **Opens browser** to http://localhost

You go from clone to working AI platform in under 5 minutes.

---

## What You Get

A complete, production-ready AI infrastructure stack:

- **Open WebUI** - Chat interface with document upload and conversation history
- **LiteLLM** - API gateway with keys, teams, budgets, and usage tracking
- **vLLM** - Fast local inference engine
- **PostgreSQL + pgvector** - Document memory and vector search
- **Redis** - Caching and coordination
- **Traefik** - TLS termination and stable URLs
- **Observability** - Logs, traces, and metrics from day one

Not a chatbot. A **platform**.

---

## Hardware Requirements

**Minimum useful configuration:**
- RTX 4060 with 8 GB VRAM (or equivalent AMD/Intel)
- 32 GB system RAM
- 500 GB NVMe storage
- Ubuntu 22.04+ / Debian 12+ (or Windows with WSL2)

**What 8 GB VRAM can do:**
- ✅ Text generation (fast)
- ✅ Document understanding
- ✅ Embeddings and vector search
- ✅ Light voice transcription
- ⚠️ Multiple large models (limited)
- ❌ Heavy video generation (needs separate worker)

We're honest about limits. An 8 GB GPU is a solid text-and-retrieval machine. It's not a datacenter.

---

## Quick Start

### 1. Clone and Start

```bash
git clone https://github.com/YasserAKareem/yam-server-core.git
cd yam-server-core
./start.sh
```

Wait 3-5 minutes for:
- Docker images to pull
- Model to download (first time only)
- Services to start
- Health checks to pass

### 2. Open Your Browser

The script automatically opens `http://localhost` when ready.

If not, visit manually: http://localhost

Default credentials are displayed in the terminal.

### 3. Start Using

- **Chat:** Type a question in Open WebUI
- **Upload documents:** Drag PDFs into the chat
- **Check usage:** Visit http://localhost/litellm/usage
- **View logs:** `docker compose logs -f`

---

## What Makes This Different

Most "run AI locally" projects give you a model running on your machine. That's the easy part.

YAM Server gives you a **platform** that:
- ✅ Survives restarts
- ✅ Has user accounts and API keys
- ✅ Tracks usage and costs
- ✅ Routes requests intelligently
- ✅ Stores documents with semantic search
- ✅ Can be backed up and restored
- ✅ Can grow from one machine to many

One command to start. Professional infrastructure underneath.

---

## Next Steps

After your first successful start:

1. **Read the docs:** [YAM_SERVER_HOW_IT_WORKS.md](docs/YAM_SERVER_HOW_IT_WORKS.md)
2. **Explore the API:** http://localhost/litellm/docs
3. **Add users:** `./scripts/add-user.sh`
4. **Configure models:** Edit `config/models.yaml`
5. **Enable observability:** `./scripts/enable-grafana.sh`

---

## Troubleshooting

**"I don't have a GPU"**
- No problem. CPU-only mode works fine for text. Start script detects and adapts.

**"8 GB VRAM isn't enough for my use case"**
- See [Hardware Recommendations](docs/HARDWARE.md) for scaling options.

**"I want to customize the setup"**
- That's fine. See [Configuration Guide](docs/CONFIGURATION.md).

**"Something failed"**
- Check `docker compose logs`
- Open an issue: [GitHub Issues](https://github.com/YasserAKareem/yam-server-core/issues)

---

## Architecture

YAM Server is not a monolith. It's a family of repositories:

- **yam-server-core** (this repo) - Platform infrastructure
- **yam-server-models** - Model profiles and routing policies
- **yam-server-observability** - Dashboards and alerts
- **yam-server-agents** - A2A agent definitions
- **yam-server-workflows** - Automation (n8n flows)
- **yam-server-business** - Frappe/ERPNext integration
- **yam-server-ui-kit** - Design system (frappe-ui based)
- **yam-server-docs** - Runbooks and ADRs

See [Repository Blueprint](docs/YAM_SERVER_REPO_BLUEPRINT.md) for the complete strategy.

---

## Philosophy

We want YAM Server to be the kind of system that:
- Starts small and tells the truth about its limits
- Gets stronger by becoming more modular, not more chaotic
- Respects how systems actually live in production
- Gives you control without requiring a PhD in ML ops

**Your gateway. Your models. Your documents. Your routes. Your repos. Your rules.**

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) (or Apache 2.0 - choose one)

---

**Ready to start? Run `./start.sh` and watch it work.**
```

---

## Topics / Keywords (for GitHub repository)

Add these topics to make the repository discoverable:

```
ai
local-llm
self-hosted
docker-compose
vllm
litellm
open-webui
platform
one-command-setup
gpu-detection
auto-configuration
compose-first
small-teams
postgres-pgvector
yam-server
```

**Priority topics (choose 5 max for visibility):**
1. `local-llm`
2. `self-hosted`
3. `docker-compose`
4. `one-command-setup`
5. `ai-platform`

---

## About Section (Repository Settings)

**Website:** `https://yam-server.dev` (when/if you create a docs site)

**Topics:** (see above)

**Include in home page:** ✅ Yes

**Releases:** ✅ Yes

**Packages:** ✅ Yes (for Docker images)

**Deployments:** ✅ Yes (for staging/production)

---

## Social Preview Image

Create a simple image (1280x640px) with:

```
┌─────────────────────────────────────────┐
│                                         │
│         YAM SERVER                      │
│    One Command. Complete Platform.     │
│                                         │
│     $ ./start.sh                        │
│     [===] Detecting GPU...              │
│     [===] Picking model...              │
│     [===] Generating credentials...     │
│     [===] Starting services...          │
│     ✓ Ready at http://localhost         │
│                                         │
└─────────────────────────────────────────┘
```

---

## Initial Issue Labels

Create these labels immediately:

| Label | Color | Description |
|-------|-------|-------------|
| `getting-started` | `#0075ca` | Issues related to initial setup |
| `one-command` | `#00ff00` | Bootstrap script issues |
| `gpu-detection` | `#fbca04` | Hardware detection problems |
| `documentation` | `#0075ca` | Improvements or additions to docs |
| `enhancement` | `#a2eeef` | New feature requests |
| `bug` | `#d73a4a` | Something isn't working |
| `good-first-issue` | `#7057ff` | Good for newcomers |

---

## Repository Description in Settings (Extended)

After creating the repo, go to Settings and add this extended description:

```
YAM Server is a Compose-first AI platform for small teams. One command (./start.sh)
detects your GPU, picks the right model, generates credentials, and launches a
complete stack: Open WebUI, LiteLLM gateway, vLLM inference, PostgreSQL+pgvector,
Redis, and observability. Designed for RTX 4060 (8GB VRAM) but scales up. Not a
chatbot demo—a production-ready platform with user management, API keys, document
memory, and audit logs. Your gateway. Your models. Your rules.
```

---

## First Commit Message

```bash
git commit -m "feat(init): bootstrap YAM Server with one-command setup

Implements the core promise: ./start.sh detects GPU, picks model,
generates credentials, and launches complete AI platform.

Includes:
- Bootstrap script with GPU detection
- Docker Compose stack (Open WebUI, LiteLLM, vLLM, PostgreSQL)
- Auto-configuration for common hardware profiles
- Health checks and startup verification
- Initial documentation emphasizing ease of use

Closes #1 (if you create a tracking issue first)
"
```

---

## Summary: What to Write in Each Field

When you're filling out the "Create new repository" form on GitHub:

1. **Repository name:** `yam-server-core`
2. **Description:** `One command to launch your AI platform. Local LLM with Open WebUI, LiteLLM, vLLM. Detects GPU, picks model, generates credentials automatically.`
3. **Public/Private:** `Public` (for open source) or `Private` (initially, then public)
4. **Initialize with README:** `✅ Yes` (then use the README content above)
5. **Add .gitignore:** `Python` or `Docker`
6. **Choose a license:** `MIT License`

After creation:
- Add topics (keywords)
- Configure settings (website, issues, projects)
- Create initial labels
- Upload social preview image
- Start building the bootstrap script

---

## Key Message to Emphasize

**In every piece of documentation, README, blog post, or demo:**

> "YAM Server keeps one promise: `./start.sh` and you have a working AI platform.
> No configuration. No manual model downloads. No credential management.
> Just one command, and everything works."

This is the North Star. Every design decision should support or at least not
undermine this promise.

---

## Final Checklist

When creating the yam-server-core repository:

- [ ] Repository name: `yam-server-core`
- [ ] Short description emphasizes "one command" promise
- [ ] README.md leads with `./start.sh` example
- [ ] LICENSE file (MIT or Apache 2.0)
- [ ] .gitignore (Python/Docker)
- [ ] Topics include `one-command-setup` and `local-llm`
- [ ] Social preview image shows the bootstrap process
- [ ] First commit message references the core promise
- [ ] Documentation linked in README
- [ ] CONTRIBUTING.md placeholder created

**Remember:** The "one command" promise is not marketing. It's an architectural
constraint. Every feature should start with "does this complicate the first-time
experience?" If yes, make it optional.
