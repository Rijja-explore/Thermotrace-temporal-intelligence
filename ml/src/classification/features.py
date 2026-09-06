import pandas as pd
from typing import List

APPROVED_FEATURES = {
    # Thermal Only (A)
    "max_frp_mw", "mean_frp_mw", "median_frp_mw", "sum_frp_mw", 
    "spatial_extent_km", "thermal_intensity", "thermal_frp_variability", 
    "thermal_frp_per_detection", "thermal_frp_per_hour", 
    "duration_hours", "detection_count",
    # Temporal (B)
    "events_previous_7d", "events_previous_30d", "events_previous_90d", 
    "frp_previous_7d", "frp_previous_30d", "frp_previous_90d", 
    "active_days_previous_7d", "active_days_previous_30d", "active_days_previous_90d", 
    "time_since_previous_event_hours", "hour_sin", "hour_cos", 
    "month_sin", "month_cos", "day_of_week_sin", "day_of_week_cos",
    # Land Cover (C)
    "forest_fraction_1km", "cropland_fraction_1km", "builtup_fraction_1km", 
    "grassland_fraction_1km", "water_fraction_1km", "natural_land_fraction",
    # Infrastructure (D)
    "distance_to_facility_km", "distance_to_major_road_km", "distance_to_railway_km", 
    "distance_to_power_line_km", "distance_to_pipeline_km", "distance_to_airport_km", 
    "distance_to_port_km", "near_power_plant", "near_factory", "near_refinery", 
    "near_mine", "near_quarry", "near_storage_facility", "near_substation"
}

EXCLUDED_FEATURES = {
    "event_id", "nearest_facility_id", "protected_area_id",
    "baseline_risk_score", "baseline_risk_level",
    "thermal_risk_component", "exposure_risk_component", "environmental_risk_component",
    "conservation_risk_component", "industrial_context_component", "infrastructure_context_component",
    "recurrence_component", "risk_reason_1", "risk_reason_2", "risk_reason_3",
    "industrial_proximity_score", "industrial_context_flag", "factory_context", "quarry_context",
    "refinery_context", "mining_context", "storage_context", "substation_context", "power_generation_context",
    "infrastructure_context_score", "road_proximity_score", "railway_proximity_score",
    "pipeline_proximity_score", "transport_corridor_flag", "population_exposure_score",
    "population_pressure_indicator", "forest_exposure_score", "cropland_exposure_score",
    "builtup_exposure_score", "grassland_exposure_score", "environmental_sensitivity_score",
    "conservation_sensitivity_score", "protected_area_alert_flag", "protected_area_proximity_class",
    "events_local_1km", "events_local_5km", "events_local_10km", "events_local_7d", "events_local_30d",
    "thermal_density_1km", "thermal_density_5km", "thermal_density_10km", "thermal_detection_density",
    "landcover_class" # Unencoded categorical excluded directly
}

ABLATION_GROUPS = {}
ABLATION_GROUPS["A"] = ["max_frp_mw", "mean_frp_mw", "median_frp_mw", "sum_frp_mw", "spatial_extent_km", "thermal_intensity", "thermal_frp_variability", "thermal_frp_per_detection", "thermal_frp_per_hour", "duration_hours", "detection_count"]
ABLATION_GROUPS["B"] = ABLATION_GROUPS["A"] + ["events_previous_7d", "events_previous_30d", "events_previous_90d", "frp_previous_7d", "frp_previous_30d", "frp_previous_90d", "active_days_previous_7d", "active_days_previous_30d", "active_days_previous_90d", "time_since_previous_event_hours", "hour_sin", "hour_cos", "month_sin", "month_cos", "day_of_week_sin", "day_of_week_cos"]
ABLATION_GROUPS["C"] = ABLATION_GROUPS["B"] + ["forest_fraction_1km", "cropland_fraction_1km", "builtup_fraction_1km", "grassland_fraction_1km", "water_fraction_1km", "natural_land_fraction"]
ABLATION_GROUPS["D"] = ABLATION_GROUPS["C"] + ["distance_to_facility_km", "distance_to_major_road_km", "distance_to_railway_km", "distance_to_power_line_km", "distance_to_pipeline_km", "distance_to_airport_km", "distance_to_port_km", "near_power_plant", "near_factory", "near_refinery", "near_mine", "near_quarry", "near_storage_facility", "near_substation"]
ABLATION_GROUPS["E"] = ABLATION_GROUPS["D"] + [] # Advanced imagery/spectral

def validate_features(columns: List[str]) -> List[str]:
    """Returns columns strictly enforcing exclusion of leakage/synthetic heuristics. Fails closed on unknown features."""
    valid = []
    for c in columns:
        if c in EXCLUDED_FEATURES or c.endswith("_id") or c == "event_id" or "baseline_risk" in c:
            raise ValueError(f"Feature rejected: explicitly excluded or identifier field: {c}")
        if c not in APPROVED_FEATURES:
            raise ValueError(f"Feature rejected: unknown/unregistered feature column: {c}")
        valid.append(c)
    return valid

def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Validates dataframe columns and numeric types."""
    valid_cols = validate_features(df.columns.tolist())
    for c in valid_cols:
        if not pd.api.types.is_numeric_dtype(df[c]):
            raise ValueError(f"Feature {c} is not numeric/categorical encoded.")
    return df[valid_cols]
