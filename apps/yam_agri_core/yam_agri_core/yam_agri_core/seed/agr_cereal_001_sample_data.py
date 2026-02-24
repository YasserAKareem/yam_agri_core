from __future__ import annotations

import json
from datetime import date

import frappe


def create_sample_data(
	*,
	site_name: str = "DEMO-SITE",
	crop_name: str = "Wheat",
	plot_name: str = "P-001",
	confirm: int = 0,
	overwrite: int = 0,
) -> dict:
	"""Create minimal sample records for AGR-CEREAL-001 demos.

	This function performs INSERT/UPDATEs and is intended to be called manually via:
	`bench --site <site> execute ... --kwargs '{"confirm":1, ...}'`.

	Safety:
	- Refuses to write unless `confirm=1`.
	- Idempotent: re-running updates existing records when `overwrite=1`, otherwise keeps them.
	"""

	if int(confirm) != 1:
		frappe.throw(
			"Refusing to write sample data. Re-run with confirm=1.",
			exc=frappe.ValidationError,
		)

	_ensure_required_doctypes()

	overwrite_b = bool(int(overwrite))

	site = _get_or_create_site(site_name=site_name, overwrite=overwrite_b)

	crop = _ensure_crop(crop_name)
	last_crop = _ensure_crop("Barley")

	plot = _get_or_create_plot(site=site, plot_name=plot_name, last_crop=last_crop, overwrite=overwrite_b)

	soil_test = _get_or_create_soil_test(site=site, plot=plot, overwrite=overwrite_b)

	yields = [
		_get_or_create_plot_yield(
			site=site, plot=plot, season="2024", crop=crop, yield_kg_per_ha=2600, overwrite=overwrite_b
		),
		_get_or_create_plot_yield(
			site=site, plot=plot, season="2025", crop=crop, yield_kg_per_ha=2400, overwrite=overwrite_b
		),
	]

	varieties = [
		_get_or_create_variety(
			site=site,
			crop=crop,
			variety_name="WHT-Prime",
			maturity_days=115,
			drought_tolerance=4.2,
			overwrite=overwrite_b,
		),
		_get_or_create_variety(
			site=site,
			crop=crop,
			variety_name="WHT-Early",
			maturity_days=95,
			drought_tolerance=3.0,
			overwrite=overwrite_b,
		),
		_get_or_create_variety(
			site=site,
			crop=crop,
			variety_name="WHT-HighYield",
			maturity_days=135,
			drought_tolerance=2.6,
			overwrite=overwrite_b,
		),
	]

	frappe.db.commit()

	return {
		"site": site,
		"crop": crop,
		"plot": plot,
		"soil_test": soil_test,
		"yields": yields,
		"varieties": varieties,
	}


def _ensure_required_doctypes() -> None:
	required = [
		"Site",
		"YAM Crop Variety",
		"YAM Plot",
		"YAM Soil Test",
		"YAM Plot Yield",
		"Crop",
	]

	missing = [dt for dt in required if not frappe.db.exists("DocType", dt)]
	if missing:
		frappe.throw(
			f"Missing required DocTypes: {', '.join(missing)}. Run migrate and install required apps.",
			exc=frappe.ValidationError,
		)


def _get_or_create_site(*, site_name: str, overwrite: bool) -> str:
	existing = frappe.get_all("Site", filters={"site_name": site_name}, pluck="name", limit=1)
	if existing:
		name = existing[0]
		if overwrite:
			doc = frappe.get_doc("Site", name)
			doc.site_type = doc.site_type or "Farm"
			doc.description = doc.description or "Demo site for AGR-CEREAL-001"
			doc.geo_location = doc.geo_location or "29.9792, 31.1342"
			doc.boundary_geojson = doc.boundary_geojson or _demo_polygon_geojson()
			doc.save(ignore_permissions=True)
		return name

	doc = frappe.get_doc(
		{
			"doctype": "Site",
			"site_name": site_name,
			"site_type": "Farm",
			"description": "Demo site for AGR-CEREAL-001",
			"geo_location": "29.9792, 31.1342",
			"boundary_geojson": _demo_polygon_geojson(),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _demo_polygon_geojson() -> str:
	# A tiny square polygon near the demo geo_location.
	geojson = {
		"type": "Polygon",
		"coordinates": [
			[
				[31.1338, 29.9788],
				[31.1346, 29.9788],
				[31.1346, 29.9796],
				[31.1338, 29.9796],
				[31.1338, 29.9788],
			]
		],
	}
	return json.dumps(geojson, separators=(",", ":"), ensure_ascii=False)


def _ensure_crop(crop_name: str) -> str:
	crop_name = (crop_name or "").strip()
	if not crop_name:
		frappe.throw("crop_name is required", exc=frappe.ValidationError)

	if frappe.db.exists("Crop", crop_name):
		return crop_name

	# Try best-effort creation with required fields.
	try:
		meta = frappe.get_meta("Crop")
		required_fields = [f for f in meta.fields if getattr(f, "reqd", 0)]

		doc = frappe.new_doc("Crop")
		if hasattr(doc, "crop_name"):
			doc.crop_name = crop_name
		if hasattr(doc, "crop"):
			doc.crop = crop_name

		# Populate any other required fields minimally.
		for df in required_fields:
			if df.fieldname in ("crop_name", "crop"):
				continue
			if getattr(doc, df.fieldname, None):
				continue

			if df.fieldtype in ("Data", "Small Text", "Long Text"):
				setattr(doc, df.fieldname, crop_name)
			elif df.fieldtype == "Select":
				options = [o.strip() for o in (df.options or "").split("\n") if o.strip()]
				if options:
					setattr(doc, df.fieldname, options[0])
			elif df.fieldtype in ("Int", "Float", "Currency"):
				setattr(doc, df.fieldname, 0)
			elif df.fieldtype == "Date":
				setattr(doc, df.fieldname, date.today().isoformat())

		# If Crop uses a name field mapping, this usually works.
		doc.name = crop_name
		doc.insert(ignore_permissions=True)
		return doc.name
	except Exception:
		# Fallback: use any existing crop so downstream Links are valid.
		first = frappe.get_all("Crop", pluck="name", limit=1)
		if first:
			return first[0]
		raise


def _get_or_create_plot(*, site: str, plot_name: str, last_crop: str, overwrite: bool) -> str:
	existing = frappe.get_all(
		"YAM Plot",
		filters={"site": site, "plot_name": plot_name},
		pluck="name",
		limit=1,
	)
	if existing:
		name = existing[0]
		if overwrite:
			doc = frappe.get_doc("YAM Plot", name)
			doc.area_ha = doc.area_ha or 10
			doc.last_crop = doc.last_crop or last_crop
			doc.boundary_geojson = doc.boundary_geojson or _demo_polygon_geojson()
			doc.save(ignore_permissions=True)
		return name

	doc = frappe.get_doc(
		{
			"doctype": "YAM Plot",
			"plot_name": plot_name,
			"site": site,
			"area_ha": 10,
			"last_crop": last_crop,
			"boundary_geojson": _demo_polygon_geojson(),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _get_or_create_soil_test(*, site: str, plot: str, overwrite: bool) -> str:
	# Keep just one soil test per plot for demo purposes.
	existing = frappe.get_all(
		"YAM Soil Test",
		filters={"site": site, "plot": plot},
		pluck="name",
		limit=1,
	)
	if existing:
		name = existing[0]
		if overwrite:
			doc = frappe.get_doc("YAM Soil Test", name)
			doc.sample_date = doc.sample_date or date.today().isoformat()
			doc.organic_matter_pct = doc.organic_matter_pct or 2.7
			doc.ph = doc.ph or 7.4
			doc.save(ignore_permissions=True)
		return name

	doc = frappe.get_doc(
		{
			"doctype": "YAM Soil Test",
			"site": site,
			"plot": plot,
			"sample_date": date.today().isoformat(),
			"organic_matter_pct": 2.7,
			"ph": 7.4,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _get_or_create_plot_yield(
	*,
	site: str,
	plot: str,
	season: str,
	crop: str,
	yield_kg_per_ha: float,
	overwrite: bool,
) -> str:
	existing = frappe.get_all(
		"YAM Plot Yield",
		filters={"site": site, "plot": plot, "season": season, "crop": crop},
		pluck="name",
		limit=1,
	)
	if existing:
		name = existing[0]
		if overwrite:
			doc = frappe.get_doc("YAM Plot Yield", name)
			doc.yield_kg_per_ha = yield_kg_per_ha
			doc.save(ignore_permissions=True)
		return name

	doc = frappe.get_doc(
		{
			"doctype": "YAM Plot Yield",
			"site": site,
			"plot": plot,
			"season": season,
			"crop": crop,
			"yield_kg_per_ha": yield_kg_per_ha,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _get_or_create_variety(
	*,
	site: str,
	crop: str,
	variety_name: str,
	maturity_days: int,
	drought_tolerance: float,
	overwrite: bool,
) -> str:
	# autoname is field:variety_name, so name==variety_name.
	if frappe.db.exists("YAM Crop Variety", variety_name):
		if overwrite:
			doc = frappe.get_doc("YAM Crop Variety", variety_name)
			doc.site = site
			doc.crop = crop
			doc.maturity_days = maturity_days
			doc.drought_tolerance = drought_tolerance
			doc.save(ignore_permissions=True)
		return variety_name

	doc = frappe.get_doc(
		{
			"doctype": "YAM Crop Variety",
			"site": site,
			"crop": crop,
			"variety_name": variety_name,
			"maturity_days": maturity_days,
			"drought_tolerance": drought_tolerance,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name
