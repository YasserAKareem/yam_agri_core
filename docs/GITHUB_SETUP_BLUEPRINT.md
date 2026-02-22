# GitHub Setup Blueprint — YAM Agri Core

> **Who is this for?** The repository owner (YasserAKareem) and any future
> team members who need to configure the GitHub repository settings for the
> YAM Agri platform.
>
> **What does it cover?** Everything you need to configure once on GitHub.com
> to enforce the roles, code-review process, and security policies described
> in the Blueprint Playbook.

---

## 1. Teams and Roles

Create the following **GitHub Teams** under your organization
(or manage as collaborators on a personal repo).

| Team / Role | GitHub permission level | Responsibilities |
|---|---|---|
| `owner` | **Admin** | Full control — Yasser only |
| `devops` | **Write** | `infra/`, `environments/`, Docker, CI/CD |
| `qa-manager` | **Write** | `environments/production/`, certificates, QCTest, approvals |
| `developer` | **Write** | Application code, DocTypes, migrations |
| `viewer` | **Read** | Stakeholders, auditors — read-only |

### How to create teams (organization repo)

1. Go to **github.com/YasserAKareem** → **Your organizations** → your org
2. Click **Teams** → **New team**
3. Add the team name and set parent if needed
4. Invite members and set their role

### How to add collaborators (personal repo)

1. Repo → **Settings** → **Collaborators and teams**
2. Click **Add people** → enter GitHub username → choose permission level

---

## 2. Branch Protection Rules

Set these rules under **Settings → Branches → Add rule**.

### 2.1 `main` branch (production-ready code)

| Setting | Value |
|---|---|
| Branch name pattern | `main` |
| Require a pull request before merging | ✅ Enabled |
| Required number of approvals | **1** (increase to 2 when team grows) |
| Dismiss stale reviews on new commits | ✅ Enabled |
| Require review from Code Owners | ✅ Enabled |
| Require status checks to pass before merging | ✅ Enabled |
| Required status checks | `CI / Secret scan`, `CI / YAML lint`, `CI / Docker Compose validate`, `PR Review Checks / PR title format` |
| Require branches to be up to date before merging | ✅ Enabled |
| Require conversation resolution before merging | ✅ Enabled |
| Restrict who can push to matching branches | ✅ Only `owner` role |
| Allow force pushes | ❌ Disabled |
| Allow deletions | ❌ Disabled |

### 2.2 `staging` branch

| Setting | Value |
|---|---|
| Branch name pattern | `staging` |
| Require a pull request before merging | ✅ Enabled |
| Required number of approvals | **1** |
| Require status checks to pass | ✅ Enabled (same checks as `main`) |
| Allow force pushes | ❌ Disabled |

### 2.3 Feature / fix branches

Use the naming convention:

```
feat/<short-description>        # new features
fix/<short-description>         # bug fixes
chore/<short-description>       # maintenance / tooling
infra/<short-description>       # infrastructure changes
docs/<short-description>        # documentation only
```

No branch protection rules are required for feature branches.

---

## 3. Repository Settings

Go to **Settings → General** and configure:

| Setting | Recommended value |
|---|---|
| Default branch | `main` |
| Allow merge commits | ✅ (with squash message) |
| Allow squash merging | ✅ (default — keeps history clean) |
| Allow rebase merging | ❌ Disabled (avoid divergent history) |
| Automatically delete head branches | ✅ Enabled |
| Issues | ✅ Enabled |
| Projects | ✅ Enabled (for backlog management) |
| Wiki | Optional |

---

## 4. Code Review Process

### 4.1 Pull Request flow

```
feature branch  →  PR to main  →  CI checks  →  Code review  →  Merge
```

1. Developer opens a PR using the **PR template** (`.github/pull_request_template.md`)
2. CI runs automatically:
   - Secret scan
   - YAML lint
   - Docker Compose validation
   - PR title format check
3. **CODEOWNERS** automatically requests review from the right person
4. Reviewer approves (or requests changes)
5. All conversations must be resolved
6. Squash-merge into `main`

### 4.2 High-risk changes (production configs)

Any change under `environments/production/` requires:
- Review and approval from **QA Manager** (or owner)
- A rollback plan documented in the PR body
- Successful staging test run referenced in the PR

### 4.3 Review etiquette

| Action | Guideline |
|---|---|
| Approval | Only approve if you have actually read and tested the change |
| Request changes | Be specific — reference the line, explain the problem, suggest a fix |
| Comments | Prefix with `nit:` for non-blocking style notes |
| Response time | Aim to review within **1 business day** |

---

## 5. Labels

Create the following labels under **Issues → Labels**:

| Label | Colour | Purpose |
|---|---|---|
| `bug` | `#d73a4a` | Confirmed bugs |
| `enhancement` | `#a2eeef` | New feature requests |
| `documentation` | `#0075ca` | Docs only |
| `infra` | `#e4e669` | Infrastructure / DevOps |
| `environments` | `#bfd4f2` | Environment config changes |
| `github-config` | `#c5def5` | .github/ changes |
| `production` | `#e11d48` | Touches production configs |
| `security` | `#b60205` | Security-related (exempt from stale) |
| `needs-triage` | `#ededed` | New issue, not yet reviewed |
| `in-progress` | `#fbca04` | Being worked on (exempt from stale) |
| `blocked` | `#e4e669` | Blocked by external dependency |
| `pinned` | `#0052cc` | Keep open indefinitely |
| `stale` | `#cccccc` | Auto-applied by stale bot |
| `wontfix` | `#ffffff` | Will not be addressed |

### Quick setup via GitHub CLI

```bash
gh label create bug         --color d73a4a --description "Confirmed bugs"
gh label create enhancement --color a2eeef --description "New feature requests"
gh label create documentation --color 0075ca --description "Docs only"
gh label create infra       --color e4e669 --description "Infrastructure / DevOps"
gh label create environments --color bfd4f2 --description "Environment config changes"
gh label create github-config --color c5def5 --description ".github/ changes"
gh label create production  --color e11d48 --description "Touches production configs"
gh label create security    --color b60205 --description "Security-related"
gh label create needs-triage --color ededed --description "New issue, not yet reviewed"
gh label create in-progress --color fbca04 --description "Being worked on"
gh label create blocked     --color e4e669 --description "Blocked by external dependency"
gh label create pinned      --color 0052cc --description "Keep open indefinitely"
gh label create stale       --color cccccc --description "Auto-applied by stale bot"
gh label create wontfix     --color ffffff --description "Will not be addressed"
```

---

## 6. GitHub Actions Workflows (what is installed)

| Workflow file | Trigger | What it does |
|---|---|---|
| `.github/workflows/ci.yml` | Push / PR to `main`, `staging` | Secret scan, YAML lint, Docker Compose validation, env config check |
| `.github/workflows/pr_review.yml` | PR opened / edited / synchronised | Title format check, PR size warning, auto-label |
| `.github/workflows/stale.yml` | Daily cron + manual | Marks stale issues after 30 days, stale PRs after 14 days, closes after 7 more days |

### Required Actions permissions

Go to **Settings → Actions → General**:

| Setting | Value |
|---|---|
| Actions permissions | Allow all actions (or restrict to trusted publishers) |
| Workflow permissions | **Read repository contents** (default); `pr_review.yml` needs `pull-requests: write` — already set in the workflow file |
| Allow GitHub Actions to create PRs | ✅ Enabled (needed by `actions/labeler`) |

---

## 7. Secrets and Variables

Go to **Settings → Secrets and variables → Actions**.

No secrets are required for the current workflows (they use only
`GITHUB_TOKEN` which is provided automatically).

When you add deployment workflows in the future, add environment-specific
secrets here — **never** in the repository code.

| Future secret name | Scope | Purpose |
|---|---|---|
| `STAGING_SSH_KEY` | Repository | Deploy to staging server |
| `PROD_SSH_KEY` | Environment: production | Deploy to production (locked to `main` branch only) |
| `FRAPPE_ADMIN_PASSWORD` | Environment: staging / production | Set at site init |

---

## 8. Environments (for deployment workflows)

Set up **GitHub Environments** under **Settings → Environments**:

### `staging` environment

- **Protection rules:** No required reviewers (auto-deploy from `staging` branch)
- **Deployment branches:** Only `staging` branch
- **Secrets:** `STAGING_SSH_KEY`, etc.

### `production` environment

- **Protection rules:** Required reviewers — add `qa-manager` and `owner`
- **Deployment branches:** Only `main` branch
- **Wait timer:** 5 minutes (grace period to cancel accidental deployments)
- **Secrets:** `PROD_SSH_KEY`, `FRAPPE_ADMIN_PASSWORD`, etc.

---

## 9. Security Settings

Go to **Settings → Security**:

| Feature | Setting |
|---|---|
| Private vulnerability reporting | ✅ Enable |
| Dependency graph | ✅ Enable |
| Dependabot alerts | ✅ Enable |
| Dependabot security updates | ✅ Enable |
| Secret scanning | ✅ Enable (available on public repos and GitHub Advanced Security) |
| Push protection | ✅ Enable (blocks commits containing secrets) |

---

## 10. CODEOWNERS Summary

The `.github/CODEOWNERS` file automatically assigns reviewers:

| Path | Required reviewer |
|---|---|
| `*` (default) | `@YasserAKareem` |
| `infra/` | `@YasserAKareem` |
| `environments/dev/` | `@YasserAKareem` |
| `environments/staging/` | `@YasserAKareem` |
| `environments/production/` | `@YasserAKareem` (update when QA Manager joins) |
| `.github/` | `@YasserAKareem` |
| `docs/` | `@YasserAKareem` |

> **When your team grows:** Replace `@YasserAKareem` with team handles such as
> `@YasserAKareem/devops`, `@YasserAKareem/qa-manager`, etc.
> Update `.github/CODEOWNERS` accordingly.

---

## 11. Recommended GitHub Apps (optional)

| App | Purpose | Link |
|---|---|---|
| **GitGuardian** | Real-time secret detection in PRs | https://www.gitguardian.com |
| **Codecov** | Code coverage reports (when tests are added) | https://codecov.io |
| **Renovate** | Automated dependency updates | https://github.com/apps/renovate |

---

## 12. First-Time Setup Checklist

Use this checklist the first time you configure the repository on GitHub:

- [ ] Create teams / add collaborators (Section 1)
- [ ] Set default branch to `main` (Section 3)
- [ ] Add branch protection rule for `main` (Section 2.1)
- [ ] Add branch protection rule for `staging` (Section 2.2)
- [ ] Create all labels (Section 5)
- [ ] Enable GitHub Actions with correct permissions (Section 6)
- [ ] Set up `staging` and `production` GitHub Environments (Section 8)
- [ ] Enable Dependabot alerts and secret scanning (Section 9)
- [ ] Verify CI workflow passes on a test PR
- [ ] Verify PR title check rejects a bad title
- [ ] Verify CODEOWNERS triggers a review request
