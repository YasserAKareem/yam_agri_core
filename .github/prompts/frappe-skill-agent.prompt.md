---
mode: agent
description: "Frappe Skill Agent — run or interpret QC scan results. Use this when you want to understand a finding, fix a violation, or add a new rule."
---

You are acting as the **Frappe Skill Agent assistant** for this session.

The full agent documentation is in the file below — read it before answering:

#file:docs/FRAPPE_SKILL_AGENT.md

## What is the Frappe Skill Agent?

A pure-Python QC scanner (`tools/frappe_skill_agent.py`) that reads every
`.py`, `.js`, and `.json` source file in the app and checks them against
11 rules (FS-001 – FS-011) derived from Frappe best practices.
It requires **no running Frappe server** — it works on source files only.

## How to run it (beginner step-by-step)

> **Prerequisite:** Python 3.10+ must be installed on your machine.
> See `docs/SETUP_LOCAL_VSCODE.md` for the full first-time setup walkthrough.

### Option A — keyboard shortcut (easiest)
1. Open this repository folder in VS Code.
2. Press **Ctrl+Shift+B** (Windows/Linux) or **Cmd+Shift+B** (macOS).
3. Select **"Frappe Skill Agent: Run (text report)"** if prompted.
4. The result appears in the VS Code **Terminal** panel at the bottom.

### Option B — VS Code menu
1. Open the menu **Terminal → Run Task…**
2. Click **"Frappe Skill Agent: Run (text report)"**.

### Option C — terminal command
```bash
# From the repo root folder:
python tools/frappe_skill_agent.py
```

## How to read the output

```
Result   : ❌ FAILED          ← there are critical or high findings
Findings : 12 total  (critical:2  high:3  medium:5  low:2)
```

| Icon | Meaning | What to do |
|------|---------|-----------|
| ✅ PASSED | No critical or high findings | Safe to open a PR |
| ❌ FAILED | At least one critical or high finding | Fix before opening a PR |

Each finding shows:
- **Rule ID** (e.g. `FS-001`) — which rule was violated
- **File + line** — exactly where the problem is
- **Message** — what is wrong
- **Planned response** (with `--verbose`) — step-by-step how to fix it

## Common fixes

| Rule | Problem | Fix |
|------|---------|-----|
| FS-001 | `frappe.throw("raw string")` | Wrap in `_()`: `frappe.throw(_("raw string"))` |
| FS-002 | JS string not in `__()` | `frappe.msgprint(__("Hello"))` |
| FS-003 | DocType JSON: `site` field not `reqd: 1` | Add `"reqd": 1` to the site field in the JSON |
| FS-011 | `permission_query_conditions` without `has_permission` | Add both entries to `hooks.py` |

## Ask Copilot for help

After running the agent, paste a finding into this chat and ask:

> "How do I fix FS-001 in this file?"

Copilot will read `docs/FRAPPE_SKILL_AGENT.md` and give you the exact fix.
