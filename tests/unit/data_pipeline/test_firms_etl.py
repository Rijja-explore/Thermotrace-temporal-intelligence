"""
ThermoTrace - Layer-0 FIRMS Canonical ETL Unit & Integration Tests
==================================================================
Validates all 10 canonical processing rules:
1. Valid coordinate pass
2. Invalid latitude (>90, <-90)
3. Invalid longitude (>180, <-180)
4. Date/time combination (acq_datetime ISO-8601 formatting, zero padding)
5. Malformed/negative numeric FRP handling
6. Confidence preservation and numeric mapping
7. Conservative duplicate detection
8. Multi-sensor protection (N20 and N21 at same location/time are kept separate)
9. Deterministic detection ID reproducibility
10. India bounding box flagging (inside vs outside)
"""

import hashlib
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_pipeline.firms.canonical_etl import (
    INDIA_BBOX,
    WGS84_BOUNDS,
    CONFIDENCE_ORDINAL_MAP,
    normalize_and_validate,
    detect_and_deduplicate,
    generate_detection_ids,
)


@pytest.fixture
def base_raw_record():
    """Provides a single valid raw FIRMS VIIRS observation template."""
    return {
        "latitude": 20.5937,
        "longitude": 78.9629,
        "bright_ti4": 335.5,
        "scan": 0.45,
        "track": 0.62,
        "acq_date": "2026-04-15",
        "acq_time": 735,  # 07:35 UTC
        "satellite": "N20",
        "instrument": "VIIRS",
        "confidence": "n",
        "version": "2",
        "bright_ti5": 298.2,
        "frp": 12.4,
        "daynight": "D",
        "type": 0.0,
        "source_product": "VIIRS_NOAA20_SP",
        "downloaded_at_utc": "2026-04-16T00:00:00Z",
    }


# Test 1: Valid coordinate
def test_valid_coordinate(base_raw_record):
    df = pd.DataFrame([base_raw_record])
    res = normalize_and_validate(df)
    assert res["quality_flag"].iloc[0] == "VALID"
    assert res["within_india_bbox"].iloc[0] == True
    assert res["latitude"].iloc[0] == 20.5937
    assert res["longitude"].iloc[0] == 78.9629


# Test 2: Invalid latitude
def test_invalid_latitude(base_raw_record):
    rec_high = dict(base_raw_record, latitude=95.123)
    rec_low = dict(base_raw_record, latitude=-92.456)
    df = pd.DataFrame([rec_high, rec_low])
    res = normalize_and_validate(df)
    assert res["quality_flag"].iloc[0] == "INVALID_COORDS"
    assert res["quality_flag"].iloc[1] == "INVALID_COORDS"


# Test 3: Invalid longitude
def test_invalid_longitude(base_raw_record):
    rec_east = dict(base_raw_record, longitude=185.0)
    rec_west = dict(base_raw_record, longitude=-190.5)
    df = pd.DataFrame([rec_east, rec_west])
    res = normalize_and_validate(df)
    assert res["quality_flag"].iloc[0] == "INVALID_COORDS"
    assert res["quality_flag"].iloc[1] == "INVALID_COORDS"


# Test 4: Date/time combination & zero padding
def test_datetime_combination(base_raw_record):
    rec1 = dict(base_raw_record, acq_date="2026-01-05", acq_time=531)  # 05:31
    rec2 = dict(base_raw_record, acq_date="2026-11-20", acq_time=1940)  # 19:40
    rec3 = dict(base_raw_record, acq_date="2026-07-04", acq_time="0005") # 00:05
    df = pd.DataFrame([rec1, rec2, rec3])
    res = normalize_and_validate(df)

    assert res["acq_time"].iloc[0] == "0531"
    assert res["acq_datetime"].iloc[0] == "2026-01-05T05:31:00"

    assert res["acq_time"].iloc[1] == "1940"
    assert res["acq_datetime"].iloc[1] == "2026-11-20T19:40:00"

    assert res["acq_time"].iloc[2] == "0005"
    assert res["acq_datetime"].iloc[2] == "2026-07-04T00:05:00"


# Test 5: Malformed / negative numeric FRP
def test_malformed_negative_frp(base_raw_record):
    rec_neg = dict(base_raw_record, frp=-5.2)
    rec_zero = dict(base_raw_record, frp=0.0)
    rec_nan = dict(base_raw_record, frp="bad_val")
    df = pd.DataFrame([rec_neg, rec_zero, rec_nan])
    res = normalize_and_validate(df)

    assert res["quality_flag"].iloc[0] == "INVALID_FRP_NEGATIVE"
    assert res["quality_flag"].iloc[1] == "SUSPICIOUS_FRP_ZERO"
    assert res["quality_flag"].iloc[2] == "MISSING_FRP"


# Test 6: Confidence preservation and ordinal numeric mapping
def test_confidence_preservation(base_raw_record):
    rec_low = dict(base_raw_record, confidence="l")
    rec_nom = dict(base_raw_record, confidence="n")
    rec_high = dict(base_raw_record, confidence="h")
    df = pd.DataFrame([rec_low, rec_nom, rec_high])
    res = normalize_and_validate(df)

    # Original categorical preserved
    assert list(res["confidence"]) == ["l", "n", "h"]
    # Documented ordinal operational index
    assert pytest.approx(res["confidence_score_operational"].iloc[0], 0.01) == 0.3
    assert pytest.approx(res["confidence_score_operational"].iloc[1], 0.01) == 0.6
    assert pytest.approx(res["confidence_score_operational"].iloc[2], 0.01) == 0.9
    # Backward compatible alias
    assert pytest.approx(res["confidence_numeric"].iloc[0], 0.01) == 0.3
    # Authoritative type preservation
    assert res["type"].iloc[0] == 0
    assert res["hotspot_type"].iloc[0] == 0


# Test 7: Conservative duplicate detection
def test_duplicate_detection(base_raw_record):
    # Two identical records
    rec1 = dict(base_raw_record)
    rec2 = dict(base_raw_record)
    df = pd.DataFrame([rec1, rec2])
    norm_df = normalize_and_validate(df)
    deduped_df, dups_removed, _ = detect_and_deduplicate(norm_df)

    assert dups_removed == 1
    assert len(deduped_df) == 1


# Test 8: N20 and N21 records remaining separate (multi-sensor agreement)
def test_cross_satellite_preservation(base_raw_record):
    # Identical space and time, but different satellites
    rec_n20 = dict(base_raw_record, satellite="N20")
    rec_n21 = dict(base_raw_record, satellite="N21")
    df = pd.DataFrame([rec_n20, rec_n21])
    norm_df = normalize_and_validate(df)
    deduped_df, dups_removed, _ = detect_and_deduplicate(norm_df)

    assert dups_removed == 0
    assert len(deduped_df) == 2
    assert set(deduped_df["satellite"]) == {"N20", "N21"}


# Test 9: Deterministic detection ID reproducibility
def test_deterministic_detection_id(base_raw_record):
    df1 = normalize_and_validate(pd.DataFrame([base_raw_record]))
    df2 = normalize_and_validate(pd.DataFrame([base_raw_record]))

    id1 = generate_detection_ids(df1).iloc[0]
    id2 = generate_detection_ids(df2).iloc[0]

    assert id1 == id2
    assert id1.startswith("DET_N20_20260415_")
    # Verify exact 12-char hex hash suffix
    suffix = id1.split("_")[-1]
    assert len(suffix) == 12


# Test 10: India bbox flagging (inside vs outside)
def test_india_bbox_flag(base_raw_record):
    # Inside: Central India
    inside_rec = dict(base_raw_record, latitude=20.5937, longitude=78.9629)
    # Outside: Arabian Sea west of 68.1
    outside_west = dict(base_raw_record, latitude=20.0, longitude=65.0)
    # Outside: Indian Ocean south of 6.5
    outside_south = dict(base_raw_record, latitude=4.0, longitude=80.0)
    # Outside: Tibet north of 35.7
    outside_north = dict(base_raw_record, latitude=37.0, longitude=80.0)
    # Outside: Myanmar/Bay of Bengal east of 97.4
    outside_east = dict(base_raw_record, latitude=20.0, longitude=99.0)

    df = pd.DataFrame([inside_rec, outside_west, outside_south, outside_north, outside_east])
    res = normalize_and_validate(df)

    assert res["within_india_bbox"].iloc[0] == True
    assert res["within_india_bbox"].iloc[1] == False
    assert res["within_india_bbox"].iloc[2] == False
    assert res["within_india_bbox"].iloc[3] == False
    assert res["within_india_bbox"].iloc[4] == False
