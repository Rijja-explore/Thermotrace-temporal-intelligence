"""
ThermoTrace Event Feature Schema & Validation Specification
============================================================

Defines canonical feature column names, data types, nullability,
and validation rules for event_features_v1.parquet.
"""

from typing import Dict, Any, List

FEATURE_SCHEMA: Dict[str, Dict[str, Any]] = {
    # 1. Base Event Identifiers & Properties
    "event_id": {"dtype": "string", "nullable": False, "description": "Unique M3 Event Identifier"},
    "start_time": {"dtype": "string", "nullable": False, "description": "Event start timestamp (ISO)"},
    "end_time": {"dtype": "string", "nullable": False, "description": "Event end timestamp (ISO)"},
    "duration_hours": {"dtype": "float32", "nullable": False, "description": "Total duration in hours"},
    "centroid_lat": {"dtype": "float32", "nullable": False, "min": 5.0, "max": 38.0, "description": "Event centroid latitude"},
    "centroid_lon": {"dtype": "float32", "nullable": False, "min": 65.0, "max": 100.0, "description": "Event centroid longitude"},
    "spatial_extent_km": {"dtype": "float32", "nullable": False, "description": "Maximum spatial diameter of cluster in km"},
    "detection_count": {"dtype": "int32", "nullable": False, "min": 1, "description": "Total satellite detections in event"},
    "unique_satellite_count": {"dtype": "int16", "nullable": False, "description": "Number of unique observing satellites"},
    "satellites": {"dtype": "string", "nullable": False, "description": "Comma-separated list of observing platforms"},
    "max_frp_mw": {"dtype": "float32", "nullable": False, "min": 0.0, "description": "Peak Fire Radiative Power (MW)"},
    "mean_frp_mw": {"dtype": "float32", "nullable": False, "min": 0.0, "description": "Average Fire Radiative Power (MW)"},
    "median_frp_mw": {"dtype": "float32", "nullable": False, "min": 0.0, "description": "Median Fire Radiative Power (MW)"},
    "sum_frp_mw": {"dtype": "float32", "nullable": False, "min": 0.0, "description": "Cumulative Fire Radiative Power (MW)"},
    "event_quality": {"dtype": "string", "nullable": False, "description": "Event cluster classification quality tag"},

    # 2. Temporal Features
    "year": {"dtype": "int16", "nullable": False, "min": 2020, "max": 2030},
    "month": {"dtype": "int8", "nullable": False, "min": 1, "max": 12},
    "day": {"dtype": "int8", "nullable": False, "min": 1, "max": 31},
    "day_of_week": {"dtype": "int8", "nullable": False, "min": 0, "max": 6, "description": "0=Monday, 6=Sunday"},
    "hour": {"dtype": "int8", "nullable": False, "min": 0, "max": 23, "description": "UTC hour of event initiation"},
    "season": {"dtype": "string", "nullable": False, "description": "WINTER, PRE_MONSOON, MONSOON, POST_MONSOON"},
    "is_day": {"dtype": "boolean", "nullable": False, "description": "Event occurred during daytime"},
    "is_night": {"dtype": "boolean", "nullable": False, "description": "Event occurred during nighttime"},
    "is_weekend": {"dtype": "boolean", "nullable": False, "description": "Event occurred on Saturday or Sunday"},

    # 3. Population Features
    "population_at_event": {"dtype": "float32", "nullable": False, "min": 0.0, "description": "Estimated pop at 100m grid cell"},
    "population_1km": {"dtype": "float32", "nullable": False, "min": 0.0, "description": "Total pop within 1km radius"},
    "population_5km": {"dtype": "float32", "nullable": False, "min": 0.0, "description": "Total pop within 5km radius"},
    "population_density_1km": {"dtype": "float32", "nullable": False, "min": 0.0, "description": "Pop density (persons/km²) in 1km buffer"},
    "population_density_5km": {"dtype": "float32", "nullable": False, "min": 0.0, "description": "Pop density (persons/km²) in 5km buffer"},

    # 4. Protected Area Features
    "inside_protected_area": {"dtype": "boolean", "nullable": False, "description": "True if event centroid inside protected area polygon"},
    "protected_area_id": {"dtype": "string", "nullable": True, "description": "WDPA site identifier if inside or nearby"},
    "protected_area_name": {"dtype": "string", "nullable": True, "description": "Protected area name in English"},
    "protected_area_designation": {"dtype": "string", "nullable": True, "description": "National Park, Sanctuary, Ramsar, etc."},
    "distance_to_protected_area_km": {"dtype": "float32", "nullable": False, "min": 0.0, "description": "Distance to nearest PA boundary (km)"},
    "protected_area_within_1km": {"dtype": "boolean", "nullable": False},
    "protected_area_within_5km": {"dtype": "boolean", "nullable": False},

    # 5. OSM Facility Context Features
    "nearest_facility_id": {"dtype": "string", "nullable": True, "description": "OSM object ID of nearest facility"},
    "nearest_facility_type": {"dtype": "string", "nullable": True, "description": "Normalized category of nearest facility"},
    "nearest_facility_name": {"dtype": "string", "nullable": True, "description": "Name of nearest facility if tagged in OSM"},
    "distance_to_facility_km": {"dtype": "float32", "nullable": False, "min": 0.0, "description": "Distance to representative facility centroid (km)"},
    "near_power_plant": {"dtype": "boolean", "nullable": False, "description": "Within 2km of power plant"},
    "near_factory": {"dtype": "boolean", "nullable": False, "description": "Within 2km of factory"},
    "near_refinery": {"dtype": "boolean", "nullable": False, "description": "Within 5km of oil/gas refinery"},
    "near_mine": {"dtype": "boolean", "nullable": False, "description": "Within 5km of mine"},
    "near_quarry": {"dtype": "boolean", "nullable": False, "description": "Within 3km of quarry"},
    "near_storage_facility": {"dtype": "boolean", "nullable": False, "description": "Within 2km of storage/tank facility"},
    "near_substation": {"dtype": "boolean", "nullable": False, "description": "Within 2km of electrical substation"},

    # 6. OSM Infrastructure Proximity Features
    "distance_to_major_road_km": {"dtype": "float32", "nullable": False, "min": 0.0},
    "distance_to_railway_km": {"dtype": "float32", "nullable": False, "min": 0.0},
    "distance_to_power_line_km": {"dtype": "float32", "nullable": False, "min": 0.0},
    "distance_to_pipeline_km": {"dtype": "float32", "nullable": False, "min": 0.0},
    "distance_to_airport_km": {"dtype": "float32", "nullable": False, "min": 0.0},
    "distance_to_port_km": {"dtype": "float32", "nullable": False, "min": 0.0},

    # 7. WorldCover Land Cover Features (Nullable if mosaic still building)
    "landcover_class": {"dtype": "int16", "nullable": True, "description": "ESA WorldCover 10m class ID at event"},
    "landcover_name": {"dtype": "string", "nullable": True, "description": "Tree cover, Cropland, Built-up, etc."},
    "forest_fraction_1km": {"dtype": "float32", "nullable": True, "min": 0.0, "max": 1.0},
    "cropland_fraction_1km": {"dtype": "float32", "nullable": True, "min": 0.0, "max": 1.0},
    "builtup_fraction_1km": {"dtype": "float32", "nullable": True, "min": 0.0, "max": 1.0},
    "grassland_fraction_1km": {"dtype": "float32", "nullable": True, "min": 0.0, "max": 1.0},
    "water_fraction_1km": {"dtype": "float32", "nullable": True, "min": 0.0, "max": 1.0},

    # 8. Administrative Boundaries (Nullable, marked pending authoritative Survey of India dataset)
    "country": {"dtype": "string", "nullable": True, "default": "India"},
    "state": {"dtype": "string", "nullable": True},
    "state_code": {"dtype": "string", "nullable": True},
    "district": {"dtype": "string", "nullable": True},
    "district_code": {"dtype": "string", "nullable": True}
}

def validate_dataframe_schema(df) -> List[str]:
    """Validates dataframe columns, dtypes, nullability, and value bounds."""
    errors = []
    for col, spec in FEATURE_SCHEMA.items():
        if col not in df.columns:
            if not spec.get("nullable", True):
                errors.append(f"Missing mandatory column: {col}")
            continue

        series = df[col]
        # Null check
        if not spec.get("nullable", True) and series.isna().any():
            null_count = series.isna().sum()
            errors.append(f"Column '{col}' has {null_count} nulls but is marked non-nullable")

        # Numeric min/max checks
        if "min" in spec and series.dtype in ["float32", "float64", "int32", "int64", "int16", "int8"]:
            min_val = series.min()
            if min_val < spec["min"]:
                errors.append(f"Column '{col}' has value {min_val} < allowed min {spec['min']}")
        if "max" in spec and series.dtype in ["float32", "float64", "int32", "int64", "int16", "int8"]:
            max_val = series.max()
            if max_val > spec["max"]:
                errors.append(f"Column '{col}' has value {max_val} > allowed max {spec['max']}")

    return errors
