# Contributing to YAM Agri Core

Thank you for taking the time to contribute! Please read this guide carefully before opening issues or pull requests.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Reporting Bugs](#reporting-bugs)
4. [Proposing Features](#proposing-features)
5. [Pull Request Process](#pull-request-process)
6. [Coding Standards](#coding-standards)
7. [Commit Messages](#commit-messages)
8. [Security](#security)

---

## Code of Conduct

Be respectful and constructive. Harassment of any kind will not be tolerated.

---

## Getting Started

1. Fork the repository and clone your fork.
2. Copy `environments/dev/.env.example` to `environments/dev/.env` and fill in your values.
3. Start the dev environment:
   ```bash
   bash infra/docker/run.sh up
   ```
4. Install pre-commit hooks:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

---

## Reporting Bugs

Use the **Bug Report** issue template. Include:

- Environment (dev / staging / production)
- Steps to reproduce
- Expected vs actual behaviour
- Relevant logs or screenshots
- Confirm the report contains **no passwords, tokens, or secrets**

---

## Proposing Features

Use the **Feature Request** issue template. Link to the relevant backlog item in
`docs/20260222 YAM_AGRI_BACKLOG v1.csv` when one exists. Write a clear acceptance
criterion so reviewers know when the feature is done.

---

## Pull Request Process

### Which branch

All PRs should target `main` unless a hotfix targeting `staging` has been
explicitly agreed with the maintainer.

### PR title

Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):

```
<type>(<scope>): <short description>
```

Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`, `infra`, `perf`, `revert`.

Example: `feat(lot): add split workflow`

### Checklist

Before opening a PR confirm:

- [ ] Branch is up-to-date with `main`
- [ ] All pre-commit hooks pass (`pre-commit run --all-files`)
- [ ] Tests added or updated for the change
- [ ] No `.env` files with real credentials committed
- [ ] Documentation updated where necessary
- [ ] For UI changes: screenshots or animated GIF attached
- [ ] For server-side logic: business logic is in the Python controller (not JS only)
- [ ] For schema changes: migration patch included

### Test cases

Add at least one test (unit or integration) per new function. Place tests under
`apps/yam_agri_core/yam_agri_core/yam_agri_core/tests/` (Frappe convention: tests live inside the
app module).

Run pure-Python tests (fast, no DB):
```bash
python -m pytest apps/yam_agri_core/yam_agri_core/yam_agri_core/tests/ -v
```

Run Frappe integration tests (requires Docker stack):
```bash
bash infra/docker/run.sh bench --site localhost run-tests --app yam_agri_core
```

---

## Coding Standards

This project follows the
[Frappe / ERPNext Coding Standards](https://github.com/frappe/erpnext/wiki/Coding-Standards).
Key rules:

### Python

- **Indentation**: Tabs (Frappe convention, enforced by `ruff format`)
- **Line length**: 110 characters max
- **Imports**: sorted by `ruff` (stdlib → third-party → local)
- All user-facing strings must be wrapped in `frappe._("")`
- Business logic belongs in the Python controller, not JavaScript
- Functions over ~10 lines should be broken into smaller helpers
- Do **not** use `frappe.db.sql` with string formatting — use query builder or parameterised queries
- Use `frappe.get_all` / `frappe.db.get_value` instead of raw SQL where possible

### DocType / Model design

- DocType names: **Title Case, Singular** (e.g. "Scale Ticket", not "ScaleTickets")
- Transaction DocTypes must use `autoname: "naming_series:"` with series `YAM-[ABBREV]-.YYYY.-`
- Master DocTypes (Site, Device, YAM Plot) use user-defined names
- Every DocType must have a `title_field` set to the most human-readable field
- Every record **must** have a `site` link — site isolation is non-negotiable
- No hard-coded role names in business logic (use `frappe.has_role`)

### Security

- **Never commit** `.env` files with real credentials
- Use `.env.example` as a template only
- Follow the [Code Security Guidelines](https://github.com/frappe/erpnext/wiki/Code-Security-Guidelines)
- AI features must be **assistive only** — no automatic lot accept/reject, recalls, or unsupervised customer communications
- AI gateway must redact PII, pricing, and customer IDs before any external LLM call

---

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0-beta.2/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

The PR title check in CI enforces this format automatically.

---

## Security

If you discover a security vulnerability please **do not** open a public issue.
Contact the maintainer directly. See the
[Code Security Guidelines](https://github.com/frappe/erpnext/wiki/Code-Security-Guidelines)
for background.
