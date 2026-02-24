from __future__ import annotations

import frappe
from frappe.permissions import add_permission, update_permission_property


def after_install() -> None:
	ensure_site_geo_fields()
	ensure_location_site_field()
	ensure_minimum_doc_permissions()

	# Dev convenience: workspace navigation + sample org chart (guarded)
	from yam_agri_core.yam_agri_core.dev_seed import (
		seed_dev_baseline_demo_data_if_enabled,
		seed_dev_org_chart_if_enabled,
	)
	from yam_agri_core.yam_agri_core.workflow_setup import ensure_workflow_states_from_active_workflows
	from yam_agri_core.yam_agri_core.workspace_setup import (
		ensure_agriculture_workspace_modernized,
		ensure_yam_agri_workspaces,
	)

	ensure_workflow_states_from_active_workflows()
	ensure_yam_agri_workspaces()
	ensure_agriculture_workspace_modernized()
	seed_dev_org_chart_if_enabled()
	seed_dev_baseline_demo_data_if_enabled()


def after_migrate() -> None:
	# Keeps dev/staging/prod consistent even if installed long ago.
	ensure_site_geo_fields()
	ensure_location_site_field()
	ensure_minimum_doc_permissions()
	normalize_lot_crop_links()

	from yam_agri_core.yam_agri_core.dev_seed import (
		seed_dev_baseline_demo_data_if_enabled,
		seed_dev_org_chart_if_enabled,
	)
	from yam_agri_core.yam_agri_core.workflow_setup import ensure_workflow_states_from_active_workflows
	from yam_agri_core.yam_agri_core.workspace_setup import (
		ensure_agriculture_workspace_modernized,
		ensure_yam_agri_workspaces,
	)

	ensure_workflow_states_from_active_workflows()
	ensure_yam_agri_workspaces()
	ensure_agriculture_workspace_modernized()
	seed_dev_org_chart_if_enabled()
	seed_dev_baseline_demo_data_if_enabled()


def normalize_lot_crop_links() -> None:
	"""Normalize legacy text values in Lot.crop to canonical Crop links.

	- Ensures every non-empty `Lot.crop` points to an existing Crop name.
	- Maps legacy text via `name`, `crop_name`, or `title` when available.
	- Logs unresolved values for manual cleanup.
	"""

	if not frappe.db.exists("DocType", "Lot"):
		return

	if not frappe.db.exists("DocType", "Crop"):
		return

	crop_meta = frappe.get_meta("Crop")
	has_crop_name = crop_meta.has_field("crop_name")
	has_title = crop_meta.has_field("title")

	lots = frappe.get_all("Lot", fields=["name", "crop"], limit_page_length=0)
	changed = False
	unresolved: set[str] = set()

	for lot in lots:
		raw_crop = (lot.get("crop") or "").strip()
		if not raw_crop:
			continue

		if frappe.db.exists("Crop", raw_crop):
			continue

		crop_name = None
		if has_crop_name:
			crop_name = frappe.db.get_value("Crop", {"crop_name": raw_crop}, "name")
		if not crop_name and has_title:
			crop_name = frappe.db.get_value("Crop", {"title": raw_crop}, "name")

		if crop_name:
			frappe.db.set_value("Lot", lot["name"], "crop", crop_name, update_modified=False)
			changed = True
			continue

		unresolved.add(raw_crop)

	if changed:
		frappe.db.commit()

	if unresolved:
		frappe.log_error(
			title="Lot crop normalization unresolved values",
			message="\n".join(sorted(unresolved)),
		)


def get_lot_crop_link_status() -> dict:
	"""Diagnostic summary for Lot->Crop migration readiness.

	Safe to run via:
	- bench --site <site> execute yam_agri_core.yam_agri_core.install.get_lot_crop_link_status
	"""
	if not frappe.db.exists("DocType", "Lot"):
		return {"available": False, "reason": "Lot doctype missing"}

	if not frappe.db.exists("DocType", "Crop"):
		return {"available": False, "reason": "Crop doctype missing"}

	crop_meta = frappe.get_meta("Crop")
	has_crop_name = crop_meta.has_field("crop_name")
	has_title = crop_meta.has_field("title")

	total = 0
	linked = 0
	mapped = 0
	unresolved_values: set[str] = set()

	lots = frappe.get_all("Lot", fields=["name", "crop"], limit_page_length=0)
	for lot in lots:
		total += 1
		crop_value = (lot.get("crop") or "").strip()
		if not crop_value:
			continue

		if frappe.db.exists("Crop", crop_value):
			linked += 1
			continue

		found = None
		if has_crop_name:
			found = frappe.db.get_value("Crop", {"crop_name": crop_value}, "name")
		if not found and has_title:
			found = frappe.db.get_value("Crop", {"title": crop_value}, "name")

		if found:
			mapped += 1
		else:
			unresolved_values.add(crop_value)

	return {
		"available": True,
		"total_lots": total,
		"linked_crop_names": linked,
		"mappable_legacy_values": mapped,
		"unresolved_count": len(unresolved_values),
		"unresolved_values": sorted(unresolved_values),
	}


def ensure_site_geo_fields() -> None:
	"""Ensure Site has centroid + polygon fields.

	- `geo_location`: Geolocation (typically point / centroid)
	- `boundary_geojson`: Code(JSON) storing polygon boundary
	"""

	if not frappe.db.exists("DocType", "Site"):
		# Nothing we can do; Site is expected to exist in the platform.
		return

	meta = frappe.get_meta("Site")

	# If Site already has these fields (e.g., our own DocType defines them),
	# do not create Custom Field entries that would conflict.
	if meta.has_field("geo_location") and meta.has_field("boundary_geojson"):
		return

	def pick_insert_after() -> str:
		for candidate in ("site_name", "description", "name"):
			if candidate == "name":
				return "description" if meta.has_field("description") else meta.fields[0].fieldname
			if meta.has_field(candidate):
				return candidate
		return meta.fields[0].fieldname

	insert_after = pick_insert_after()

	_ensure_custom_field(
		dt="Site",
		fieldname="geo_location",
		label="Geo Location",
		fieldtype="Geolocation",
		insert_after=insert_after,
	)

	_ensure_custom_field(
		dt="Site",
		fieldname="boundary_geojson",
		label="Boundary (GeoJSON)",
		fieldtype="Code",
		options="JSON",
		insert_after="geo_location",
	)


def ensure_location_site_field() -> None:
	"""Ensure Location has Site link for Agriculture site-isolation bridge."""

	if not frappe.db.exists("DocType", "Location"):
		return

	meta = frappe.get_meta("Location")
	if meta.has_field("site"):
		return

	insert_after = "location_name" if meta.has_field("location_name") else meta.fields[0].fieldname
	_ensure_custom_field(
		dt="Location",
		fieldname="site",
		label="Site",
		fieldtype="Link",
		options="Site",
		insert_after=insert_after,
	)


def ensure_minimum_doc_permissions() -> None:
	"""Keep critical DocType permissions aligned for QA flows.

	This prevents legacy Custom DocPerm drift from removing QA Manager access.
	"""

	_ensure_doctype_role_permissions(
		doctype="Lot",
		role="QA Manager",
		flags={"read": 1, "write": 1, "create": 0, "delete": 0},
	)
	_ensure_doctype_role_permissions(
		doctype="Lot",
		role="System Manager",
		flags={"read": 1, "write": 1, "create": 1, "delete": 1},
	)
	_ensure_doctype_role_permissions(
		doctype="StorageBin",
		role="QA Manager",
		flags={"read": 1, "write": 1, "create": 1, "delete": 0},
	)
	_ensure_doctype_role_permissions(
		doctype="StorageBin",
		role="System Manager",
		flags={"read": 1, "write": 1, "create": 1, "delete": 0},
	)


def _ensure_doctype_role_permissions(*, doctype: str, role: str, flags: dict[str, int]) -> None:
	if not frappe.db.exists("DocType", doctype):
		return

	has_row = frappe.db.exists(
		"Custom DocPerm",
		{"parent": doctype, "role": role, "permlevel": 0},
	)
	if not has_row:
		add_permission(doctype, role, 0)

	for fieldname, value in flags.items():
		update_permission_property(doctype, role, 0, fieldname, int(value))


def get_site_location_bridge_status() -> dict:
	"""Diagnostic summary for Site->Location bridge used by Agriculture isolation.

	Safe to run via:
	- bench --site <site> execute yam_agri_core.yam_agri_core.install.get_site_location_bridge_status
	"""
	if not frappe.db.exists("DocType", "Location"):
		return {"available": False, "reason": "Location doctype missing"}

	location_meta = frappe.get_meta("Location")
	if not location_meta.has_field("site"):
		return {"available": False, "reason": "Location.site custom field missing"}

	rows = frappe.get_all("Location", fields=["name", "site"], limit_page_length=0)
	mapped = [r.get("name") for r in rows if (r.get("site") or "").strip()]
	unmapped = [r.get("name") for r in rows if not (r.get("site") or "").strip()]

	return {
		"available": True,
		"total_locations": len(rows),
		"mapped_count": len(mapped),
		"unmapped_count": len(unmapped),
		"unmapped_locations": sorted(unmapped),
	}


def _ensure_custom_field(
	*,
	dt: str,
	fieldname: str,
	label: str,
	fieldtype: str,
	insert_after: str,
	options: str | None = None,
) -> None:
	existing = frappe.db.get_value(
		"Custom Field",
		{"dt": dt, "fieldname": fieldname},
		"name",
	)
	if existing:
		return

	doc = frappe.get_doc(
		{
			"doctype": "Custom Field",
			"dt": dt,
			"fieldname": fieldname,
			"label": label,
			"fieldtype": fieldtype,
			"insert_after": insert_after,
		}
	)
	if options:
		doc.options = options

	doc.save(ignore_permissions=True)
	frappe.db.commit()
