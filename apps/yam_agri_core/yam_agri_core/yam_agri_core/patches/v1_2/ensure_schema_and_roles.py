import frappe
from frappe.permissions import add_permission, update_permission_property


def execute():
	ensure_site_geo_fields()
	ensure_location_site_field()
	ensure_role_profiles()
	ensure_minimum_doc_permissions()


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


def ensure_role_profiles() -> None:
	"""Create baseline role profiles used by site-isolated operators.

	Note: access to business records is still constrained by Site User Permissions.
	These profiles grant role capabilities only; without explicit Site grants,
	query hooks return no records by default.
	"""

	if not frappe.db.exists("DocType", "Role Profile"):
		return

	_ensure_role_profile(
		"YAM QA Manager",
		[
			"QA Manager",
			"Agriculture Manager",
		],
	)
	_ensure_role_profile(
		"YAM Site Operator",
		[
			"Quality Manager",
			"Stock User",
		],
	)


def _ensure_role_profile(profile_name: str, roles: list[str]) -> None:
	if frappe.db.exists("Role Profile", profile_name):
		doc = frappe.get_doc("Role Profile", profile_name)
	else:
		doc = frappe.new_doc("Role Profile")
		doc.role_profile = profile_name

	existing_roles = {row.role for row in (doc.get("roles") or []) if row.role}
	for role in roles:
		if not role or not frappe.db.exists("Role", role):
			continue
		if role not in existing_roles:
			doc.append("roles", {"role": role})

	doc.save(ignore_permissions=True)
	frappe.db.commit()


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
	"""Diagnostic summary for Site->Location bridge used by site isolation.

	Safe to run via:
	- bench --site <site> execute yam_agri_core.yam_agri_core.patches.v1_2.ensure_schema_and_roles.get_site_location_bridge_status
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
