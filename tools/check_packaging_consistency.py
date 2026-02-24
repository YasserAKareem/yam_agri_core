from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps" / "yam_agri_core"
PKG_INIT = APP_DIR / "yam_agri_core" / "__init__.py"
PYPROJECT = APP_DIR / "pyproject.toml"
SETUP = APP_DIR / "setup.py"


def read_package_version() -> str:
    text = PKG_INIT.read_text(encoding="utf-8")
    match = re.search(r"^__version__\s*=\s*[\"']([^\"']+)[\"']", text, re.MULTILINE)
    if not match:
        raise RuntimeError("__version__ not found in package __init__.py")
    return match.group(1)


def check_pyproject() -> list[str]:
    text = PYPROJECT.read_text(encoding="utf-8")
    errors: list[str] = []
    if "build-backend = \"flit_core.buildapi\"" not in text:
        errors.append("pyproject missing flit_core.buildapi backend")
    if "dynamic = [\"version\"]" not in text:
        errors.append("pyproject must declare dynamic version")
    if "name = \"yam_agri_core\"" not in text:
        errors.append("pyproject project.name should be yam_agri_core")
    if "[tool.flit.module]" not in text or "name = \"yam_agri_core\"" not in text:
        errors.append("pyproject missing [tool.flit.module] name = yam_agri_core")
    return errors


def setup_py_version() -> str:
    proc = subprocess.run(
        [sys.executable, "setup.py", "--version"],
        cwd=str(APP_DIR),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"setup.py --version failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def main() -> int:
    errors: list[str] = []

    package_version = read_package_version()
    setup_version = setup_py_version()
    if setup_version != package_version:
        errors.append(
            f"setup.py version ({setup_version}) != package __version__ ({package_version})"
        )

    errors.extend(check_pyproject())

    if errors:
        print("Packaging consistency check FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Packaging consistency check PASSED")
    print(f"version={package_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
