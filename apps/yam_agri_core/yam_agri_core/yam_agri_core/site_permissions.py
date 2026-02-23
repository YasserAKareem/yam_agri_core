from __future__ import annotations

from typing import Iterable

import frappe


def get_allowed_sites(user: str | None = None) -> list[str]:
    user = user or frappe.session.user

    if user in ("Administrator",):
        return []

    if frappe.has_role("System Manager", user=user):
        return []

    # User Permission: allow='Site', for_value=<Site name>
    allowed = frappe.get_all(
        "User Permission",
        filters={"user": user, "allow": "Site"},
        pluck="for_value",
    )

    # Normalize + drop empties
    return [s for s in (v.strip() for v in allowed or []) if s]


def build_site_query_condition(doctype: str, user: str | None = None) -> str | None:
    """Return SQL WHERE condition for site isolation.

    - Returns None for System Manager / Administrator to allow full access.
    - Returns '1=0' when user has no allowed sites.
    """

    user = user or frappe.session.user

    if user in ("Administrator",):
        return None

    if frappe.has_role("System Manager", user=user):
        return None

    allowed_sites = get_allowed_sites(user)
    if not allowed_sites:
        return "1=0"

    escaped = ",".join(frappe.db.escape(s) for s in allowed_sites)
    return f"`tab{doctype}`.`site` in ({escaped})"


def has_site_permission(site: str | None, user: str | None = None) -> bool:
    user = user or frappe.session.user

    if user in ("Administrator",):
        return True

    if frappe.has_role("System Manager", user=user):
        return True

    if not site:
        return False

    allowed_sites = set(get_allowed_sites(user))
    return site in allowed_sites


def resolve_site(site_identifier: str | None) -> str:
    """Resolve a Site identifier to a Site document name.

    Supports:
    - direct match on name
    - fallback match on field 'site_name' if it exists
    - if None/blank: first available Site
    """

    if not site_identifier:
        site_name = frappe.db.get_value("Site", {}, "name")
        if not site_name:
            frappe.throw("No Site records exist; create a Site first.")
        return site_name

    site_identifier = site_identifier.strip()
    if frappe.db.exists("Site", site_identifier):
        return site_identifier

    meta = frappe.get_meta("Site")
    if meta.has_field("site_name"):
        by_site_name = frappe.db.get_value("Site", {"site_name": site_identifier}, "name")
        if by_site_name:
            return by_site_name

    frappe.throw(f"Site not found: {site_identifier}")


def assert_site_access(site: str, user: str | None = None) -> None:
    user = user or frappe.session.user
    if not has_site_permission(site, user=user):
        frappe.throw("Not permitted for this Site", frappe.PermissionError)


def site_query_conditions(user: str) -> str | None:
    user = user or frappe.session.user

    if user in ("Administrator",):
        return None

    if frappe.has_role("System Manager", user=user):
        return None

    allowed_sites = get_allowed_sites(user)
    if not allowed_sites:
        return "1=0"

    escaped = ",".join(frappe.db.escape(s) for s in allowed_sites)
    return f"`tabSite`.`name` in ({escaped})"


def yam_plot_query_conditions(user: str) -> str | None:
    return build_site_query_condition("YAM Plot", user=user)


def yam_soil_test_query_conditions(user: str) -> str | None:
    return build_site_query_condition("YAM Soil Test", user=user)


def yam_plot_yield_query_conditions(user: str) -> str | None:
    return build_site_query_condition("YAM Plot Yield", user=user)


def yam_crop_variety_query_conditions(user: str) -> str | None:
    return build_site_query_condition("YAM Crop Variety", user=user)


def yam_crop_variety_recommendation_query_conditions(user: str) -> str | None:
    return build_site_query_condition("YAM Crop Variety Recommendation", user=user)
