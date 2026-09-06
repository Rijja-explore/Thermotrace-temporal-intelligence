"""
ThermoTrace - Event Engine v0.1 Unit & Verification Tests (Module M3)
=====================================================================
Validates spatiotemporal eventization rules:
1. Two detections close in space & time (<1km, <6h) merge into one event.
2. Detections outside spatial radius (>1km) remain separate.
3. Detections outside temporal window (>6h) remain separate.
4. Chaining prevention stops runaway spatial extent / duration.
5. Single detection forms a valid SINGLE_DETECTION event.
6. Multi-satellite (N20 + N21) detections merge cleanly with unique_satellite_count = 2.
7. Event-to-detection link table contains 100% of input detections.
8. Deterministic event ID reproducibility.
9. Spatial extent calculation (0.0 for singleton, positive for multi-point).
10. FRP and brightness temperature aggregations.
"""

import math
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_pipeline.events.build_events import (
    BoundedUnionFind,
    spatiotemporal_cluster,
    build_event_records,
)


@pytest.fixture
def sample_detection_df():
    """Constructs a synthetic detection dataframe with controlled space, time, and sensors."""
    # Base location: Nagpur (approx 21.1458° N, 79.0882° E)
    records = [
        # Event 1: Cluster of 3 detections (2 from N20, 1 from N21, ~30 mins apart, <500m apart)
        {
            "detection_id": "DET_N20_20260415_A001",
            "latitude": 21.1458,
            "longitude": 79.0882,
            "acq_datetime": "2026-04-15T07:00:00",
            "satellite": "N20",
            "frp": 10.0,
            "bright_ti4": 330.0,
            "bright_ti5": 295.0,
            "daynight": "D",
            "confidence": "h",
            "source": "VIIRS_NOAA20_SP",
        },
        {
            "detection_id": "DET_N20_20260415_A002",
            "latitude": 21.1470,  # ~130m away
            "longitude": 79.0890,
            "acq_datetime": "2026-04-15T07:00:00",
            "satellite": "N20",
            "frp": 15.0,
            "bright_ti4": 340.0,
            "bright_ti5": 298.0,
            "daynight": "D",
            "confidence": "n",
            "source": "VIIRS_NOAA20_SP",
        },
        {
            "detection_id": "DET_N21_20260415_A003",
            "latitude": 21.1465,  # ~80m away
            "longitude": 79.0885,
            "acq_datetime": "2026-04-15T07:50:00",  # 50 mins later (N21 pass)
            "satellite": "N21",
            "frp": 25.0,
            "bright_ti4": 350.0,
            "bright_ti5": 302.0,
            "daynight": "D",
            "confidence": "h",
            "source": "VIIRS_NOAA21_NRT",
        },
        # Event 2: Same location as Event 1, but 24 hours later (should NOT merge with Event 1)
        {
            "detection_id": "DET_N20_20260416_B001",
            "latitude": 21.1458,
            "longitude": 79.0882,
            "acq_datetime": "2026-04-16T07:00:00",  # 24 hours later
            "satellite": "N20",
            "frp": 8.0,
            "bright_ti4": 325.0,
            "bright_ti5": 290.0,
            "daynight": "D",
            "confidence": "l",
            "source": "VIIRS_NOAA20_SP",
        },
        # Event 3: Single isolated detection 50km away at Bhopal
        {
            "detection_id": "DET_N20_20260415_C001",
            "latitude": 23.2599,
            "longitude": 77.4126,
            "acq_datetime": "2026-04-15T07:00:00",
            "satellite": "N20",
            "frp": 5.0,
            "bright_ti4": 315.0,
            "bright_ti5": 288.0,
            "daynight": "D",
            "confidence": "n",
            "source": "VIIRS_NOAA20_SP",
        },
    ]

    df = pd.DataFrame(records)
    df["acq_dt"] = pd.to_datetime(df["acq_datetime"])
    t_ref = df["acq_dt"].iloc[0]
    df["epoch_hours"] = (df["acq_dt"] - t_ref).dt.total_seconds() / 3600.0

    lat0 = float(df["latitude"].mean())
    lon0 = float(df["longitude"].mean())
    cos_lat0 = math.cos(math.radians(lat0))
    R = 6371.0
    df["proj_x_km"] = np.radians(df["longitude"].values - lon0) * R * cos_lat0
    df["proj_y_km"] = np.radians(df["latitude"].values - lat0) * R

    return df


# Test 1 & 6: Spatial & temporal proximity merges detections, including multi-sensor
def test_spatial_temporal_merge_and_multisensor(sample_detection_df):
    labels, merged, rejected = spatiotemporal_cluster(
        sample_detection_df,
        spatial_radius_km=1.0,
        temporal_window_hours=6.0,
    )
    events_df, links_df = build_event_records(sample_detection_df, labels)

    # Detections 0, 1, 2 should merge into 1 event
    assert labels[0] == labels[1]
    assert labels[1] == labels[2]

    evt1 = events_df[events_df["event_id"] == links_df.loc[0, "event_id"]].iloc[0]
    assert evt1["detection_count"] == 3
    assert evt1["unique_satellite_count"] == 2
    assert evt1["satellites"] == "N20,N21"


# Test 2 & 3: Temporal gap prevents merge
def test_temporal_gap_prevents_merge(sample_detection_df):
    labels, _, _ = spatiotemporal_cluster(
        sample_detection_df,
        spatial_radius_km=1.0,
        temporal_window_hours=6.0,
    )
    # Detection 3 is at the exact same location as 0, but 24h later -> separate event
    assert labels[3] != labels[0]


# Test 4: Chaining prevention stops runaway spatial diameter / duration
def test_chaining_prevention():
    # Construct a chain of 10 points, each 0.8 km apart and 3 hours apart
    # Total distance: ~7.2 km, total time: 27 hours
    x = np.array([i * 0.8 for i in range(10)])
    y = np.zeros(10)
    t = np.array([i * 3.0 for i in range(10)])

    # Restrict max duration to 12 hours
    buf = BoundedUnionFind(10, x, y, t, max_duration_hours=12.0, max_extent_km=15.0)
    for i in range(9):
        buf.union(i, i + 1)

    # Verify that the entire chain did NOT merge into a single 27-hour event
    roots = set(buf.find(i) for i in range(10))
    assert len(roots) > 1
    assert buf.rejected_chaining_edges > 0


# Test 5: Single detection event
def test_single_detection_event(sample_detection_df):
    labels, _, _ = spatiotemporal_cluster(
        sample_detection_df,
        spatial_radius_km=1.0,
        temporal_window_hours=6.0,
    )
    events_df, links_df = build_event_records(sample_detection_df, labels)

    # Detection 4 is at Bhopal (isolated)
    evt_bhopal_id = links_df.loc[4, "event_id"]
    evt_bhopal = events_df[events_df["event_id"] == evt_bhopal_id].iloc[0]

    assert evt_bhopal["detection_count"] == 1
    assert evt_bhopal["event_quality"] == "SINGLE_DETECTION"
    assert evt_bhopal["spatial_extent_km"] == 0.0
    assert evt_bhopal["duration_hours"] == 0.0


# Test 7: Link table contains 100% of input detections
def test_link_table_completeness(sample_detection_df):
    labels, _, _ = spatiotemporal_cluster(sample_detection_df)
    _, links_df = build_event_records(sample_detection_df, labels)

    assert len(links_df) == len(sample_detection_df)
    assert set(links_df["detection_id"]) == set(sample_detection_df["detection_id"])


# Test 8: Deterministic event ID reproducibility
def test_deterministic_event_id(sample_detection_df):
    labels1, _, _ = spatiotemporal_cluster(sample_detection_df)
    events_df1, links_df1 = build_event_records(sample_detection_df, labels1)

    labels2, _, _ = spatiotemporal_cluster(sample_detection_df)
    events_df2, links_df2 = build_event_records(sample_detection_df, labels2)

    pd.testing.assert_frame_equal(events_df1, events_df2)
    pd.testing.assert_frame_equal(links_df1, links_df2)


# Test 9: Spatial extent calculation (0.0 for singleton, >0 for multi-point)
def test_spatial_extent_calculation(sample_detection_df):
    labels, _, _ = spatiotemporal_cluster(sample_detection_df)
    events_df, links_df = build_event_records(sample_detection_df, labels)

    evt_multi = events_df[events_df["detection_count"] > 1].iloc[0]
    assert evt_multi["spatial_extent_km"] > 0.0

    evt_single = events_df[events_df["detection_count"] == 1].iloc[0]
    assert evt_single["spatial_extent_km"] == 0.0


# Test 10: FRP and brightness temperature aggregations
def test_feature_aggregations(sample_detection_df):
    labels, _, _ = spatiotemporal_cluster(sample_detection_df)
    events_df, links_df = build_event_records(sample_detection_df, labels)

    # Event 1 contains detections with FRP 10, 15, 25
    evt1 = events_df[events_df["detection_count"] == 3].iloc[0]
    assert evt1["max_frp_mw"] == 25.0
    assert pytest.approx(evt1["mean_frp_mw"], 0.01) == 16.67
    assert evt1["median_frp_mw"] == 15.0
    assert evt1["sum_frp_mw"] == 50.0
    assert evt1["max_bright_ti4"] == 350.0
    assert evt1["confidence_high_count"] == 2
    assert evt1["confidence_nominal_count"] == 1
