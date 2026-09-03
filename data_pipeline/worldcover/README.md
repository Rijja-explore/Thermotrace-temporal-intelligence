# ThermoTrace ESA WorldCover 10m Land Cover Processing Pipeline

This module manages the acquisition, inspection, validation, and canonical mosaicing of the **ESA WorldCover 10m 2021 v200** product for the entire Indian subcontinent.

---

## 1. Source Product & Provenance
* **Dataset:** ESA WorldCover 10m 2021 v200
* **Provider:** European Space Agency (ESA) / VITO Remote Sensing
* **Release Version:** v200 (released 2022, representing 2021 land cover)
* **Nominal Resolution:** 10 meters (`0.000083333333°`)
* **Spatial Reference:** EPSG:4326 (WGS 84 geographic coordinates)
* **Grid Format:** 3° × 3° tiles (36,000 × 36,000 pixels per tile)
* **Datatype:** 8-bit unsigned integer (`uint8`), single band

---

## 2. Directory Structure

```
data/
├── raw/
│   └── worldcover/
│       └── india/                           # 91 raw GeoTIFF tiles (6.40 GB, immutable)
│           ├── ESA_WorldCover_10m_2021_v200_N06E072_Map.tif
│           ├── ...
│           └── download_manifest.json
├── processed/
│   └── worldcover/
│       └── worldcover_india_10m.tif          # Canonical 142.56B-pixel BigTIFF mosaic
reports/
└── worldcover/
    ├── worldcover_tile_inventory.json       # Tile-by-tile metadata & validation
    ├── worldcover_quality_report.json        # Mosaic QA & class distribution
    └── worldcover_quality_summary.md         # Human-readable markdown summary

data_pipeline/
└── worldcover/
    ├── download_worldcover_india.py          # Resumable downloader with backoff
    ├── inspect_worldcover.py                 # Tile inventory and QA inspector
    ├── build_worldcover_mosaic.py            # Streaming windowed BigTIFF mosaic builder
    └── README.md                             # Pipeline documentation
```

---

## 3. ESA WorldCover Classification Scheme

| Value | Land Cover Class | Description |
|---|---|---|
| `10` | **Tree cover** | Any canopy cover formed by trees ≥ 10% |
| `20` | **Shrubland** | Woody vegetation cover < 5m height |
| `30` | **Grassland** | Herbaceous vegetation cover |
| `40` | **Cropland** | Cultivated agricultural fields |
| `50` | **Built-up** | Human-made structures, buildings, urban roads |
| `60` | **Bare / sparse vegetation** | Sand, rock, gravel, arid soil with < 10% vegetation |
| `70` | **Snow and ice** | Perennial and seasonal snow cover, glaciers |
| `80` | **Permanent water bodies** | Lakes, reservoirs, major river courses, marine |
| `90` | **Herbaceous wetland** | Areas with waterlogged soil dominated by herbs |
| `95` | **Mangroves** | Saline coastal vegetation |
| `100`| **Moss and lichen** | Alpine / high-altitude arctic flora |
| `0`  | **NoData / External** | Background oceans and areas outside land borders |

---

## 4. Pipeline Execution & Methodological Constraints

### A. Non-Interference with Raw Data
All 91 downloaded GeoTIFF tiles in `data/raw/worldcover/india/` are strictly immutable. They are preserved intact with original checksums.

### B. Memory-Safe Windowed Mosaicing
Because a full-extent 10m India mosaic spans `396,000 × 360,000` pixels (142.56 billion cells), loading the uncompressed array into RAM would consume >142 GB. The pipeline streams each 36,000×36,000 tile in strips of 3,600 rows directly into pre-indexed windows of a BigTIFF GeoTIFF with 512×512 block tiling and LZW lossless compression. RAM consumption is strictly capped at <400 MB.

### C. Nearest-Neighbour Semantic Invariance
Because land cover values represent categorical classifications rather than continuous fields, all spatial operations and indexing preserve exact integer labels. No bilinear or cubic interpolation is applied.

---

## 5. Usage Commands

```bash
# 1. Download India tiles (resumable with automatic retry)
python ThermoTrace_WorldCover_Downloader/data_pipeline/worldcover/download_worldcover_india.py

# 2. Inspect tiles, verify integrity and generate tile inventory
python data_pipeline/worldcover/inspect_worldcover.py

# 3. Build canonical 10m mosaic and execute Step 5 QA
python data_pipeline/worldcover/build_worldcover_mosaic.py
```
