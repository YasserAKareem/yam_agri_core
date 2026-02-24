from __future__ import annotations

from typing import Iterable

import frappe


def _user_has_role(role: str, user: str | None = None) -> bool:
    user = user or frappe.session.user
    try:
        return role in (frappe.get_roles(user) or [])
    except Exception:
        return False


def get_allowed_sites(user: str | None = None) -> list[str]:
    user = user or frappe.session.user

    if user in ("Administrator",):
        return []

    if _user_has_role("System Manager", user=user):
        return []

    # User Permission: allow='Site', for_value=<Site name>
    allowed = frappe.get_all(
        "User Permission",
        filters={"user": user, "allow": "Site"},
        pluck="for_value",
    )

    # Normalize + drop empties
    return [s for s in (v.strip() for v in allowed or []) if s]


def get_allowed_locations(user: str | None = None) -> list[str]:
    user = user or frappe.session.user

    if user in ("Administrator",):
        return []

    if _user_has_role("System Manager", user=user):
        return []

    if not frappe.db.exists("DocType", "Location"):
        return []

    location_meta = frappe.get_meta("Location")
    if not location_meta.has_field("site"):
        return []

    allowed_sites = get_allowed_sites(user)
    if not allowed_sites:
        return []

    locations = frappe.get_all("Location", filters={"site": ["in", allowed_sites]}, pluck="name")
    return [loc for loc in (v.strip() for v in (locations or [])) if loc]


def build_site_query_condition(doctype: str, user: str | None = None) -> str | None:
    """Return SQL WHERE condition for site isolation.

    - Returns None for System Manager / Administrator to allow full access.
    - Returns '1=0' when user has no allowed sites.
    """

    user = user or frappe.session.user

    if user in ("Administrator",):
        return None

    if _user_has_role("System Manager", user=user):
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

    if _user_has_role("System Manager", user=user):
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

    if _user_has_role("System Manager", user=user):
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


def lot_query_conditions(user: str) -> str | None:
    return build_site_query_condition("Lot", user=user)


def qc_test_query_conditions(user: str) -> str | None:
    return build_site_query_condition("QCTest", user=user)


def certificate_query_conditions(user: str) -> str | None:
    return build_site_query_condition("Certificate", user=user)


def nonconformance_query_conditions(user: str) -> str | None:
    return build_site_query_condition("Nonconformance", user=user)


def device_query_conditions(user: str) -> str | None:
    return build_site_query_condition("Device", user=user)


def observation_query_conditions(user: str) -> str | None:
    return build_site_query_condition("Observation", user=user)


def scale_ticket_query_conditions(user: str) -> str | None:
    return build_site_query_condition("ScaleTicket", user=user)


def transfer_query_conditions(user: str) -> str | None:
    return build_site_query_condition("Transfer", user=user)


def storage_bin_query_conditions(user: str) -> str | None:
    return build_site_query_condition("StorageBin", user=user)


def evidence_pack_query_conditions(user: str) -> str | None:
    return build_site_query_condition("EvidencePack", user=user)


def complaint_query_conditions(user: str) -> str | None:
    return build_site_query_condition("Complaint", user=user)


def location_query_conditions(user: str) -> str | None:
    user = user or frappe.session.user

    if user in ("Administrator",):
        return None

    if _user_has_role("System Manager", user=user):
        return None

    if not frappe.db.exists("DocType", "Location"):
        return None

    location_meta = frappe.get_meta("Location")
    if not location_meta.has_field("site"):
        return None

    allowed_sites = get_allowed_sites(user)
    if not allowed_sites:
        return "1=0"

    escaped = ",".join(frappe.db.escape(s) for s in allowed_sites)
    return f"`tabLocation`.`site` in ({escaped})"


def weather_query_conditions(user: str) -> str | None:
    user = user or frappe.session.user

    if user in ("Administrator",):
        return None

    if _user_has_role("System Manager", user=user):
        return None

    allowed_locations = get_allowed_locations(user)
    if not allowed_locations:
        return "1=0"

    escaped = ",".join(frappe.db.escape(loc) for loc in allowed_locations)
    return f"`tabWeather`.`location` in ({escaped})"


def crop_cycle_query_conditions(user: str) -> str | None:
    user = user or frappe.session.user

    if user in ("Administrator",):
        return None

    if _user_has_role("System Manager", user=user):
        return None

    allowed_locations = get_allowed_locations(user)
    if not allowed_locations:
        return "1=0"

    escaped = ",".join(frappe.db.escape(loc) for loc in allowed_locations)
    return (
        "exists ("
        "select 1 from `tabLinked Location` ll "
        "where ll.parent = `tabCrop Cycle`.`name` "
        "and ll.parenttype = 'Crop Cycle' "
        f"and ll.location in ({escaped})"
        ")"
    )


def _extract_doc_site(doc) -> str | None:
    site = None

    if isinstance(doc, dict):
        site = doc.get("site")
    else:
        site = getattr(doc, "site", None)

    if site:
        return str(site).strip()
    return None


def _extract_doc_location(doc) -> str | None:
    location = None

    if isinstance(doc, dict):
        location = doc.get("location")
    else:
        location = getattr(doc, "location", None)

    if location:
        return str(location).strip()
    return None


def _location_site(location: str | None) -> str | None:
    if not location:
        return None
    if not frappe.db.exists("DocType", "Location"):
        return None
    location_meta = frappe.get_meta("Location")
    if not location_meta.has_field("site"):
        return None
    return frappe.db.get_value("Location", location, "site")


def _site_has_permission(site: str | None, user: str | None = None) -> bool:
    user = user or frappe.session.user

    if user in ("Administrator",):
        return True

    if _user_has_role("System Manager", user=user):
        return True

    return has_site_permission(site, user=user)


def _doctype_has_site_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
    return _site_has_permission(_extract_doc_site(doc), user=user)


def site_has_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
    if isinstance(doc, dict):
        site_name = doc.get("name") or doc.get("site")
    else:
        site_name = getattr(doc, "name", None) or getattr(doc, "site", None)
    return _site_has_permission(site_name, user=user)


def lot_has_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
    return _doctype_has_site_permission(doc, user=user, permission_type=permission_type)


def qc_test_has_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
    return _doctype_has_site_permission(doc, user=user, permission_type=permission_type)


def certificate_has_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
    return _doctype_has_site_permission(doc, user=user, permission_type=permission_type)


def nonconformance_has_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
    return _doctype_has_site_permission(doc, user=user, permission_type=permission_type)


def device_has_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
    return _doctype_has_site_permission(doc, user=user, permission_type=permission_type)


def observation_has_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
    return _doctype_has_site_permission(doc, user=user, permission_type=permission_type)


def scale_ticket_has_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
    return _doctype_has_site_permission(doc, user=user, permission_type=permission_type)


def transfer_has_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
    return _doctype_has_site_permission(doc, user=user, permission_type=permission_type)


def storage_bin_has_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
    return _doctype_has_site_permission(doc, user=user, permission_type=permission_type)


def evidence_pack_has_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
    return _doctype_has_site_permission(doc, user=user, permission_type=permission_type)


def complaint_has_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
    return _doctype_has_site_permission(doc, user=user, permission_type=permission_type)


def location_has_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
    location = None
    if isinstance(doc, dict):
        location = doc.get("name")
    else:
        location = getattr(doc, "name", None)
    return _site_has_permission(_location_site(location), user=user)


def weather_has_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
    return _site_has_permission(_location_site(_extract_doc_location(doc)), user=user)


def crop_cycle_has_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
    if user in ("Administrator",):
        return True
    if _user_has_role("System Manager", user=user):
        return True

    cycle_name = doc.get("name") if isinstance(doc, dict) else getattr(doc, "name", None)
    if not cycle_name:
        return False

    locations = frappe.get_all(
        "Linked Location",
        filters={"parent": cycle_name, "parenttype": "Crop Cycle"},
        pluck="location",
    )
    if not locations:
        return False

    allowed_sites = set(get_allowed_sites(user=user))
    if not allowed_sites:
        return False

    for location in locations:
        site = _location_site(location)
        if site and site in allowed_sites:
            return True

    return False


def enforce_qc_test_site_consistency(doc, method: str | None = None) -> None:
    site = (getattr(doc, "site", None) or "").strip()
    if not site:
        frappe.throw("Every record must belong to a Site", frappe.ValidationError)

    assert_site_access(site)

    lot = (getattr(doc, "lot", None) or "").strip()
    if lot:
        lot_site = frappe.db.get_value("Lot", lot, "site")
        if lot_site and str(lot_site).strip() != site:
            frappe.throw("Lot site must match QCTest site", frappe.ValidationError)


def enforce_certificate_site_consistency(doc, method: str | None = None) -> None:
    site = (getattr(doc, "site", None) or "").strip()
    if not site:
        frappe.throw("Every record must belong to a Site", frappe.ValidationError)

    assert_site_access(site)

    lot = (getattr(doc, "lot", None) or "").strip()
    if lot:
        lot_site = frappe.db.get_value("Lot", lot, "site")
        if lot_site and str(lot_site).strip() != site:
            frappe.throw("Lot site must match Certificate site", frappe.ValidationError)
