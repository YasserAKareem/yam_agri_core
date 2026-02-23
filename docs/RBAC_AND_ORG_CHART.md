# RBAC Baseline + Org Chart Mapping (No Role Duplication)

## Goal
Use the **standard ERPNext/Frappe roles** (segregation-of-duties aware) as the baseline for all YAM Agri development.

- We **do not duplicate** roles like `Stock User`, `Quality Manager`, `Agriculture Manager`, etc.
- We model your **human roles** (job functions in the org chart) using **Role Profiles** and **User Permissions**.
- We enforce platform rules:
  - **Site isolation by default** (users do not see other sites’ data)
  - **High-risk actions require approval** (QA Manager / Quality Manager)
  - AI is **assistive only** (no unsupervised accept/reject/recall/customer comms)

## Baseline Roles (ERPNext/Frappe)
Treat these as the canonical set for permissions design:

- Accounts Manager, Accounts User
- Administrator
- Agriculture Manager
- Auditor
- Delivery Manager, Delivery User
- Employee, Employee Self Service
- HR User
- Item Manager
- Maintenance Manager, Maintenance User
- Manufacturing Manager, Manufacturing User
- Projects Manager, Projects User
- Purchase Manager, Purchase Master Manager, Purchase User
- Quality Manager
- Sales Manager, Sales Master Manager, Sales User
- Stock Manager, Stock User
- Supplier
- Support Team
- System Manager
- Website Manager

## “Human Roles” = Role Profiles (Subsets)
Frappe roles are not hierarchical. The clean pattern is:

- **Role** = permission primitive (from the baseline set)
- **Role Profile** = “human role” bundle (subset of baseline roles)
- **User** = assigned one or more role profiles + direct roles (rare)

Examples (illustrative; finalize from your org chart):

- **YAM Farm Ops (Field)**: `Agriculture Manager` + `Stock User`
- **YAM Warehouse**: `Stock User` (and `Stock Manager` only if required)
- **YAM QA Manager**: `Quality Manager` (+ minimal read roles for context)
- **YAM Procurement**: `Purchase User` (and `Purchase Manager` when needed)
- **YAM Sales / Customer**: `Sales User` + `Support Team` (if they also handle tickets)
- **YAM Compliance / Audit**: `Auditor` (read-only patterns) + scoped reports

Design rule: start with the smallest subset of baseline roles that enables the job.

## Org Chart Linkage (Employee → User → Role Profile)
Recommended source of truth:

- Use ERPNext `Employee` with:
  - `user_id` (links Employee to User)
  - `department` / `designation`
  - optional: `reports_to`

Mapping approach:

1. Define a mapping table in docs (and later a config DocType) from:
   - Department + Designation → Role Profile(s)
2. Assign Role Profiles to the user (manually first, then optionally automated).

Automation (Build option):
- Implement a small sync job (server-side) that updates `User.roles`/role profiles when the linked `Employee` changes.
- Keep it **idempotent** (re-running yields the same roles).

## Site Isolation (Non‑negotiable)
Even with correct roles, we must isolate data by Site.

- Use `User Permission` records to restrict `Site` per user.
- Add permission query conditions / match rules so docs always filter by Site.
- Default: new users get **no Site access** until explicitly assigned.

## High‑Risk Actions (Approval Required)
We implement approvals via:

- **Workflow** with transitions requiring `Quality Manager` (or the chosen QA approver role profile)
- Server-side validation that blocks state changes without approval

High-risk examples:
- lot accept/reject, recalls, certificate issuance/override, CAPA closure, shipment release without mandatory QC/cert

## Build Checklist (Move to “Build”)

1. Finalize org chart mapping
   - produce: department/designation list + owners
2. Create Role Profiles in ERPNext
   - one per human role; only baseline roles inside
3. Implement Site isolation defaults
   - ensure all YAM DocTypes include `site`
   - add User Permissions + permission query conditions
4. Implement approval workflows
   - for high-risk doctypes and transitions (QA Manager gate)
5. Add smoke tests / acceptance checks
   - confirm Site A user cannot see Site B data

## Notes / Pitfalls
- Avoid giving broad roles (`System Manager`, `Administrator`) to operational users.
- Prefer Role Profiles over directly assigning many roles.
- Segregation-of-duties is a policy layer: we still must design docperms/workflows accordingly.
