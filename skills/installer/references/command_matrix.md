# Dependency Install Command Matrix

Use this matrix to choose package-manager install commands after checking lockfiles.

## Precedence Rules

1. Prefer lockfile-specific package managers over generic defaults.
2. Prefer deterministic/immutable modes in CI.
3. Prefer install/sync commands over upgrade/update commands unless asked.

## JavaScript / TypeScript

| Detected files | Manager | Local install | CI install |
| --- | --- | --- | --- |
| `package.json` + `pnpm-lock.yaml` | pnpm | `pnpm install` | `pnpm install --frozen-lockfile` |
| `package.json` + `yarn.lock` | yarn | `yarn install` | `yarn install --immutable` |
| `package.json` + `bun.lock` or `bun.lockb` | bun | `bun install` | `bun install --frozen-lockfile` |
| `package.json` + `package-lock.json` | npm | `npm ci` | `npm ci` |
| `package.json` only | npm | `npm install` | `npm install` |

## Python

| Detected files | Manager | Local install | CI install |
| --- | --- | --- | --- |
| `uv.lock` | uv | `uv sync` | `uv sync --frozen` |
| `poetry.lock` | Poetry | `poetry install` | `poetry install --sync` |
| `Pipfile.lock` | pipenv | `pipenv sync` | `pipenv sync` |
| `Pipfile` only | pipenv | `pipenv install` | `pipenv install` |
| `requirements.txt` | pip | `python -m pip install -r requirements.txt` | `python -m pip install -r requirements.txt` |
| `pyproject.toml` only | uv | `uv sync` | `uv sync --frozen` |

## Other Ecosystems

| Detected files | Manager | Suggested install command |
| --- | --- | --- |
| `go.mod` | Go modules | `go mod download` |
| `Cargo.toml` | Cargo | `cargo fetch` |
| `Gemfile.lock` | Bundler | `bundle install --deployment` |
| `Gemfile` | Bundler | `bundle install` |
| `composer.lock` | Composer | `composer install --no-interaction` |
| `composer.json` | Composer | `composer install` |
| `pom.xml` | Maven | `mvn -B -DskipTests dependency:go-offline` |
| `build.gradle` or `build.gradle.kts` | Gradle | `./gradlew dependencies` |

## Notes

- For monorepos, inspect root and package/service directories separately.
- If multiple ecosystems are present, pick one target install path at a time.
- Run install commands from the directory where the manifest file lives.
