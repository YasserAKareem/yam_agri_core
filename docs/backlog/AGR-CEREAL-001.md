# AGR-CEREAL-001 — Crop/Variety Recommendations (MVP)

## What’s implemented

- Deterministic, explainable recommender (proposal-only)
- Whitelisted API method returning ranked recommendations
- Script Report returning rows + chart payload
- Demo runner returning a ready-to-use payload

## API

### Get recommendations

- Method: `yam_agri_core.api.agr_cereal_001.get_variety_recommendations`
- Type: whitelisted, **no writes**
- Site access: enforced via `User Permission` on `Site`

Example payload (JSON):

```json
{
  "site": "<SITE>",
  "season": "2026",
  "crop": "Wheat",
  "plot": {"last_crop": "Barley", "area_ha": 10},
  "soil_test": {"organic_matter_pct": 2.7, "ph": 7.4},
  "yield_history": [
    {"season": "2024", "crop": "Wheat", "yield_kg_per_ha": 2600},
    {"season": "2025", "crop": "Wheat", "yield_kg_per_ha": 2400}
  ],
  "varieties": [
    {"variety_name": "WHT-Prime", "maturity_days": 115, "drought_tolerance": 4.2},
    {"variety_name": "WHT-Early", "maturity_days": 95, "drought_tolerance": 3.0}
  ]
}
```

### Run demo

- Method: `yam_agri_core.seed.agr_cereal_001_demo.run_demo`

## Report

- Report: `YAM Crop Variety Recommendations`
- Type: Script Report
- Chart: returned via `chart` object in `execute()`

## Next steps

- Add DocTypes for plot/soil/yield and `YAM Crop Variety` master
- Bind report and API to real DocType data (instead of demo variety list)
- Add permissions/query conditions for new DocTypes using site isolation helpers
