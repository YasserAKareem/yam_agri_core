from __future__ import annotations

import json

import frappe


def ensure_yam_agri_workspaces() -> None:
    """Create YAM Agri workspace pages (and links) if missing.

    Design goals:
    - Minimal UX: just workspace pages + navigation to existing DocTypes.
    - Idempotent: safe to run after every migrate.
    - Non-destructive: only adds missing records/links; does not delete extras.
    """

    if not frappe.db.exists("DocType", "Workspace"):
        return

    # Desk module tiles map to Module Def records.
    _yam_module = "YAM Agri"
    _ensure_module_def(module_name=_yam_module, app_name="yam_agri_core")
    if frappe.db.exists("DocType", "Workspace Sidebar"):
        # Not all installs have it, but if present we use it to make a Desk tile.
        has_workspace_sidebar = True
    else:
        has_workspace_sidebar = False

    # Parent workspace
    _ensure_workspace(
        name="YAM Agri",
        title="YAM Agri",
        module=_yam_module,
        icon="agriculture",
        sequence_id=30,
        parent_page=None,
    )

    # Sub-workspaces (simple navigation structure)
    children = [
        ("Traceability & Lots", "Traceability & Lots", "stock"),
        ("Quality (QA/QMS)", "Quality (QA/QMS)", "quality"),
        ("Evidence & Audits", "Evidence & Audits", "file-text"),
        ("Devices & Observations", "Devices & Observations", "iot"),
        ("Complaints", "Complaints", "support"),
    ]
    for idx, (name, title, icon) in enumerate(children, start=1):
        _ensure_workspace(
            name=name,
            title=title,
            module=_yam_module,
            icon=icon,
            sequence_id=30 + idx,
            parent_page="YAM Agri",
        )

    # Parent page shortcuts (like standard modules such as Build)
    _ensure_shortcuts(
        workspace="YAM Agri",
        shortcuts=[
            ("DocType", "Site", "List", "Sites"),
            ("DocType", "Lot", "List", "Lots"),
            ("DocType", "StorageBin", "List", "Storage Bins"),
            ("DocType", "Crop", "List", "Crops"),
            ("DocType", "QCTest", "List", "QC Tests"),
            ("DocType", "Certificate", "List", "Certificates"),
            ("DocType", "Nonconformance", "List", "Nonconformance"),
        ],
    )
    _ensure_workspace_content_from_shortcuts(workspace="YAM Agri", header_text="YAM Agri")

    # Shortcuts (minimal; reuse-first)
    traceability_shortcuts: list[tuple[str, str, str, str]] = [
        ("DocType", "Lot", "List", "Lots"),
        ("DocType", "Site", "List", "Sites"),
    ]
    quality_shortcuts: list[tuple[str, str, str, str]] = [
        ("DocType", "QCTest", "List", "QC Tests"),
        ("DocType", "Certificate", "List", "Certificates"),
        ("DocType", "Nonconformance", "List", "Nonconformance"),
        ("DocType", "Quality Inspection", "List", "Quality Inspections"),
    ]
    evidence_shortcuts: list[tuple[str, str, str, str]] = [
        ("DocType", "File", "List", "Files"),
        ("DocType", "Audit Trail", "List", "Audit Trail"),
        ("DocType", "Deleted Document", "List", "Deleted Documents"),
    ]
    devices_shortcuts: list[tuple[str, str, str, str]] = [
        ("DocType", "API Request Log", "List", "API Request Log"),
    ]
    complaints_shortcuts: list[tuple[str, str, str, str]] = [
        ("DocType", "Issue", "List", "Issues"),
    ]

    # Include any installed YAM Agri Core DocTypes in sensible buckets.
    for dt in _get_yam_agri_core_doctypes():
        if dt in {"Lot", "Transfer", "ScaleTicket", "Scale Ticket", "StorageBin", "Storage Bin"}:
            traceability_shortcuts.append(("DocType", dt, "List", dt))
        elif dt in {"QCTest", "Certificate", "Nonconformance"}:
            quality_shortcuts.append(("DocType", dt, "List", dt))
        elif dt in {"EvidencePack", "Evidence Pack"}:
            evidence_shortcuts.append(("DocType", dt, "List", dt))
        elif dt in {"Device", "Observation"}:
            devices_shortcuts.append(("DocType", dt, "List", dt))
        elif dt in {"Complaint"}:
            complaints_shortcuts.append(("DocType", dt, "List", dt))

    for dt in _get_agriculture_doctypes():
        if dt in {"Crop", "Crop Cycle", "Fertilizer", "Disease"}:
            traceability_shortcuts.append(("DocType", dt, "List", dt))
        elif dt in {"Soil Analysis", "Plant Analysis", "Water Analysis"}:
            quality_shortcuts.append(("DocType", dt, "List", dt))
        elif dt in {"Weather", "Weather Parameter"}:
            devices_shortcuts.append(("DocType", dt, "List", dt))

    for dt in _get_yam_agri_qms_trace_doctypes():
        if dt in {"Lot", "Transfer", "ScaleTicket", "Scale Ticket", "StorageBin", "Storage Bin"}:
            traceability_shortcuts.append(("DocType", dt, "List", dt))
        elif dt in {"QCTest", "Certificate", "Nonconformance"}:
            quality_shortcuts.append(("DocType", dt, "List", dt))
        elif dt in {"EvidencePack", "Evidence Pack"}:
            evidence_shortcuts.append(("DocType", dt, "List", dt))
        elif dt in {"Device", "Observation"}:
            devices_shortcuts.append(("DocType", dt, "List", dt))
        elif dt in {"Complaint"}:
            complaints_shortcuts.append(("DocType", dt, "List", dt))

    # Optional standard ERPNext navigation (only if installed)
    traceability_shortcuts.extend(
        [
            ("DocType", "Stock Entry", "List", "Stock Entries"),
            ("DocType", "Warehouse", "List", "Warehouses"),
        ]
    )

    _ensure_shortcuts(
        workspace="Traceability & Lots",
        shortcuts=traceability_shortcuts,
    )
    _ensure_workspace_content_from_shortcuts(
        workspace="Traceability & Lots",
        header_text="Traceability & Lots",
    )

    _ensure_shortcuts(
        workspace="Quality (QA/QMS)",
        shortcuts=quality_shortcuts,
    )
    _ensure_workspace_content_from_shortcuts(
        workspace="Quality (QA/QMS)",
        header_text="Quality (QA/QMS)",
    )

    _ensure_shortcuts(
        workspace="Evidence & Audits",
        shortcuts=evidence_shortcuts,
    )
    _ensure_workspace_content_from_shortcuts(
        workspace="Evidence & Audits",
        header_text="Evidence & Audits",
    )

    _ensure_shortcuts(
        workspace="Devices & Observations",
        shortcuts=devices_shortcuts,
    )
    _ensure_workspace_content_from_shortcuts(
        workspace="Devices & Observations",
        header_text="Devices & Observations",
    )

    _ensure_shortcuts(
        workspace="Complaints",
        shortcuts=complaints_shortcuts,
    )
    _ensure_workspace_content_from_shortcuts(
        workspace="Complaints",
        header_text="Complaints",
    )

    if has_workspace_sidebar:
        _ensure_workspace_sidebar()
        _ensure_desktop_icon_for_workspace_sidebar(label="YAM Agri", app_name="yam_agri_core")

    # Ensure upstream Agriculture workspace renders with modern shortcut blocks.
    ensure_agriculture_workspace_modernized()

    frappe.db.commit()


def ensure_agriculture_workspace_modernized() -> None:
    """Modernize Agriculture workspace to Manufacturing-like card layout.

    Keeps a classified, sectioned UX (cards + links) while filtering out missing
    DocTypes to avoid broken links on partially-installed sites.
    """

    if not frappe.db.exists("DocType", "Workspace"):
        return

    if not frappe.db.exists("Workspace", "Agriculture"):
        return

    _set_agriculture_workspace_links_and_content(workspace="Agriculture")
    _ensure_agriculture_workspace_sidebar()


def _set_agriculture_workspace_links_and_content(*, workspace: str) -> None:
    """Force Agriculture workspace to classified, route-safe shortcut layout."""
    if not frappe.db.exists("Workspace", workspace):
        return

    doc = frappe.get_doc("Workspace", workspace)

    sections: list[tuple[str, list[str]]] = [
        ("Crops & Lands", ["Crop", "Crop Cycle", "Location"]),
        (
            "Analytics",
            [
                "Plant Analysis",
                "Soil Analysis",
                "Water Analysis",
                "Soil Texture",
                "Weather",
                "Agriculture Analysis Criteria",
            ],
        ),
        ("Diseases & Fertilizers", ["Disease", "Fertilizer"]),
    ]

    existing = {dt for dt in frappe.get_all("DocType", filters={"module": "Agriculture"}, pluck="name")}

    # Keep links empty to avoid legacy desk card routing; rely on shortcuts instead.
    doc.set("links", [])

    # Rebuild shortcut rows with valid Agriculture DocTypes only.
    doc.set("shortcuts", [])
    for _, doctypes in sections:
        for dt in doctypes:
            if dt not in existing:
                continue
            doc.append(
                "shortcuts",
                {
                    "type": "URL",
                    "url": _get_app_route_for_doctype(dt),
                    "label": dt,
                },
            )

    blocks: list[dict] = [
        {
            "type": "header",
            "data": {
                "text": '<span class="h4"><b>Reports &amp; Masters</b></span>',
                "col": 12,
            },
        }
    ]

    for section_label, doctypes in sections:
        valid_doctypes = [dt for dt in doctypes if dt in existing]
        if not valid_doctypes:
            continue
        blocks.append(
            {
                "type": "header",
                "data": {
                    "text": f'<span class="h5"><b>{section_label}</b></span>',
                    "col": 12,
                },
            }
        )
        for dt in valid_doctypes:
            blocks.append(
                {
                    "type": "shortcut",
                    "data": {
                        "shortcut_name": dt,
                        "col": 3,
                    },
                }
            )

    doc.content = json.dumps(blocks)
    doc.save(ignore_permissions=True)
    _unset_workspace_app(workspace)


def _get_app_route_for_doctype(doctype_name: str) -> str:
    """Return canonical /app route for a DocType label/name."""
    return f"/app/{frappe.scrub(doctype_name).replace('_', '-')}"


def _ensure_agriculture_workspace_sidebar() -> None:
    """Create Manufacturing-style Agriculture sidebar with stable app routes."""
    if not frappe.db.exists("DocType", "Workspace Sidebar"):
        return

    title = "Agriculture"
    module = "Agriculture"

    if frappe.db.exists("Workspace Sidebar", title):
        doc = frappe.get_doc("Workspace Sidebar", title)
    else:
        doc = frappe.get_doc(
            {
                "doctype": "Workspace Sidebar",
                "title": title,
                "module": module,
                "header_icon": "agriculture",
                "standard": 0,
            }
        )
        doc.insert(ignore_permissions=True)

    changed = False
    if (doc.module or "") != module:
        doc.module = module
        changed = True
    if (doc.header_icon or "") != "agriculture":
        doc.header_icon = "agriculture"
        changed = True
    if doc.get("for_user"):
        doc.for_user = None
        changed = True

    desired_items: list[dict] = [
        {
            "label": "Home",
            "link_type": "Workspace",
            "type": "Link",
            "link_to": "Agriculture",
            "child": 0,
        },
        {
            "label": "Crops & Lands",
            "link_type": "DocType",
            "type": "Section Break",
            "child": 0,
        },
        {
            "label": "Crop",
            "link_type": "URL",
            "type": "Link",
            "url": _get_app_route_for_doctype("Crop"),
            "child": 1,
        },
        {
            "label": "Crop Cycle",
            "link_type": "URL",
            "type": "Link",
            "url": _get_app_route_for_doctype("Crop Cycle"),
            "child": 1,
        },
        {
            "label": "Analytics",
            "link_type": "DocType",
            "type": "Section Break",
            "child": 0,
        },
        {
            "label": "Plant Analysis",
            "link_type": "URL",
            "type": "Link",
            "url": _get_app_route_for_doctype("Plant Analysis"),
            "child": 1,
        },
        {
            "label": "Soil Analysis",
            "link_type": "URL",
            "type": "Link",
            "url": _get_app_route_for_doctype("Soil Analysis"),
            "child": 1,
        },
        {
            "label": "Water Analysis",
            "link_type": "URL",
            "type": "Link",
            "url": _get_app_route_for_doctype("Water Analysis"),
            "child": 1,
        },
        {
            "label": "Soil Texture",
            "link_type": "URL",
            "type": "Link",
            "url": _get_app_route_for_doctype("Soil Texture"),
            "child": 1,
        },
        {
            "label": "Weather",
            "link_type": "URL",
            "type": "Link",
            "url": _get_app_route_for_doctype("Weather"),
            "child": 1,
        },
        {
            "label": "Agriculture Analysis Criteria",
            "link_type": "URL",
            "type": "Link",
            "url": _get_app_route_for_doctype("Agriculture Analysis Criteria"),
            "child": 1,
        },
        {
            "label": "Diseases & Fertilizers",
            "link_type": "DocType",
            "type": "Section Break",
            "child": 0,
        },
        {
            "label": "Disease",
            "link_type": "URL",
            "type": "Link",
            "url": _get_app_route_for_doctype("Disease"),
            "child": 1,
        },
        {
            "label": "Fertilizer",
            "link_type": "URL",
            "type": "Link",
            "url": _get_app_route_for_doctype("Fertilizer"),
            "child": 1,
        },
    ]

    doc.set("items", [])
    for item in desired_items:
        doc.append("items", item)
        changed = True

    if changed:
        doc.save(ignore_permissions=True)


def _ensure_desktop_icon_for_workspace_sidebar(*, label: str, app_name: str) -> None:
    """Ensure Desk home tile exists via Desktop Icon.

    Even with Workspace/Workspace Sidebar in place, the Desk home screen is driven by
    Desktop Icon records (cached per user). We create/update a global icon owned by
    Administrator so it appears for all users.
    """
    if not frappe.db.exists("DocType", "Desktop Icon"):
        return

    filters = {"label": label, "icon_type": "Link", "link_type": "Workspace Sidebar", "link_to": label}
    name = frappe.db.exists("Desktop Icon", filters)
    if name:
        doc = frappe.get_doc("Desktop Icon", name)
        changed = False
        if (doc.icon or "") != "agriculture":
            doc.icon = "agriculture"
            changed = True
        if int(doc.hidden or 0) != 0:
            doc.hidden = 0
            changed = True
        # app_name is used for grouping under an app tile if present.
        if hasattr(doc, "app_name") and (doc.app_name or "") != app_name:
            doc.app_name = app_name
            changed = True
        if changed:
            doc.save(ignore_permissions=True)
    else:
        doc = frappe.get_doc(
            {
                "doctype": "Desktop Icon",
                "label": label,
                "link_type": "Workspace Sidebar",
                "icon_type": "Link",
                "link_to": label,
                "icon": "agriculture",
                "hidden": 0,
                "standard": 0,
                "app_name": app_name,
            }
        )
        # Ensure it's treated as global (queried for all users).
        doc.owner = "Administrator"
        doc.insert(ignore_permissions=True)

    try:
        from frappe.desk.doctype.desktop_icon.desktop_icon import clear_desktop_icons_cache

        clear_desktop_icons_cache()
    except Exception:
        # Best-effort: cache will rebuild on next login.
        pass


def _ensure_module_def(*, module_name: str, app_name: str) -> None:
    """Ensure a Module Def exists so the Desk home tile can appear."""
    if not frappe.db.exists("DocType", "Module Def"):
        return

    if frappe.db.exists("Module Def", module_name):
        doc = frappe.get_doc("Module Def", module_name)
        changed = False
        if (doc.app_name or "") != app_name:
            doc.app_name = app_name
            changed = True
        if int(doc.custom or 0) != 1:
            doc.custom = 1
            changed = True
        if changed:
            doc.save(ignore_permissions=True)
        return

    doc = frappe.get_doc(
        {
            "doctype": "Module Def",
            "module_name": module_name,
            "app_name": app_name,
            "custom": 1,
        }
    )
    doc.insert(ignore_permissions=True)


def _ensure_workspace(
    *,
    name: str,
    title: str,
    module: str,
    icon: str,
    sequence_id: int,
    parent_page: str | None,
) -> None:
    if frappe.db.exists("Workspace", name):
        doc = frappe.get_doc("Workspace", name)
        changed = False
        for field, value in {
            "label": name,
            "title": title,
            "type": "Workspace",
            "module": module,
            "public": 1,
            "is_hidden": 0,
            "sequence_id": float(sequence_id),
            "icon": icon,
            "parent_page": parent_page,
        }.items():
            if getattr(doc, field, None) != value:
                setattr(doc, field, value)
                changed = True
        if changed:
            doc.save(ignore_permissions=True)
        _unset_workspace_app(name)
        return

    doc = frappe.get_doc(
        {
            "doctype": "Workspace",
            "name": name,
            "label": name,
            "title": title,
            "type": "Workspace",
            "module": module,
            "public": 1,
            "is_hidden": 0,
            "sequence_id": float(sequence_id),
            "icon": icon,
            "parent_page": parent_page,
        }
    )
    doc.insert(ignore_permissions=True)
    _unset_workspace_app(name)


def _get_yam_agri_core_doctypes() -> list[str]:
    """Return installed DocTypes that belong to the YAM Agri Core module.

    This keeps the workspace aligned with the live inventory without relying on
    exported CSVs being present in the runtime environment.
    """
    try:
        dts = frappe.get_all("DocType", filters={"module": "YAM Agri Core"}, pluck="name")
        # Keep it deterministic.
        return sorted(set(dts))
    except Exception:
        return []


def _get_agriculture_doctypes() -> list[str]:
    """Return installed DocTypes that belong to the Agriculture module."""
    return _get_module_doctypes("Agriculture")


def _get_yam_agri_qms_trace_doctypes() -> list[str]:
    """Return installed DocTypes that belong to the Yam Agri Qms Trace module."""
    return _get_module_doctypes("Yam Agri Qms Trace")


def _get_module_doctypes(module_name: str) -> list[str]:
    try:
        dts = frappe.get_all("DocType", filters={"module": module_name}, pluck="name")
        return sorted(set(dts))
    except Exception:
        return []


def _ensure_shortcuts(*, workspace: str, shortcuts: list[tuple[str, str, str, str]]) -> None:
    """Ensure Workspace Shortcut rows exist.

    Each tuple is (type, link_to, doc_view, label).
    """
    if not frappe.db.exists("Workspace", workspace):
        return

    doc = frappe.get_doc("Workspace", workspace)

    # Remove invalid DocType shortcuts that reference missing doctypes.
    removed_invalid = False
    for row in list(doc.shortcuts or []):
        if (row.type or "").strip() != "DocType":
            continue
        link_to = (row.link_to or "").strip()
        if link_to and not frappe.db.exists("DocType", link_to):
            try:
                doc.shortcuts.remove(row)
                removed_invalid = True
            except Exception:
                pass

    if removed_invalid:
        doc.save(ignore_permissions=True)
        _unset_workspace_app(workspace)

    # Deduplicate existing shortcut rows by (type, link_to, doc_view).
    # Keep one row; prefer a label that isn't exactly the DocType name.
    seen: dict[tuple[str, str, str], object] = {}
    removed_any = False
    for row in list(doc.shortcuts or []):
        key = (
            (row.type or "").strip(),
            (row.link_to or "").strip(),
            (row.doc_view or "").strip(),
        )
        if key not in seen:
            seen[key] = row
            continue

        keep = seen[key]
        keep_label = (getattr(keep, "label", "") or getattr(keep, "link_to", "") or "").strip()
        row_label = (row.label or row.link_to or "").strip()
        link_to = (row.link_to or "").strip()
        keep_score = 1 if keep_label and keep_label != link_to else 0
        row_score = 1 if row_label and row_label != link_to else 0
        if row_score > keep_score:
            try:
                doc.shortcuts.remove(keep)
                removed_any = True
            except Exception:
                pass
            seen[key] = row
        else:
            try:
                doc.shortcuts.remove(row)
                removed_any = True
            except Exception:
                pass

    if removed_any:
        doc.save(ignore_permissions=True)
        _unset_workspace_app(workspace)

    existing = set()
    for s in doc.shortcuts or []:
        existing.add(
            (
                (s.type or "").strip(),
                (s.link_to or "").strip(),
                (s.doc_view or "").strip(),
            )
        )

    changed = False
    for shortcut_type, link_to, doc_view, label in shortcuts:
        key = (shortcut_type, link_to, doc_view)
        if key in existing:
            continue
        if shortcut_type == "DocType" and not frappe.db.exists("DocType", link_to):
            # Avoid broken links if optional modules aren't installed.
            continue
        doc.append(
            "shortcuts",
            {
                "type": shortcut_type,
                "link_to": link_to,
                "doc_view": doc_view,
                "label": label,
            },
        )
        existing.add(key)
        changed = True

    if changed:
        doc.save(ignore_permissions=True)
        _unset_workspace_app(workspace)


def _ensure_workspace_content_from_shortcuts(*, workspace: str, header_text: str) -> None:
    """Populate Workspace.content so the page renders blocks.

    Frappe's workspace renderer is driven by EditorJS blocks stored in `content`.
    If content is empty (common for programmatically created workspaces), the
    page shows blank even if `shortcuts` exist.

    We only set content when it's empty to avoid overwriting user customizations.
    """
    if not frappe.db.exists("Workspace", workspace):
        return

    doc = frappe.get_doc("Workspace", workspace)

    # Parse current content.
    current_blocks: list[dict] = []
    try:
        if isinstance(doc.content, str) and doc.content.strip():
            parsed = json.loads(doc.content)
            if isinstance(parsed, list):
                current_blocks = parsed
    except Exception:
        current_blocks = []

    # Don't overwrite user-customized pages. We only manage the simple layout.
    if current_blocks:
        only_simple_layout = all(
            isinstance(b, dict) and b.get("type") in {"header", "shortcut"} for b in current_blocks
        )
        if not only_simple_layout:
            return

    # Build blocks: header + shortcut widgets (grid).
    blocks: list[dict] = [
        {
            "type": "header",
            "data": {
                "text": header_text,
                "col": 12,
            },
        },
    ]

    seen_labels: set[str] = set()
    for shortcut in doc.shortcuts or []:
        label = (shortcut.label or shortcut.link_to or "").strip()
        if not label:
            continue
        if label in seen_labels:
            continue
        seen_labels.add(label)
        blocks.append(
            {
                "type": "shortcut",
                "data": {
                    "shortcut_name": label,
                    "col": 3,
                },
            }
        )

    doc.content = json.dumps(blocks)
    doc.save(ignore_permissions=True)
    _unset_workspace_app(workspace)


def _unset_workspace_app(workspace: str) -> None:
    """Keep Workspace.app unset to prevent orphan cleanup deletions.

    Frappe's migrate process deletes public Workspaces with `app` set unless they
    exist as exported JSON files in an installed app. Since we generate these
    programmatically, we keep `app` empty.
    """
    try:
        frappe.db.set_value("Workspace", workspace, "app", None, update_modified=False)
    except Exception:
        pass


def _ensure_workspace_sidebar() -> None:
    """Ensure a Desk tile exists (Accounting-style) via Workspace Sidebar."""
    if not frappe.db.exists("DocType", "Workspace Sidebar"):
        return

    # These two fields control the tile.
    title = "YAM Agri"
    module = "YAM Agri"

    # Idempotency: Workspace Sidebar appears to use Title as primary key/name.
    # If a sidebar with our desired title already exists (even user-specific),
    # reuse it and normalize it to global to avoid duplicate insert errors.
    name = None
    if frappe.db.exists("Workspace Sidebar", title):
        name = title
    else:
        name = frappe.db.get_value(
            "Workspace Sidebar",
            {"module": module, "for_user": ["in", ["", None]]},
            "name",
        )
    if name:
        doc = frappe.get_doc("Workspace Sidebar", name)
        changed = False
        if (doc.title or "") != title:
            doc.title = title
            changed = True
        if (doc.header_icon or "") != "agriculture":
            doc.header_icon = "agriculture"
            changed = True
        # Ensure this is global (not user-specific), so the Desk tile is visible.
        if doc.get("for_user"):
            doc.for_user = None
            changed = True
        if (doc.module or "") != module:
            doc.module = module
            changed = True
        if changed:
            doc.save(ignore_permissions=True)
    else:
        doc = frappe.get_doc(
            {
                "doctype": "Workspace Sidebar",
                "title": title,
                "module": module,
                "header_icon": "agriculture",
                "standard": 0,
            }
        )
        doc.insert(ignore_permissions=True)

    # Items power the left navigation when inside the module.
    desired_items = [
        {"type": "Section Break", "label": "YAM Agri", "collapsible": 1, "keep_closed": 0},
        {
            "type": "Link",
            "label": "Traceability & Lots",
            "link_type": "Workspace",
            "link_to": "Traceability & Lots",
            "child": 1,
        },
        {
            "type": "Link",
            "label": "Quality (QA/QMS)",
            "link_type": "Workspace",
            "link_to": "Quality (QA/QMS)",
            "child": 1,
        },
        {
            "type": "Link",
            "label": "Evidence & Audits",
            "link_type": "Workspace",
            "link_to": "Evidence & Audits",
            "child": 1,
        },
        {
            "type": "Link",
            "label": "Devices & Observations",
            "link_type": "Workspace",
            "link_to": "Devices & Observations",
            "child": 1,
        },
        {
            "type": "Link",
            "label": "Complaints",
            "link_type": "Workspace",
            "link_to": "Complaints",
            "child": 1,
        },
    ]

    existing = set()
    for it in doc.items or []:
        existing.add(((it.type or "").strip(), (it.label or "").strip(), (it.link_to or "").strip()))

    changed = False
    for item in desired_items:
        key = (
            (item.get("type") or "").strip(),
            (item.get("label") or "").strip(),
            (item.get("link_to") or "").strip(),
        )
        if key in existing:
            continue
        if item.get("type") == "Link" and item.get("link_type") == "Workspace":
            if item.get("link_to") and not frappe.db.exists("Workspace", item["link_to"]):
                continue
        doc.append("items", item)
        changed = True

    if changed:
        doc.save(ignore_permissions=True)


def get_yam_agri_workspace_status() -> dict:
    """Return a diagnostic snapshot of YAM Agri workspace state.

    Safe to run via:
    - bench --site <site> execute yam_agri_core.yam_agri_core.workspace_setup.get_yam_agri_workspace_status
    """
    module_name = "YAM Agri"

    module_def = None
    if frappe.db.exists("DocType", "Module Def") and frappe.db.exists("Module Def", module_name):
        md = frappe.get_doc("Module Def", module_name)
        module_def = {
            "name": md.name,
            "app_name": getattr(md, "app_name", None),
            "custom": int(md.custom or 0),
        }

    workspaces = []
    if frappe.db.exists("DocType", "Workspace"):
        for ws in frappe.get_all(
            "Workspace",
            filters={"module": module_name},
            fields=["name", "title", "module", "app", "public", "is_hidden", "for_user", "content"],
            order_by="name asc",
        ):
            content = (ws.get("content") or "").strip()
            block_count = 0
            content_json_ok = True
            if content:
                try:
                    parsed = json.loads(content)
                    block_count = len(parsed) if isinstance(parsed, list) else 0
                except Exception:
                    content_json_ok = False
            workspaces.append(
                {
                    "name": ws.get("name"),
                    "title": ws.get("title"),
                    "module": ws.get("module"),
                    "app": ws.get("app"),
                    "public": int(ws.get("public") or 0),
                    "is_hidden": int(ws.get("is_hidden") or 0),
                    "for_user": ws.get("for_user"),
                    "content_len": len(content),
                    "content_json_ok": content_json_ok,
                    "block_count": block_count,
                }
            )

    sidebars = []
    if frappe.db.exists("DocType", "Workspace Sidebar"):
        try:
            meta = frappe.get_meta("Workspace Sidebar")
            available = {df.fieldname for df in (meta.fields or []) if getattr(df, "fieldname", None)}
        except Exception:
            available = set()
        fields = ["name", "title", "module"]
        for optional in ["for_user", "header_icon", "standard"]:
            if optional in available:
                fields.append(optional)
        sidebars = frappe.get_all(
            "Workspace Sidebar",
            filters={"module": module_name},
            fields=fields,
            order_by="title asc",
        )

    desktop_icons = []
    if frappe.db.exists("DocType", "Desktop Icon"):
        try:
            meta = frappe.get_meta("Desktop Icon")
            available = {df.fieldname for df in (meta.fields or []) if getattr(df, "fieldname", None)}
        except Exception:
            available = set()
        fields = ["name", "label"]
        for optional in [
            "hidden",
            "owner",
            "standard",
            "icon_type",
            "link_type",
            "link_to",
            "app_name",
            "parent_icon",
        ]:
            if optional in available:
                fields.append(optional)
        desktop_icons = frappe.get_all(
            "Desktop Icon",
            filters={"label": module_name, "link_type": "Workspace Sidebar"},
            fields=fields,
            order_by="name asc",
        )

    return {
        "module": module_name,
        "module_def": module_def,
        "workspace_count": len(workspaces),
        "workspaces": workspaces,
        "sidebar_count": len(sidebars),
        "sidebars": sidebars,
        "desktop_icon_count": len(desktop_icons),
        "desktop_icons": desktop_icons,
    }
