import pandas as pd
from pathlib import Path


# --------------------------------------------------
# Paths
# --------------------------------------------------

PROFILE_FILE = Path("data/processed/facility_profiles.csv")
OUTPUT_FILE = Path("data/baselines/facility_baselines.csv")


# --------------------------------------------------
# Historical observation period
# --------------------------------------------------

OBSERVATION_DAYS = 365


# --------------------------------------------------
# Load facility profiles
# --------------------------------------------------

print("Loading facility profiles...")

profiles = pd.read_csv(PROFILE_FILE)


# --------------------------------------------------
# Generate baseline measures
# --------------------------------------------------

print("Generating facility baselines...")

baselines = profiles.copy()


# Historical events observed per 30 days.
# This is normalized from the actual 365-day
# observation period; no arbitrary threshold is used.

baselines["events_per_30_days"] = (
    baselines["total_events"] / OBSERVATION_DAYS
) * 30


# --------------------------------------------------
# Historical evidence count
# --------------------------------------------------

baselines["historical_event_observations"] = (
    baselines["total_events"]
)


# --------------------------------------------------
# Select baseline fields
# --------------------------------------------------

baseline_columns = [
    "facility_id",
    "name",
    "operator",
    "facility_category",
    "landuse",
    "industrial",
    "man_made",
    "power",
    "building",
    "source",
    "longitude",
    "latitude",

    # Frequency baseline
    "total_events",
    "active_days",
    "avg_events_per_month",
    "median_events_per_month",
    "active_months",
    "events_per_30_days",

    # Thermal intensity baseline
    "mean_frp_mw",
    "median_frp_mw",
    "max_frp_mw",
    "min_frp_mw",
    "mean_thermal_intensity",
    "max_thermal_intensity",

    # Temporal baseline
    "most_active_hour",
    "most_active_month",
    "day_events",
    "night_events",
    "weekday_events",
    "weekend_events",

    # Spatial baseline
    "mean_distance_km",
    "median_distance_km",
    "max_distance_km",
    "mean_spatial_extent_km",
    "max_spatial_extent_km",

    # Event characteristics
    "mean_duration_hours",
    "median_duration_hours",
    "max_duration_hours",
    "mean_detection_count",
    "median_detection_count",
    "max_detection_count",
    "mean_satellite_count",
    "max_satellite_count",

    # Evidence
    "historical_event_observations"
]


baselines = baselines[baseline_columns]


# --------------------------------------------------
# Basic validation
# --------------------------------------------------

print("Validating baseline output...")

if baselines["facility_id"].duplicated().any():
    raise ValueError("Duplicate facility IDs found.")

if baselines["facility_id"].isna().any():
    raise ValueError("Missing facility IDs found.")

if (baselines["total_events"] <= 0).any():
    raise ValueError("Invalid total event count found.")

if (baselines["events_per_30_days"] < 0).any():
    raise ValueError("Invalid normalized event rate found.")


# --------------------------------------------------
# Save
# --------------------------------------------------

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

baselines.to_csv(OUTPUT_FILE, index=False)


# --------------------------------------------------
# Summary
# --------------------------------------------------

print()
print("Baseline generation completed.")
print("Facilities:", len(baselines))
print("Columns:", len(baselines.columns))
print("Output:", OUTPUT_FILE)
print()
print("Observation period:", OBSERVATION_DAYS, "days")
print("Total historical events:", baselines["total_events"].sum())