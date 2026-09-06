# ThermoTrace Protected Areas (WDPA) QA Summary

**Generated:** 2026-09-03T03:52:13.970301+00:00  
**Status:** **PASSED** (0 warnings, 0 errors)

---

## 1. Raw Data Inventory & Structure
* **Source Directory:** `D:\New folder (2)\data\raw\protected_areas`
* **Archives:** 3 equal-part split ZIP archives (`IND_shp_0.zip`, `IND_shp_1.zip`, `IND_shp_2.zip`) per UNEP-WCMC distribution standards.
* **Reference Files:** `Shapefile_splitting_README.txt`, `WDPA_sources_Sep2026.csv` (387 source metadata records).

---

## 2. Selected Spatial Dataset & Layers
| Parameter | Canonical Polygon Layer | Supplementary Point Layer |
|---|---|---|
| **Layer Name** | `WDPA_WDOECM_Sep2026_Public_IND_shp-polygons` | `WDPA_WDOECM_Sep2026_Public_IND_shp-points` |
| **Role in ThermoTrace** | **Primary spatial boundary intersection** with thermal detections | Centroid references for sites without digitized boundaries |
| **Feature Count** | **63 protected areas** | **27 protected areas** |
| **Geometry Types** | `Polygon` (52), `MultiPolygon` (11) | `MultiPoint` (27) |
| **Geometry Validity** | **63 / 63 (100% Valid)** | **27 / 27 (100% Valid)** |
| **CRS** | `EPSG:4326` | `EPSG:4326` |
| **Total GIS Area** | **27,794.23 km²** | N/A (Points) |
| **Spatial Extent** | `[70.118694, 8.140104]` to `[93.92524, 34.41148]` | `[72.039167, 8.95]` to `[91.65, 34.083333]` |

---

## 3. Schema & Concept Mapping
* **Total Fields:** 33
* **Identifier:** `SITE_ID` (100% populated, 0 duplicates across chunks)
* **Parcel Identifier:** `SITE_PID`
* **Name (English):** `NAME_ENG` (0 unnamed protected areas)
* **Name (Local):** `NAME`
* **Designation:** `DESIG_ENG` (3 designation categories, e.g. National Park, Wildlife Sanctuary, Ramsar Site, Community Reserve)
* **Designation Type:** `DESIG_TYPE` (100% populated)
* **IUCN Category:** `IUCN_CAT` (9 categories)
* **Legal Status:** `STATUS` (100% 'Designated')
* **Country:** `ISO3` (100% 'IND')

---

## 4. Quality Assurance Findings
* **Invalid Geometries:** `0` (Zero repair operations required)
* **Duplicate Identifiers:** `0`
* **Empty Geometries:** `0`
* **Non-India Inclusions:** `0`
* **Warnings:** 0
  * None
* **Errors:** 0
  * None

---

## 5. Next Steps for Canonical Asset Generation
The 3 non-overlapping polygon chunks will be consolidated into a single canonical GeoPackage layer `protected_areas_polygons` in `data/processed/protected_areas/protected_areas_india.gpkg`, with points stored in layer `protected_areas_points`.
