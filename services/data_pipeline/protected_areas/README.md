# ThermoTrace Protected Areas Layer: India WDPA/WDOECM

This module prepares the canonical **World Database on Protected Areas (WDPA)** and **Other Effective Area-based Conservation Measures (WDOECM)** dataset for India for spatial containment queries with thermal anomalies (e.g., NASA FIRMS, Copernicus Sentinel).

---

## 1. Source Dataset & Provenance
* **Source:** UNEP-WCMC & IUCN World Database on Protected Areas (WDPA)
* **Release Version:** September 2026 Public Release (IND)
* **Raw Root:** `data/raw/protected_areas/`
* **Raw Files:**
  * `Shapefile_splitting_README.txt` (UNEP-WCMC shapefile partition documentation)
  * `WDPA_sources_Sep2026.csv` (Source metadata registry, 387 records)
  * `WDPA_WDOECM_Sep2026_Public_IND_shp_0.zip` (Part 0: 21 polygons, 9 points)
  * `WDPA_WDOECM_Sep2026_Public_IND_shp_1.zip` (Part 1: 21 polygons, 9 points)
  * `WDPA_WDOECM_Sep2026_Public_IND_shp_2.zip` (Part 2: 21 polygons, 9 points)

---

## 2. Directory Structure

```
data/
├── raw/
│   └── protected_areas/
│       ├── Shapefile_splitting_README.txt
│       ├── WDPA_sources_Sep2026.csv
│       ├── WDPA_WDOECM_Sep2026_Public_IND_shp_0.zip
│       ├── WDPA_WDOECM_Sep2026_Public_IND_shp_1.zip
│       └── WDPA_WDOECM_Sep2026_Public_IND_shp_2.zip
├── processed/
│   └── protected_areas/
│       └── protected_areas_india.gpkg        # Canonical multi-layer GeoPackage
│           ├── layer: protected_areas_polygons  (63 boundary polygons)
│           ├── layer: protected_areas_points    (27 centroid points)
│           └── layer: protected_areas_combined  (90 sites with centroids)
reports/
└── protected_areas/
    ├── protected_areas_inspection.json
    ├── protected_areas_quality_summary.md
    └── protected_areas_canonical_validation.json

data_pipeline/protected_areas/
├── inspect_protected_areas.py                # Multi-partition inspection tool
├── process_protected_areas.py                # Canonical GeoPackage generator
└── README.md                                 # Documentation
```

---

## 3. Spatial Layers & Schema

### Primary Boundary Layer: `protected_areas_polygons`
Used for exact polygon containment testing with thermal event centroids.

| Attribute | Type | Description |
|---|---|---|
| `SITE_ID` | Integer | Canonical unique Protected Area identifier (WDPAID) |
| `SITE_PID` | String | Unique parcel identifier |
| `SITE_TYPE` | String | `PA` (Protected Area) or `OECM` |
| `NAME_ENG` | String | Official English name |
| `NAME` | String | National/local name |
| `DESIG_ENG` | String | Designation (e.g. National Park, Wildlife Sanctuary, Ramsar Site) |
| `DESIG_TYPE` | String | Designation type (`National`, `Regional`, `International`) |
| `IUCN_CAT` | String | IUCN Management Category (Ia, Ib, II, III, IV, V, VI, Not Reported) |
| `REALM` | String | `Terrestrial` or `Marine` |
| `REP_AREA` | Float | Reported area in square kilometers |
| `GIS_AREA` | Float | GIS calculated area in square kilometers |
| `STATUS` | String | Legal status (`Designated`) |
| `STATUS_YR` | Integer | Year of official designation |
| `GOV_TYPE` | String | Governance model |
| `MANG_AUTH` | String | Responsible management authority |
| `ISO3` | String | Country ISO3 code (`IND`) |
| `geometry` | Polygon / MultiPolygon | EPSG:4326 |

---

## 4. QA & Validation Metrics
* **Total Features Consolidated:** 90 sites (63 polygon boundaries, 27 supplementary points).
* **Geometry Validity:** 100% valid (0 invalid, 0 self-intersecting, 0 empty).
* **Duplicate Identifiers:** 0 duplicates.
* **Country Integrity:** 100% `ISO3 == 'IND'`.
* **Total GIS Protected Area:** 17,998.67 km² (across polygon-mapped sites).
* **Spatial Extent:** `[70.118694° E, 8.140104° N]` to `[93.925240° E, 34.411480° N]`.

---

## 5. Usage & Reproduction Commands

### Run Inspection & QA
```bash
python data_pipeline/protected_areas/inspect_protected_areas.py
```

### Build and Validate Canonical GeoPackage
```bash
python data_pipeline/protected_areas/process_protected_areas.py
```
