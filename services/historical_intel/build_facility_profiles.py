import pandas as pd
from pathlib import Path


# --------------------------------------------------
# Paths
# --------------------------------------------------

FACILITY_FILE = Path("data/processed/industrial_facilities.csv")
EVENT_FILE = Path("data/processed/historical_thermal_events.csv")
OUTPUT_FILE = Path("data/processed/facility_profiles.csv")


# --------------------------------------------------
# Load data
# --------------------------------------------------

print("Loading facility data...")
facilities = pd.read_csv(FACILITY_FILE)

print("Loading historical thermal events...")
events = pd.read_csv(EVENT_FILE)


# --------------------------------------------------
# Prepare event data
# --------------------------------------------------

events["start_time"] = pd.to_datetime(events["start_time"])
events["end_time"] = pd.to_datetime(events["end_time"])

events["date"] = events["start_time"].dt.date
events["month"] = events["start_time"].dt.to_period("M")
events["hour"] = events["start_time"].dt.hour


# --------------------------------------------------
# Basic facility-wise statistics
# --------------------------------------------------

print("Building facility profiles...")

profiles = events.groupby("nearest_facility_id").agg(
    total_events=("event_id", "count"),
    active_days=("date", "nunique"),
    active_months=("month", "nunique"),

    mean_frp_mw=("mean_frp_mw", "mean"),
    median_frp_mw=("mean_frp_mw", "median"),
    max_frp_mw=("max_frp_mw", "max"),
    min_frp_mw=("mean_frp_mw", "min"),

    mean_thermal_intensity=("thermal_intensity", "mean"),
    max_thermal_intensity=("thermal_intensity", "max"),

    mean_distance_km=("distance_to_facility_km", "mean"),
    median_distance_km=("distance_to_facility_km", "median"),
    max_distance_km=("distance_to_facility_km", "max"),

    mean_spatial_extent_km=("spatial_extent_km", "mean"),
    max_spatial_extent_km=("spatial_extent_km", "max"),

    mean_duration_hours=("duration_hours", "mean"),
    median_duration_hours=("duration_hours", "median"),
    max_duration_hours=("duration_hours", "max"),

    mean_detection_count=("detection_count", "mean"),
    median_detection_count=("detection_count", "median"),
    max_detection_count=("detection_count", "max"),

    mean_satellite_count=("unique_satellite_count", "mean"),
    max_satellite_count=("unique_satellite_count", "max")
).reset_index()


# --------------------------------------------------
# Monthly activity
# --------------------------------------------------

monthly = (
    events.groupby(["nearest_facility_id", "month"])
    .size()
    .reset_index(name="monthly_events")
)

monthly_stats = monthly.groupby("nearest_facility_id").agg(
    avg_events_per_month=("monthly_events", "mean"),
    median_events_per_month=("monthly_events", "median")
).reset_index()


# --------------------------------------------------
# Day / night activity
# --------------------------------------------------

day_night = (
    events.groupby(["nearest_facility_id", "is_night"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)

day_night = day_night.rename(
    columns={
        True: "night_events",
        False: "day_events"
    }
)

if "night_events" not in day_night.columns:
    day_night["night_events"] = 0

if "day_events" not in day_night.columns:
    day_night["day_events"] = 0

profiles = profiles.merge(
    day_night[
        ["nearest_facility_id", "day_events", "night_events"]
    ],
    on="nearest_facility_id",
    how="left"
)

# --------------------------------------------------
# Weekday / weekend activity
# --------------------------------------------------

weekend = (
    events.groupby(["nearest_facility_id", "is_weekend"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)

weekend = weekend.rename(
    columns={
        True: "weekend_events",
        False: "weekday_events"
    }
)

if "weekend_events" not in weekend.columns:
    weekend["weekend_events"] = 0

if "weekday_events" not in weekend.columns:
    weekend["weekday_events"] = 0

profiles = profiles.merge(
    weekend[
        ["nearest_facility_id", "weekday_events", "weekend_events"]
    ],
    on="nearest_facility_id",
    how="left"
)

# --------------------------------------------------
# Most active hour
# --------------------------------------------------

hour_counts = (
    events.groupby(["nearest_facility_id", "hour"])
    .size()
    .reset_index(name="count")
)

most_active_hour = (
    hour_counts.loc[
        hour_counts.groupby("nearest_facility_id")["count"].idxmax()
    ][["nearest_facility_id", "hour"]]
    .rename(columns={"hour": "most_active_hour"})
)

profiles = profiles.merge(
    most_active_hour,
    on="nearest_facility_id",
    how="left"
)


# --------------------------------------------------
# Most active month
# --------------------------------------------------

month_counts = (
    events.groupby(["nearest_facility_id", "month"])
    .size()
    .reset_index(name="count")
)

most_active_month = (
    month_counts.loc[
        month_counts.groupby("nearest_facility_id")["count"].idxmax()
    ][["nearest_facility_id", "month"]]
)

most_active_month["most_active_month"] = (
    most_active_month["month"].astype(str)
)

most_active_month = most_active_month[
    ["nearest_facility_id", "most_active_month"]
]

profiles = profiles.merge(
    most_active_month,
    on="nearest_facility_id",
    how="left"
)


# --------------------------------------------------
# Merge monthly statistics
# --------------------------------------------------

profiles = profiles.merge(
    monthly_stats,
    on="nearest_facility_id",
    how="left"
)


# --------------------------------------------------
# Merge facility master information
# --------------------------------------------------

facility_columns = [
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
    "latitude"
]

facility_info = facilities[facility_columns].copy()

profiles = profiles.merge(
    facility_info,
    left_on="nearest_facility_id",
    right_on="facility_id",
    how="left"
)


# --------------------------------------------------
# Historical observation count
# --------------------------------------------------
profiles["day_events"] = profiles["day_events"].fillna(0).astype(int)
profiles["night_events"] = profiles["night_events"].fillna(0).astype(int)
profiles["weekday_events"] = profiles["weekday_events"].fillna(0).astype(int)
profiles["weekend_events"] = profiles["weekend_events"].fillna(0).astype(int)

profiles["historical_event_observations"] = profiles["total_events"]


# --------------------------------------------------
# Save output
# --------------------------------------------------

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

profiles.to_csv(OUTPUT_FILE, index=False)

print()
print("Facility profile generation completed.")
print("Facilities:", len(profiles))
print("Output:", OUTPUT_FILE)
print("Columns:", len(profiles.columns))