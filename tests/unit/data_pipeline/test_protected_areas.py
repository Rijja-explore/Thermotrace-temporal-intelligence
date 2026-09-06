"""
Unit and QA Tests for ThermoTrace Protected Areas Module
========================================================

Tests:
- source archive immutability
- canonical GeoPackage layer existence
- feature and geometry counts
- CRS and spatial bounds
- attribute completeness and schema
- geometry validity
"""

from pathlib import Path
import pytest
import pyogrio

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "protected_areas"
if not RAW_DIR.exists():
    RAW_DIR = PROJECT_ROOT / "ThermoTrace_ProtectedAREA"

CANONICAL_GPKG = PROJECT_ROOT / "data" / "processed" / "protected_areas" / "protected_areas_india.gpkg"

def test_raw_files_immutability():
    """Verify raw files exist and have expected byte lengths."""
    expected_sizes = {
        "Shapefile_splitting_README.txt": 464,
        "WDPA_sources_Sep2026.csv": 120414,
        "WDPA_WDOECM_Sep2026_Public_IND_shp_0.zip": 440099,
        "WDPA_WDOECM_Sep2026_Public_IND_shp_1.zip": 109357,
        "WDPA_WDOECM_Sep2026_Public_IND_shp_2.zip": 1188472
    }
    for filename, exp_size in expected_sizes.items():
        p = RAW_DIR / filename
        assert p.exists(), f"Missing raw file: {filename}"
        assert p.stat().st_size == exp_size, f"Size changed for {filename}!"

def test_canonical_layers_and_counts():
    """Verify layers and feature counts in canonical GeoPackage."""
    assert CANONICAL_GPKG.exists(), f"Canonical GPKG missing: {CANONICAL_GPKG}"
    layers = dict(pyogrio.list_layers(str(CANONICAL_GPKG)))
    assert "protected_areas_polygons" in layers
    assert "protected_areas_points" in layers
    assert "protected_areas_combined" in layers

    polys = pyogrio.read_dataframe(str(CANONICAL_GPKG), layer="protected_areas_polygons")
    points = pyogrio.read_dataframe(str(CANONICAL_GPKG), layer="protected_areas_points")
    combined = pyogrio.read_dataframe(str(CANONICAL_GPKG), layer="protected_areas_combined")

    assert len(polys) == 63
    assert len(points) == 27
    assert len(combined) == 90

def test_geometry_validity():
    """Verify 100% geometry validity and non-empty geometries."""
    polys = pyogrio.read_dataframe(str(CANONICAL_GPKG), layer="protected_areas_polygons")
    assert polys.geometry.is_valid.all(), "Found invalid polygon geometries!"
    assert not polys.geometry.is_empty.any(), "Found empty polygon geometries!"

    points = pyogrio.read_dataframe(str(CANONICAL_GPKG), layer="protected_areas_points")
    assert points.geometry.is_valid.all(), "Found invalid point geometries!"
    assert not points.geometry.is_empty.any(), "Found empty point geometries!"

def test_crs_and_bounds():
    """Verify EPSG:4326 CRS and Indian subcontinental bounds."""
    polys = pyogrio.read_dataframe(str(CANONICAL_GPKG), layer="protected_areas_polygons")
    assert polys.crs.to_string() == "EPSG:4326"
    b = polys.total_bounds
    assert b[0] >= 68.0 and b[2] <= 98.0
    assert b[1] >= 6.0 and b[3] <= 36.0

def test_attribute_integrity():
    """Verify crucial attributes are populated without duplicates."""
    polys = pyogrio.read_dataframe(str(CANONICAL_GPKG), layer="protected_areas_polygons")
    assert polys["SITE_ID"].duplicated().sum() == 0, "Duplicate SITE_IDs found!"
    assert (polys["ISO3"] == "IND").all(), "Non-IND features detected!"
    assert polys["NAME_ENG"].notna().all(), "Missing English names!"
    assert (polys["NAME_ENG"].str.strip() != "").all(), "Empty English names!"
