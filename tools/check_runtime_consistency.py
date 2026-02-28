#!/usr/bin/env python3
"""Runtime consistency checks for MCP + Docker compose contract.

This script prevents regressions caused by runtime/path drift across
Windows/WSL/Docker documentation and launch config.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _fail(message: str, failures: list[str]) -> None:
	failures.append(message)


def _read_text(path: Path) -> str:
	return path.read_text(encoding="utf-8")


def check_mcp_config(failures: list[str]) -> None:
	mcp_path = REPO_ROOT / ".vscode" / "mcp.json"
	if not mcp_path.exists():
		_fail("Missing .vscode/mcp.json", failures)
		return

	try:
		data = json.loads(_read_text(mcp_path))
	except json.JSONDecodeError as exc:
		_fail(f"Invalid JSON in .vscode/mcp.json: {exc}", failures)
		return

	servers = data.get("servers", {})
	for server_name, server_def in servers.items():
		if not isinstance(server_def, dict):
			continue
		if server_def.get("type") != "stdio":
			continue
		command = str(server_def.get("command", "")).strip().lower()
		if command == "npx":
			_fail(
				f".vscode/mcp.json server '{server_name}' uses direct 'npx' command; use tools/mcp/launch_mcp.py",
				failures,
			)
		args = server_def.get("args", [])
		if command == "python" and isinstance(args, list):
			if not any(str(arg).replace("\\", "/") == "tools/mcp/launch_mcp.py" for arg in args):
				_fail(
					f".vscode/mcp.json server '{server_name}' uses python without tools/mcp/launch_mcp.py",
					failures,
				)


def check_compose_defaults(failures: list[str]) -> None:
	expected_default = 'DOCKER_COMPOSE_FILE="docker-compose.yml"'
	for rel_path in ["infra/docker/run.sh", "infra/docker/preflight.sh"]:
		path = REPO_ROOT / rel_path
		if not path.exists():
			_fail(f"Missing required file: {rel_path}", failures)
			continue
		content = _read_text(path)
		if expected_default not in content:
			_fail(f"{rel_path} does not default to docker-compose.yml", failures)


def check_doc_references(failures: list[str]) -> None:
	docs_to_check = [
		"README.md",
		"infra/docker/README.md",
		"docs/AGENTS_AND_MCP_BLUEPRINT.md",
		"docs/Docs v1.1/08_DEPLOYMENT_GUIDE.md",
		"docs/Docs v1.1/09_OPERATIONS_RUNBOOK.md",
	]
	for rel_path in docs_to_check:
		path = REPO_ROOT / rel_path
		if not path.exists():
			continue
		content = _read_text(path)
		if "docker-compose.yaml" in content:
			_fail(f"{rel_path} contains non-canonical 'docker-compose.yaml' reference", failures)


def check_first_party_compose_service_usage(failures: list[str]) -> None:
	invalid_service_pattern = re.compile(r"docker compose[^\n]*\brestart\s+frappe\b|docker compose[^\n]*\blogs\s+-f\s+frappe\b", re.IGNORECASE)
	for path in REPO_ROOT.rglob("*.md"):
		rel_path = path.relative_to(REPO_ROOT).as_posix()
		if rel_path.startswith("infra/frappe_docker/"):
			continue
		content = _read_text(path)
		if invalid_service_pattern.search(content):
			_fail(
				f"{rel_path} uses non-existent compose service 'frappe'; use 'backend' or run.sh wrappers",
				failures,
			)


def main() -> int:
	failures: list[str] = []
	check_mcp_config(failures)
	check_compose_defaults(failures)
	check_doc_references(failures)
	check_first_party_compose_service_usage(failures)

	if failures:
		print("Runtime consistency check: FAILED")
		for failure in failures:
			print(f" - {failure}")
		return 1

	print("Runtime consistency check: OK")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
