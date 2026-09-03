# ThermoTrace Population Layer QA Summary (WorldPop 2025 India 100m)

**Generated:** 2026-09-03T03:46:27.250850+00:00  
**Status:** **PASSED** (1 warnings, 0 errors)

---

## 1. Observed Facts (Raster Metadata)
* **Source Path:** `D:\New folder (2)\data\raw\population\ind_pop_2025_CN_100m_R2025A_v1.tif`
* **File Size:** 742.06 MiB (778,106,191 bytes)
* **Coordinate Reference System (CRS):** `EPSG:4326`
* **Raster Dimensions:** 35,040 columns × 34,507 rows (1,209,125,280 total pixels)
* **Band Count:** 1 band (`float32`)
* **Spatial Resolution:** 0.00083333° × 0.00083333° (~100m cell size at equator)
* **Bounding Extent:**
  * West: `68.195832`
  * South: `6.755834`
  * East: `97.395832`
  * North: `35.511667`
* **NoData Value:** `-99999.0`

---

## 2. Calculated Population Statistics
| Metric | Value | Description |
|---|---|---|
| **Total Estimated Population** | **1,457,435,338.1** | Sum of population in all valid raster cells |
| **Valid Land Pixels** | **139,189,379** (11.51%) | Terrestrial pixels inside India coverage |
| **NoData Pixels** | **1,069,935,901** (88.49%) | Oceanic and external background cells |
| **Mean Population / Cell** | **10.4709** persons | Arithmetic mean across valid cells |
| **Standard Deviation** | **19.3655** persons | Standard deviation across valid cells |
| **Median Population / Cell** | **4.4031** persons | 50th percentile (representative sampling) |
| **Minimum Value** | **0.0000** persons | Smallest observed valid population value |
| **Maximum Value** | **1911.6967** persons | Peak density cell (Lon 72.711249, Lat 11.692917) |
| **Zero-Population Cells** | **17,468** (0.01%) | Uninhabited land cells (mountains, deserts, forests) |
| **Nonzero Cells** | **139,171,911** (99.99%) | Populated settlements and habitations |

### Quantile Distribution (Persons / 100m Cell)
* **P10:** 0.3613
* **P25:** 1.5085
* **P50 (Median):** 4.4031
* **P75:** 11.1721
* **P90:** 24.9758
* **P95:** 39.3734
* **P99:** 96.3731

---

## 3. Data Quality & Warnings
* **Corrupted Blocks:** `0`
* **Negative Values:** `0`
* **NaN Values:** `0`
* **Infinite Values:** `0`
* **Warnings Logged:** 1
  * Raster bounds do not fully encompass standard India BBOX [68.1, 6.5, 97.4, 35.7].
* **Errors Logged:** 0
  * None

---

## 4. Operational Notes
1. **Raw File Immutability:** The raw GeoTIFF was inspected in read-only streaming mode and was not modified.
2. **Spatial Masking:** Bounding box covers the entire Indian subcontinent. National boundary masking should be performed downstream using the project's authoritative administrative polygon.
