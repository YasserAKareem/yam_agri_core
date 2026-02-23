# Agents & MCP Blueprint — YAM Agri Core

> **Who is this for?** The repository owner (Yasser) and every team member
> who uses GitHub Copilot, VS Code, or a compatible MCP client to work on
> the YAM Agri platform.
>
> **What does it cover?**
> 1. Which team members / roles get a dedicated Copilot Agent — and why
> 2. Which roles do NOT get an agent — and why
> 3. MCP (Model Context Protocol) server configuration for local dev
> 4. **Yemen-specific local dev environment setup** — offline resilience,
>    power-cut recovery, low-bandwidth image delivery

---

## 1. Which Roles Get a Copilot Agent?

> Note: these are **GitHub/dev contributor roles** for Copilot usage. Platform access control for ERPNext/Frappe uses the **standard ERPNext roles** (segregation-of-duties aware) and org-chart job functions are modeled as **Role Profiles**.
>
> See: `docs/planning/RBAC_AND_ORG_CHART.md`

### What is a Copilot Agent (`.github/agents/*.md`)?

A Copilot Agent is a **role-specific instruction file** that tells GitHub
Copilot *who you are*, *what rules apply*, and *what you must never do* when
working in that role. Each file lives in `.github/agents/` and is selected
when you start a Copilot session for that role.

### Role eligibility decision table

| Persona | Role in platform | GitHub/dev user? | Agent created? | Reason |
|---|---|---|---|---|
| **U1** Smallholder Farmer | End user — sends SMS | ❌ No | ❌ No | No GitHub access; interacts via SMS only |
| **U2** Farm Supervisor | End user — FieldPWA | ❌ No | ❌ No | No GitHub access; interacts via mobile app |
| **U3** QA / Food Safety Inspector | Business expert; approves workflows | ⚠️ Indirect | ❌ No | May review docs, but not a code contributor |
| **U4** Silo / Store Operator | End user — SiloDashboard | ❌ No | ❌ No | No GitHub access |
| **U5** Logistics Coordinator | End user — LogisticsApp | ❌ No | ❌ No | No GitHub access |
| **U6** Agri-Business Owner | Owns the product vision; final approver | ✅ Owner | ✅ **owner.md** | Needs product-strategy context for Copilot sessions |
| **U7** System Admin / IT | Manages infra, Docker, CI, backups | ✅ DevOps | ✅ **devops.md** | Writes compose files, workflows, shell scripts |
| **U8** External Auditor / Donor | Read-only portal access | ❌ No | ❌ No | No GitHub access; read-only consumer |
| **U9** AI Copilot (non-human) | Platform AI layer | — | — | This IS the AI — not a GitHub dev role |
| — | **Application Developer** | ✅ Developer | ✅ **developer.md** | Writes Frappe DocTypes, Python, JavaScript |
| — | **QA / Compliance Engineer** | ✅ QA Manager | ✅ **qa-manager.md** | Owns compliance rules, HACCP logic, test criteria |

### Summary: 4 agents created

| Agent file | Who uses it | Activation |
|---|---|---|
| `.github/agents/developer.md` | Frappe app developer | Start a Copilot chat session; reference this file for app dev tasks |
| `.github/agents/devops.md` | Infrastructure / DevOps engineer | Start a Copilot session for compose, CI, shell script work |
| `.github/agents/qa-manager.md` | QA / food-safety engineer | Start a Copilot session for compliance logic and test writing |
| `.github/agents/owner.md` | Yasser (platform owner) | Start a Copilot session for strategic decisions and backlog work |

---

## 2. MCP (Model Context Protocol) Configuration

### What is MCP?

MCP is a protocol that allows GitHub Copilot (and other AI tools) to call
**external tools** — file system access, GitHub API, Frappe REST API — during
a coding session, instead of relying solely on chat context.

### Configuration file: `.vscode/mcp.json`

The file at `.vscode/mcp.json` configures MCP servers for VS Code and
GitHub Copilot Agent mode. The following servers are configured:

| Server ID | What it does | Prerequisite |
|---|---|---|
| `github` | Full GitHub MCP server via Copilot API — search code, read issues, open PRs | GitHub Copilot subscription |
| `frappe-filesystem` | Read and write files in the workspace — Copilot can reference any project file without copy-paste | `npx` (Node.js installed) |
| `frappe-api` | Fetch HTTP URLs — lets Copilot call the local Frappe REST API during a session | Dev stack running (`bash run.sh up`) |

### How to activate MCP in VS Code

1. Install **GitHub Copilot** extension (v1.220+ for MCP support)
2. Open the repository in VS Code
3. Click the **Copilot Chat** icon → switch to **Agent mode** (the sparkle/agent icon)
4. MCP servers listed in `.vscode/mcp.json` activate automatically
5. In chat, you can now say:
   - `@github search for "lot validation" in this repo`
   - `@frappe-filesystem read infra/docker/docker-compose.yml`
   - `@frappe-api fetch http://localhost:8000/api/resource/Lot`

### Adding a Frappe MCP server (future)

When the `yam_agri_core` app has a REST API layer, add a dedicated Frappe
MCP server:

```json
"frappe-yam": {
  "type": "stdio",
  "command": "python",
  "args": ["-m", "frappe_mcp.server"],
  "env": {
    "FRAPPE_URL": "http://localhost:8000",
    "FRAPPE_API_KEY": "${env:FRAPPE_API_KEY}",
    "FRAPPE_API_SECRET": "${env:FRAPPE_API_SECRET}"
  }
}
```

> **Security note**: never put real API keys in `.vscode/mcp.json`.
> Use `${env:VARIABLE_NAME}` to read from your local environment or VS Code
> secret store — never commit credentials.

---

## 3. Yemen-Specific Local Dev Environment

### Why this matters

Yemen presents real infrastructure risks that affect every developer on this
project:

| Risk | Frequency | Impact on dev |
|---|---|---|
| **Power outages** | Daily (2–8 hours) | Docker containers stop abruptly; data corruption risk |
| **Slow / intermittent internet** | Constant | Cannot pull Docker images at site; `docker pull` hangs |
| **No internet at field sites** | Common | Completely offline dev/demo needed |
| **Low-spec hardware** | Common | 8 GB RAM laptops; cannot run heavy stacks |
| **VPN required for remote access** | When accessing staging | WireGuard setup needed |

### Setup for a developer starting fresh (with internet)

Run these steps **before** travelling to a site or when you have good connectivity:

```bash
# 1. Clone the repository
git clone https://github.com/YasserAKareem/yam_agri_core.git
cd yam_agri_core/infra/docker

# 2. Copy and configure the environment file
cp .env.example .env
# Edit .env — change FRAPPE_SITE, ADMIN_PASSWORD, etc.

# 3. Pull all Docker images AND save them as an offline archive
bash run.sh prefetch
# This creates ./offline-images.tar (may be 2–4 GB)
# Copy this .tar to a USB drive or shared folder for offline use

# 4. Start the stack normally
bash run.sh up

# 5. Initialise the Frappe site (first time only)
bash run.sh init
```

### Starting the stack with NO internet (offline / field site)

```bash
cd yam_agri_core/infra/docker

# Ensure offline-images.tar is present (copy from USB or shared folder)
ls -lh offline-images.tar

# Load images and start the stack
bash run.sh offline-init

# Initialise the Frappe site
bash run.sh init
```

### After a power cut or ungraceful shutdown

Docker containers may not restart automatically after an unexpected power
loss. Run these steps when power is restored:

```bash
cd yam_agri_core/infra/docker

# 1. Check what happened
bash run.sh status

# 2. If containers stopped, restart them
bash run.sh up

# 3. If the database is corrupted (MariaDB crash recovery needed):
#    a. Stop everything
bash run.sh down
#    b. Start only the database to let InnoDB crash-recovery run
docker compose -f docker-compose.yaml up db
#    c. Watch logs; once MariaDB says "ready for connections", restart all
bash run.sh up
```

> **Prevention**: The `docker-compose.yaml` uses `restart: always` on all
> services so they come back automatically after a clean power-restore reboot.
> The risk is **mid-write corruption** — see the backup section below.

### Backup and restore

Run a backup before any risky operation (migrations, resets, Yemen site visits):

```bash
# Create a timestamped backup in ./backups/
bash run.sh backup

# List available backups
ls -lt ./backups/

# Restore the most recent backup
bash run.sh restore

# Restore a specific backup
bash run.sh restore ./backups/20260222_0800/
```

Backup files are stored in `./backups/` (excluded from Git via `.gitignore`).
**Copy the `./backups/` directory to an external drive** before transporting
the laptop to a field site.

### Memory budget (8 GB laptop)

Keep the total Docker memory usage under 6 GB:

| Service | Approximate RAM |
|---|---|
| MariaDB 10.6 | ~400 MB |
| Redis (×3) | ~50 MB each |
| Frappe/ERPNext worker | ~1.5–2 GB |
| nginx | ~50 MB |
| **Total** | **~2.5–3 GB** |

If you see the system becoming sluggish, stop non-essential services:

```bash
# Stop only mock services to free memory
docker compose -f docker-compose.yaml stop mock_iot mock_scale
```

### VPN access (remote / staging)

The staging server is accessible only via **WireGuard VPN**:

1. Install WireGuard: `sudo apt install wireguard` (Linux) or download from wireguard.com
2. Request a WireGuard peer config from the IT admin (U7 — Ibrahim Al-Sana'ani)
3. Activate: `sudo wg-quick up <config-name>`
4. The staging Frappe site will be accessible at `yam-staging.vpn.internal`

> **Never share your WireGuard private key.** Each developer has a unique peer.

### Low-bandwidth tips

| Situation | What to do |
|---|---|
| Pulling images slowly | Use `bash run.sh prefetch` in advance on a fast connection |
| Pushing large PRs on 3G | Use `git push --no-verify` for draft PRs; enable compression: `git config --global core.compression 9` |
| Cloning slowly | Use shallow clone: `git clone --depth 1 ...` then `git fetch --unshallow` later |
| GitHub Actions slow/failing | Check CI logs via the GitHub MCP server in Copilot Agent mode |

---

## 4. New Agent Creation Guide (for future team members)

When a new team member joins, follow these steps to create their agent:

### Step 1 — Determine their role

| Role | Base agent file to copy | Customise |
|---|---|---|
| Frontend/mobile developer | `developer.md` | Add React Native / PWA specifics |
| Data engineer | `developer.md` | Add Qdrant, MariaDB pipeline specifics |
| Field IT technician | `devops.md` | Add Raspberry Pi / Field Hub specifics |
| Agronomist | `qa-manager.md` | Add crop-specific QC thresholds |
| Customer success | `owner.md` | Scope to customer-facing portal only |

### Step 2 — Create the agent file

```bash
cp .github/agents/developer.md .github/agents/<role>.md
# Edit: change "Your role" section, update DocType list, update "must NOT do" rules
```

### Step 3 — Add to CODEOWNERS

Update `.github/CODEOWNERS` to add the new team member's GitHub username
to the paths they own.

### Step 4 — Add as a GitHub collaborator

Follow Section 1 of `docs/GITHUB_SETUP_BLUEPRINT.md` to add them with the
appropriate permission level.

### Step 5 — Validate their local dev setup

Ask them to run through the **"Starting fresh (with internet)"** steps in
Section 3 of this document, and confirm:
- [ ] `bash run.sh up` succeeds
- [ ] `bash run.sh init` succeeds
- [ ] They can log in to the Frappe desk at `http://localhost:8000/desk`
- [ ] `bash run.sh backup` produces a file in `./backups/`

---

## 5. AI Safety Reminder

All agent instruction files enforce this rule — it is non-negotiable:

> **AI is assistive only. It suggests; humans decide and execute.**

No agent, MCP server call, or automated workflow may:
- Automatically accept or reject a grain lot
- Issue a product recall without human confirmation
- Send customer communications autonomously
- Bypass site-level data isolation
- Commit or deploy to production without human review

This applies in Copilot chat sessions, MCP tool calls, and all GitHub Actions
workflows.
