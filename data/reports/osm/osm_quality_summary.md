# ThermoTrace OSM Layer-1 Quality Assurance Summary

**Generated:** 2026-09-03T04:15:47.859186+00:00  
**Status:** **PASSED** (0 invalid geometries, 0 empty geometries)  
**GeoPackage:** `D:\New folder (2)\data\processed\osm\osm_india.gpkg` (737.67 MB)

---

## 1. Overview & Verification
* **Source PBF:** `data/raw/osm/india/india-260901.osm.pbf` (**Immutable, verified 100% intact & unmodified**)
* **GeoPackage Layers:**
  1. `osm_facilities`: **169,927 features**
  2. `osm_infrastructure`: **1,137,267 features**
* **Total Objects Preserved:** **1,307,194 features**
* **Coordinate Reference System:** `EPSG:4326` (EPSG:4326)
* **Spatial Extent:**
  * West: `68.500797` | South: `8.081518`
  * East: `96.99696` | North: `35.377822`

---

## 2. Industrial Facilities QA (`osm_facilities`)
* **Total Facilities:** **169,927**
* **Geometry Validity:** **169,927 / 169,927 (100% Valid)**
* **Invalid / Empty / Null Geometries:** **0**
* **Geometry Types:**
  * `Polygon`: 119,798 (70.5%)
  * `Point`: 50,114 (29.5%)
  * `LineString`: 15 (0.0%)
* **Named vs Unnamed:**
  * Named: 22,232 (13.1%)
  * Unnamed: 147,695 (86.9%) (identified via functional tags)
* **Operator Tagged:** 4,953 (2.9%)
* **Representative Centroid Coordinates (`rep_lon`, `rep_lat`):** Verified valid across 100% of features. Explicitly documented as spatial matching points, **not** exact thermal vents.

### Facility Category Breakdown
| Normalized Category | Feature Count | Percentage |
|---|---|---|
| `POWER_PLANT` | **60,570** | 35.6% |
| `OTHER_INDUSTRIAL` | **31,936** | 18.8% |
| `INDUSTRIAL_AREA` | **21,261** | 12.5% |
| `SUBSTATION` | **17,052** | 10.0% |
| `FACTORY` | **12,108** | 7.1% |
| `STORAGE_FACILITY` | **10,999** | 6.5% |
| `QUARRY` | **10,418** | 6.1% |
| `WASTE_PROCESSING` | **2,612** | 1.5% |
| `WAREHOUSE` | **2,126** | 1.3% |
| `MINE` | **696** | 0.4% |
| `OIL_GAS` | **79** | 0.0% |
| `REFINERY` | **35** | 0.0% |
| `CHEMICAL_PLANT` | **26** | 0.0% |
| `CEMENT_PLANT` | **7** | 0.0% |
| `STEEL_PLANT` | **2** | 0.0% |

---

## 3. Infrastructure QA (`osm_infrastructure`)
* **Total Infrastructure:** **1,137,267**
* **Geometry Validity:** **1,137,267 / 1,137,267 (100% Valid)**
* **Invalid / Empty / Null Geometries:** **0**
* **Geometry Types:**
  * `LineString`: 1,054,817 (92.8%)
  * `Polygon`: 43,993 (3.9%)
  * `Point`: 38,456 (3.4%)
  * `MultiPolygon`: 1 (0.0%)

### Infrastructure Category Breakdown
| Normalized Category | Feature Count | Percentage |
|---|---|---|
| `MAJOR_ROAD` | **894,263** | 78.6% |
| `RAILWAY` | **105,295** | 9.3% |
| `POWER_PLANT` | **60,569** | 5.3% |
| `POWER_LINE` | **47,717** | 4.2% |
| `SUBSTATION` | **17,052** | 1.5% |
| `AIRPORT` | **12,245** | 1.1% |
| `PORT` | **80** | 0.0% |
| `PIPELINE` | **46** | 0.0% |

---

## 4. Key Limitations & Operational Directives
1. **OSM is Voluntary Context:** Do not present OSM as an exhaustive national registry.
2. **Spatial Association Only:** Distance calculations from thermal detections to facilities indicate spatial proximity; do not assert industrial ownership without multi-sensor correlation.
