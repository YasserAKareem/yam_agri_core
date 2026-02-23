from __future__ import annotations

import unittest

from yam_agri_core.yam_agri_core.ai.agr_cereal_001 import recommend


class TestAgrCereal001(unittest.TestCase):
    def test_recommend_returns_ranked_list(self):
        recs = recommend(
            plot={"site": "S1", "last_crop": "Barley"},
            season="2026",
            crop="Wheat",
            varieties=[
                {"variety_name": "A", "maturity_days": 115, "drought_tolerance": 4.2},
                {"variety_name": "B", "maturity_days": 95, "drought_tolerance": 3.0},
            ],
            soil_test={"organic_matter_pct": 2.7},
            yield_history=[{"season": "2025", "crop": "Wheat", "yield_kg_per_ha": 2500}],
            price_per_kg=0.25,
            base_cost_per_ha=300.0,
        )

        self.assertTrue(recs)
        self.assertTrue(all(r.variety for r in recs))
        self.assertEqual(recs, sorted(recs, key=lambda r: (r.score, r.confidence), reverse=True))

    def test_rotation_penalty_applies_when_same_crop(self):
        recs_ok = recommend(
            plot={"site": "S1", "last_crop": "Barley"},
            season="2026",
            crop="Wheat",
            varieties=[{"variety_name": "A"}],
        )
        recs_bad = recommend(
            plot={"site": "S1", "last_crop": "Wheat"},
            season="2026",
            crop="Wheat",
            varieties=[{"variety_name": "A"}],
        )

        self.assertGreaterEqual(recs_ok[0].predicted_yield_kg_per_ha, recs_bad[0].predicted_yield_kg_per_ha)
        self.assertGreaterEqual(recs_ok[0].score, recs_bad[0].score)
