from __future__ import annotations

import frappe


def extend_bootinfo(bootinfo: dict) -> None:
    """Patch bootinfo for small UX consistency fixes.

    Fixes:
    - Ensure `DocType` appears in Data Export doctype dropdown when the current
      user actually has export permission for it.

    Why:
    - The Data Export UI uses `frappe.boot.user.can_export`.
    - In some setups, `DocType` is filtered out from that list even though
      `can_export('DocType')` returns true server-side.
    """

    user = bootinfo.get("user") or {}
    can_export = user.get("can_export")
    if not isinstance(can_export, list):
        can_export = []
        user["can_export"] = can_export
        bootinfo["user"] = user

    if "DocType" in can_export:
        return

    # Prefer the dedicated export check if present.
    allowed = False
    try:
        can_export_fn = getattr(frappe.permissions, "can_export", None)
        if callable(can_export_fn):
            allowed = bool(can_export_fn("DocType"))
        else:
            allowed = bool(frappe.has_permission("DocType", "export"))
    except Exception:
        allowed = False

    if allowed:
        can_export.append("DocType")


def boot_session(bootinfo: dict) -> None:
    # Compatibility hook: some Frappe builds call `boot_session`.
    extend_bootinfo(bootinfo)
