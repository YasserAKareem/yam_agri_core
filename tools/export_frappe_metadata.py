"""Export live Frappe site metadata to CSV.

Goal: give humans + AI agents a reliable, versioned snapshot of the *installed* truth
(ERPNext + all installed apps), so we can prevent duplication and align to E2E processes.

Run inside the dev stack (example):
  cd infra/docker
  bash run.sh bench --site localhost execute tools.export_frappe_metadata.run

This script is read-only with respect to business documents.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


def _require_frappe():
    try:
        import frappe  # type: ignore

        return frappe
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "This script must be executed via bench (so frappe is available)."
        ) from exc


def _timestamp_dir() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _stringify(row.get(k)) for k in fieldnames})


def _stringify(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (int, float, bool)):
        return str(v)
    if isinstance(v, (dict, list, tuple)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return str(v)


def _get_all(
    frappe,
    doctype: str,
    *,
    fields: list[str],
    filters: dict[str, Any] | None = None,
    order_by: str | None = None,
) -> list[dict[str, Any]]:
    kwargs: dict[str, Any] = {
        "doctype": doctype,
        "fields": fields,
        "limit_page_length": 0,
    }
    if filters:
        kwargs["filters"] = filters
    if order_by:
        kwargs["order_by"] = order_by
    return frappe.get_all(**kwargs)


def run(
    *,
    output_dir: str | None = None,
    include_reports: int = 1,
    include_workspaces: int = 1,
    include_customizations: int = 1,
) -> dict[str, Any]:
    """Export metadata into CSV files.

    Args:
        output_dir: Destination directory (relative to bench cwd). Defaults to
            docs/metadata_exports/<utc_timestamp>/
        include_reports: Export Report doctype (and roles).
        include_workspaces: Export Workspace and (best-effort) workspace links.
        include_customizations: Export Custom Field + Property Setter (if installed).

    Returns:
        Summary dict for quick inspection in bench output.
    """

    frappe = _require_frappe()

    if not output_dir:
        output_dir = f"docs/metadata_exports/{_timestamp_dir()}"

    base = Path(output_dir)
    base.mkdir(parents=True, exist_ok=True)

    exported: dict[str, int] = {}

    # ── DocTypes ───────────────────────────────────────────────────────────

    doctype_fields = [
        "name",
        "module",
        "custom",
        "issingle",
        "istable",
        "is_submittable",
        "autoname",
        "naming_rule",
        "title_field",
        "search_fields",
        "sort_field",
        "sort_order",
        "quick_entry",
        "allow_rename",
        "allow_copy",
        "allow_import",
        "allow_guest_to_view",
        "restrict_to_domain",
        "editable_grid",
        "track_changes",
        "read_only",
        "in_create",
        "is_tree",
        "show_name_in_global_search",
        "beta",
        "modified",
    ]
    doctypes = _get_all(frappe, "DocType", fields=doctype_fields, order_by="name asc")
    _write_csv(base / "doctypes.csv", doctypes, doctype_fields)
    exported["doctypes.csv"] = len(doctypes)

    docfield_fields = [
        "parent",
        "parenttype",
        "parentfield",
        "idx",
        "fieldname",
        "label",
        "fieldtype",
        "options",
        "reqd",
        "unique",
        "read_only",
        "hidden",
        "in_list_view",
        "in_filter",
        "in_global_search",
        "in_standard_filter",
        "permlevel",
        "depends_on",
        "mandatory_depends_on",
        "read_only_depends_on",
        "default",
        "description",
        "collapsible",
        "length",
        "precision",
        "modified",
    ]
    docfields = _get_all(frappe, "DocField", fields=docfield_fields, order_by="parent asc, idx asc")
    _write_csv(base / "docfields.csv", docfields, docfield_fields)
    exported["docfields.csv"] = len(docfields)

    docperm_fields = [
        "parent",
        "role",
        "permlevel",
        "read",
        "write",
        "create",
        "delete",
        "submit",
        "cancel",
        "amend",
        "report",
        "export",
        "import",
        "share",
        "print",
        "email",
        "if_owner",
        "modified",
    ]
    docperms = _get_all(frappe, "DocPerm", fields=docperm_fields, order_by="parent asc, permlevel asc")
    _write_csv(base / "docperms.csv", docperms, docperm_fields)
    exported["docperms.csv"] = len(docperms)

    # ── Workflows ─────────────────────────────────────────────────────────

    wf_fields = [
        "name",
        "workflow_name",
        "document_type",
        "is_active",
        "workflow_state_field",
        "send_email_alert",
        "modified",
    ]
    workflows = _get_all(frappe, "Workflow", fields=wf_fields, order_by="workflow_name asc")
    _write_csv(base / "workflows.csv", workflows, wf_fields)
    exported["workflows.csv"] = len(workflows)

    wf_state_fields = [
        "parent",
        "state",
        "doc_status",
        "allow_edit",
        "style",
        "update_field",
        "update_value",
        "idx",
        "modified",
    ]
    workflow_states = _get_all(
        frappe,
        "Workflow Document State",
        fields=wf_state_fields,
        order_by="parent asc, idx asc",
    )
    _write_csv(base / "workflow_states.csv", workflow_states, wf_state_fields)
    exported["workflow_states.csv"] = len(workflow_states)

    wf_transition_fields = [
        "parent",
        "state",
        "action",
        "next_state",
        "allowed",
        "condition",
        "idx",
        "modified",
    ]
    workflow_transitions = _get_all(
        frappe,
        "Workflow Transition",
        fields=wf_transition_fields,
        order_by="parent asc, idx asc",
    )
    _write_csv(base / "workflow_transitions.csv", workflow_transitions, wf_transition_fields)
    exported["workflow_transitions.csv"] = len(workflow_transitions)

    # ── Reports / Workspaces (best-effort) ────────────────────────────────

    if int(include_reports):
        report_fields = [
            "name",
            "report_name",
            "ref_doctype",
            "report_type",
            "module",
            "is_standard",
            "disabled",
            "prepared_report",
            "modified",
        ]
        reports = _get_all(frappe, "Report", fields=report_fields, order_by="report_name asc")
        _write_csv(base / "reports.csv", reports, report_fields)
        exported["reports.csv"] = len(reports)

    if int(include_workspaces):
        workspace_fields = [
            "name",
            "label",
            "title",
            "module",
            "public",
            "parent_page",
            "restrict_to_domain",
            "for_user",
            "sequence_id",
            "icon",
            "modified",
        ]
        workspaces = _get_all(frappe, "Workspace", fields=workspace_fields, order_by="sequence_id asc")
        _write_csv(base / "workspaces.csv", workspaces, workspace_fields)
        exported["workspaces.csv"] = len(workspaces)

        # Workspace links live in a child table. Name may differ by version; try common ones.
        link_rows: list[dict[str, Any]] = []
        link_fieldnames = [
            "parent",
            "type",
            "label",
            "link_type",
            "link_to",
            "onboard",
            "hidden",
            "dependencies",
            "is_query_report",
            "idx",
        ]
        for child_dt in ("Workspace Link", "Workspace Links", "Workspace Shortcut"):
            try:
                rows = _get_all(frappe, child_dt, fields=link_fieldnames, order_by="parent asc, idx asc")
                if rows:
                    link_rows.extend(rows)
            except Exception:
                continue
        if link_rows:
            _write_csv(base / "workspace_links.csv", link_rows, link_fieldnames)
            exported["workspace_links.csv"] = len(link_rows)

    if int(include_customizations):
        # These exist in most sites; export best-effort.
        for dt_name, out_file, fields in (
            (
                "Custom Field",
                "custom_fields.csv",
                [
                    "name",
                    "dt",
                    "fieldname",
                    "label",
                    "fieldtype",
                    "options",
                    "insert_after",
                    "reqd",
                    "read_only",
                    "hidden",
                    "in_list_view",
                    "in_filter",
                    "modified",
                ],
            ),
            (
                "Property Setter",
                "property_setters.csv",
                [
                    "name",
                    "doc_type",
                    "field_name",
                    "property",
                    "property_type",
                    "value",
                    "default_value",
                    "modified",
                ],
            ),
        ):
            try:
                rows = _get_all(frappe, dt_name, fields=fields, order_by="modified desc")
                _write_csv(base / out_file, rows, fields)
                exported[out_file] = len(rows)
            except Exception:
                # If customization doctypes not installed or permission blocked.
                pass

    summary = {
        "output_dir": str(base),
        "exported": exported,
    }

    # Print for bench execute readability.
    frappe.logger().info(summary)
    return summary
