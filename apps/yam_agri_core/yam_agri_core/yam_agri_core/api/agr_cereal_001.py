from __future__ import annotations

import frappe

from yam_agri_core.yam_agri_core.ai.agr_cereal_001 import recommend
from yam_agri_core.yam_agri_core.site_permissions import assert_site_access


@frappe.whitelist()
def get_variety_recommendations(
    *,
    site: str,
    season: str,
    crop: str,
    plot: dict | None = None,
    soil_test: dict | None = None,
    yield_history: list[dict] | None = None,
    varieties: list[dict] | None = None,
    price_per_kg: float | None = None,
    base_cost_per_ha: float | None = None,
) -> dict:
    """Return crop-variety recommendations (proposal only; no writes).

    Inputs are kept as dicts for MVP to avoid hard dependency on new DocTypes.
    """

    assert_site_access(site)

    plot = plot or {}
    plot.setdefault("site", site)

    varieties = varieties or _get_varieties(site=site, crop=crop)

    recs = recommend(
        plot=plot,
        season=season,
        crop=crop,
        varieties=varieties,
        soil_test=soil_test,
        yield_history=yield_history,
        price_per_kg=float(price_per_kg) if price_per_kg is not None else 0.25,
        base_cost_per_ha=float(base_cost_per_ha) if base_cost_per_ha is not None else 300.0,
    )

    return {
        "site": site,
        "season": season,
        "crop": crop,
        "count": len(recs),
        "recommendations": [
            {
                "crop": r.crop,
                "variety": r.variety,
                "score": r.score,
                "predicted_yield_kg_per_ha": r.predicted_yield_kg_per_ha,
                "predicted_margin_per_ha": r.predicted_margin_per_ha,
                "rotation_compliance": r.rotation_compliance,
                "confidence": r.confidence,
                "explanation": r.explanation,
            }
            for r in recs
        ],
    }


def _get_varieties(*, site: str, crop: str) -> list[dict]:
    try:
        if frappe.db.exists("DocType", "YAM Crop Variety"):
            rows = frappe.get_all(
                "YAM Crop Variety",
                filters={"site": site, "crop": crop},
                fields=["variety_name", "maturity_days", "drought_tolerance"],
                limit=500,
            )
            return rows or []
    except Exception:
        return []

    return []
