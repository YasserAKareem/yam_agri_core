from __future__ import annotations

import frappe
from frappe import _


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
			frappe.throw(_("No Site records exist; create a Site first."))
		return site_name

	site_identifier = site_identifier.strip()
	if frappe.db.exists("Site", site_identifier):
		return site_identifier

	meta = frappe.get_meta("Site")
	if meta.has_field("site_name"):
		by_site_name = frappe.db.get_value("Site", {"site_name": site_identifier}, "name")
		if by_site_name:
			return by_site_name

	frappe.throw(_("Site not found: {0}").format(site_identifier))


def _location_site(location: str | None) -> str | None:
	if not location:
		return None
	if not frappe.db.exists("DocType", "Location"):
		return None
	location_meta = frappe.get_meta("Location")
	if not location_meta.has_field("site"):
		return None
	return frappe.db.get_value("Location", location, "site")


def assert_site_access(site: str, user: str | None = None) -> None:
	user = user or frappe.session.user
	if not has_site_permission(site, user=user):
		frappe.throw(_("Not permitted for this Site"), frappe.PermissionError)
