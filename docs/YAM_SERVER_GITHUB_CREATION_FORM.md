# YAM Server - GitHub Repository Creation Forms

> **Purpose:** Complete GitHub repository creation form information for all 8 YAM Server repositories in a single document

---

## Repository 1: yam-server-core

### General

**Repository name:**
```
yam-server-core
```

**Description (350 characters):**
```
One command to launch your AI platform. Local LLM with Open WebUI, LiteLLM, vLLM. Detects GPU, picks model, generates credentials automatically. Compose-first AI platform for small teams. Your gateway. Your models. Your documents. Your routes. Your repos. Your rules. Bootstrap script handles everything: GPU detection, model selection, credential generation, service orchestration, health checks.
```

### Configuration

**Start with a template:**
```
No template
```

**Add .gitignore:**
```
Python
```

### Jumpstart your project with Copilot (optional)

**Prompt (30000 characters):**
```
You are working on YAM Server Core, the platform infrastructure that makes the "one command" promise real.

## Repository Context

**Purpose:** Platform infrastructure - Docker Compose orchestration, bootstrap logic, service configuration

**Key Principle:** The `./scripts/start.sh` command must ALWAYS work. Every change must preserve or improve the one-command setup experience.

## What This Repository Owns

- Docker Compose files for the core platform
- Bootstrap script (`start.sh`) - THE one command that starts everything
- GPU detection and model selection logic
- Credential generation (secure random keys, passwords, tokens)
- Service health checks and orchestration
- Backup and restore scripts
- Core documentation (getting started, architecture overview)

## What This Repository Does NOT Own

- Model profiles or routing policies → yam-server-models
- Monitoring dashboards → yam-server-observability
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

## Core Stack

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

## Bootstrap Flow

The `start.sh` script is the heart of the platform. Here's what it does:

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

## Repository Family Context

This repo is part of the YAM Server multi-repository family. When making changes that affect other repos:
- Link PRs across repositories
- Update version compatibility documentation
- Coordinate releases with affected repos
- Test integration with latest versions of dependencies

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

## Questions to Ask

When uncertain about a change:
1. Does this preserve the one-command promise?
2. Will this work on minimal hardware (RTX 4060)?
3. Is there a CPU fallback?
4. Are health checks implemented?
5. Is this documented?
6. Does this belong in a different repo?
```

---

## Repository 2: yam-server-models

### General

**Repository name:**
```
yam-server-models
```

**Description (350 characters):**
```
Model profiles, semantic routing policies, LiteLLM catalogs, and hardware benchmarks for YAM Server. Know which model for which GPU. Quantization guidance (Q4 vs Q8), VRAM calculators, compatibility matrices. Test on RTX 4060 (8GB VRAM). Benchmark methodology. System prompts. Model selection decision trees. Hardware-aware routing. Real performance data per GPU configuration.
```

### Configuration

**Start with a template:**
```
No template
```

**Add .gitignore:**
```
Python
```

### Jumpstart your project with Copilot (optional)

**Prompt (30000 characters):**
```
You are working on YAM Server Models, the knowledge base for model selection and routing.

## Repository Context

**Purpose:** Model profiles, routing policies, hardware benchmarks, quantization guidance

**Key Principle:** Every hardware configuration should have a clear, tested recommendation.

## What Goes Here

### ✅ Belongs in this repo:
- Model profile YAML files (VRAM requirements, capabilities, benchmarks)
- Semantic router route definitions
- LiteLLM catalog and router configs
- Hardware compatibility matrices
- Quantization guides and recommendations
- System prompts and templates
- Benchmark results and scripts
- VRAM calculators and validation tools

### ❌ Does NOT belong here:
- Docker Compose files → yam-server-core
- Service deployment configs → yam-server-core
- Observability dashboards → yam-server-observability
- Application logic → yam-server-business

## Critical Rules

### 1. Every Profile Must Be Tested
- Never add a model profile without benchmark data
- Benchmark on actual hardware, not estimates
- Include VRAM measurements (idle and peak)
- Document actual tokens/second performance

### 2. Hardware Recommendations Must Be Conservative
- Recommend models that comfortably fit in available VRAM
- Leave 10-15% VRAM headroom for safety
- Test with realistic batch sizes (4-8 for multi-user)
- Verify with long contexts (8k+ tokens)

### 3. Quantization Guidance Must Be Honest
- Q4 is not "almost as good as" Q8 - document the tradeoffs
- Provide actual quality comparisons, not just theory
- Benchmark quantization impact on your models
- Recommend Q8 when VRAM allows

### 4. Routing Policies Must Be Deterministic
- Semantic routes must have clear, non-overlapping utterances
- Provide fallback routes for ambiguous queries
- Test route selection with real user queries
- Document routing logic decisions

### 5. Benchmark Data Must Be Reproducible
- Document exact hardware configuration
- Include GPU driver version, CUDA version
- List all environment variables
- Provide benchmark scripts for reproduction

## Model Profile Template

```yaml
name: model-name
family: model-family
version: "x.y"
parameter_count: XB
quantization: Q4_K_M|Q8_0|BF16

vram_requirements:
  minimum_gb: X
  recommended_gb: Y
  context_8k: Z
  context_32k: W

capabilities:
  - capability-1
  - capability-2

context_length:
  default: 8192
  maximum: 32768

performance_targets:
  tokens_per_second: X-Y
  time_to_first_token_ms: X-Y
  batch_size: X-Y

recommended_for:
  - use-case-1
  - use-case-2

not_recommended_for:
  - use-case-1
  - use-case-2

vllm_config:
  gpu_memory_utilization: 0.9
  max_model_len: 8192
  tensor_parallel_size: 1
  dtype: float16

litellm_config:
  model: "vllm/model-name"
  api_base: "http://vllm:8001/v1"
  rpm: 60
  tpm: 10000

benchmarks:
  - hardware: gpu-model
    tokens_per_second: X
    time_to_first_token_ms: Y
    throughput_batch_4: Z

model_source:
  huggingface: "org/model-name"
  gguf: "TheBloke/model-name-GGUF"
  quantized: "model-name.gguf"
```

## Model Selection Decision Tree

```
Start: What's your GPU?
│
├─ No GPU (CPU only)
│  └─> phi-3-mini or llama-3.2-1b-q4
│
├─ 4-6 GB VRAM
│  └─> llama-3.2-1b-q4 or llama-3.2-3b-q4
│
├─ 6-10 GB VRAM
│  ├─ Need speed? → llama-3.2-3b-q4
│  └─ Need quality? → llama-3.1-8b-q4
│
├─ 10-16 GB VRAM
│  ├─ General use → llama-3.1-8b-q8
│  ├─ Coding → llama-3.1-8b-q8 with code prompt
│  └─ Experimentation → mixtral-8x7b-q4
│
└─ 16+ GB VRAM
   ├─ Best quality → llama-3.1-70b-q4
   ├─ Mixture of experts → mixtral-8x7b-q4
   └─ Multi-model serving → Multiple smaller models
```

## Quantization Guide

### Q4_K_M (4.5 bits per weight)
- **Size:** ~50% of original
- **Quality:** ~95% of original
- **Use when:** VRAM is limited, speed matters
- **Best for:** General chat, most use cases

### Q8_0 (8 bits per weight)
- **Size:** ~75% of original
- **Quality:** ~98% of original
- **Use when:** You have VRAM to spare, quality matters
- **Best for:** Coding, analysis, creative writing

### BF16/FP16 (16 bits)
- **Size:** 100% of original
- **Quality:** 100% (original training precision)
- **Use when:** VRAM is abundant, maximum quality needed
- **Best for:** Research, benchmarking, production where quality is critical

## Hardware Compatibility Matrix

```yaml
gpus:
  rtx-4060-8gb:
    vram: 8
    recommended_models:
      - llama-3.2-1b-q4   # 2-3 GB VRAM
      - llama-3.2-3b-q4   # 4-6 GB VRAM
      - phi-3-mini        # 4 GB VRAM
    possible_but_tight:
      - llama-3.1-8b-q4   # 7-8 GB VRAM
    not_recommended:
      - llama-3.1-8b-q8   # 14 GB VRAM
      - llama-3.1-70b-q4  # 40+ GB VRAM
```

## Validation Requirements

Before submitting a PR:

1. **Profile Validation:**
```bash
python tools/profile-validator.py profiles/<family>/<model>.yaml
```

2. **Route Validation:**
```bash
python tools/route-validator.py routing/semantic-router/routes.yaml
```

3. **Benchmark Validation:**
```bash
python tools/benchmark-validator.py benchmarks/hardware/<gpu>.yaml
```

4. **Schema Compliance:**
```bash
pytest tests/test_schemas.py
```

## Common Tasks

### Adding a New Model

1. Create profile YAML in `profiles/<family>/<model>.yaml`
2. Run benchmark: `python benchmarks/scripts/run-benchmark.py <model>`
3. Add to compatibility matrix: `hardware/compatibility-matrix.yaml`
4. Update LiteLLM catalog: `python tools/catalog-generator.py`
5. Add route recommendations if specialized
6. Write documentation in `docs/models/<family>.md`
7. Submit PR with all validation passing

## Never Do This

- ❌ Add a model without benchmarks
- ❌ Recommend models you haven't tested
- ❌ Estimate VRAM requirements (measure them)
- ❌ Copy benchmarks from model card (run your own)
- ❌ Create overlapping semantic routes
- ❌ Recommend models that don't fit in specified VRAM
- ❌ Use aggressive memory settings as defaults

## Always Do This

- ✅ Test on actual hardware
- ✅ Benchmark with realistic workloads
- ✅ Leave VRAM headroom in recommendations
- ✅ Validate all YAMLs against schemas
- ✅ Document quantization tradeoffs honestly
- ✅ Provide CPU fallback options
- ✅ Update documentation when adding models
```

---

## Repository 3: yam-server-observability

### General

**Repository name:**
```
yam-server-observability
```

**Description (350 characters):**
```
Grafana dashboards, Prometheus rules, Loki/Tempo configs, and SLO definitions for YAM Server. The watchtower that makes the platform dependable. Symptom-based alerting. Runbooks for every alert. Three severity levels. Platform overview, model performance, resource usage, API gateway, user experience dashboards. 99.5% availability target. Error budgets. Alert philosophy.
```

### Configuration

**Start with a template:**
```
No template
```

**Add .gitignore:**
```
Python
```

### Jumpstart your project with Copilot (optional)

**Prompt (30000 characters):**
```
You are working on YAM Server Observability, the watchtower that makes the platform dependable.

## Repository Context

**Purpose:** Grafana dashboards, Prometheus alerts, SLO definitions, operational runbooks

**Key Principle:** Alert on user impact, not internal metrics. Every alert must have a runbook.

## What Goes Here

- Grafana dashboard JSON files
- Prometheus alert rules
- Loki log aggregation config
- Tempo trace collection setup
- SLO definitions (availability, latency, error rate)
- Alert thresholds and escalation policies
- Retention policies
- Operational runbooks (what to do when X fires)

## Critical Rules

### 1. Alerts Must Be Actionable
- Every alert must have a runbook
- Never alert on something that doesn't require human action
- Three severity levels only: critical, warning, info
- Critical = pages on-call, Warning = Slack, Info = log only

### 2. SLOs Must Be Realistic
- Based on actual hardware capabilities (RTX 4060 8GB VRAM)
- Include error budgets with burn rate alerts
- Review monthly, adjust quarterly
- Document rationale for every target

### 3. Dashboards Must Load Fast
- Optimize queries, use recording rules
- Limit time series per panel
- Use appropriate aggregation intervals
- Test dashboard performance

### 4. No Alert Fatigue
- Warning alerts must not page humans
- Tune thresholds based on actual patterns
- Delete alerts that fire but don't require action
- Review alert history monthly

## Dashboard Catalog

| Dashboard | Purpose | Key Metrics |
|-----------|---------|-------------|
| **Platform Overview** | Health at a glance | Uptime, requests, errors |
| **Model Performance** | Inference quality | Tokens/sec, latency, VRAM |
| **Resource Usage** | Hardware monitoring | GPU, CPU, memory, disk |
| **API Gateway** | LiteLLM metrics | Auth, routing, rate limits |
| **User Experience** | End-user perspective | P95 latency, success rate |

## SLO Targets (v1.0)

```yaml
# slos/latency.yaml
availability_target: 99.5%   # 43 minutes downtime per month
latency_p95_ms: 500
latency_p99_ms: 1000
error_budget:
  monthly: 0.5%
  alert_threshold: 50%  # Alert when 50% of error budget consumed
```

## Alert Philosophy

We follow **symptom-based alerting**:
- Alert on user impact, not internal metrics
- Actionable alerts only (always has a runbook)
- Three severity levels: critical, warning, info
- Pages wake humans only for critical alerts

## Critical Alerts

- GPU temperature > 85°C
- VRAM utilization > 95%
- API gateway down > 1 minute
- P95 latency > 2x SLO
- Error rate > 5%

## Runbook Template

```markdown
# Runbook: [Operation or Incident Name]

**Purpose:** [One-line description]
**Severity:** [P0-Critical | P1-High | P2-Medium | P3-Low]
**SLA:** [Response time / Resolution time]

## Symptoms
- [What you'll observe]

## Impact
- **Users Affected:** [All | Specific subset]
- **Business Impact:** [Revenue | Reputation | Operations]

## Quick Check
```bash
./scripts/health-check.sh
docker compose ps service-name
```

## Resolution
1. [Step 1]
2. [Step 2]

## Verification
- [ ] Service health check passes
- [ ] Metrics return to normal
```

## Dashboard Design Principles

- Overview first, details on demand
- Time ranges: 1h, 6h, 24h, 7d
- Consistent color scheme (green=good, yellow=warning, red=critical)
- Always show error budget burn rate

## Never Do This

- ❌ Alert without a runbook
- ❌ Page for non-critical issues
- ❌ Use internal metrics for alerts (use symptoms)
- ❌ Create dashboards that take >5s to load
- ❌ Set unrealistic SLOs
- ❌ Skip alert testing
```

---

## Repository 4: yam-server-agents

### General

**Repository name:**
```
yam-server-agents
```

**Description (350 characters):**
```
A2A agent definitions, tool wrappers, and orchestration patterns for YAM Server. Build agents that coordinate with each other. Research agents, coding assistants, document analyzers. Tool schemas, policy packs, safety constraints. Sequential, parallel, hierarchical orchestration. Function calling. Agent-to-agent communication. Resource limits. Approval workflows for sensitive actions.
```

### Configuration

**Start with a template:**
```
No template
```

**Add .gitignore:**
```
Python
```

### Jumpstart your project with Copilot (optional)

**Prompt (30000 characters):**
```
You are working on YAM Server Agents, building agent-to-agent (A2A) orchestration.

## Repository Context

**Purpose:** A2A agent definitions, tool wrappers, policy packs, orchestration patterns

**Key Principle:** Agents are assistive only. They suggest, humans approve, no autonomous actions.

## What Goes Here

- Agent definition YAML files
- Tool wrapper Python modules
- Function calling schemas
- Policy packs (allowed tools, constraints)
- Orchestration patterns (sequential, parallel, hierarchical)
- Example agent workflows
- Agent testing framework

## Critical Rules

### 1. Agents Are Assistive Only
- Agents suggest, humans approve
- No agent can write to production databases
- All sensitive actions require human confirmation
- Audit trail for every agent action

### 2. Tool Safety
- Tool allow-lists (explicit permission required)
- Resource limits (execution time, API calls)
- Input validation on all tool parameters
- Rate limiting per agent

### 3. Policy Enforcement
- Every agent has a policy pack
- Policies checked before tool invocation
- Violations logged and blocked
- Regular policy review

## Agent Definition Template

```yaml
name: agent-name
version: "1.0"
description: "What this agent does"

capabilities:
  - capability-1
  - capability-2

tools:
  - tool-name-1
  - tool-name-2

model_preferences:
  primary: llama-3.1-8b-q8
  fallback: llama-3.2-3b-q4

system_prompt: |
  You are a [role]. When given a task:
  1. Break it into steps
  2. Use tools to gather information
  3. Synthesize findings
  4. Present recommendations

policy:
  max_tool_calls: 10
  max_execution_time_seconds: 300
  requires_approval: false
  allowed_domains:
    - "*.edu"
    - "*.gov"
```

## Tool Wrapper Pattern

```python
from typing import List, Dict

async def tool_function(param1: str, param2: int) -> Dict:
    \"\"\"
    Tool description.

    Args:
        param1: Description
        param2: Description

    Returns:
        Result dictionary
    \"\"\"
    # Implementation
    pass

# Tool schema for function calling
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "tool_name",
        "description": "Description",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Description"
                }
            },
            "required": ["param1"]
        }
    }
}
```

## Orchestration Patterns

### Sequential
Agent A → Result → Agent B → Result → Agent C

### Parallel
Agent A → Result ↘
Agent B → Result → Aggregator → Final Result
Agent C → Result ↗

### Hierarchical
Coordinator Agent
├─> Specialist Agent 1
├─> Specialist Agent 2
└─> Specialist Agent 3

## Never Do This

- ❌ Let agents write to production data
- ❌ Skip approval for sensitive actions
- ❌ Use untrusted tool sources
- ❌ Allow unlimited tool invocations
- ❌ Skip policy checks
```

---

## Repository 5: yam-server-workflows

### General

**Repository name:**
```
yam-server-workflows
```

**Description (350 characters):**
```
n8n flows, event-driven automation, and integration pipelines for YAM Server. Version-controlled workflow definitions. Document processing, email monitoring, alert dispatching, approval flows, data sync, scheduled reports. Connectors for Slack, email, databases, APIs. Error handling, retry logic, conditional routing. Test before deploy. Workflow CI/CD. Idempotent by design.
```

### Configuration

**Start with a template:**
```
No template
```

**Add .gitignore:**
```
Node
```

### Jumpstart your project with Copilot (optional)

**Prompt (30000 characters):**
```
You are working on YAM Server Workflows, automating operations with n8n.

## Repository Context

**Purpose:** n8n workflow definitions, event-driven jobs, ingest pipelines, automation orchestration

**Key Principle:** All workflows in git, not trapped in a UI. Version control enables workflow CI/CD.

## What Goes Here

- n8n workflow JSON exports
- Event-driven job configurations
- Ingest pipeline definitions
- Connector logic (pull from external systems)
- Scheduled task definitions
- Approval flow templates
- Integration test data

## Critical Rules

### 1. Workflows Must Be Exportable
- All workflows export cleanly to JSON
- No secrets in workflow files
- Use n8n credentials manager
- Test import/export cycle

### 2. Error Branches Required
- Every workflow must handle errors
- Log errors to monitoring
- Notify on failures
- Implement retry logic

### 3. Testing Before Merge
- Test workflows with representative data
- Dry-run before production deploy
- Validate against schema
- Check for secrets in workflow files

### 4. Idempotency
- Safe to re-run without side effects
- Check for existing records
- Use upsert instead of insert
- Handle duplicate events

## Workflow Design Principles

- **Single Responsibility:** One workflow = one job
- **Composability:** Build from reusable sub-workflows
- **Observability:** Log inputs, outputs, errors
- **Idempotency:** Safe to re-run

## Common Patterns

### Data Transformation
Use Function nodes for complex logic

### Error Handling
Every workflow should have error branches:
Main Flow → [Success] → Continue
         → [Error] → Log Error → Notify Admin

### Retry Logic
For flaky APIs, use exponential backoff:
Attempt 1 → Wait 1s → Attempt 2 → Wait 2s → Attempt 3

## Never Do This

- ❌ Hardcode API keys or passwords
- ❌ Create workflows without error handling
- ❌ Deploy without testing
- ❌ Leave workflows undocumented
```

---

## Repository 6: yam-server-business

### General

**Repository name:**
```
yam-server-business
```

**Description (350 characters):**
```
Frappe/ERPNext business applications for YAM Server. Custom DocTypes, workflows, and AI-assisted business features. Where AI meets operations. Agriculture management, inventory tracking, sales distribution. AI crop advisor, demand forecasting, pricing optimization. Side-by-side deployment with LiteLLM. Assistive AI only - suggests, never autonomous. Human approval required.
```

### Configuration

**Start with a template:**
```
No template
```

**Add .gitignore:**
```
Python
```

### Jumpstart your project with Copilot (optional)

**Prompt (30000 characters):**
```
You are working on YAM Server Business, the Frappe/ERPNext business application layer.

## Repository Context

**Purpose:** Frappe/ERPNext business application layer with AI-assisted features

**Key Principle:** AI suggests, humans approve, Frappe enforces business rules. Never autonomous.

## What Goes Here

- Frappe app definitions (custom DocTypes, forms, workflows)
- ERPNext customizations for specific business domains
- Business logic and validation rules
- Custom reports and dashboards
- Print formats and templates
- Business-specific API endpoints
- Integration connectors to YAM Server AI services
- Custom Frappe UI components and pages
- Role profiles and permission rules
- Fixtures and seed data

## Critical Rules

### 1. AI is Assistive Only
- Never write directly to business tables from AI
- All AI suggestions stored in read-only fields
- Human approval required for high-risk decisions
- Audit trail for all AI interactions

### 2. Human Approval Required
- Critical decisions need explicit approval
- Role-based approval workflows
- No auto-apply of AI suggestions
- Clear approve/reject actions

### 3. Frappe Enforces Rules
- Business validation happens in Python controllers
- Never skip validation for AI suggestions
- Standard workflow applies to all records
- No special paths for AI-generated data

### 4. Side-by-Side Deployment
- Don't embed YAM Server inside Frappe container
- Frappe and AI stack run separately
- Integration via API calls only
- Share PostgreSQL if needed (read-only for AI)

## Integration Pattern

```python
# ✅ CORRECT: Assistive pattern
ai_suggestion = get_ai_recommendation(context)
crop_cycle.ai_recommendation = ai_suggestion  # Read-only field
# Human reviews and decides whether to apply

# ❌ WRONG: Autonomous action
ai_suggestion = get_ai_recommendation(context)
crop_cycle.apply_fertilizer_amount = ai_suggestion["amount"]
crop_cycle.save()  # AI directly modified business data
```

## LiteLLM Integration

```python
import httpx
import frappe

class LiteLLMClient:
    def __init__(self):
        self.base_url = frappe.conf.get("yam_server_litellm_url")
        self.api_key = frappe.conf.get("yam_server_api_key")

    async def chat_completion(self, messages, model="default"):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": model,
                    "messages": messages
                }
            )
            return response.json()
```

## Never Do This

- ❌ Let AI write directly to DocTypes
- ❌ Embed LiteLLM inside Frappe container
- ❌ Skip business validation for AI suggestions
- ❌ Store API keys in DocTypes or database
- ❌ Make platform dependent on AI availability
```

---

## Repository 7: yam-server-ui-kit

### General

**Repository name:**
```
yam-server-ui-kit
```

**Description (350 characters):**
```
Vue 3 UI design system for YAM Server based on frappe-ui. Reusable components, design tokens, accessibility patterns. Build once, use everywhere. AI-native components: AIAssistCard, ConfidenceIndicator, SuggestionPanel. WCAG 2.1 AA compliant. RTL support for Arabic. Dark mode. Storybook documentation. Design tokens for colors, typography, spacing, shadows. Component library.
```

### Configuration

**Start with a template:**
```
No template
```

**Add .gitignore:**
```
Node
```

### Jumpstart your project with Copilot (optional)

**Prompt (30000 characters):**
```
You are working on YAM Server UI Kit, the Vue 3 design system.

## Repository Context

**Purpose:** Vue 3 UI/UX design system based on frappe-ui with reusable components

**Key Principle:** Accessibility first. Every component must be WCAG 2.1 AA compliant.

## What Goes Here

- Vue 3 component library built on frappe-ui
- Design tokens (colors, typography, spacing, shadows)
- UI patterns and templates
- Storybook documentation
- Accessibility guidelines
- Responsive design utilities
- Theme configurations
- Icon library and illustrations
- Component usage guidelines

## Critical Rules

### 1. Accessibility First
- Every component must be WCAG 2.1 AA compliant
- Semantic HTML
- ARIA attributes
- Keyboard navigation
- Screen reader support
- Focus management
- Color contrast

### 2. Storybook Required
- No component without stories
- At least 3 variants per component
- Interactive controls
- Documentation in story

### 3. TypeScript Types
- All props and events must be typed
- No `any` types
- Proper generics where needed

### 4. RTL Testing
- Test components in RTL mode
- Use logical properties (start/end not left/right)
- Test with Arabic content

### 5. Design Tokens Only
- Never use hardcoded colors
- Never use hardcoded spacing
- Use theme tokens

## AI-Native Components

### AIAssistCard
Shows AI suggestions with confidence indicator and accept/dismiss actions

### ConfidenceIndicator
Visual representation of confidence score (0-100)
- High (80-100): Green
- Medium (50-79): Amber
- Low (0-49): Red

### SuggestionPanel
Container for multiple AI suggestions with filtering

## Component Checklist

Before merging a component:
- [ ] TypeScript types for all props
- [ ] Storybook stories (at least 3 variants)
- [ ] Unit tests (behavior, not implementation)
- [ ] Accessibility test passing
- [ ] RTL rendering correct
- [ ] Dark mode variant works
- [ ] Mobile responsive
- [ ] Documentation in story

## Never Do This

- ❌ Hardcode colors (use design tokens)
- ❌ Skip ARIA attributes
- ❌ Ignore keyboard navigation
- ❌ Use divs for buttons
- ❌ Forget focus indicators
```

---

## Repository 8: yam-server-docs

### General

**Repository name:**
```
yam-server-docs
```

**Description (350 characters):**
```
Architecture, runbooks, ADRs, and operational playbooks for YAM Server. Docs as infrastructure - searchable, linkable, citable. C4 model diagrams, architecture decision records, incident runbooks, onboarding guides, security threat model, hardware selection, troubleshooting. ADRs never deleted. Runbooks tested during incident simulation. Mermaid diagrams. Markdown standards.
```

### Configuration

**Start with a template:**
```
No template
```

**Add .gitignore:**
```
None
```

### Jumpstart your project with Copilot (optional)

**Prompt (30000 characters):**
```
You are working on YAM Server Docs, the architecture and operational knowledge base.

## Repository Context

**Purpose:** Architecture documentation, runbooks, ADRs, onboarding, troubleshooting

**Key Principle:** Docs are code. Review, test, version control.

## What Goes Here

- Architecture documentation (ADRs, C4 diagrams)
- Runbooks (incident response, recovery procedures)
- Onboarding guides
- Security and threat models
- Hardware selection guides
- Operational playbooks
- Glossary and terminology
- API documentation
- Troubleshooting guides

## Critical Rules

### 1. Docs are Code
- Review, test, version control
- Every doc has an owner
- Update with code changes
- Link from code to docs

### 2. Runbooks Must Work
- Test during incident simulation
- Update after every real incident
- Include exact commands
- Verify commands before committing

### 3. ADRs are Permanent
- Never delete ADRs
- Deprecate with status change
- Link to superseding ADR
- Keep history visible

### 4. Links Must be Relative
- Survive repo moves
- No absolute GitHub URLs
- Test links in CI

### 5. Examples Required
- Every concept needs example
- Code blocks must have language
- Include expected output

## ADR Template

```markdown
# ADR-NNNN: [Short Title]

**Status:** [Proposed | Accepted | Deprecated]
**Date:** YYYY-MM-DD
**Deciders:** [Names or roles]

## Decision
[What is the change?]

## Rationale
[Why are we doing this?]

## Consequences
### Positive
- [What becomes better?]

### Negative
- [What becomes harder?]
```

## Runbook Template

```markdown
# Runbook: [Operation Name]

**Purpose:** [One-line description]
**Severity:** [P0-P3]

## Symptoms
- [What you'll observe]

## Quick Check
```bash
./scripts/health-check.sh
```

## Resolution
1. [Step 1 with exact command]
2. [Step 2]

## Verification
- [ ] Check 1 passes
- [ ] Check 2 passes
```

## Documentation Standards

### Markdown
- Use GitHub-flavored markdown
- Headers: # for title, ## for sections
- Code blocks with language identifier
- Links: Relative for internal

### Diagrams
- Use Mermaid (renders in GitHub)
- Include alt text
- Store source in markdown

## Never Do This

- ❌ Copy docs without updating context
- ❌ Leave commands untested
- ❌ Delete ADRs (deprecate instead)
- ❌ Use absolute GitHub URLs
- ❌ Skip runbook testing
```

---

**End of Document**

This single file contains all GitHub repository creation form information for the complete YAM Server multi-repository family.
