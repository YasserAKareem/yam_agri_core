---
name: installer
description: Detect and run the safest dependency installation workflow for a project by reading manifests and lockfiles. Use when a user asks to set up a repo, install dependencies, bootstrap a dev environment, resolve missing packages, or choose the correct package-manager install command.
---

# Installer

## Overview

Identify dependency manifests, choose lockfile-aware install commands, and execute setup with minimal side effects.

## Workflow

1. Detect project files before running install commands.
   - Run `python scripts/detect_install_plan.py .` in the target directory.
   - Use `python scripts/detect_install_plan.py . --ci` for CI-safe recommendations.
2. Resolve ambiguity early.
   - If multiple ecosystems or package managers are detected, ask which one to install first.
   - For monorepos, run detection at the workspace root and relevant package/service directories.
3. Prefer deterministic commands.
   - Use lockfile-enforcing commands in CI and when reproducibility is required.
   - Avoid upgrade-style commands (`npm update`, `pip install -U`, etc.) unless explicitly requested.
4. Execute installation in the correct directory.
   - Run only the minimum required command.
   - Avoid `sudo` or global installs unless the user explicitly asks.
5. Verify completion.
   - Run a lightweight check (for example `npm -v`, `python -m pip --version`, `go env GOPATH`) if the user asked for verification.
   - Report command output summaries and any failures with next troubleshooting action.

## Command Selection Rules

- Prefer lockfile-specific commands when lockfiles exist.
- Prefer the package manager implied by lockfiles over heuristics.
- Choose one primary install path at a time, then confirm before running secondary paths.
- Read [references/command_matrix.md](references/command_matrix.md) for command guidance and precedence.

## Resources

- `scripts/detect_install_plan.py`: Detect manifests/lockfiles and print recommended commands.
- `references/command_matrix.md`: Lockfile-aware command matrix and precedence rules.
