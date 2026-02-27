from __future__ import annotations

import frappe

from yam_agri_core.yam_agri_core.permissions.site_scope import (
	_location_site,
	_user_has_role,
	get_allowed_sites,
	has_site_permission,
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



def _site_has_permission(site: str | None, user: str | None = None) -> bool:
	user = user or frappe.session.user

	if user in ("Administrator",):
		return True

	if _user_has_role("System Manager", user=user):
		return True

	return has_site_permission(site, user=user)


def _doctype_has_site_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
	user = user or frappe.session.user

	if user in ("Administrator",):
		return True

	if _user_has_role("System Manager", user=user):
		return True

	if doc is None:
		return bool(get_allowed_sites(user=user))

	site = _extract_doc_site(doc)
	if site:
		return _site_has_permission(site, user=user)

	docname = doc.get("name") if isinstance(doc, dict) else getattr(doc, "name", None)
	doctype = doc.get("doctype") if isinstance(doc, dict) else getattr(doc, "doctype", None)
	if docname and doctype and frappe.db.exists(doctype, docname):
		doc_site = frappe.db.get_value(doctype, docname, "site")
		return _site_has_permission(doc_site, user=user)

	return False


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


def observation_threshold_policy_has_permission(
	doc, user: str | None = None, permission_type: str | None = None
) -> bool:
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


def season_policy_has_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
	return _doctype_has_site_permission(doc, user=user, permission_type=permission_type)


def site_tolerance_policy_has_permission(
	doc, user: str | None = None, permission_type: str | None = None
) -> bool:
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


def yam_plot_has_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
	return _doctype_has_site_permission(doc, user=user, permission_type=permission_type)


def yam_soil_test_has_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
	return _doctype_has_site_permission(doc, user=user, permission_type=permission_type)


def yam_plot_yield_has_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
	return _doctype_has_site_permission(doc, user=user, permission_type=permission_type)


def yam_crop_variety_has_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
	return _doctype_has_site_permission(doc, user=user, permission_type=permission_type)


def yam_crop_variety_recommendation_has_permission(
	doc, user: str | None = None, permission_type: str | None = None
) -> bool:
	return _doctype_has_site_permission(doc, user=user, permission_type=permission_type)
