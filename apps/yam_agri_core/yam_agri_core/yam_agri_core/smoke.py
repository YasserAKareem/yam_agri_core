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


def get_at10_readiness() -> dict:
    """Readiness report for manual AT-10 execution.

    Safe to run via:
    - bench --site <site> execute yam_agri_core.yam_agri_core.smoke.get_at10_readiness
    """

    sites = frappe.get_all("Site", fields=["name"], limit_page_length=500)
    qa_users = ["qa_manager_a@example.com", "qa_manager_b@example.com"]

    existing_users = frappe.get_all(
        "User",
        filters={"name": ["in", qa_users]},
        fields=["name", "enabled"],
        limit_page_length=20,
    )

    has_roles = frappe.get_all(
        "Has Role",
        filters={"parent": ["in", qa_users]},
        fields=["parent", "role"],
        limit_page_length=200,
    )

    site_permissions = frappe.get_all(
        "User Permission",
        filters={"allow": "Site"},
        fields=["user", "for_value"],
        limit_page_length=500,
    )

    locations = []
    location_site_field = False
    if frappe.db.exists("DocType", "Location"):
        location_site_field = frappe.get_meta("Location").has_field("site")
        if location_site_field:
            locations = frappe.get_all("Location", fields=["name", "site"], limit_page_length=500)

    mapped_locations = [loc for loc in locations if (loc.get("site") or "").strip()]

    readiness = {
        "sites": {
            "count": len(sites),
            "names": [s["name"] for s in sites],
            "ok": len(sites) >= 2,
        },
        "qa_users": {
            "expected": qa_users,
            "existing": existing_users,
            "ok": len(existing_users) == 2,
        },
        "qa_roles": {
            "entries": has_roles,
            "ok": len(has_roles) > 0,
        },
        "site_permissions": {
            "entries": site_permissions,
            "ok": len(site_permissions) > 0,
        },
        "location_bridge": {
            "site_field_present": location_site_field,
            "mapped_locations_count": len(mapped_locations),
            "ok": location_site_field and len(mapped_locations) > 0,
        },
    }

    readiness["status"] = "ready" if all([
        readiness["sites"]["ok"],
        readiness["qa_users"]["ok"],
        readiness["qa_roles"]["ok"],
        readiness["site_permissions"]["ok"],
        readiness["location_bridge"]["ok"],
    ]) else "not_ready"

    return readiness
