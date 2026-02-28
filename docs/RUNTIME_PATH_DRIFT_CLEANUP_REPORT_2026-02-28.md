# Runtime Path Drift Cleanup Report

- Date: 2026-02-28
- Scope: Plan "Runtime Path Drift Cleanup" (Windows/WSL/Docker + MCP launch stability)
- Commit: `6aa569fc59763cdc6128ea095e715676a17fb196`
- Status: Completed (Phase 1 + Phase 2)

## 1) Issues Identified

1. MCP startup fragility on Windows due to direct `npx` stdio command resolution.
2. Runtime contract drift between `.yml` and `.yaml` compose naming in scripts/docs.
3. Ops docs using non-existent compose service name `frappe` instead of `backend`.
4. No automated CI guard to prevent reintroduction of the above drifts.

## 2) Scan Result

### Executed checks

- `python tools/check_runtime_consistency.py` → `Runtime consistency check: OK`
- `ruff check tools/check_runtime_consistency.py tools/mcp/launch_mcp.py` → `All checks passed!`
- JSON grep: direct MCP `"command": "npx"` → no matches.
- Markdown grep: `docker compose ... logs/restart ... frappe` → no matches in first-party docs.

### Residual references (intentional / non-blocking)

- `docker-compose.yaml` remains in fallback logic in:
  - `infra/docker/run.sh`
  - `infra/docker/preflight.sh`
- Architecture reference includes environment file:
  - `docs/C4 model Architecture v1.1/08_DEPLOYMENT_DEV.md` references
    `environments/dev/docker-compose.yaml` (expected).

## 3) Options Considered

### Option A — Keep direct `npx` in MCP config

- Pros: simplest config.
- Cons: unstable on Windows path resolution in VS Code stdio launch.

### Option B — Switch MCP stdio command to Python launcher (selected)

- Pros: deterministic cross-platform launch (`npx.cmd` on Windows, `npx` elsewhere).
- Cons: adds one helper script.

### Option C — Enforce strict `.yml` only with no fallback

- Pros: maximum standardization.
- Cons: breaks local setups still using `.yaml` naming.

### Option D — `.yml` canonical + `.yaml` fallback (selected)

- Pros: stable standard + backward compatibility.
- Cons: minor dual-path handling in scripts.

## 4) Decisions

1. Use `infra/docker/docker-compose.yml` as canonical dev compose contract.
2. Keep `.yaml` fallback in script logic for compatibility only.
3. Route MCP package startup through `tools/mcp/launch_mcp.py`.
4. Add CI guard script (`tools/check_runtime_consistency.py`) and run it in CI.
5. Standardize first-party operations docs to `backend` service naming.

## 5) Work Done

### Runtime + MCP

- Updated `.vscode/mcp.json` to use Python launcher for:
  - `frappe-filesystem`
  - `frappe-api`
- Added `tools/mcp/launch_mcp.py`.

### Compose contract

- Updated defaults to `.yml` first in:
  - `infra/docker/run.sh`
  - `infra/docker/preflight.sh`

### Documentation alignment

- Updated runtime policy and compose references in:
  - `README.md`
  - `docs/AGENTS_AND_MCP_BLUEPRINT.md`
  - `docs/Docs v1.1/08_DEPLOYMENT_GUIDE.md`
  - `docs/Docs v1.1/09_OPERATIONS_RUNBOOK.md`
- Corrected invalid service commands in operations runbook:
  - `frappe` → `backend`

### Guardrails

- Added `tools/check_runtime_consistency.py`.
- Added CI step in `.github/workflows/ci.yml`:
  - `Runtime consistency check (MCP + compose contract)`

## 6) Result

- Runtime path drift risk reduced for Windows/WSL/Docker and MCP startup.
- First-party runtime docs and scripts now share a single canonical contract.
- CI now blocks regressions for core drift classes covered by the guard script.

## 7) Validation

### Command evidence

```text
python tools/check_runtime_consistency.py
Runtime consistency check: OK

ruff check tools/check_runtime_consistency.py tools/mcp/launch_mcp.py
All checks passed!
```

### Commit evidence

- Commit: `6aa569fc59763cdc6128ea095e715676a17fb196`
- Message: `fix(runtime): stabilize MCP launch and enforce compose contract`
- Files changed: 10

## 8) Follow-up Options

1. Extend guard script to validate compose service names against `docker compose config --services` dynamically.
2. Add a markdown quality check to CI for key runbooks (`README.md`, `docs/Docs v1.1/*`, `docs/AGENTS_AND_MCP_BLUEPRINT.md`).
3. Add a small troubleshooting section in `README.md` for MCP launcher dependency checks (`python`, `node`, `npx`).
