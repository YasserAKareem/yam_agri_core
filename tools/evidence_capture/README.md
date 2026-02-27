# Evidence Capture Prerequisites

This folder contains browser-based evidence scripts (Playwright) and JSON scenarios.

## Before Running

1. Ensure the docker stack is up:
   - `bash infra/docker/run.sh up`
2. Verify Desk login is reachable:
   - `curl -I http://localhost:8000/login`
   - Expect `HTTP/1.1 200` (not `502`).
3. Install Playwright for local Python:
   - `python3 -m pip install --user --break-system-packages playwright`
   - `~/.local/bin/playwright install chromium`

## Linux Shared Libraries

On minimal Linux hosts, Playwright Chromium may fail with missing:
- `libnspr4.so`
- `libnss3.so`
- `libasound.so.2`

Install OS packages if available (example: Ubuntu):
- `libnspr4`, `libnss3`, `libasound2t64`

If `apt install` is not available, provide these libraries via `LD_LIBRARY_PATH`
before running the collector.

## Run Collector

Example:

```bash
python3 tools/evidence_capture/run_evidence_collector.py \
  --scenario tools/evidence_capture/scenario.at01_at10.json
```

## Common Recovery

If `/login` returns `502` after backend/container recreation:
- restart frontend so nginx refreshes upstream target:
  - `docker compose -f infra/docker/docker-compose.yml restart frontend`

