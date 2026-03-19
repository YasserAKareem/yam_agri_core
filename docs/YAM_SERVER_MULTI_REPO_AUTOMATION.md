# YAM Server - Multi-Repository Automation Guide

> **Purpose:** Complete automation framework for managing all 8 YAM Server repositories with GitHub Copilot (Claude agent), VS Code, and Docker Desktop on Windows 11 + WSL

---

## Overview

This guide provides the **concrete base** for automating multi-repository development and integration across the entire YAM Server ecosystem.

### The 8 Repositories

| # | Repository | Purpose | Cadence |
|---|------------|---------|---------|
| 1 | **yam-server-core** | Platform infrastructure | Stable |
| 2 | **yam-server-models** | Model profiles, routing | Frequent |
| 3 | **yam-server-observability** | Dashboards, alerts | Moderate |
| 4 | **yam-server-agents** | A2A agent definitions | Frequent |
| 5 | **yam-server-workflows** | n8n automation | Frequent |
| 6 | **yam-server-business** | Frappe/ERPNext apps | Moderate |
| 7 | **yam-server-ui-kit** | Vue 3 design system | Frequent |
| 8 | **yam-server-docs** | Architecture, runbooks | Continuous |

---

## Windows 11 + WSL + Docker Desktop Setup

### 1. Enable WSL 2

```powershell
# Run in PowerShell as Administrator
wsl --install
wsl --set-default-version 2
wsl --install -d Ubuntu-22.04

# Restart computer
```

### 2. Install Docker Desktop

1. Download from https://www.docker.com/products/docker-desktop/
2. Install with WSL 2 backend enabled
3. Settings → General → "Use WSL 2 based engine" ✅
4. Settings → Resources → WSL Integration → Enable "Ubuntu-22.04" ✅

### 3. Enable GPU Support (NVIDIA)

```powershell
# Windows: Install NVIDIA Driver (535+)
# Download from https://www.nvidia.com/Download/index.aspx

# WSL: Install CUDA Toolkit
wsl
sudo apt-get update
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-wsl-ubuntu.pin
sudo mv cuda-wsl-ubuntu.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda-repo-wsl-ubuntu-12-1-local_12.1.0-1_amd64.deb
sudo dpkg -i cuda-repo-wsl-ubuntu-12-1-local_12.1.0-1_amd64.deb
sudo cp /var/cuda-repo-wsl-ubuntu-12-1-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda

# Verify
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### 4. VS Code Setup

```bash
# Install VS Code on Windows
# Download from https://code.visualstudio.com/

# Install WSL extension
code --install-extension ms-vscode-remote.remote-wsl

# Install recommended extensions
code --install-extension github.copilot
code --install-extension github.copilot-chat
code --install-extension ms-azuretools.vscode-docker
code --install-extension redhat.vscode-yaml
code --install-extension timonwong.shellcheck
code --install-extension esbenp.prettier-vscode
```

---

## Multi-Repository Workspace Setup

### Directory Structure

```
~/yam-server/                           # Root workspace
├── repos/
│   ├── yam-server-core/
│   ├── yam-server-models/
│   ├── yam-server-observability/
│   ├── yam-server-agents/
│   ├── yam-server-workflows/
│   ├── yam-server-business/
│   ├── yam-server-ui-kit/
│   └── yam-server-docs/
├── .vscode/
│   ├── yam-server.code-workspace      # Multi-root workspace
│   ├── settings.json                  # Global settings
│   └── tasks.json                     # Cross-repo tasks
├── scripts/
│   ├── clone-all.sh                   # Clone all repos
│   ├── update-all.sh                  # Pull all repos
│   ├── status-all.sh                  # Check status
│   ├── test-all.sh                    # Run all tests
│   └── build-all.sh                   # Build everything
└── .github-copilot/
    ├── global-context.md              # Shared context
    ├── methods.md                     # Development methods
    └── rules.md                       # Global rules
```

### Clone All Repositories

```bash
# scripts/clone-all.sh
#!/usr/bin/env bash
set -euo pipefail

readonly ORG="YasserAKareem"
readonly WORKSPACE="$HOME/yam-server"

repos=(
  "yam-server-core"
  "yam-server-models"
  "yam-server-observability"
  "yam-server-agents"
  "yam-server-workflows"
  "yam-server-business"
  "yam-server-ui-kit"
  "yam-server-docs"
)

mkdir -p "$WORKSPACE/repos"
cd "$WORKSPACE/repos"

for repo in "${repos[@]}"; do
  if [[ -d "$repo" ]]; then
    echo "✓ $repo already exists"
  else
    echo "⬇ Cloning $repo..."
    git clone "https://github.com/$ORG/$repo.git"
  fi
done

echo ""
echo "✅ All repositories cloned to $WORKSPACE/repos/"
echo ""
echo "Next steps:"
echo "  cd $WORKSPACE"
echo "  code yam-server.code-workspace"
```

### VS Code Multi-Root Workspace

```json
// .vscode/yam-server.code-workspace
{
  "folders": [
    {
      "name": "1️⃣ Core",
      "path": "repos/yam-server-core"
    },
    {
      "name": "2️⃣ Models",
      "path": "repos/yam-server-models"
    },
    {
      "name": "3️⃣ Observability",
      "path": "repos/yam-server-observability"
    },
    {
      "name": "4️⃣ Agents",
      "path": "repos/yam-server-agents"
    },
    {
      "name": "5️⃣ Workflows",
      "path": "repos/yam-server-workflows"
    },
    {
      "name": "6️⃣ Business",
      "path": "repos/yam-server-business"
    },
    {
      "name": "7️⃣ UI Kit",
      "path": "repos/yam-server-ui-kit"
    },
    {
      "name": "8️⃣ Docs",
      "path": "repos/yam-server-docs"
    }
  ],
  "settings": {
    "files.exclude": {
      "**/node_modules": true,
      "**/__pycache__": true,
      "**/.pytest_cache": true,
      "**/dist": true,
      "**/build": true,
      "**/.venv": true,
      "**/venv": true
    },
    "search.exclude": {
      "**/node_modules": true,
      "**/dist": true,
      "**/.git": true
    },
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": true
    },
    "git.enableSmartCommit": true,
    "git.confirmSync": false,
    "github.copilot.enable": {
      "*": true
    }
  },
  "extensions": {
    "recommendations": [
      "github.copilot",
      "github.copilot-chat",
      "ms-azuretools.vscode-docker",
      "redhat.vscode-yaml",
      "timonwong.shellcheck",
      "charliermarsh.ruff",
      "esbenp.prettier-vscode",
      "vue.volar",
      "dbaeumer.vscode-eslint"
    ]
  },
  "tasks": {
    "version": "2.0.0",
    "tasks": [
      {
        "label": "Update All Repos",
        "type": "shell",
        "command": "${workspaceFolder:1️⃣ Core}/../../../scripts/update-all.sh",
        "problemMatcher": []
      },
      {
        "label": "Status All Repos",
        "type": "shell",
        "command": "${workspaceFolder:1️⃣ Core}/../../../scripts/status-all.sh",
        "problemMatcher": []
      },
      {
        "label": "Test All Repos",
        "type": "shell",
        "command": "${workspaceFolder:1️⃣ Core}/../../../scripts/test-all.sh",
        "problemMatcher": []
      },
      {
        "label": "Start YAM Server (Core)",
        "type": "shell",
        "command": "./scripts/start.sh",
        "options": {
          "cwd": "${workspaceFolder:1️⃣ Core}"
        },
        "problemMatcher": []
      }
    ]
  }
}
```

---

## GitHub Copilot (Claude Agent) Configuration

### Global Context Document

```markdown
# .github-copilot/global-context.md

# YAM Server - Global Context

You are working across **8 specialized repositories** that together form the YAM Server platform.

## Repository Family

| Repo | Purpose | Primary Language | When to Use |
|------|---------|------------------|-------------|
| **core** | Platform infrastructure | Bash, Docker Compose | Service orchestration, bootstrap |
| **models** | Model profiles, routing | YAML, Python | Model configuration, routing policies |
| **observability** | Monitoring, alerts | YAML, PromQL | Dashboards, metrics, SLOs |
| **agents** | A2A agent definitions | Python, YAML | Agent development, tool wrappers |
| **workflows** | n8n automation | JSON, JavaScript | Workflow automation, integrations |
| **business** | Frappe/ERPNext apps | Python, JavaScript | Business logic, DocTypes |
| **ui-kit** | Design system | Vue 3, TypeScript | UI components, design tokens |
| **docs** | Architecture, runbooks | Markdown | Documentation, ADRs, runbooks |

## Cross-Repository Principles

1. **One Command Promise** (core) - Must always work
2. **Hardware Honesty** (models) - Test on RTX 4060 (8GB VRAM)
3. **Symptom-Based Alerting** (observability) - Alert on user impact
4. **Assistive AI Only** (agents, business) - AI suggests, humans approve
5. **Version Control Workflows** (workflows) - All workflows in git
6. **AI-Native Components** (ui-kit) - Design for AI-assisted UX
7. **Docs as Code** (docs) - Test, version, review

## Integration Points

### Core ← Models
Core bootstrap reads model compatibility matrix from models repo

### Core ← Observability
Core exposes metrics, observability provides dashboards

### Core ← Agents
Core provides inference API, agents define tool wrappers

### Core ← Workflows
n8n in core runs workflows defined in workflows repo

### Core ← Business
Frappe apps call LiteLLM API from core

### Business ← UI Kit
Frappe apps use Vue components from ui-kit

### All → Docs
All repos link to architecture docs and runbooks

## Development Workflow

1. **Feature spans single repo:** Work in that repo only
2. **Feature spans multiple repos:** Create linked PRs
3. **Breaking changes:** Coordinate releases across repos
4. **Testing:** Test integration between repos before merging

## Critical Rules Across All Repos

1. Never break the one-command bootstrap (core)
2. Test on minimal hardware (RTX 4060 8GB)
3. AI never writes directly to business data
4. All services must have health checks
5. Documentation must be updated with code
6. Secrets never in source code
7. Accessibility (WCAG 2.1 AA) required
8. RTL support for Arabic users
```

### MCP (Model Context Protocol) Configuration

```json
// .github-copilot/mcp-config.json
{
  "mcpServers": {
    "yam-server-platform": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "env": {
        "WORKSPACE_ROOT": "${workspaceFolder}",
        "REPOS": "core,models,observability,agents,workflows,business,ui-kit,docs"
      }
    }
  },
  "resources": [
    {
      "uri": "file:///${workspaceFolder}/repos/yam-server-core/docker/docker-compose.yml",
      "name": "Core Platform Stack"
    },
    {
      "uri": "file:///${workspaceFolder}/repos/yam-server-models/hardware/compatibility-matrix.yaml",
      "name": "Hardware Compatibility"
    },
    {
      "uri": "file:///${workspaceFolder}/repos/yam-server-docs/architecture/c4-model/",
      "name": "Architecture Diagrams"
    }
  ],
  "tools": [
    {
      "name": "clone_all_repos",
      "description": "Clone all YAM Server repositories",
      "command": "${workspaceFolder}/scripts/clone-all.sh"
    },
    {
      "name": "update_all_repos",
      "description": "Pull latest changes for all repos",
      "command": "${workspaceFolder}/scripts/update-all.sh"
    },
    {
      "name": "status_all_repos",
      "description": "Check git status across all repos",
      "command": "${workspaceFolder}/scripts/status-all.sh"
    },
    {
      "name": "test_all_repos",
      "description": "Run tests across all repositories",
      "command": "${workspaceFolder}/scripts/test-all.sh"
    },
    {
      "name": "start_platform",
      "description": "Start YAM Server platform",
      "command": "${workspaceFolder}/repos/yam-server-core/scripts/start.sh"
    }
  ],
  "agents": {
    "platform-architect": {
      "description": "Helps with cross-repository architectural decisions",
      "context": [
        "global-context.md",
        "repos/yam-server-docs/architecture/design-principles.md"
      ],
      "tools": ["status_all_repos"]
    },
    "integration-tester": {
      "description": "Tests integration between repositories",
      "context": [
        "global-context.md",
        "repos/yam-server-docs/architecture/integration-patterns.md"
      ],
      "tools": ["test_all_repos", "start_platform"]
    }
  }
}
```

---

## Automation Scripts

### Update All Repositories

```bash
# scripts/update-all.sh
#!/usr/bin/env bash
set -euo pipefail

readonly REPOS_DIR="$HOME/yam-server/repos"

repos=(
  "yam-server-core"
  "yam-server-models"
  "yam-server-observability"
  "yam-server-agents"
  "yam-server-workflows"
  "yam-server-business"
  "yam-server-ui-kit"
  "yam-server-docs"
)

echo "🔄 Updating all YAM Server repositories..."
echo ""

for repo in "${repos[@]}"; do
  if [[ -d "$REPOS_DIR/$repo" ]]; then
    echo "📦 $repo"
    cd "$REPOS_DIR/$repo"

    # Store current branch
    current_branch=$(git branch --show-current)

    # Check if working directory is clean
    if [[ -n $(git status --porcelain) ]]; then
      echo "  ⚠️  Working directory not clean, skipping"
    else
      # Pull latest
      git pull --rebase origin "$current_branch" 2>&1 | sed 's/^/  /'
    fi

    echo ""
  else
    echo "❌ $repo not found"
    echo ""
  fi
done

echo "✅ Update complete"
```

### Status All Repositories

```bash
# scripts/status-all.sh
#!/usr/bin/env bash
set -euo pipefail

readonly REPOS_DIR="$HOME/yam-server/repos"

repos=(
  "yam-server-core"
  "yam-server-models"
  "yam-server-observability"
  "yam-server-agents"
  "yam-server-workflows"
  "yam-server-business"
  "yam-server-ui-kit"
  "yam-server-docs"
)

echo "📊 YAM Server Repository Status"
echo ""

for repo in "${repos[@]}"; do
  if [[ -d "$REPOS_DIR/$repo" ]]; then
    cd "$REPOS_DIR/$repo"

    # Get current branch
    branch=$(git branch --show-current)

    # Check for uncommitted changes
    if [[ -n $(git status --porcelain) ]]; then
      status="🔴 Uncommitted changes"
    else
      status="✅ Clean"
    fi

    # Check for unpushed commits
    unpushed=$(git log origin/"$branch".."$branch" --oneline 2>/dev/null | wc -l)
    if [[ $unpushed -gt 0 ]]; then
      status="$status, ⬆️  $unpushed unpushed"
    fi

    echo "📦 $repo"
    echo "   Branch: $branch"
    echo "   Status: $status"
    echo ""
  fi
done
```

### Test All Repositories

```bash
# scripts/test-all.sh
#!/usr/bin/env bash
set -euo pipefail

readonly REPOS_DIR="$HOME/yam-server/repos"

test_repo() {
  local repo=$1
  local test_command=$2

  echo "🧪 Testing $repo..."
  cd "$REPOS_DIR/$repo"

  if eval "$test_command"; then
    echo "  ✅ Tests passed"
    return 0
  else
    echo "  ❌ Tests failed"
    return 1
  fi
}

failed_repos=()

# Core: Shell script tests
if ! test_repo "yam-server-core" "./tests/run_all.sh"; then
  failed_repos+=("yam-server-core")
fi

# Models: YAML validation + Python tests
if ! test_repo "yam-server-models" "python tools/profile-validator.py profiles/ && pytest"; then
  failed_repos+=("yam-server-models")
fi

# Observability: YAML validation
if ! test_repo "yam-server-observability" "yamllint dashboards/ alerts/"; then
  failed_repos+=("yam-server-observability")
fi

# Agents: Python tests
if ! test_repo "yam-server-agents" "pytest"; then
  failed_repos+=("yam-server-agents")
fi

# Workflows: JSON validation
if ! test_repo "yam-server-workflows" "python tests/test_workflow_schema.py"; then
  failed_repos+=("yam-server-workflows")
fi

# Business: Frappe tests (if bench available)
if command -v bench &> /dev/null; then
  if ! test_repo "yam-server-business" "bench --site test run-tests --app yam_agriculture"; then
    failed_repos+=("yam-server-business")
  fi
else
  echo "⚠️  Skipping yam-server-business (bench not found)"
fi

# UI Kit: Vitest
if ! test_repo "yam-server-ui-kit" "npm test"; then
  failed_repos+=("yam-server-ui-kit")
fi

# Docs: Markdown linting
if ! test_repo "yam-server-docs" "markdownlint **/*.md"; then
  failed_repos+=("yam-server-docs")
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ ${#failed_repos[@]} -eq 0 ]]; then
  echo "✅ All tests passed"
  exit 0
else
  echo "❌ Failed repositories:"
  for repo in "${failed_repos[@]}"; do
    echo "   - $repo"
  done
  exit 1
fi
```

---

## Development Workflows

### Workflow 1: Single-Repo Feature

```bash
# Example: Adding a new model profile

# 1. Navigate to models repo
cd ~/yam-server/repos/yam-server-models

# 2. Create feature branch
git checkout -b feature/add-qwen-model

# 3. Make changes
# - Create profiles/qwen/qwen-2.5-7b-q4.yaml
# - Update hardware/compatibility-matrix.yaml
# - Run benchmark

# 4. Test
python tools/profile-validator.py profiles/qwen/qwen-2.5-7b-q4.yaml
pytest

# 5. Commit
git add .
git commit -m "feat(models): add Qwen 2.5 7B model profile"

# 6. Push and open PR
git push origin feature/add-qwen-model
gh pr create --title "Add Qwen 2.5 7B model profile"
```

### Workflow 2: Multi-Repo Feature

```bash
# Example: New AI-assisted feature in business app

# 1. Create feature branches in both repos
cd ~/yam-server/repos/yam-server-business
git checkout -b feature/ai-crop-advisor

cd ~/yam-server/repos/yam-server-agents
git checkout -b feature/crop-advisor-agent

# 2. Implement in agents repo first
cd ~/yam-server/repos/yam-server-agents
# - Create agents/agriculture/crop-advisor.yaml
# - Create tools/agriculture/soil-analyzer.py
# - Test

# 3. Integrate in business repo
cd ~/yam-server/repos/yam-server-business
# - Create api/ai_crop_advisor.py
# - Update crop_cycle DocType
# - Test integration

# 4. Create linked PRs
cd ~/yam-server/repos/yam-server-agents
git push origin feature/crop-advisor-agent
gh pr create --title "feat(agents): add crop advisor agent"

cd ~/yam-server/repos/yam-server-business
git push origin feature/ai-crop-advisor
gh pr create --title "feat(business): integrate crop advisor AI" \
  --body "Depends on YasserAKareem/yam-server-agents#123"

# 5. Merge in dependency order
# - First: agents PR
# - Second: business PR
```

### Workflow 3: Platform-Wide Update

```bash
# Example: Update all repos to use new LiteLLM API version

# 1. Update core with new LiteLLM version
cd ~/yam-server/repos/yam-server-core
# - Update docker-compose.yml
# - Test

# 2. Update dependent repos
# Agents
cd ~/yam-server/repos/yam-server-agents
# - Update API client

# Business
cd ~/yam-server/repos/yam-server-business
# - Update integrations/litellm/client.py

# Workflows
cd ~/yam-server/repos/yam-server-workflows
# - Update LiteLLM connector nodes

# 3. Create coordinated PRs
# Use same PR title prefix: "chore: upgrade to LiteLLM v2.0"
# Link PRs with "Part of platform-wide LiteLLM v2.0 upgrade"

# 4. Merge all simultaneously
```

---

## Testing & Verification

### Integration Test Script

```bash
# scripts/integration-test.sh
#!/usr/bin/env bash
set -euo pipefail

echo "🧪 YAM Server Integration Test"
echo ""

# 1. Start platform
echo "1️⃣ Starting platform..."
cd ~/yam-server/repos/yam-server-core
./scripts/start.sh

# 2. Wait for healthy
echo "2️⃣ Waiting for services..."
./scripts/health-check.sh

# 3. Test model inference
echo "3️⃣ Testing inference..."
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer $(cat .env | grep LITELLM_API_KEY | cut -d'=' -f2)" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "default",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# 4. Test agent execution
echo "4️⃣ Testing agent..."
# (Agent test logic)

# 5. Test workflow trigger
echo "5️⃣ Testing workflow..."
# (Workflow test logic)

# 6. Test UI kit components
echo "6️⃣ Testing UI components..."
cd ~/yam-server/repos/yam-server-ui-kit
npm run test:integration

echo ""
echo "✅ Integration test complete"
```

### Checkpoint Verification

Create checkpoints for each major milestone:

```yaml
# checkpoints/v1.0-bootstrap-working.yaml
name: "v1.0 Bootstrap Working"
date: "2026-03-17"
description: "One-command bootstrap successfully starts platform"

verification:
  - name: "GPU Detection"
    command: "cd ~/yam-server/repos/yam-server-core && ./scripts/gpu-detect.sh"
    expected: "NVIDIA RTX 4060, 8 GB VRAM"

  - name: "Model Selection"
    command: "grep MODEL_PRESET ~/yam-server/repos/yam-server-core/.env"
    expected: "MODEL_PRESET=llama-3.2-3b-q4"

  - name: "All Services Healthy"
    command: "cd ~/yam-server/repos/yam-server-core && ./scripts/health-check.sh"
    expected_exit_code: 0

  - name: "Chat Request Works"
    command: "curl -sf http://localhost/health"
    expected_exit_code: 0

repos_state:
  yam-server-core: "v1.0.0"
  yam-server-models: "v1.0.0"
  yam-server-docs: "v1.0.0"
```

---

## GitHub Copilot Agent Skills

### Skill: Cross-Repo Search

```python
# .github-copilot/skills/cross_repo_search.py
"""
Search across all YAM Server repositories
"""
import subprocess
from pathlib import Path

def search_all_repos(pattern: str, file_pattern: str = "*") -> dict:
    """
    Search for pattern across all repos.

    Args:
        pattern: Text pattern to search
        file_pattern: File glob pattern (e.g., "*.py", "*.yaml")

    Returns:
        Dict mapping repo name to list of matches
    """
    repos_dir = Path.home() / "yam-server" / "repos"
    repos = [
        "yam-server-core",
        "yam-server-models",
        "yam-server-observability",
        "yam-server-agents",
        "yam-server-workflows",
        "yam-server-business",
        "yam-server-ui-kit",
        "yam-server-docs",
    ]

    results = {}

    for repo in repos:
        repo_path = repos_dir / repo
        if not repo_path.exists():
            continue

        # Use ripgrep for fast search
        cmd = [
            "rg",
            "--json",
            "--glob", file_pattern,
            pattern
        ]

        try:
            output = subprocess.check_output(
                cmd,
                cwd=repo_path,
                text=True
            )
            matches = [line for line in output.split('\n') if line]
            if matches:
                results[repo] = matches
        except subprocess.CalledProcessError:
            # No matches
            pass

    return results
```

### Skill: Dependency Graph

```python
# .github-copilot/skills/dependency_graph.py
"""
Generate dependency graph between repositories
"""

def get_repo_dependencies() -> dict:
    """
    Returns dependency graph showing which repos depend on which.
    """
    return {
        "yam-server-core": {
            "depends_on": [],
            "depended_by": [
                "yam-server-models",
                "yam-server-observability",
                "yam-server-agents",
                "yam-server-workflows",
                "yam-server-business"
            ]
        },
        "yam-server-models": {
            "depends_on": ["yam-server-core"],
            "depended_by": ["yam-server-core"]  # Circular for model catalog
        },
        "yam-server-business": {
            "depends_on": [
                "yam-server-core",
                "yam-server-ui-kit",
                "yam-server-agents"
            ],
            "depended_by": []
        },
        # ... rest of graph
    }

def get_merge_order(changed_repos: list) -> list:
    """
    Given a list of repos with changes, return merge order.
    """
    graph = get_repo_dependencies()

    # Topological sort
    ordered = []
    visited = set()

    def visit(repo):
        if repo in visited:
            return
        visited.add(repo)

        for dep in graph[repo]["depends_on"]:
            if dep in changed_repos:
                visit(dep)

        ordered.append(repo)

    for repo in changed_repos:
        visit(repo)

    return ordered
```

---

## Quick Reference

### Common Commands

```bash
# Clone all repos
~/yam-server/scripts/clone-all.sh

# Update all repos
~/yam-server/scripts/update-all.sh

# Check status
~/yam-server/scripts/status-all.sh

# Run all tests
~/yam-server/scripts/test-all.sh

# Start platform
cd ~/yam-server/repos/yam-server-core
./scripts/start.sh

# Open workspace in VS Code
code ~/yam-server/.vscode/yam-server.code-workspace
```

### VS Code Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+P` | Command palette |
| `Ctrl+P` | Quick open file (across all repos) |
| `Ctrl+Shift+F` | Search across workspace |
| `Ctrl+Shift+B` | Run build task |
| `Ctrl+Shift+'` | Open terminal |
| `Ctrl+K Ctrl+O` | Open folder (switch repos) |

### GitHub Copilot Chat Commands

```
@workspace What is the architecture of YAM Server?
@workspace How do I add a new model?
@workspace Where is GPU detection implemented?
@workspace Show me all DocTypes that use AI
@workspace How do repos integrate with each other?
```

---

## Troubleshooting

### Issue: WSL Can't Access GPU

**Symptoms:** `nvidia-smi` not found in WSL

**Fix:**
```bash
# Check Windows driver
nvidia-smi.exe

# Reinstall CUDA in WSL
# Follow GPU setup steps in section 3
```

### Issue: Docker Desktop Not Starting

**Symptoms:** Docker commands fail

**Fix:**
1. Open Docker Desktop
2. Settings → Resources → WSL Integration
3. Enable "Ubuntu-22.04"
4. Restart Docker Desktop

### Issue: VS Code Can't Find Repos

**Symptoms:** Workspace folders show "Not Found"

**Fix:**
```bash
# Verify repos exist
ls ~/yam-server/repos/

# Reopen workspace
code ~/yam-server/.vscode/yam-server.code-workspace
```

---

## Next Steps

1. ✅ Complete Windows 11 + WSL + Docker setup
2. ✅ Clone all 8 repositories
3. ✅ Open multi-root workspace in VS Code
4. ✅ Configure GitHub Copilot with global context
5. ✅ Run integration test to verify setup
6. ✅ Start building!

---

**You now have a complete, automated multi-repository development environment for YAM Server. Happy coding! 🚀**
