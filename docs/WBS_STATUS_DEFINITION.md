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

## Category Column Policy (automation)

The row-level refresh script (`tools/refresh_wbs_rows.py`) enforces `Done` with category gating.

- Required WBS columns (auto-created if missing):
  - `Schema`, `Validation`, `Permissions/Isolation`, `Workflow`, `Evidence`
- A row can be `Done` only when **all applicable category cells** are marked complete.
- Accepted complete tokens (case-insensitive):
  - `✅`, `Done`, `Complete`, `Completed`, `Yes`, `Y`, `True`, `1`
- Accepted not-applicable tokens:
  - `N/A`, `NA`, `Not Applicable`, `-`
- If milestone says `Done` but categories are incomplete, automation downgrades the row to `Partial`.

## Consistency Notes

- Do not mark `Done` if evidence is stale or missing.
- If a regression occurs, downgrade status and refresh dates.
- Use automation scripts where possible to keep status updates repeatable and auditable.
