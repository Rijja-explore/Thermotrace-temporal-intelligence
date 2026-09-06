# ThermoTrace AI Classification Methodology

## Taxonomy & Target Classes

ThermoTrace classifies thermal anomalies into 6 distinct operational classes:

1. `persistent_industrial_source`: Continuous/recurrent industrial flares or process heat (e.g. refineries, chemical plants).
2. `industrial_fire_or_abnormal_event`: Accidental industrial fire, flare excursion, or unannounced thermal spike.
3. `wildfire_or_forest_fire`: Vegetation or forest canopy fires.
4. `agricultural_burning`: Seasonal crop residue / stubble burning episodes.
5. `mining_or_other_industrial_activity`: Coal seam fires, quarry blasting, or mining thermal activity.
6. `unknown_requires_verification`: Ambiguous or sparse thermal signals requiring human analyst review.

## Feature Space & Leakage Exclusion

The classification engine consumes 47 approved features categorized into:
- **Thermal Signal Features:** `max_frp_mw`, `mean_frp_mw`, `brightness_ti4`, `brightness_ti5`, `confidence_mean`.
- **Temporal Activity Features:** `active_days_90d`, `detection_count_30d`, `persistence_ratio`, `spatial_stability_m`.
- **Spatial Infrastructure Features:** `dist_to_industrial`, `near_refinery`, `near_factory`, `near_mine`.
- **Land Cover Context Features:** `lc_urban_100m`, `lc_forest_100m`, `lc_crop_100m`.

**Explicit Leakage Safeguard:** Synthetic risk scores, baseline risk variables, and ground-truth target labels are strictly excluded from the feature space (`features.py:EXCLUDED_FEATURES`).
