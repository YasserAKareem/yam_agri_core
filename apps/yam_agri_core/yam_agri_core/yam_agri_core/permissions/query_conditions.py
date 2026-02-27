from __future__ import annotations

import frappe

from yam_agri_core.yam_agri_core.permissions.site_scope import (
	_user_has_role,
	get_allowed_locations,
	get_allowed_sites,
)


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


def observation_threshold_policy_query_conditions(user: str) -> str | None:
	return build_site_query_condition("Observation Threshold Policy", user=user)


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


def season_policy_query_conditions(user: str) -> str | None:
	return build_site_query_condition("Season Policy", user=user)


def site_tolerance_policy_query_conditions(user: str) -> str | None:
	return build_site_query_condition("Site Tolerance Policy", user=user)


def ai_interaction_log_query_conditions(user: str) -> str | None:
	return build_site_query_condition("AI Interaction Log", user=user)


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
