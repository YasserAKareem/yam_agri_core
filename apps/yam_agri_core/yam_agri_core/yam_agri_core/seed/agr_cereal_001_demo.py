from __future__ import annotations

import frappe

from yam_agri_core.yam_agri_core.api.agr_cereal_001 import get_variety_recommendations
from yam_agri_core.yam_agri_core.site_permissions import assert_site_access


@frappe.whitelist()
def run_demo(*, site: str = "") -> dict:
	"""Return a demo payload and recommendations for AGR-CEREAL-001.

	No writes; safe to run repeatedly.
	"""

	site = site or _default_site()
	assert_site_access(site)

	season = "2026"
	crop = "Wheat"

	plot = {
		"site": site,
		"plot_name": "P-001",
		"area_ha": 10,
		"last_crop": "Barley",
	}

	soil_test = {
		"site": site,
		"organic_matter_pct": 2.7,
		"ph": 7.4,
	}

	yield_history = [
		{"season": "2024", "crop": "Wheat", "yield_kg_per_ha": 2600},
		{"season": "2025", "crop": "Wheat", "yield_kg_per_ha": 2400},
	]

	varieties = [
		{"variety_name": "WHT-Prime", "maturity_days": 115, "drought_tolerance": 4.2},
		{"variety_name": "WHT-Early", "maturity_days": 95, "drought_tolerance": 3.0},
		{"variety_name": "WHT-HighYield", "maturity_days": 135, "drought_tolerance": 2.6},
	]

	result = get_variety_recommendations(
		site=site,
		season=season,
		crop=crop,
		plot=plot,
		soil_test=soil_test,
		yield_history=yield_history,
		varieties=varieties,
		price_per_kg=0.25,
		base_cost_per_ha=300.0,
	)

	return {
		"demo_input": {
			"site": site,
			"season": season,
			"crop": crop,
			"plot": plot,
			"soil_test": soil_test,
			"yield_history": yield_history,
			"varieties": varieties,
		},
		"result": result,
	}


def _default_site() -> str:
	# Frappe core normally uses `Site` DocType.
	# For demo, pick first site the user can access.
	if not frappe.db.exists("DocType", "Site"):
		return ""

	site = frappe.get_all("Site", pluck="name", limit=1)
	if site:
		return site[0]

	return ""  # caller must provide
