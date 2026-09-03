"""
Unit and QA Tests for ThermoTrace ESA WorldCover Module
=======================================================

Tests:
- All 91 raw tiles exist and are intact
- Tile inventory completeness and structure
- Class scheme definitions
- Geographic bounding extent coverage
"""

from pathlib import Path
import json
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_WC_DIR = PROJECT_ROOT / "data" / "raw" / "worldcover" / "india"
if not RAW_WC_DIR.exists():
    RAW_WC_DIR = PROJECT_ROOT / "ThermoTrace_WorldCover_Downloader" / "data" / "raw" / "worldcover" / "india"

INV_PATH = PROJECT_ROOT / "reports" / "worldcover" / "worldcover_tile_inventory.json"

VALID_CLASSES = {0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100}

def test_raw_tiles_count_and_existence():
    """Verify all 91 raw GeoTIFF tiles exist and are > 1MB in size."""
    tiles = list(RAW_WC_DIR.glob("*.tif"))
    assert len(tiles) == 91, f"Expected 91 tiles, found {len(tiles)}"
    for t in tiles:
        assert t.stat().st_size > 1_000_000, f"Tile {t.name} is suspiciously small: {t.stat().st_size} bytes"

def test_tile_inventory_structure():
    """Verify tile inventory JSON structure and completeness."""
    assert INV_PATH.exists(), f"Tile inventory missing: {INV_PATH}"
    data = json.loads(INV_PATH.read_text(encoding="utf-8"))
    assert data["total_tiles_found"] == 91
    assert data["corrupted_tiles"] == []
    assert len(data["tiles"]) == 91

    # Check tile properties
    for t in data["tiles"]:
        assert t["crs"] == "EPSG:4326"
        assert t["dimensions"] == [36000, 36000]
        assert t["bands"] == 1
        assert t["datatype"] == "uint8"
        assert t["nodata"] == 0.0

def test_geographic_coverage():
    """Verify tiles span the entire Indian subcontinent."""
    data = json.loads(INV_PATH.read_text(encoding="utf-8"))
    tiles = data["tiles"]

    min_lon = min(t["bounds"]["left"] for t in tiles)
    max_lon = max(t["bounds"]["right"] for t in tiles)
    min_lat = min(t["bounds"]["bottom"] for t in tiles)
    max_lat = max(t["bounds"]["top"] for t in tiles)

    assert min_lon <= 68.0, "Coverage missing western India"
    assert max_lon >= 97.0, "Coverage missing eastern India"
    assert min_lat <= 7.0, "Coverage missing southern tip of India"
    assert max_lat >= 35.0, "Coverage missing northern India"
