"""Permission helper utilities.

These helpers are meant for controlled, temporary permission changes during admin operations
(e.g. enabling Export on a sensitive DocType for a short time), and then rolling them back.

Run via bench:
  bench --site <site> execute yam_agri_core.yam_agri_core.perm_tools.set_export_permission \
    --kwargs '{"doctype":"DocType","role":"Administrator","permlevel":0,"enable":1}'

"""

from __future__ import annotations

from typing import Any


def set_export_permission(
    *,
    doctype: str,
    role: str = "Administrator",
    permlevel: int = 0,
    enable: int = 1,
) -> dict[str, Any]:
    """Toggle the DocPerm.export flag for a role on a given DocType.

    This updates existing DocPerm rows in-place (no Custom DocPerm), so it is easy to revert.

    Args:
        doctype: Target DocType name (e.g. "DocType").
        role: Role to modify.
        permlevel: Permission level to target (usually 0).
        enable: 1 to grant Export, 0 to revoke.
    """

    import frappe

    target = 1 if int(enable) else 0

    rows = frappe.get_all(
        "DocPerm",
        filters={"parent": doctype, "role": role, "permlevel": int(permlevel)},
        fields=["name", "export"],
        order_by="permlevel asc",
    )

    if not rows:
        return {
            "ok": False,
            "doctype": doctype,
            "role": role,
            "permlevel": int(permlevel),
            "message": "No matching DocPerm rows found",
        }

    before = [{"name": r["name"], "export": int(r.get("export") or 0)} for r in rows]

    for r in rows:
        frappe.db.set_value(
            "DocPerm",
            r["name"],
            "export",
            target,
            update_modified=False,
        )

    frappe.db.commit()

    after_rows = frappe.get_all(
        "DocPerm",
        filters={"parent": doctype, "role": role, "permlevel": int(permlevel)},
        fields=["name", "export"],
        order_by="permlevel asc",
    )
    after = [{"name": r["name"], "export": int(r.get("export") or 0)} for r in after_rows]

    return {
        "ok": True,
        "doctype": doctype,
        "role": role,
        "permlevel": int(permlevel),
        "before": before,
        "after": after,
    }
