#!/usr/bin/env python3
"""Launch Node-based MCP servers in a cross-platform way.

This wrapper avoids Windows PATH issues where VS Code may fail to resolve `npx`
in stdio server definitions. It prefers `npx.cmd` on Windows and `npx` elsewhere.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _find_npx() -> str | None:
	candidates = ["npx.cmd", "npx"] if os.name == "nt" else ["npx"]
	for candidate in candidates:
		resolved = shutil.which(candidate)
		if resolved:
			return resolved
	return None


def main() -> int:
	if len(sys.argv) < 2:
		print("Usage: launch_mcp.py <npm-package> [package-args...]", file=sys.stderr)
		return 2

	npx_bin = _find_npx()
	if not npx_bin:
		print("ERROR: npx was not found. Install Node.js (includes npm/npx).", file=sys.stderr)
		return 127

	package_name = sys.argv[1]
	package_args = sys.argv[2:]
	command = [npx_bin, "-y", package_name, *package_args]

	completed = subprocess.run(command, check=False)
	return completed.returncode


if __name__ == "__main__":
	raise SystemExit(main())
