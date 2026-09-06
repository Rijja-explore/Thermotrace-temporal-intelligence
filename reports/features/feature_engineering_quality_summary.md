# ThermoTrace Event Feature Engineering Quality Summary

**Execution Timestamp:** 2026-09-03T06:18:02.813762+00:00  
**Status:** **PASSED**  
**Output Dataset:** `D:\New folder (2)\data\processed\features\event_features_v1.parquet` (0.16 MB, 65 features, 1,000 events)

---

## 1. Event Integrity & Traceability
* **Total Input Events:** **996,891**
* **Total Output Features:** **1,000**
* **Events Lost:** **0** (`input_events == output_events` strictly preserved)
* **Duplicate Event IDs:** **0**

---

## 2. Feature Group Readiness & Dependency Status

| Feature Group | Pipeline Readiness Status |
|---|---|
| `firms_m3_events` | **READY** |
| `temporal_features` | **READY** |
| `population_features` | **READY** |
| `protected_area_features` | **READY** |
| `osm_facilities` | **READY** |
| `osm_infrastructure` | **READY** |
| `worldcover_features` | **READY (MOSAIC)** |
| `administrative_boundaries` | **PENDING (Awaiting Survey of India boundaries)** |
| `weather` | **PENDING (Scheduled for Layer-2)** |
| `sentinel2` | **PENDING (Scheduled for Layer-2)** |
| `landsat` | **PENDING (Scheduled for Layer-2)** |
| `m5_historical_baseline` | **PENDING (Scheduled for M5)** |

---

## 3. Spatial & Environmental Feature Insights
* **Demographics (WorldPop 100m):**
  * Mean population at event pixel: **10.28 persons**
  * Mean population in 1km buffer: **3425.52 persons**
  * Mean population in 5km buffer: **56076.01 persons**
* **Conservation & Ecology (WDPA):**
  * Events directly inside protected areas: **0**
  * Events within 1km of protected areas: **0**
* **Industrial Context (OSM):**
  * Events near power plants (<2km): **101**
  * Events near factories (<2km): **67**
  * Events near refineries (<5km): **9**
  * Events near mines (<5km): **0**
  * Events near quarries (<3km): **120**
* **Infrastructure Proximity (OSM):**
  * Mean distance to major road: **134.29 km**
  * Mean distance to railway: **157.74 km**

---

## 4. Key Architectural Rules Preserved
1. **Raw Data Immutability:** Raw sources in `data/raw/` were treated as read-only.
2. **Independent Datasets:** No monolithic physical merging of raw layers; event features reside in an independent derived analytical table.
3. **Traceability:** Every feature links directly back to its source layer and record.
