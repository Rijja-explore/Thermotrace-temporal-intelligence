# ThermoTrace Population Layer: India 100m WorldPop 2025

This module manages the inspection, quality assurance, and processing-ready preparation of the **WorldPop 2025 100m UN-adjusted population raster for India**.

---

## 1. Overview & Dataset Details

* **Source File:** `data/raw/population/ind_pop_2025_CN_100m_R2025A_v1.tif` (Immutable)
* **Dataset Version:** WorldPop R2025A (Constrained Individual Countries 2025, 100m resolution)
* **Demographic Baseline:** ~1.457 Billion persons represented in valid cells
* **Coordinate Reference System:** EPSG:4326 (WGS 84 geographic latitude/longitude)
* **Cell Resolution:** 0.00083333° (~100m at equator)
* **Dimensions:** 35,040 columns × 34,507 rows (1,209,125,280 cells)
* **NoData Value:** `-99999.0`

---

## 2. Directory Structure

```
data/
├── raw/
│   └── population/
│       └── ind_pop_2025_CN_100m_R2025A_v1.tif   # Immutable raw GeoTIFF
├── processed/
│   └── population/
│       ├── population_india_100m.tif            # Processing-ready Cloud-Optimized GeoTIFF
│       └── population_india_sample_100km.tif    # 1000x1000 QA validation tile (NCR)
reports/
└── population/
    ├── population_inspection.json               # Full machine-readable inspection
    ├── population_quality_report.json           # Machine-readable QA metrics
    └── population_quality_summary.md            # Human-readable QA document

data_pipeline/population/
├── inspect_population.py                        # Chunked streaming QA tool
├── process_population.py                        # Pyramided asset generator
└── README.md                                    # Documentation
```

---

## 3. QA Metrics Summary

* **Valid Land Pixels:** 139,189,379 (11.5% of raster grid)
* **NoData Pixels:** 1,069,935,901 (88.5% of raster grid)
* **Negative Values (excl. NoData):** `0`
* **NaN / Infinite Pixels:** `0`
* **Corrupted / Unreadable Blocks:** `0`
* **Mean Population / Cell:** 10.4709 persons
* **Median Population / Cell:** 4.4031 persons
* **Zero Population Cells:** 17,468 (0.01% of valid land cells)
* **Nonzero Cells:** 139,171,911 (99.99%)

---

## 4. Usage Commands

### Inspect Raw Population Raster
```bash
python data_pipeline/population/inspect_population.py
```

### Build Processed Tiled GeoTIFF & Overviews
```bash
python data_pipeline/population/process_population.py
```

### Run Population Unit & Equivalence Tests
```bash
pytest tests/test_population.py
```
