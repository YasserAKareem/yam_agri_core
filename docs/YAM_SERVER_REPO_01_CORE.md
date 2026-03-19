# YAM Server Core - Repository Creation Guide

> **Repository:** `yam-server-core`
> **Purpose:** Platform infrastructure - the foundation that makes the "one command" promise real
> **Owner:** Platform Engineering, DevOps
> **Release Cadence:** Stable - changes only when platform contract changes

---

## GitHub Repository Form

### Repository Name
```
yam-server-core
```

### Description (160 characters)
```
One command to launch your AI platform. Local LLM with Open WebUI, LiteLLM, vLLM. Detects GPU, picks model, generates credentials automatically.
```

### Visibility
- **Initial:** Private (during development)
- **Target:** Public (once documented and tested)

### Initialize with
- ✅ README file (see template below)
- ✅ .gitignore template: `Python`
- ✅ License: `MIT License`

### Topics/Keywords
```
ai, local-llm, docker-compose, vllm, litellm, open-webui, self-hosted,
platform, yam-server, gpu-acceleration, one-command-setup, inference-gateway
```

---

## Initial File Structure

```
yam-server-core/
├── .github/
│   ├── copilot-instructions.md          # GitHub Copilot agent config
│   ├── workflows/
│   │   ├── ci.yml                        # Lint, test, validate
│   │   ├── docker-build.yml              # Build and push images
│   │   └── release.yml                   # Tag and release
│   ├── CODEOWNERS                        # Ownership mapping
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       └── feature_request.md
├── docker/
│   ├── docker-compose.yml                # Core stack definition
│   ├── docker-compose.dev.yml            # Dev overrides
│   ├── docker-compose.gpu.yml            # GPU-specific config
│   ├── .env.example                      # Environment template
│   └── services/
│       ├── traefik/                      # Reverse proxy config
│       ├── open-webui/                   # UI customizations
│       ├── litellm/                      # Gateway config
│       ├── vllm/                         # Inference config
│       ├── postgres/                     # DB init scripts
│       └── redis/                        # Cache config
├── scripts/
│   ├── start.sh                          # THE one command bootstrap
│   ├── stop.sh                           # Clean shutdown
│   ├── backup.sh                         # Backup data and config
│   ├── restore.sh                        # Restore from backup
│   ├── health-check.sh                   # Service health validation
│   ├── gpu-detect.sh                     # GPU detection logic
│   └── credentials-gen.sh                # Secure credential generation
├── config/
│   ├── models.yaml                       # Model catalog (links to yam-server-models)
│   ├── routes.yaml                       # Semantic router config
│   └── defaults/                         # Default configurations
├── docs/
│   ├── ARCHITECTURE.md                   # System architecture
│   ├── GETTING_STARTED.md                # Setup guide
│   ├── TROUBLESHOOTING.md                # Common issues
│   ├── HARDWARE_GUIDE.md                 # Hardware recommendations
│   └── API.md                            # API documentation
├── tests/
│   ├── test_bootstrap.sh                 # Bootstrap script tests
│   ├── test_gpu_detect.sh                # GPU detection tests
│   ├── test_services.sh                  # Service integration tests
│   └── fixtures/                         # Test data
├── .vscode/
│   ├── settings.json                     # VS Code settings
│   ├── tasks.json                        # Build tasks
│   ├── launch.json                       # Debug configs
│   └── extensions.json                   # Recommended extensions
├── .gitignore
├── .dockerignore
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── CHANGELOG.md
└── pyproject.toml                        # Python tooling config
```

---

## README.md Template

```markdown
# YAM Server Core

> One command to launch your complete local AI platform.

## The Promise

```bash
./scripts/start.sh
```

That's it. No configuration files to edit. No models to download manually. No credentials to generate.

The bootstrap script:
- **Detects your GPU** (NVIDIA, AMD, or CPU-only)
- **Picks the right model** for your hardware (8GB VRAM → Llama 3.2 3B, 16GB → Llama 3.1 8B)
- **Generates secure credentials** (API keys, passwords, tokens)
- **Starts everything** (Open WebUI, LiteLLM, vLLM, PostgreSQL+pgvector, Redis)
- **Health checks** until ready
- **Opens browser** to http://localhost

You go from clone to working AI platform in under 5 minutes.

---

## What You Get

A complete, production-ready AI infrastructure stack:

| Component | Purpose | Why It's Here |
|-----------|---------|---------------|
| **Traefik** | Reverse proxy, TLS termination | Stable URLs, HTTPS, routing |
| **Open WebUI** | Chat interface | Clean UX for users |
| **LiteLLM** | API gateway | Auth, budgets, logging, model catalog |
| **vLLM** | Inference engine | Fast local inference |
| **vLLM Semantic Router** | Routing decisions | Smart model selection |
| **PostgreSQL + pgvector** | Database + vectors | App state, document retrieval |
| **Redis** | Cache + coordination | Speed, session management |
| **Apache Tika** | Document extraction | PDF, DOCX, etc. to text |
| **Embeddings service** | Vector generation | Semantic search |

---

## Hardware Requirements

### Minimum Useful Configuration
- **GPU:** RTX 4060 (8 GB VRAM)
- **RAM:** 32 GB system memory
- **Storage:** 500 GB NVMe SSD
- **CPU:** Modern quad-core

### What 8GB VRAM Can Do
- ✅ Text generation (fast)
- ✅ Embeddings and document retrieval
- ✅ Light voice work
- ⚠️ Multiple large models simultaneously (limited)
- ❌ Heavy video generation (needs separate worker)

### Recommended Configuration
- **GPU:** RTX 4070 Ti (12-16 GB VRAM)
- **RAM:** 64 GB system memory
- **Storage:** 1 TB NVMe SSD
- **CPU:** 8-core modern processor

---

## Quick Start

### Prerequisites
- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Git
- **Windows users:** WSL 2 enabled
- **Linux users:** NVIDIA Container Toolkit (for GPU support)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/YasserAKareem/yam-server-core.git
cd yam-server-core
```

2. **Run the bootstrap script:**
```bash
./scripts/start.sh
```

3. **Wait for setup to complete** (3-5 minutes first run)

4. **Access the platform:**
- Open WebUI: http://localhost
- LiteLLM API: http://localhost/litellm
- API Docs: http://localhost/docs

---

## What Happens During Bootstrap

The `start.sh` script is the heart of the "one command" promise. Here's what it does:

1. **Environment Check**
   - Validates Docker is running
   - Checks available disk space
   - Verifies network connectivity

2. **GPU Detection**
   - Detects NVIDIA GPUs via `nvidia-smi`
   - Detects AMD GPUs via `rocm-smi`
   - Falls back to CPU-only if no GPU found
   - Determines available VRAM

3. **Model Selection**
   - 4-6 GB VRAM → Llama 3.2 1B (Q4)
   - 6-10 GB VRAM → Llama 3.2 3B (Q4)
   - 10-16 GB VRAM → Llama 3.1 8B (Q4)
   - 16-24 GB VRAM → Llama 3.1 70B (Q4) or Mixtral
   - CPU-only → Phi-3 Mini (3.8B)

4. **Credential Generation**
   - LiteLLM API key (32-byte random)
   - PostgreSQL password (24-byte random)
   - Redis password (24-byte random)
   - Admin user credentials
   - Writes to `.env` file

5. **Service Startup**
   - Pulls Docker images (cached after first run)
   - Starts services in dependency order
   - PostgreSQL → Redis → Embeddings → Tika → vLLM → LiteLLM → Open WebUI

6. **Health Checks**
   - Waits for PostgreSQL ready
   - Waits for Redis ready
   - Waits for vLLM model loaded
   - Waits for LiteLLM gateway ready
   - Waits for Open WebUI ready

7. **Post-Setup**
   - Creates default admin user
   - Imports initial model catalog
   - Sets up default semantic routes
   - Opens browser to Open WebUI

---

## Repository Family

YAM Server Core is part of a multi-repository family:

| Repository | Purpose | When You Need It |
|------------|---------|------------------|
| **yam-server-core** | Platform infrastructure | Always (this repo) |
| **yam-server-models** | Model profiles, routing | Customizing models |
| **yam-server-observability** | Dashboards, alerts | Production monitoring |
| **yam-server-agents** | A2A agent definitions | Building agents |
| **yam-server-workflows** | n8n automation | Workflow automation |
| **yam-server-business** | Frappe/ERPNext apps | Business integration |
| **yam-server-ui-kit** | Design system | Custom UI components |
| **yam-server-docs** | Runbooks, ADRs | Deep architecture |

See [YAM_SERVER_REPO_BLUEPRINT.md](../docs/YAM_SERVER_REPO_BLUEPRINT.md) for the complete strategy.

---

## Configuration

### Environment Variables

The `.env` file (auto-generated by `start.sh`) contains:

```bash
# Core Platform
COMPOSE_PROJECT_NAME=yam-server
DOMAIN=localhost

# GPU Configuration (auto-detected)
GPU_TYPE=nvidia  # nvidia, amd, or cpu
GPU_VRAM_GB=8
MODEL_PRESET=llama-3.2-3b-q4

# Credentials (auto-generated)
LITELLM_API_KEY=<random-32-bytes>
POSTGRES_PASSWORD=<random-24-bytes>
REDIS_PASSWORD=<random-24-bytes>
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<random-16-bytes>

# Service Ports (internal)
TRAEFIK_PORT=80
TRAEFIK_HTTPS_PORT=443
POSTGRES_PORT=5432
REDIS_PORT=6379
LITELLM_PORT=8000
VLLM_PORT=8001
OPEN_WEBUI_PORT=3000

# Model Configuration
VLLM_MODEL_PATH=/models/llama-3.2-3b-q4
VLLM_MAX_MODEL_LEN=4096
VLLM_GPU_MEMORY_UTILIZATION=0.9

# Vector Database
PGVECTOR_DIMENSIONS=768
```

### Manual Override

To override auto-detection, create `.env` before running `start.sh`:

```bash
cp docker/.env.example .env
# Edit .env with your preferences
./scripts/start.sh
```

---

## Development Workflow

### Working on YAM Server Core

1. **Fork and clone:**
```bash
git clone https://github.com/YOUR_USERNAME/yam-server-core.git
cd yam-server-core
git remote add upstream https://github.com/YasserAKareem/yam-server-core.git
```

2. **Create feature branch:**
```bash
git checkout -b feature/your-feature-name
```

3. **Start development environment:**
```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up -d
```

4. **Make changes and test:**
```bash
./tests/test_bootstrap.sh
./tests/test_services.sh
```

5. **Commit and push:**
```bash
git add .
git commit -m "feat: your feature description"
git push origin feature/your-feature-name
```

6. **Open Pull Request** to upstream

---

## Testing

### Automated Tests

Run the full test suite:
```bash
./tests/run_all.sh
```

Individual test suites:
```bash
./tests/test_bootstrap.sh      # Bootstrap script tests
./tests/test_gpu_detect.sh     # GPU detection tests
./tests/test_services.sh       # Service integration tests
```

### Manual Testing Checklist

- [ ] `start.sh` completes without errors
- [ ] GPU is detected correctly
- [ ] Appropriate model is selected
- [ ] All services start and pass health checks
- [ ] Open WebUI is accessible at http://localhost
- [ ] Chat functionality works
- [ ] Document upload and retrieval works
- [ ] `stop.sh` cleanly shuts down all services
- [ ] `backup.sh` creates valid backup
- [ ] `restore.sh` successfully restores from backup

---

## Troubleshooting

### Common Issues

**1. GPU not detected**
```bash
# Verify GPU is visible to Docker
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# For WSL users: ensure Docker Desktop has WSL integration enabled
```

**2. Out of VRAM errors**
```bash
# Reduce model size in .env
VLLM_GPU_MEMORY_UTILIZATION=0.7  # Default is 0.9
```

**3. Services fail to start**
```bash
# Check logs
docker compose -f docker/docker-compose.yml logs -f

# Restart specific service
docker compose -f docker/docker-compose.yml restart vllm
```

**4. Slow inference**
```bash
# Verify GPU is being used
docker compose -f docker/docker-compose.yml exec vllm nvidia-smi

# Check model loading
docker compose -f docker/docker-compose.yml logs vllm | grep "model loaded"
```

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for comprehensive troubleshooting.

---

## Operations

### Backup

Create a backup of all data and configuration:
```bash
./scripts/backup.sh
```

Backups are stored in `./backups/<timestamp>/` and include:
- PostgreSQL database dump
- Redis snapshot
- Configuration files
- Model cache (optional)

### Restore

Restore from a backup:
```bash
./scripts/restore.sh ./backups/2026-03-17_20-30-00/
```

### Updates

Update to the latest version:
```bash
git pull origin main
./scripts/stop.sh
docker compose -f docker/docker-compose.yml pull
./scripts/start.sh
```

---

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

### Request Flow

```
User Request
    ↓
[Browser] → [Traefik :80]
    ↓
[Open WebUI :3000]
    ↓
[LiteLLM Gateway :8000] ← Auth, budgets, logging
    ↓
[vLLM Semantic Router] ← Route to appropriate model
    ↓
[vLLM Inference :8001] ← GPU inference
    ↓
[Response] → User
```

### Document Retrieval Flow

```
Document Upload
    ↓
[Open WebUI] → [Apache Tika] → Extract text
    ↓
[Embeddings Service] → Generate vectors
    ↓
[PostgreSQL + pgvector] → Store vectors

Query
    ↓
[Embeddings Service] → Generate query vector
    ↓
[PostgreSQL + pgvector] → Similarity search
    ↓
[LiteLLM] → Augment prompt with context
    ↓
[vLLM] → Generate response
```

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code of conduct
- Development setup
- Testing requirements
- PR process
- Coding standards

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Support

- **Documentation:** [docs/](docs/)
- **Issues:** [GitHub Issues](https://github.com/YasserAKareem/yam-server-core/issues)
- **Discussions:** [GitHub Discussions](https://github.com/YasserAKareem/yam-server-core/discussions)

---

**Your gateway. Your models. Your documents. Your rules.**
```

---

## GitHub Copilot Agent Configuration

Create `.github/copilot-instructions.md`:

```markdown
# Copilot Instructions for yam-server-core

You are working on **YAM Server Core**, the platform infrastructure that makes the "one command" promise real.

## Repository Context

**Purpose:** Platform infrastructure - Docker Compose orchestration, bootstrap logic, service configuration

**Key Principle:** The `./scripts/start.sh` command must ALWAYS work. Every change must preserve or improve the one-command setup experience.

**What this repo owns:**
- Docker Compose files for core services
- Bootstrap script (`start.sh`)
- GPU detection and model selection logic
- Credential generation
- Service health checks
- Backup and restore scripts

**What this repo does NOT own:**
- Model profiles → yam-server-models
- Dashboards → yam-server-observability
- Agent definitions → yam-server-agents
- Workflows → yam-server-workflows

## Development Rules

### 1. Never Break the Bootstrap
- Every PR must pass `./tests/test_bootstrap.sh`
- GPU detection must degrade gracefully (CPU fallback)
- Model selection must be deterministic based on available VRAM
- Credential generation must use cryptographically secure randomness

### 2. Dependencies Must Be Explicit
- All service dependencies in `docker-compose.yml` must use `depends_on` with health checks
- Never assume a service is ready just because container started
- Always implement health check endpoints

### 3. Configuration Must Be Discoverable
- All environment variables must be documented in `.env.example`
- Defaults must be sensible for the target hardware (RTX 4060 with 8GB VRAM)
- Never require manual editing unless absolutely necessary

### 4. Testing Must Be Automated
- Unit tests for shell scripts
- Integration tests for service communication
- End-to-end tests for the complete bootstrap flow

### 5. Documentation Must Stay Current
- Update ARCHITECTURE.md when adding new services
- Update TROUBLESHOOTING.md when fixing issues
- Update README.md when changing user-facing behavior

## Code Style

### Shell Scripts
- Use `#!/usr/bin/env bash` shebang
- Enable strict mode: `set -euo pipefail`
- Use functions for reusability
- Add comments for complex logic
- Use shellcheck for linting

### Docker Compose
- Use version 3.8+ format
- Always specify resource limits
- Use health checks for all services
- Volume mounts must be read-only where possible

### Python Scripts
- Use type hints
- Follow PEP 8
- Use `black` for formatting
- Use `ruff` for linting

## Common Tasks

### Adding a New Service

1. Add service definition to `docker/docker-compose.yml`
2. Create service-specific config in `docker/services/<service-name>/`
3. Add health check endpoint
4. Update `scripts/health-check.sh`
5. Add integration test in `tests/test_services.sh`
6. Document in `docs/ARCHITECTURE.md`

### Changing Bootstrap Logic

1. Update `scripts/start.sh`
2. Add test case in `tests/test_bootstrap.sh`
3. Test on all supported platforms (Linux, WSL, macOS)
4. Document changes in CHANGELOG.md

### Adding GPU Support

1. Update `scripts/gpu-detect.sh`
2. Add model selection logic based on VRAM
3. Update `docker/docker-compose.gpu.yml`
4. Test on target hardware
5. Document in `docs/HARDWARE_GUIDE.md`

## Testing Checklist

Before submitting a PR, ensure:
- [ ] `./tests/run_all.sh` passes
- [ ] Bootstrap works on clean system (no .env)
- [ ] Bootstrap respects existing .env
- [ ] GPU detection works correctly
- [ ] Model selection is appropriate for detected VRAM
- [ ] All services pass health checks
- [ ] Backup and restore work correctly
- [ ] Documentation is updated

## Never Do This

- ❌ Break the one-command setup promise
- ❌ Require manual configuration for common use cases
- ❌ Add services without health checks
- ❌ Use hardcoded credentials
- ❌ Assume GPU is always available
- ❌ Add dependencies without updating docker-compose.yml
- ❌ Change defaults without testing on target hardware (RTX 4060)

## Always Do This

- ✅ Test on minimal hardware (RTX 4060, 8GB VRAM)
- ✅ Provide CPU fallback for all GPU features
- ✅ Generate credentials securely
- ✅ Validate environment before starting services
- ✅ Implement graceful degradation
- ✅ Update documentation alongside code
- ✅ Keep the `start.sh` script idempotent

## Questions to Ask

When uncertain about a change:
1. Does this preserve the one-command promise?
2. Will this work on minimal hardware (RTX 4060)?
3. Is there a CPU fallback?
4. Are health checks implemented?
5. Is this documented?
6. Does this belong in a different repo?

## Repository Family Context

This repo is part of the YAM Server multi-repository family. When making changes that affect other repos:
- Link PRs across repositories
- Update version compatibility documentation
- Coordinate releases with affected repos
- Test integration with latest versions of dependencies
```

---

## VS Code Workspace Configuration

Create `.vscode/settings.json`:

```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll": true
  },
  "files.associations": {
    "*.yml": "yaml",
    "*.yaml": "yaml",
    "docker-compose*.yml": "docker-compose",
    ".env*": "properties"
  },
  "yaml.schemas": {
    "https://json.schemastore.org/docker-compose.json": "docker-compose*.yml"
  },
  "shellcheck.enable": true,
  "shellcheck.run": "onSave",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  },
  "[yaml]": {
    "editor.defaultFormatter": "redhat.vscode-yaml",
    "editor.tabSize": 2
  },
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[markdown]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.wordWrap": "on"
  },
  "files.exclude": {
    "**/.git": true,
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".env": true,
    "backups/": true
  },
  "search.exclude": {
    "**/node_modules": true,
    "**/backups": true,
    "**/.venv": true
  }
}
```

Create `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Bootstrap: Start YAM Server",
      "type": "shell",
      "command": "./scripts/start.sh",
      "problemMatcher": [],
      "group": {
        "kind": "build",
        "isDefault": true
      }
    },
    {
      "label": "Bootstrap: Stop YAM Server",
      "type": "shell",
      "command": "./scripts/stop.sh",
      "problemMatcher": []
    },
    {
      "label": "Test: Run All Tests",
      "type": "shell",
      "command": "./tests/run_all.sh",
      "problemMatcher": []
    },
    {
      "label": "Test: Bootstrap",
      "type": "shell",
      "command": "./tests/test_bootstrap.sh",
      "problemMatcher": []
    },
    {
      "label": "Test: GPU Detection",
      "type": "shell",
      "command": "./tests/test_gpu_detect.sh",
      "problemMatcher": []
    },
    {
      "label": "Test: Services",
      "type": "shell",
      "command": "./tests/test_services.sh",
      "problemMatcher": []
    },
    {
      "label": "Docker: View Logs",
      "type": "shell",
      "command": "docker compose -f docker/docker-compose.yml logs -f",
      "problemMatcher": []
    },
    {
      "label": "Docker: Health Check",
      "type": "shell",
      "command": "./scripts/health-check.sh",
      "problemMatcher": []
    },
    {
      "label": "Backup: Create Backup",
      "type": "shell",
      "command": "./scripts/backup.sh",
      "problemMatcher": []
    },
    {
      "label": "Lint: ShellCheck",
      "type": "shell",
      "command": "find scripts tests -name '*.sh' -exec shellcheck {} +",
      "problemMatcher": ["$shellcheck"]
    },
    {
      "label": "Lint: YAML",
      "type": "shell",
      "command": "yamllint docker/",
      "problemMatcher": []
    },
    {
      "label": "Lint: Python",
      "type": "shell",
      "command": "ruff check .",
      "problemMatcher": []
    }
  ]
}
```

Create `.vscode/extensions.json`:

```json
{
  "recommendations": [
    "ms-azuretools.vscode-docker",
    "redhat.vscode-yaml",
    "timonwong.shellcheck",
    "charliermarsh.ruff",
    "esbenp.prettier-vscode",
    "github.copilot",
    "github.copilot-chat",
    "tamasfe.even-better-toml",
    "davidanson.vscode-markdownlint"
  ]
}
```

---

## MCP Server Configuration

Model Context Protocol server for enhanced agent capabilities.

Create `.mcp/config.json`:

```json
{
  "mcpServers": {
    "yam-server-core": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "env": {
        "REPO_ROOT": "${workspaceFolder}",
        "REPO_NAME": "yam-server-core"
      },
      "capabilities": {
        "resources": true,
        "tools": true,
        "prompts": true
      }
    }
  },
  "resources": [
    {
      "uri": "file:///${workspaceFolder}/docker/docker-compose.yml",
      "name": "Docker Compose Configuration",
      "description": "Core service orchestration"
    },
    {
      "uri": "file:///${workspaceFolder}/scripts/start.sh",
      "name": "Bootstrap Script",
      "description": "One-command platform setup"
    },
    {
      "uri": "file:///${workspaceFolder}/docs/ARCHITECTURE.md",
      "name": "Architecture Documentation",
      "description": "System architecture and design decisions"
    }
  ],
  "tools": [
    {
      "name": "test_bootstrap",
      "description": "Test the bootstrap script",
      "command": "./tests/test_bootstrap.sh"
    },
    {
      "name": "detect_gpu",
      "description": "Detect available GPU and VRAM",
      "command": "./scripts/gpu-detect.sh"
    },
    {
      "name": "health_check",
      "description": "Check health of all services",
      "command": "./scripts/health-check.sh"
    },
    {
      "name": "view_logs",
      "description": "View service logs",
      "command": "docker compose -f docker/docker-compose.yml logs"
    }
  ]
}
```

---

## Automation Context

### Context Document (context.md)

Create `docs/context.md`:

```markdown
# YAM Server Core - Context

## What is this repository?

YAM Server Core is the foundation of the YAM Server platform. It owns the Docker Compose orchestration, bootstrap logic, and service configuration that makes the "one command" promise real.

## Key Architectural Decisions

### ADR-001: One Command Bootstrap
**Decision:** The entire platform must start with a single command (`./scripts/start.sh`).
**Rationale:** Reduces friction for new users, eliminates configuration errors, makes onboarding predictable.
**Consequences:** All configuration must be auto-detected or auto-generated. Manual steps are failures.

### ADR-002: GPU Detection
**Decision:** Automatically detect GPU type and available VRAM, select appropriate model.
**Rationale:** Users shouldn't need to know their exact hardware specs or compatible models.
**Consequences:** Must support NVIDIA, AMD, and CPU-only fallback. Model selection logic must be conservative.

### ADR-003: Secure by Default
**Decision:** Generate all credentials automatically using cryptographically secure randomness.
**Rationale:** Default credentials are security vulnerabilities. Random generation eliminates this risk.
**Consequences:** Credential recovery requires backup/restore. No "default password" convenience.

### ADR-004: Service Health Checks
**Decision:** All services must implement health checks. Bootstrap waits for healthy state.
**Rationale:** Starting services doesn't mean they're ready. Health checks prevent race conditions.
**Consequences:** Every service needs health endpoint. Startup time is slightly longer but predictable.

## Target Hardware

**Primary:** RTX 4060 with 8GB VRAM, 32GB RAM
**Why:** Most common affordable GPU for local AI. If it works here, it works for most users.

## Service Dependencies

```
Level 1 (Foundation):
  - PostgreSQL (database)
  - Redis (cache)

Level 2 (Processing):
  - Apache Tika (document extraction)
  - Embeddings Service (vector generation)

Level 3 (Inference):
  - vLLM (GPU inference engine)

Level 4 (Gateway):
  - LiteLLM (API gateway, auth, routing)

Level 5 (Frontend):
  - Open WebUI (user interface)

Level 6 (Edge):
  - Traefik (reverse proxy, TLS)
```

## Critical Paths

### Bootstrap Success Criteria
1. GPU detection completes (or CPU fallback)
2. Model selection appropriate for VRAM
3. Credentials generated and stored in .env
4. All services start without errors
5. Health checks pass for all services
6. Browser opens to working UI

Any failure in this chain breaks the core promise.

## Non-Negotiables

1. **One command must always work** - No manual configuration for standard hardware
2. **CPU fallback must exist** - Platform works without GPU (slower, but works)
3. **Credentials must be secure** - No default passwords, no weak generation
4. **Health checks are mandatory** - Services must signal readiness
5. **Backwards compatibility** - Updates must not break existing .env files

## Integration Points

### With yam-server-models
- Reads model catalog from `config/models.yaml`
- Links to model repository via git submodule
- Model selection logic references hardware compatibility matrix

### With yam-server-observability
- Exposes metrics endpoints for Prometheus
- Logs to stdout in JSON format for Loki
- Traces instrumented with OpenTelemetry

### With other repos
- Provides base platform for agents, workflows, business apps
- Other repos deploy as extensions, not modifications

## Testing Strategy

1. **Unit Tests:** Shell script functions, GPU detection logic
2. **Integration Tests:** Service-to-service communication
3. **End-to-End Tests:** Full bootstrap on clean system
4. **Hardware Tests:** Actual GPUs with different VRAM sizes

## Development Workflow

1. Make changes in feature branch
2. Run `./tests/run_all.sh`
3. Test bootstrap on clean Docker environment
4. Update documentation if user-facing changes
5. Open PR with linked issues
6. Wait for CI to pass
7. Merge after review
```

### Methods Document (methods.md)

Create `docs/methods.md`:

```markdown
# YAM Server Core - Development Methods

## Coding Patterns

### Shell Script Pattern

All shell scripts follow this template:

```bash
#!/usr/bin/env bash
# Description: What this script does
# Usage: ./script-name.sh [args]

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'  # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

# Main function
main() {
    log_info "Starting..."
    # Implementation
    log_info "Complete"
}

# Run main
main "$@"
```

### Docker Compose Service Pattern

All services follow this pattern:

```yaml
services:
  service-name:
    image: org/image:tag
    container_name: yam-${SERVICE_NAME}
    restart: unless-stopped

    environment:
      - ENV_VAR=${ENV_VAR}

    volumes:
      - ./config:/config:ro
      - service-data:/data

    networks:
      - yam-network

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

    depends_on:
      dependency:
        condition: service_healthy

    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

volumes:
  service-data:

networks:
  yam-network:
    name: yam-network
```

### GPU Detection Pattern

```bash
detect_gpu() {
    local gpu_type="cpu"
    local vram_gb=0

    # Check for NVIDIA
    if command -v nvidia-smi &> /dev/null; then
        gpu_type="nvidia"
        vram_gb=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
        vram_gb=$((vram_gb / 1024))  # Convert MB to GB

    # Check for AMD
    elif command -v rocm-smi &> /dev/null; then
        gpu_type="amd"
        vram_gb=$(rocm-smi --showmeminfo vram --csv | tail -1 | cut -d',' -f2)
        vram_gb=$((vram_gb / 1024))  # Convert MB to GB

    # CPU fallback
    else
        log_warn "No GPU detected, will use CPU-only inference"
    fi

    echo "${gpu_type},${vram_gb}"
}
```

### Model Selection Pattern

```bash
select_model() {
    local vram_gb=$1
    local model=""

    if (( vram_gb >= 24 )); then
        model="llama-3.1-70b-q4"
    elif (( vram_gb >= 16 )); then
        model="llama-3.1-8b-q8"
    elif (( vram_gb >= 10 )); then
        model="llama-3.1-8b-q4"
    elif (( vram_gb >= 6 )); then
        model="llama-3.2-3b-q4"
    elif (( vram_gb >= 4 )); then
        model="llama-3.2-1b-q4"
    else
        model="phi-3-mini"  # CPU-friendly
    fi

    echo "${model}"
}
```

### Health Check Pattern

```bash
wait_for_service() {
    local service=$1
    local url=$2
    local max_attempts=60
    local attempt=0

    log_info "Waiting for ${service} to be healthy..."

    while (( attempt < max_attempts )); do
        if curl -sf "${url}" > /dev/null 2>&1; then
            log_info "${service} is healthy"
            return 0
        fi

        attempt=$((attempt + 1))
        sleep 2
    done

    log_error "${service} failed to become healthy"
    return 1
}
```

## Testing Patterns

### Shell Script Test

```bash
#!/usr/bin/env bash

test_gpu_detection() {
    source ../scripts/gpu-detect.sh

    # Test NVIDIA detection
    if command -v nvidia-smi &> /dev/null; then
        result=$(detect_gpu)
        gpu_type=$(echo "$result" | cut -d',' -f1)

        if [[ "$gpu_type" == "nvidia" ]]; then
            echo "✅ NVIDIA detection works"
        else
            echo "❌ NVIDIA detection failed"
            exit 1
        fi
    fi
}

test_gpu_detection
```

### Docker Service Test

```bash
test_service_health() {
    local service=$1
    local health_url=$2

    echo "Testing ${service} health..."

    # Start service
    docker compose up -d ${service}

    # Wait for healthy
    local attempts=0
    while (( attempts < 30 )); do
        if docker compose ps ${service} | grep -q "healthy"; then
            echo "✅ ${service} is healthy"
            return 0
        fi
        attempts=$((attempts + 1))
        sleep 2
    done

    echo "❌ ${service} failed health check"
    docker compose logs ${service}
    return 1
}
```

## CI/CD Patterns

### GitHub Actions Workflow

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: ShellCheck
        run: |
          sudo apt-get install shellcheck
          find scripts tests -name '*.sh' -exec shellcheck {} +

      - name: YAML Lint
        run: |
          pip install yamllint
          yamllint docker/

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Tests
        run: |
          ./tests/run_all.sh

  integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Test Bootstrap
        run: |
          ./tests/test_bootstrap.sh

      - name: Test Services
        run: |
          ./tests/test_services.sh
```

## Documentation Patterns

### Architecture Documentation

Use C4 model:
- Context diagram (Level 1)
- Container diagram (Level 2)
- Component diagram (Level 3)
- Code diagram (Level 4 - optional)

### Runbook Template

```markdown
# Runbook: [Operation Name]

## When to Use
[Describe the scenario]

## Prerequisites
- [ ] Requirement 1
- [ ] Requirement 2

## Steps
1. **Step 1**
   ```bash
   command-here
   ```
   Expected output:
   ```
   output-here
   ```

2. **Step 2**
   [Description]

## Verification
How to verify success:
- [ ] Check 1
- [ ] Check 2

## Rollback
If something goes wrong:
1. [Rollback step 1]
2. [Rollback step 2]

## Related
- [Link to related runbook]
- [Link to architecture doc]
```
```

---

## First Commit Checklist

When creating the yam-server-core repository:

- [ ] Create repository on GitHub with correct name and description
- [ ] Initialize with README.md using template above
- [ ] Add MIT License
- [ ] Add .gitignore (Python template)
- [ ] Create `.github/copilot-instructions.md`
- [ ] Create `.github/CODEOWNERS`
- [ ] Create `.github/workflows/ci.yml`
- [ ] Create `.vscode/` configuration files
- [ ] Create `scripts/start.sh` (stub with TODO)
- [ ] Create `docker/docker-compose.yml` (basic structure)
- [ ] Create `docker/.env.example`
- [ ] Create `tests/run_all.sh` (stub)
- [ ] Create `docs/ARCHITECTURE.md` (initial)
- [ ] Create `docs/context.md`
- [ ] Create `docs/methods.md`
- [ ] Add topics/tags on GitHub
- [ ] Enable GitHub Issues
- [ ] Set up branch protection for `main`
- [ ] Create initial milestone for v1.0.0

---

## Integration with Windows 11 + WSL + Docker Desktop

### WSL Configuration

1. **Enable WSL 2:**
```powershell
wsl --install
wsl --set-default-version 2
```

2. **Install Ubuntu:**
```powershell
wsl --install -d Ubuntu-22.04
```

3. **Configure Docker Desktop:**
- Settings → Resources → WSL Integration
- Enable integration with Ubuntu-22.04
- Enable GPU support (if NVIDIA GPU present)

### VS Code Setup

1. **Install WSL Extension:**
```
code --install-extension ms-vscode-remote.remote-wsl
```

2. **Open repository in WSL:**
```bash
code --remote wsl+Ubuntu-22.04 /home/user/yam-server-core
```

3. **Recommended Extensions** (auto-install from `extensions.json`):
- Docker
- YAML
- ShellCheck
- GitHub Copilot
- Ruff (Python linting)

### GPU Passthrough (NVIDIA)

1. **Install NVIDIA Driver** (on Windows host)
2. **Install CUDA Toolkit in WSL:**
```bash
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-wsl-ubuntu.pin
sudo mv cuda-wsl-ubuntu.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda-repo-wsl-ubuntu-12-1-local_12.1.0-1_amd64.deb
sudo dpkg -i cuda-repo-wsl-ubuntu-12-1-local_12.1.0-1_amd64.deb
sudo apt-get update
sudo apt-get install -y cuda
```

3. **Verify GPU Access:**
```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

---

## Quick Command Reference

```bash
# Bootstrap
./scripts/start.sh                 # Start platform
./scripts/stop.sh                  # Stop platform
./scripts/health-check.sh          # Check service health

# Testing
./tests/run_all.sh                 # Run all tests
./tests/test_bootstrap.sh          # Test bootstrap script
./tests/test_services.sh           # Test service integration

# Operations
./scripts/backup.sh                # Create backup
./scripts/restore.sh <backup-dir>  # Restore from backup
./scripts/gpu-detect.sh            # Detect GPU and VRAM

# Docker
docker compose -f docker/docker-compose.yml up -d     # Start services
docker compose -f docker/docker-compose.yml logs -f   # View logs
docker compose -f docker/docker-compose.yml ps        # Check status
docker compose -f docker/docker-compose.yml down      # Stop services

# Development
code --remote wsl+Ubuntu-22.04 .   # Open in VS Code (from WSL)
git checkout -b feature/my-feature # Create feature branch
```

---

**Status:** Ready for repository creation
**Next Steps:** Create GitHub repository and begin implementing bootstrap script
