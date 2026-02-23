from __future__ import annotations

import frappe


def after_install() -> None:
    ensure_site_geo_fields()


def after_migrate() -> None:
    # Keeps dev/staging/prod consistent even if installed long ago.
    ensure_site_geo_fields()


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
