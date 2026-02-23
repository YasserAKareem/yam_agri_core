from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Recommendation:
    crop: str
    variety: str
    score: float
    predicted_yield_kg_per_ha: float
    predicted_margin_per_ha: float
    rotation_compliance: bool
    confidence: float
    explanation: str


def recommend(
    *,
    plot: dict,
    season: str,
    crop: str,
    varieties: list[dict],
    soil_test: dict | None = None,
    yield_history: list[dict] | None = None,
    price_per_kg: float = 0.25,
    base_cost_per_ha: float = 300.0,
) -> list[Recommendation]:
    """Deterministic, explainable recommender for AGR-CEREAL-001.

    This is intentionally simple for MVP and designed for auditability.
    """

    yield_history = yield_history or []

    last_crop = (plot.get("last_crop") or "").strip()
    rotation_compliance = (last_crop.lower() != crop.lower()) if last_crop else True

    history_for_crop = [y for y in yield_history if (y.get("crop") or "").strip().lower() == crop.lower()]
    if history_for_crop:
        base_yield = sum(float(y.get("yield_kg_per_ha") or 0) for y in history_for_crop) / max(
            1, len(history_for_crop)
        )
    else:
        base_yield = 2500.0

    om = None
    if soil_test:
        try:
            om = float(soil_test.get("organic_matter_pct"))
        except (TypeError, ValueError):
            om = None

    confidence = 0.3
    if soil_test:
        confidence += 0.3
    if yield_history:
        confidence += 0.3
    if rotation_compliance:
        confidence += 0.1
    confidence = max(0.0, min(1.0, confidence))

    recs: list[Recommendation] = []
    for v in varieties:
        variety_name = (v.get("variety_name") or v.get("name") or "").strip()
        if not variety_name:
            continue

        maturity_days = _safe_float(v.get("maturity_days"))
        drought_tol = _safe_float(v.get("drought_tolerance"))

        yield_adj = 0.0
        explain_bits: list[str] = []

        if om is not None:
            # organic matter: crude modifier +/- 10%
            if om >= 3.0:
                yield_adj += 0.08
                explain_bits.append(f"Organic matter {om:.1f}% supports yield (+8%).")
            elif om <= 1.5:
                yield_adj -= 0.07
                explain_bits.append(f"Organic matter {om:.1f}% is low (-7%).")
            else:
                explain_bits.append(f"Organic matter {om:.1f}% neutral.")
        else:
            explain_bits.append("No soil test organic matter available.")

        if drought_tol is not None:
            # drought tolerance score 0-5
            yield_adj += (drought_tol - 2.5) * 0.01
            explain_bits.append(f"Drought tolerance {drought_tol:.1f} adjusts yield.")

        if maturity_days is not None:
            # prefer 100-130 day maturity; penalize extremes
            if 100 <= maturity_days <= 130:
                yield_adj += 0.03
                explain_bits.append(f"Maturity {maturity_days:.0f}d in preferred range (+3%).")
            else:
                yield_adj -= 0.02
                explain_bits.append(f"Maturity {maturity_days:.0f}d outside preferred range (-2%).")

        if not rotation_compliance:
            yield_adj -= 0.05
            explain_bits.append("Rotation non-compliant (same crop last season) (-5%).")
        else:
            explain_bits.append("Rotation compliant.")

        predicted_yield = max(0.0, base_yield * (1.0 + yield_adj))

        revenue_per_ha = predicted_yield * float(price_per_kg)
        # tiny cost modifier: drought tolerant varieties may cost more
        cost_per_ha = float(base_cost_per_ha) + (10.0 if (drought_tol or 0) >= 4 else 0.0)
        margin_per_ha = revenue_per_ha - cost_per_ha

        score = margin_per_ha + (50.0 if rotation_compliance else 0.0)

        assumptions = f"Assumptions: price_per_kg={price_per_kg}, base_cost_per_ha={base_cost_per_ha}."
        explanation = " ".join(explain_bits + [assumptions])

        recs.append(
            Recommendation(
                crop=crop,
                variety=variety_name,
                score=round(score, 3),
                predicted_yield_kg_per_ha=round(predicted_yield, 3),
                predicted_margin_per_ha=round(margin_per_ha, 3),
                rotation_compliance=rotation_compliance,
                confidence=round(confidence, 3),
                explanation=explanation,
            )
        )

    recs.sort(key=lambda r: (r.score, r.confidence), reverse=True)
    return recs


def _safe_float(v) -> float | None:
    try:
        if v is None or v == "":
            return None
        return float(v)
    except (TypeError, ValueError):
        return None
