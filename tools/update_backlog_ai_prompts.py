"""Add an 'AI Prompt' column to the YAM Agri backlog CSV and populate it.

This is a deterministic helper intended to make backlog prompts consistent and runnable
one item at a time.

Usage (PowerShell):
  python tools/update_backlog_ai_prompts.py
"""

from __future__ import annotations

import csv
import io
from pathlib import Path


BACKLOG_PATH = Path("docs/20260222 YAM_AGRI_BACKLOG v1.csv")
AI_PROMPT_COL = "AI Prompt"

REQUIRED_COLS = [
    "Idea ID",
    "Stage",
    "Primary user(s)",
    "Sub-domain",
    "Description",
    "AI Mode",
    "Actionability",
    "KPIs",
    "Risks",
    "Integrations / data sources",
]


def _sniff_dialect(sample: str) -> csv.Dialect:
    try:
        return csv.Sniffer().sniff(sample)
    except Exception:
        # Fall back to the most likely format for this file.
        return csv.get_dialect("excel")


def main() -> int:
    if not BACKLOG_PATH.exists():
        raise SystemExit(f"Backlog CSV not found: {BACKLOG_PATH}")

    raw = BACKLOG_PATH.read_bytes()
    text = raw.decode("utf-8", errors="replace")

    dialect = _sniff_dialect(text[:4096])

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    rows = list(reader)

    if not rows:
        raise SystemExit("Backlog CSV has no rows")

    fieldnames = list(reader.fieldnames or [])
    missing = [c for c in REQUIRED_COLS if c not in fieldnames]
    if missing:
        raise SystemExit(f"Missing expected columns: {missing}")

    if AI_PROMPT_COL not in fieldnames:
        fieldnames.append(AI_PROMPT_COL)

    base_context = (
        "You are GitHub Copilot (GPT-5.2) acting as a coding agent in the 'yam_agri_core' repo "
        "(Frappe/ERPNext v16). Follow platform rules: Site isolation by default; high-risk actions require QA Manager approval; "
        "AI is assistive only (no unsupervised accept/reject/recall/customer comms); never commit secrets. "
    )

    for row in rows:
        idea_id = (row.get("Idea ID") or "").strip()
        stage = (row.get("Stage") or "").strip()
        users = (row.get("Primary user(s)") or "").strip()
        subdomain = (row.get("Sub-domain") or "").strip()
        ai_mode = (row.get("AI Mode") or "").strip()
        actionability = (row.get("Actionability") or "").strip()
        kpis = (row.get("KPIs") or "").strip()
        risks = (row.get("Risks") or "").strip()
        integrations = (row.get("Integrations / data sources") or "").strip()

        prompt = (
            f"{base_context}Implement backlog item {idea_id} (Stage {stage}) for users: {users}. "
            f"Feature: {subdomain}. AI mode: {ai_mode}. Actionability: {actionability}. "
            f"Deliver an MVP that includes: (1) Frappe DocTypes/fields/workflows/permissions needed (Site-linked + permission rules); "
            f"(2) server-side controllers/validations/background jobs as appropriate; "
            f"(3) sample data (fixtures/seed data) for a quick demo; "
            f"(4) at least one Report (query/script report) and one Dashboard/Chart aligned to KPIs ({kpis}); "
            "(5) minimal tests or smoke checks; (6) short docs/runbook updates. "
            f"Integrations to stub or mock: {integrations}. Risks to mitigate: {risks}. "
            "Keep scope tight; do not add extra pages/features beyond the backlog item."
        )

        row[AI_PROMPT_COL] = prompt

    # Write back as Excel CSV (comma + quotes) with Windows-friendly newlines.
    with BACKLOG_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            dialect="excel",
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated {BACKLOG_PATH} with '{AI_PROMPT_COL}' for {len(rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
