# ThermoTrace OSM M4/M1 Data Preparation: India Industrial & Infrastructure Context

This module prepares the full-India OpenStreetMap (OSM) dataset for **ThermoTrace** industrial thermal intelligence and spatial infrastructure analysis.

---

## 1. Executive Summary & Verification

* **Source File:** `data/raw/osm/india/india-260901.osm.pbf` (**Immutable, 1,705,764,974 bytes, 100% verified unmodified**)
* **Canonical Output:** `data/processed/osm/osm_india.gpkg` (**737.67 MB**, EPSG:4326)
  * **Layer `osm_facilities`**: **169,927 features** (119,798 Polygons, 50,114 Points, 15 LineStrings)
  * **Layer `osm_infrastructure`**: **1,137,267 features** (1,054,817 LineStrings, 43,993 Polygons, 38,456 Points, 1 MultiPolygon)
* **Total Preserved Features:** **1,307,194 features**
* **Geometry Validity:** **100% Valid** (0 invalid, 0 empty, 0 nulls across both layers)
* **Duplicate Identifiers:** **0 duplicates**

---

## 2. Directory Structure

```
data/
├── raw/
│   └── osm/
│       └── india/
│           └── india-260901.osm.pbf          # Immutable raw source
├── processed/
│   └── osm/
│       ├── facilities/                       # Partition exports
│       ├── infrastructure/                   # Partition exports
│       └── osm_india.gpkg                    # Multi-layer GeoPackage (EPSG:4326)
│           ├── layer: osm_facilities         (169,927 features)
│           └── layer: osm_infrastructure     (1,137,267 features)
reports/
└── osm/
    ├── osm_inspection_summary.json           # Initial pre-extraction profile
    ├── osm_quality_report.json               # Final post-extraction QA report
    ├── osm_quality_summary.md                # Human-readable QA document
    ├── osm_admin_boundary_inspection.json    # Administrative boundary inspection
    └── osm_admin_boundary_inspection.md      # Administrative boundary assessment & recommendation

data_pipeline/osm/
├── inspect_osm.py                            # Read-only PBF inspection tool
├── extract_osm_context.py                    # Streaming extraction pipeline
├── qa_osm_gpkg.py                            # GeoPackage verification & QA tool
├── inspect_admin_boundaries.py               # Administrative boundary profiling tool
└── README.md                                 # Technical documentation
```

---

## 3. Normalized Category Distributions

### A. Industrial Facilities (`osm_facilities`)
| Normalized Category | Feature Count | Percentage |
|---|---|---|
| `POWER_PLANT` | **62,899** | 37.0% |
| `OTHER_INDUSTRIAL` | **26,433** | 15.6% |
| `INDUSTRIAL_AREA` | **24,700** | 14.5% |
| `SUBSTATION` | **17,063** | 10.0% |
| `QUARRY` | **10,477** | 6.2% |
| `STORAGE_FACILITY` | **10,021** | 5.9% |
| `FACTORY` | **12,740** | 7.5% |
| `WASTE_PROCESSING` | **2,620** | 1.5% |
| `WAREHOUSE` | **2,128** | 1.3% |
| `MINE` | **696** | 0.4% |
| `OIL_GAS` | **79** | 0.05% |
| `REFINERY` | **35** | 0.02% |
| `CHEMICAL_PLANT` | **27** | 0.02% |
| `CEMENT_PLANT` | **7** | 0.004% |
| `STEEL_PLANT` | **2** | 0.001% |

* **Representative Coordinates (`rep_lon`, `rep_lat`):** Verified valid across 100% of features. Explicitly documented as spatial matching centroids, **not** exact thermal vents.

### B. Infrastructure Network (`osm_infrastructure`)
| Normalized Category | Feature Count | Percentage |
|---|---|---|
| `MAJOR_ROAD` (motorway, trunk, primary, secondary, tertiary) | **894,632** | 78.7% |
| `RAILWAY` (rail, freight corridors, yards, subways) | **105,297** | 9.3% |
| `POWER_PLANT` | **62,898** | 5.5% |
| `POWER_LINE` (transmission lines, cables) | **47,718** | 4.2% |
| `SUBSTATION` | **17,063** | 1.5% |
| `AIRPORT` (runways, taxiways, helipads, aprons) | **12,290** | 1.1% |
| `PIPELINE` (oil, gas, water pipelines) | **1,922** | 0.2% |
| `PORT` (seaports, shipping terminals, harbours) | **105** | 0.01% |

---

## 4. Administrative Boundary Assessment & Recommendation

An inspection of `boundary=administrative` features was performed across the PBF extract (`admin_level=2, 4, 6`):

> [!IMPORTANT]
> **RECOMMENDATION: ACQUIRE A SEPARATE AUTHORITATIVE BOUNDARY DATASET**
> 
> OpenStreetMap administrative boundaries **should NOT be used** as the primary national/state clipping boundary for ThermoTrace India:
> 1. **Legal & Territorial Compliance:** OSM depicts borders according to de-facto ground control (Line of Control, Line of Actual Control), which does not match the official Survey of India sovereign boundary required for regulatory compliance.
> 2. **Clip Fragmentations:** Subcontinental PBF regional extracts cut border relations extending into neighboring nations, leading to broken/unclosed perimeter polygons.
> 3. **Non-Standard Codes:** OSM boundaries lack standardized Local Government Directory (LGD) or Census 2011/2021 codes.
> 4. **Solution:** Ingest authoritative Survey of India / Bharat Maps or Datameet India GeoJSON/Shapefiles for national, state (36), and district (780+) boundaries.

---

## 5. Usage Commands

```bash
# 1. Inspect raw PBF
python data_pipeline/osm/inspect_osm.py

# 2. Extract facilities & infrastructure into GeoPackage
python data_pipeline/osm/extract_osm_context.py

# 3. Perform Layer-1 QA on the GeoPackage
python data_pipeline/osm/qa_osm_gpkg.py

# 4. Inspect administrative boundary relations
python data_pipeline/osm/inspect_admin_boundaries.py
```
