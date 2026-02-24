# WBS Status Definition

This document defines explicit row-level status semantics for `Done`, `Partial`, and `Not Started` so WBS progress is not inferred from repo heuristics.

## Category Model (per WBS row)

Each row is evaluated against these five categories:

1. **Schema**
   - DocType/fields exist with required constraints and naming where applicable.
2. **Validation**
   - Business rule checks implemented (server-side validation, cross-link consistency, non-negative/required domain checks).
3. **Permissions / Isolation**
   - Site ownership enforced and cross-site visibility/access blocked by default.
4. **Workflow**
   - Core lifecycle transitions/actions implemented (e.g., Draft -> Approved paths, minimal usable flow).
5. **Evidence**
   - Repeatable acceptance check exists with current execution evidence (script output/checklist/report).

## Status Rules

- **Done**
  - All applicable categories for the row are complete.
  - Latest run/evidence confirms behavior.

- **Partial**
  - At least one applicable category is complete, but not all.
  - Typical examples:
    - Schema + validation done, but permissions not complete.
    - Code complete, but no repeatable acceptance evidence.

- **Not Started**
  - No applicable category is complete, or only placeholder/stub exists.

## Date Field Policy

When updating WBS row columns:

- `Execution Status`
  - One of: `Done`, `Partial`, `Not Started`.
- `Status Updated On`
  - Set on every status update (`yyyy-mm-dd`).
- `Started On`
  - Set when status becomes `Partial` or `Done`.
- `Completed On`
  - Set only when status is `Done`; clear when not `Done`.

## Consistency Notes

- Do not mark `Done` if evidence is stale or missing.
- If a regression occurs, downgrade status and refresh dates.
- Use automation scripts where possible to keep status updates repeatable and auditable.
