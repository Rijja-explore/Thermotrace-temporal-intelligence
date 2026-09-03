"""
ThermoTrace Feature Engineering V2: Validation & Integrity Auditor
==================================================================

Automated data integrity checks and statistical validation for the V2 feature table.
"""

from typing import Dict, Any
import numpy as np
import pandas as pd

def validate_v2_feature_table(v1_df: pd.DataFrame, v2_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Executes comprehensive validation tests comparing V1 and V2 datasets.
    Raises AssertionError if any critical guarantee is violated.
    """
    n_v1 = len(v1_df)
    n_v2 = len(v2_df)

    # 1. Cardinality Assertions
    assert n_v2 == n_v1, f"Row count mismatch! V1: {n_v1}, V2: {n_v2}"
    assert v2_df["event_id"].is_unique, "Duplicate event_ids detected in V2!"
    assert (v2_df["event_id"].values == v1_df["event_id"].values).all(), "Event ID order mismatch between V1 and V2!"

    # 2. Coordinate Validity
    assert v2_df["centroid_lat"].between(5.0, 38.0).all(), "Latitudes out of bounds!"
    assert v2_df["centroid_lon"].between(65.0, 100.0).all(), "Longitudes out of bounds!"

    # 3. FRP & Thermal Validations
    assert (v2_df["max_frp_mw"] >= 0.0).all(), "Negative max_frp_mw detected!"
    assert (v2_df["sum_frp_mw"] >= 0.0).all(), "Negative sum_frp_mw detected!"
    assert (v2_df["log_max_frp"] >= 0.0).all(), "Negative log_max_frp detected!"
    assert not np.isinf(v2_df["thermal_intensity"].values).any(), "Inf detected in thermal_intensity!"
    assert not np.isinf(v2_df["thermal_frp_variability"].values).any(), "Inf detected in thermal_frp_variability!"

    # 4. Temporal Cyclical Bounds [-1.0, 1.0]
    cyclic_cols = ["hour_sin", "hour_cos", "month_sin", "month_cos", "day_of_week_sin", "day_of_week_cos"]
    for c in cyclic_cols:
        assert v2_df[c].between(-1.0001, 1.0001).all(), f"Cyclic feature {c} outside [-1, 1]!"

    # 5. Recurrence Non-Negativity
    rec_cols = ["events_previous_7d", "events_previous_30d", "events_previous_90d",
                "frp_previous_7d", "frp_previous_30d", "frp_previous_90d",
                "active_days_previous_7d", "active_days_previous_30d", "active_days_previous_90d",
                "time_since_previous_event_hours"]
    for c in rec_cols:
        assert (v2_df[c] >= 0.0).all(), f"Negative value in recurrence feature {c}!"

    # 6. Spatial Density Non-Negativity
    dens_cols = ["events_local_1km", "events_local_5km", "events_local_10km",
                 "thermal_density_1km", "thermal_density_5km", "thermal_density_10km"]
    for c in dens_cols:
        assert (v2_df[c] >= 0.0).all(), f"Negative value in density feature {c}!"

    # 7. Exposure & Context Scores [0.0, 100.0]
    score_cols = [
        "population_exposure_score", "forest_exposure_score", "cropland_exposure_score",
        "builtup_exposure_score", "grassland_exposure_score", "environmental_sensitivity_score",
        "conservation_sensitivity_score", "industrial_proximity_score", "infrastructure_context_score",
        "thermal_risk_component", "exposure_risk_component", "environmental_risk_component",
        "conservation_risk_component", "industrial_context_component", "infrastructure_context_component",
        "recurrence_component", "baseline_risk_score"
    ]
    for c in score_cols:
        assert v2_df[c].between(0.0, 100.0001).all(), f"Score {c} out of [0, 100] bounds!"

    # 8. Baseline Risk Categories
    valid_risk_levels = {"LOW", "MODERATE", "HIGH", "CRITICAL"}
    assert set(v2_df["baseline_risk_level"].unique()).issubset(valid_risk_levels), "Invalid baseline_risk_level!"

    # 9. Risk Reasons Non-Null
    assert v2_df["risk_reason_1"].notna().all(), "Null in risk_reason_1!"
    assert v2_df["risk_reason_2"].notna().all(), "Null in risk_reason_2!"
    assert v2_df["risk_reason_3"].notna().all(), "Null in risk_reason_3!"

    return {
        "status": "PASS",
        "verified_rows": n_v2,
        "verified_columns": len(v2_df.columns),
        "new_v2_features_added": len(v2_df.columns) - len(v1_df.columns)
    }
