from __future__ import annotations

import frappe

from yam_agri_core.yam_agri_core.ai.agr_cereal_001 import recommend
from yam_agri_core.yam_agri_core.site_permissions import assert_site_access


def execute(filters=None):
	filters = frappe._dict(filters or {})

	site = (filters.get("site") or "").strip()
	season = (filters.get("season") or "").strip()
	crop = (filters.get("crop") or "").strip()

	if not site or not season or not crop:
		return _columns(), [], None, None

	assert_site_access(site)

	varieties = _get_varieties(site=site, crop=crop)

	plot = {"site": site, "last_crop": ""}
	soil_test = None
	yield_history = []

	recs = recommend(
		plot=plot,
		season=season,
		crop=crop,
		varieties=varieties,
		soil_test=soil_test,
		yield_history=yield_history,
	)

	rows = [
		{
			"variety": r.variety,
			"score": r.score,
			"predicted_yield_kg_per_ha": r.predicted_yield_kg_per_ha,
			"predicted_margin_per_ha": r.predicted_margin_per_ha,
			"rotation_compliance": 1 if r.rotation_compliance else 0,
			"confidence": r.confidence,
		}
		for r in recs
	]

	chart = {
		"data": {
			"labels": [r.variety for r in recs[:10]],
			"datasets": [
				{
					"name": "Predicted Margin/ha",
					"values": [r.predicted_margin_per_ha for r in recs[:10]],
				}
			],
		},
		"type": "bar",
	}

	return _columns(), rows, None, chart


def _columns():
	return [
		{
			"label": "Variety",
			"fieldname": "variety",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": "Score",
			"fieldname": "score",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": "Predicted Yield (kg/ha)",
			"fieldname": "predicted_yield_kg_per_ha",
			"fieldtype": "Float",
			"width": 160,
		},
		{
			"label": "Predicted Margin/ha",
			"fieldname": "predicted_margin_per_ha",
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"label": "Rotation Compliant",
			"fieldname": "rotation_compliance",
			"fieldtype": "Check",
			"width": 130,
		},
		{
			"label": "Confidence",
			"fieldname": "confidence",
			"fieldtype": "Float",
			"width": 110,
		},
	]


def _get_varieties(*, site: str, crop: str) -> list[dict]:
	# Prefer real master data when the DocType is installed/migrated.
	try:
		if frappe.db.exists("DocType", "YAM Crop Variety"):
			rows = frappe.get_all(
				"YAM Crop Variety",
				filters={"site": site, "crop": crop},
				fields=["variety_name", "maturity_days", "drought_tolerance"],
				limit=200,
			)
			if rows:
				return rows
	except Exception:
		# If DocType doesn't exist yet, or DB isn't migrated, fall back to demo.
		pass

	# Demo varieties so the report renders immediately.
	crop_l = (crop or "").strip().lower()
	if crop_l in ("wheat", "triticum aestivum"):
		return [
			{"variety_name": "WHT-Prime", "maturity_days": 115, "drought_tolerance": 4.2},
			{"variety_name": "WHT-Early", "maturity_days": 95, "drought_tolerance": 3.0},
			{"variety_name": "WHT-HighYield", "maturity_days": 135, "drought_tolerance": 2.6},
		]

	return [
		{"variety_name": f"{crop.upper()}-A", "maturity_days": 110, "drought_tolerance": 3.0},
		{"variety_name": f"{crop.upper()}-B", "maturity_days": 125, "drought_tolerance": 3.8},
	]
