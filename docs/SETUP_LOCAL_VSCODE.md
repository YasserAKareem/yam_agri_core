# Setting Up the Frappe Skill Agent in Local VS Code

> **Audience:** Complete beginners — no prior Frappe or Python experience needed.
> **Time:** ~10 minutes (first time); 2 minutes every time after.

---

## What you will have at the end

- VS Code opens the YAM Agri Core project with all settings pre-configured.
- Press **Ctrl+Shift+B** (or Cmd+Shift+B on Mac) → the **Frappe Skill Agent** runs and tells you every rule violation in the codebase.
- GitHub Copilot knows your role and the project rules automatically.

---

## Step 1 — Install the prerequisites

You only do this once per machine.

### 1a. Install Python 3.10 or newer

1. Go to <https://www.python.org/downloads/>
2. Click the big yellow **"Download Python 3.x.x"** button.
3. Run the installer. On the first screen, **check "Add Python to PATH"** before clicking Install.
4. Open a terminal and verify:
   ```
   python --version
   ```
   You should see `Python 3.10.x` or higher.

### 1b. Install Git

1. Go to <https://git-scm.com/downloads>
2. Download and run the installer (accept all defaults).
3. Verify:
   ```
   git --version
   ```

### 1c. Install VS Code

1. Go to <https://code.visualstudio.com/>
2. Download and run the installer (accept all defaults).

---

## Step 2 — Clone the repository

1. Open a terminal (on Windows: search for "Command Prompt" or "PowerShell").
2. Navigate to the folder where you want to store the project, e.g.:
   ```
   cd C:\Projects
   ```
3. Clone:
   ```
   git clone https://github.com/YasserAKareem/yam_agri_core.git
   ```
4. Move into the project folder:
   ```
   cd yam_agri_core
   ```

---

## Step 3 — Open the project in VS Code

```
code .
```

> If `code` is not found on Windows, open VS Code manually and use
> **File → Open Folder…** to open the `yam_agri_core` folder.

VS Code opens. You will see a pop-up in the bottom-right corner:
> **"Do you want to install the recommended extensions for this repository?"**

Click **Install** — this installs:

| Extension | What it does |
|-----------|-------------|
| **GitHub Copilot** | AI coding assistant (requires a free GitHub account) |
| **GitHub Copilot Chat** | Chat with Copilot inside VS Code |
| **Python** | Python language support, syntax highlighting |
| **Debugpy** | Python debugger |
| **Ruff** | Auto-formats Python code on save and highlights lint errors |

> **No pop-up?** Go to the Extensions sidebar (Ctrl+Shift+X), search each name above, and install manually.

---

## Step 4 — Run the Frappe Skill Agent

### The easy way (keyboard shortcut)

1. Make sure the `yam_agri_core` folder is open in VS Code.
2. Press **Ctrl+Shift+B** (Windows/Linux) or **Cmd+Shift+B** (Mac).
3. If VS Code asks "Select a task to run", choose:
   **"Frappe Skill Agent: Run (text report)"**

The Terminal panel opens at the bottom and the agent runs. It takes about 3–5 seconds.

### What the output looks like

**When there are no critical/high problems (✅ PASSED):**
```
========================================================================
  Frappe Skill QC Agent — Report
  Result   : ✅ PASSED
  Findings : 5 total  (critical:0  high:0  medium:4  low:1)
========================================================================
```
→ Safe to open a Pull Request.

**When there are problems (❌ FAILED):**
```
========================================================================
  Frappe Skill QC Agent — Report
  Result   : ❌ FAILED
  Findings : 12 total  (critical:2  high:3  medium:5  low:2)
========================================================================

[CRITICAL] FS-001 · apps/.../lot.py:42
  frappe.throw() called with raw string not wrapped in _()
  Fix: change frappe.throw("message") → frappe.throw(_("message"))
```
→ Fix the `critical` and `high` findings before opening a PR.

### Other ways to run the agent

| Method | How |
|--------|-----|
| Menu | **Terminal → Run Task… → Frappe Skill Agent: Run (text report)** |
| Terminal | `python tools/frappe_skill_agent.py` |
| Verbose (see full fix steps) | `python tools/frappe_skill_agent.py --verbose` |
| JSON output (for scripts) | `python tools/frappe_skill_agent.py --format json` |

---

## Step 5 — Use Copilot to fix a finding

If the agent reports a violation and you don't know how to fix it:

1. Open **Copilot Chat** — click the chat bubble icon in the left sidebar, or press **Ctrl+Shift+I** (Windows/Linux) / **Cmd+Shift+I** (Mac).
2. Click the **📎 paperclip** icon → **"Prompt…"** → pick **"frappe-skill-agent"**.

   > This loads all the agent documentation and rule descriptions into Copilot automatically.

3. Paste the finding into the chat:
   ```
   [CRITICAL] FS-001 · apps/yam_agri_core/.../lot.py:42
   frappe.throw() called with raw string not wrapped in _()
   ```
4. Ask: **"How do I fix this?"**

Copilot will show you the exact line to change.

---

## Step 6 — Choose your role prompt (optional but recommended)

The repo has 4 additional prompts for different team roles.
Use these to get more focused Copilot answers:

| Your role | Prompt to pick |
|-----------|---------------|
| Writing Python / JS code | `developer` |
| Docker / CI / infrastructure | `devops` |
| QA / food safety / certificates | `qa-manager` |
| Business owner / dashboards | `owner` |

In Copilot Chat → 📎 → "Prompt…" → choose the one that matches your role.

---

## Troubleshooting

| Problem | Solution |
|---------|---------|
| `python` not found | Re-install Python and check "Add Python to PATH". Then restart VS Code. |
| `git` not found | Re-install Git (accept defaults). Then restart VS Code. |
| "No tasks found" when pressing Ctrl+Shift+B | Make sure you opened the **root** `yam_agri_core` folder (not a sub-folder). |
| Copilot Chat not available | Sign in to GitHub in VS Code: click the person icon at the bottom-left. |
| Agent exits with code 2 (config error) | Run `python tools/frappe_skill_agent.py --help` in the Terminal and check the error message. |

---

## What's next?

- Fix all `critical` and `high` findings before every Pull Request.
- Read `docs/FRAPPE_SKILL_AGENT.md` for the full rule reference (FS-001 – FS-011).
- See `.vscode/tasks.json` to understand all the available tasks.
