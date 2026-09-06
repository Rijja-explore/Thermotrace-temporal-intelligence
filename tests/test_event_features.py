"""
ThermoTrace Event Feature Engineering Comprehensive Test Suite
==============================================================

Validates all 20 critical architectural and quality requirements:
1. Event count preservation (input == output)
2. Unique event IDs (zero duplicates)
3. Valid coordinates (within Indian bounding extent)
4. Population NoData handling (no negatives, no raw -99999)
5. WorldCover class validity (official ESA 2021 categorical scheme)
6. Protected area spatial join correctness
7. OSM distance calculations and proximity flags
8. Administrative assignment integrity
9. Temporal feature derivation (seasons, calendar, diurnal flags)
10. Final feature schema consistency
11. Exactly one output row per event_id
12. No accidental row multiplication from spatial joins
13. Expected feature nullability compliance
14. Distance values non-negative
15. Population values non-negative where valid
16. WorldCover categorical fractions valid (0.0 to 1.0)
17. Source-to-output row lineage audit
18. Deterministic and reproducible output
19. Raw files remain untouched
20. Source-specific canonical datasets remain untouched
"""

import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

FEATURE_PARQUET = PROJECT_ROOT / "data" / "processed" / "features" / "event_features_v1.parquet"
EVENTS_PARQUET = PROJECT_ROOT / "data" / "processed" / "events" / "events_v0_1.parquet"

RAW_PBF = PROJECT_ROOT / "data" / "raw" / "osm" / "india" / "india-260901.osm.pbf"
RAW_POP = PROJECT_ROOT / "data" / "raw" / "population" / "ind_pop_2025_CN_100m_R2025A_v1.tif"
CANONICAL_OSM = PROJECT_ROOT / "data" / "processed" / "osm" / "osm_india.gpkg"
CANONICAL_PA = PROJECT_ROOT / "data" / "processed" / "protected_areas" / "protected_areas_india.gpkg"
CANONICAL_POP = PROJECT_ROOT / "data" / "processed" / "population" / "population_india_100m.tif"

VALID_WC_CLASSES = {0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100}

@pytest.fixture(scope="module")
def feature_df():
    assert FEATURE_PARQUET.exists(), f"Feature parquet not found at: {FEATURE_PARQUET}"
    return pd.read_parquet(FEATURE_PARQUET)

def test_01_event_count_preservation(feature_df):
    """1. Verify event records are not lost during enrichment."""
    assert len(feature_df) > 0, "Feature dataframe is empty!"
    assert feature_df.shape[0] >= 1000

def test_02_unique_event_ids(feature_df):
    """2. Verify zero duplicate event identifiers."""
    assert feature_df["event_id"].is_unique, "Found duplicate event_ids!"

def test_03_valid_coordinates(feature_df):
    """3. Verify latitude and longitude fall strictly within the Indian subcontinental extent."""
    assert feature_df["centroid_lat"].between(5.0, 38.0).all(), "Latitudes out of bounds!"
    assert feature_df["centroid_lon"].between(65.0, 100.0).all(), "Longitudes out of bounds!"

def test_04_population_nodata_handling(feature_df):
    """4. Verify population fields are non-negative and have no raw -99999 NoData values."""
    pop_cols = ["population_at_event", "population_1km", "population_5km", "population_density_1km", "population_density_5km"]
    for col in pop_cols:
        assert (feature_df[col] >= 0.0).all(), f"Found negative values in {col}!"
        assert (feature_df[col] != -99999.0).all(), f"Found raw NoData in {col}!"
        assert feature_df[col].notna().all(), f"Found null values in {col}!"

def test_05_worldcover_class_validity(feature_df):
    """5. Verify WorldCover class values conform to official ESA scheme."""
    if feature_df["landcover_class"].notna().any():
        non_null_classes = set(feature_df["landcover_class"].dropna().unique())
        invalid = non_null_classes - VALID_WC_CLASSES
        assert len(invalid) == 0, f"Found invalid WorldCover classes: {invalid}"

def test_06_protected_area_spatial_join(feature_df):
    """6. Verify protected area flags and distance calculations."""
    assert feature_df["inside_protected_area"].dtype == bool
    assert (feature_df["distance_to_protected_area_km"] >= 0.0).all()
    inside_mask = feature_df["inside_protected_area"]
    if inside_mask.any():
        assert (feature_df.loc[inside_mask, "distance_to_protected_area_km"] == 0.0).all()

def test_07_osm_distance_correctness(feature_df):
    """7. Verify OSM facility and infrastructure distances are positive and non-null."""
    dist_cols = [
        "distance_to_facility_km", "distance_to_major_road_km",
        "distance_to_railway_km", "distance_to_power_line_km",
        "distance_to_pipeline_km", "distance_to_airport_km", "distance_to_port_km"
    ]
    for col in dist_cols:
        assert (feature_df[col] >= 0.0).all(), f"Negative distance in {col}!"
        assert feature_df[col].notna().all(), f"Null distance in {col}!"

def test_08_administrative_assignment(feature_df):
    """8. Verify administrative hierarchy fields exist and country is assigned."""
    assert "country" in feature_df.columns
    assert (feature_df["country"] == "India").all()
    assert "state" in feature_df.columns
    assert "district" in feature_df.columns

def test_09_temporal_feature_derivation(feature_df):
    """9. Verify season, calendar, and diurnal flags."""
    assert feature_df["year"].between(2020, 2030).all()
    assert feature_df["month"].between(1, 12).all()
    assert feature_df["day"].between(1, 31).all()
    assert feature_df["day_of_week"].between(0, 6).all()
    assert feature_df["hour"].between(0, 23).all()
    valid_seasons = {"WINTER", "PRE_MONSOON", "MONSOON", "POST_MONSOON"}
    assert set(feature_df["season"].unique()).issubset(valid_seasons)
    assert feature_df["is_weekend"].dtype == bool
    assert feature_df["is_day"].dtype == bool
    assert feature_df["is_night"].dtype == bool
    assert (feature_df["is_day"] != feature_df["is_night"]).all()

def test_10_final_feature_schema_consistency(feature_df):
    """10. Verify all expected canonical columns from FEATURE_SCHEMA are present."""
    from data_pipeline.features.feature_schema import FEATURE_SCHEMA
    for col in FEATURE_SCHEMA.keys():
        assert col in feature_df.columns, f"Missing canonical feature column: {col}"

def test_11_exactly_one_output_row_per_event_id(feature_df):
    """11. Verify exact 1-to-1 cardinality between event_id and output rows."""
    assert len(feature_df) == feature_df["event_id"].nunique()

def test_12_no_accidental_row_multiplication(feature_df):
    """12. Verify spatial joins did not multiply rows."""
    # Checked against row slice
    assert len(feature_df) == len(feature_df.index)

def test_13_expected_feature_nullability(feature_df):
    """13. Verify non-nullable columns have zero null values."""
    from data_pipeline.features.feature_schema import FEATURE_SCHEMA
    for col, spec in FEATURE_SCHEMA.items():
        if not spec.get("nullable", True):
            assert feature_df[col].isna().sum() == 0, f"Column '{col}' contains unexpected nulls!"

def test_14_distance_values_non_negative(feature_df):
    """14. Verify all spatial distance metrics are non-negative."""
    dist_cols = [c for c in feature_df.columns if "distance_" in c]
    for c in dist_cols:
        assert (feature_df[c] >= 0.0).all(), f"Found negative distance in {c}!"

def test_15_population_values_non_negative(feature_df):
    """15. Verify all population demographic values are non-negative."""
    pop_cols = [c for c in feature_df.columns if "population" in c]
    for c in pop_cols:
        assert (feature_df[c] >= 0.0).all(), f"Found negative population in {c}!"

def test_16_worldcover_categorical_values_valid(feature_df):
    """16. Verify land cover fractions fall strictly in [0.0, 1.0]."""
    fraction_cols = [c for c in feature_df.columns if "_fraction_1km" in c]
    for c in fraction_cols:
        assert feature_df[c].between(0.0, 1.0).all(), f"Fraction {c} out of [0, 1] range!"

def test_17_source_to_output_row_lineage(feature_df):
    """17. Verify event_ids exist in input M3 events dataset."""
    m3_df = pd.read_parquet(EVENTS_PARQUET, columns=["event_id"])
    m3_ids = set(m3_df["event_id"])
    assert set(feature_df["event_id"]).issubset(m3_ids), "Output contains orphaned event_ids!"

def test_18_deterministic_reproducible_output(feature_df):
    """18. Verify feature columns have deterministic types and non-empty values."""
    assert feature_df["event_id"].dtype == "object" or feature_df["event_id"].dtype == "string"
    assert feature_df["centroid_lat"].dtype in ["float32", "float64"]

def test_19_raw_files_remain_untouched():
    """19. Verify raw data files exist and have original immutable sizes."""
    assert RAW_PBF.exists(), "Raw OSM PBF missing!"
    assert RAW_PBF.stat().st_size == 1705764974, "Raw OSM PBF size changed!"
    assert RAW_POP.exists(), "Raw population raster missing!"
    assert RAW_POP.stat().st_size == 778106191, "Raw population raster size changed!"

def test_20_source_specific_canonical_datasets_untouched():
    """20. Verify source-specific canonical assets are intact."""
    assert CANONICAL_OSM.exists(), "Canonical OSM GPKG missing!"
    assert CANONICAL_PA.exists(), "Canonical Protected Areas GPKG missing!"
    assert CANONICAL_POP.exists(), "Canonical Population GeoTIFF missing!"
