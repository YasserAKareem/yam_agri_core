from __future__ import annotations

import frappe


def run_phase2_smoke() -> dict:
    """Minimal post-migrate smoke for Phase 2 integration.

    Safe to run via:
    - bench --site <site> execute yam_agri_core.yam_agri_core.smoke.run_phase2_smoke
    """

    checks: dict[str, object] = {
        "apps": {
            "agriculture": "agriculture" in (frappe.get_installed_apps() or []),
            "yam_agri_core": "yam_agri_core" in (frappe.get_installed_apps() or []),
            "yam_agri_qms_trace": "yam_agri_qms_trace" in (frappe.get_installed_apps() or []),
        },
        "doctypes": {
            "StorageBin": frappe.db.exists("DocType", "StorageBin") is not None,
            "Lot": frappe.db.exists("DocType", "Lot") is not None,
            "Crop": frappe.db.exists("DocType", "Crop") is not None,
            "Location": frappe.db.exists("DocType", "Location") is not None,
            "Weather": frappe.db.exists("DocType", "Weather") is not None,
            "Crop Cycle": frappe.db.exists("DocType", "Crop Cycle") is not None,
        },
    }

    location_site_field = False
    if checks["doctypes"]["Location"]:
        location_site_field = frappe.get_meta("Location").has_field("site")

    checks["bridge"] = {
        "location_site_field": location_site_field,
    }

    checks["workspace"] = {
        "yam_agri": frappe.db.exists("Workspace", "YAM Agri") is not None,
        "traceability": frappe.db.exists("Workspace", "Traceability & Lots") is not None,
    }

    checks["permission_hooks"] = {
        "StorageBin": "StorageBin" in (frappe.get_hooks("permission_query_conditions") or {}),
        "Weather": "Weather" in (frappe.get_hooks("permission_query_conditions") or {}),
        "Crop Cycle": "Crop Cycle" in (frappe.get_hooks("permission_query_conditions") or {}),
    }

    checks["status"] = "ok" if all([
        all(checks["apps"].values()),
        all(checks["doctypes"].values()),
        checks["bridge"]["location_site_field"],
        all(checks["workspace"].values()),
        all(checks["permission_hooks"].values()),
    ]) else "needs_attention"

    return checks
