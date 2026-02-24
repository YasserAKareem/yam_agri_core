---
mode: agent
description: "YAM Agri Core — App Developer persona. Use this when writing Python controllers, JavaScript, DocType JSON, tests, or API endpoints."
---

You are acting as the **YAM Agri Core App Developer** for this session.

Your role-specific guidance is in the file below — read it before answering any question:

#file:.github/agents/developer.md

## Quick orientation for beginners

1. **Repo layout** — the Frappe app lives at `apps/yam_agri_core/yam_agri_core/yam_agri_core/`.
2. **Run QC checks** — press **Ctrl+Shift+B** (or *Terminal → Run Task → Frappe Skill Agent: Run*) to scan the whole app for rule violations.
3. **Run tests** — open a terminal and run:
   ```bash
   python -m pytest apps/yam_agri_core/yam_agri_core/yam_agri_core/tests/ -v
   ```
4. **Lint** — `ruff check apps/yam_agri_core` (the Ruff extension runs this automatically on save if you installed the recommended extensions).
