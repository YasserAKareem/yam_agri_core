#!/usr/bin/env python3
"""Detect likely dependency install commands from manifests and lockfiles."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Candidate:
    ecosystem: str
    manager: str
    command: str
    reason: str


def choose_javascript(root: Path, ci: bool) -> list[Candidate]:
    package_json = root / "package.json"
    if not package_json.exists():
        return []

    has_pnpm_lock = (root / "pnpm-lock.yaml").exists()
    has_yarn_lock = (root / "yarn.lock").exists()
    has_bun_lock = (root / "bun.lock").exists() or (root / "bun.lockb").exists()
    has_npm_lock = (root / "package-lock.json").exists() or (root / "npm-shrinkwrap.json").exists()

    if has_pnpm_lock:
        cmd = "pnpm install --frozen-lockfile" if ci else "pnpm install"
        return [Candidate("javascript", "pnpm", cmd, "Detected package.json + pnpm-lock.yaml")]
    if has_yarn_lock:
        cmd = "yarn install --immutable" if ci else "yarn install"
        return [Candidate("javascript", "yarn", cmd, "Detected package.json + yarn.lock")]
    if has_bun_lock:
        cmd = "bun install --frozen-lockfile" if ci else "bun install"
        return [Candidate("javascript", "bun", cmd, "Detected package.json + bun lockfile")]
    if has_npm_lock:
        cmd = "npm ci" if ci else "npm ci"
        return [Candidate("javascript", "npm", cmd, "Detected package.json + npm lockfile")]
    return [Candidate("javascript", "npm", "npm install", "Detected package.json without lockfile")]


def choose_python(root: Path, ci: bool) -> list[Candidate]:
    has_pyproject = (root / "pyproject.toml").exists()
    has_uv_lock = (root / "uv.lock").exists()
    has_poetry_lock = (root / "poetry.lock").exists()
    has_pipfile = (root / "Pipfile").exists()
    has_pipfile_lock = (root / "Pipfile.lock").exists()
    has_requirements = (root / "requirements.txt").exists()

    candidates: list[Candidate] = []
    if has_uv_lock:
        cmd = "uv sync --frozen" if ci else "uv sync"
        candidates.append(Candidate("python", "uv", cmd, "Detected uv.lock"))
        return candidates
    if has_poetry_lock:
        cmd = "poetry install --sync" if ci else "poetry install"
        candidates.append(Candidate("python", "poetry", cmd, "Detected poetry.lock"))
        return candidates
    if has_pipfile or has_pipfile_lock:
        cmd = "pipenv sync" if has_pipfile_lock else "pipenv install"
        candidates.append(Candidate("python", "pipenv", cmd, "Detected Pipfile/Pipfile.lock"))
        return candidates
    if has_requirements:
        candidates.append(
            Candidate(
                "python",
                "pip",
                "python -m pip install -r requirements.txt",
                "Detected requirements.txt",
            )
        )
        return candidates
    if has_pyproject:
        cmd = "uv sync --frozen" if ci else "uv sync"
        candidates.append(Candidate("python", "uv", cmd, "Detected pyproject.toml"))
    return candidates


def choose_go(root: Path) -> list[Candidate]:
    if (root / "go.mod").exists():
        return [Candidate("go", "go", "go mod download", "Detected go.mod")]
    return []


def choose_rust(root: Path) -> list[Candidate]:
    if (root / "Cargo.toml").exists():
        return [Candidate("rust", "cargo", "cargo fetch", "Detected Cargo.toml")]
    return []


def choose_ruby(root: Path) -> list[Candidate]:
    if (root / "Gemfile.lock").exists():
        return [Candidate("ruby", "bundler", "bundle install --deployment", "Detected Gemfile.lock")]
    if (root / "Gemfile").exists():
        return [Candidate("ruby", "bundler", "bundle install", "Detected Gemfile")]
    return []


def choose_php(root: Path) -> list[Candidate]:
    if (root / "composer.lock").exists():
        return [Candidate("php", "composer", "composer install --no-interaction", "Detected composer.lock")]
    if (root / "composer.json").exists():
        return [Candidate("php", "composer", "composer install", "Detected composer.json")]
    return []


def choose_java(root: Path) -> list[Candidate]:
    if (root / "pom.xml").exists():
        return [Candidate("java", "maven", "mvn -B -DskipTests dependency:go-offline", "Detected pom.xml")]
    if (root / "build.gradle").exists() or (root / "build.gradle.kts").exists():
        return [Candidate("java", "gradle", "./gradlew dependencies", "Detected Gradle build file")]
    return []


def find_candidates(root: Path, ci: bool) -> list[Candidate]:
    candidates: list[Candidate] = []
    candidates.extend(choose_javascript(root, ci))
    candidates.extend(choose_python(root, ci))
    candidates.extend(choose_go(root))
    candidates.extend(choose_rust(root))
    candidates.extend(choose_ruby(root))
    candidates.extend(choose_php(root))
    candidates.extend(choose_java(root))
    return candidates


def detect_files(root: Path) -> list[str]:
    markers = [
        "package.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "bun.lock",
        "bun.lockb",
        "package-lock.json",
        "npm-shrinkwrap.json",
        "pyproject.toml",
        "uv.lock",
        "poetry.lock",
        "Pipfile",
        "Pipfile.lock",
        "requirements.txt",
        "go.mod",
        "Cargo.toml",
        "Gemfile",
        "Gemfile.lock",
        "composer.json",
        "composer.lock",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
    ]
    return [name for name in markers if (root / name).exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect dependency install commands from project manifests.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory to inspect (default: current directory).",
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Recommend lockfile-enforcing CI-friendly commands when possible.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.path).resolve()
    if not root.exists() or not root.is_dir():
        print(f"Path is not a directory: {root}")
        return 1

    files = detect_files(root)
    candidates = find_candidates(root, args.ci)

    if args.json:
        data = {
            "path": str(root),
            "ci_mode": args.ci,
            "detected_files": files,
            "recommendations": [asdict(candidate) for candidate in candidates],
        }
        print(json.dumps(data, indent=2))
        return 0

    print(f"Path: {root}")
    if files:
        print("Detected files:")
        for name in files:
            print(f"- {name}")
    else:
        print("Detected files: none")

    if not candidates:
        print("\nNo install plan detected. Inspect subdirectories or provide ecosystem-specific command.")
        return 0

    print("\nRecommended install commands:")
    for candidate in candidates:
        print(f"- [{candidate.ecosystem}/{candidate.manager}] {candidate.command}")
        print(f"  Reason: {candidate.reason}")

    if len(candidates) > 1:
        print("\nMultiple ecosystems were detected. Choose one target before running commands.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
