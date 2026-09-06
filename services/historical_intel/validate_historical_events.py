import pandas as pd
from pathlib import Path


# --------------------------------------------------
# Paths
# --------------------------------------------------

EVENT_FILE = Path("data/processed/historical_thermal_events.csv")
FACILITY_FILE = Path("data/processed/industrial_facilities.csv")


# --------------------------------------------------
# Load data
# --------------------------------------------------

print("Loading historical thermal events...")
events = pd.read_csv(EVENT_FILE)

print("Loading industrial facilities...")
facilities = pd.read_csv(FACILITY_FILE)


# --------------------------------------------------
# Required columns
# --------------------------------------------------

required_event_columns = [
    "event_id",
    "start_time",
    "end_time",
    "centroid_lat",
    "centroid_lon",
    "max_frp_mw",
    "mean_frp_mw",
    "median_frp_mw",
    "duration_hours",
    "nearest_facility_id",
    "nearest_facility_type",
    "distance_to_facility_km"
]

required_facility_columns = [
    "facility_id",
    "latitude",
    "longitude",
    "facility_category"
]


# --------------------------------------------------
# Column validation
# --------------------------------------------------

print("Checking required columns...")

missing_event_columns = [
    col for col in required_event_columns
    if col not in events.columns
]

missing_facility_columns = [
    col for col in required_facility_columns
    if col not in facilities.columns
]

if missing_event_columns:
    raise ValueError(
        f"Missing event columns: {missing_event_columns}"
    )

if missing_facility_columns:
    raise ValueError(
        f"Missing facility columns: {missing_facility_columns}"
    )


# --------------------------------------------------
# Date validation
# --------------------------------------------------

print("Checking dates...")

events["start_time"] = pd.to_datetime(events["start_time"])
events["end_time"] = pd.to_datetime(events["end_time"])

if events["start_time"].isna().any():
    raise ValueError("Missing start times found.")

if events["end_time"].isna().any():
    raise ValueError("Missing end times found.")

if (events["end_time"] < events["start_time"]).any():
    raise ValueError("Events with end time before start time found.")


# --------------------------------------------------
# Coordinate validation
# --------------------------------------------------

print("Checking coordinates...")

if events["centroid_lat"].isna().any():
    raise ValueError("Missing event latitude found.")

if events["centroid_lon"].isna().any():
    raise ValueError("Missing event longitude found.")

if not events["centroid_lat"].between(-90, 90).all():
    raise ValueError("Invalid event latitude found.")

if not events["centroid_lon"].between(-180, 180).all():
    raise ValueError("Invalid event longitude found.")


# --------------------------------------------------
# FRP validation
# --------------------------------------------------

print("Checking FRP values...")

frp_columns = [
    "max_frp_mw",
    "mean_frp_mw",
    "median_frp_mw"
]

for column in frp_columns:
    if events[column].isna().any():
        raise ValueError(
            f"Missing values found in {column}."
        )

    if (events[column] < 0).any():
        raise ValueError(
            f"Negative values found in {column}."
        )


# --------------------------------------------------
# Duration validation
# --------------------------------------------------

print("Checking event duration...")

if events["duration_hours"].isna().any():
    raise ValueError("Missing event duration found.")

if (events["duration_hours"] < 0).any():
    raise ValueError("Negative event duration found.")


# --------------------------------------------------
# Facility association validation
# --------------------------------------------------

print("Checking facility associations...")

if events["nearest_facility_id"].isna().any():
    raise ValueError(
        "Historical events without facility association found."
    )

if events["distance_to_facility_km"].isna().any():
    raise ValueError(
        "Missing facility distance found."
    )

if (events["distance_to_facility_km"] < 0).any():
    raise ValueError(
        "Negative facility distance found."
    )

# Historical event dataset was created using
# a 5 km facility-association processing rule.
if (events["distance_to_facility_km"] > 5).any():
    raise ValueError(
        "Event found beyond the 5 km association rule."
    )


# --------------------------------------------------
# Facility ID matching
# --------------------------------------------------

print("Checking facility IDs against master data...")

event_facility_ids = set(
    events["nearest_facility_id"].astype(str)
)

master_facility_ids = set(
    facilities["facility_id"].astype(str)
)

unmatched_ids = event_facility_ids - master_facility_ids

if unmatched_ids:
    raise ValueError(
        f"Unmatched facility IDs found: {len(unmatched_ids)}"
    )


# --------------------------------------------------
# Duplicate event validation
# --------------------------------------------------

print("Checking duplicate event IDs...")

duplicate_events = events["event_id"].duplicated().sum()

if duplicate_events > 0:
    raise ValueError(
        f"Duplicate event IDs found: {duplicate_events}"
    )


# --------------------------------------------------
# Summary
# --------------------------------------------------

print()
print("Historical event validation completed successfully.")
print()
print("Total historical events:", len(events))
print(
    "Unique facilities with events:",
    events["nearest_facility_id"].nunique()
)
print(
    "Observation start:",
    events["start_time"].min()
)
print(
    "Observation end:",
    events["end_time"].max()
)
print(
    "Maximum facility distance:",
    events["distance_to_facility_km"].max()
)
print(
    "Unmatched facility IDs:",
    len(unmatched_ids)
)
print(
    "Duplicate event IDs:",
    duplicate_events
)