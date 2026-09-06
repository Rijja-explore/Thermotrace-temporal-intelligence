# ThermoTrace Full-Scale Event Feature Engineering Quality Summary

**Execution Timestamp:** 2026-09-03T10:14:43.086750+00:00  
**Status:** **PASS**  
**Canonical Output Dataset:** `d:\New folder (2)\data\processed\features\event_features_v1.parquet` (93.98 MB, 65 features, 996,891 events)

---

## 1. Event Cardinality & Integrity
* **Input M3 Events:** **996,891**
* **Output Feature Events:** **996,891**
* **Unique Event IDs:** **996,891**
* **Duplicate Event IDs:** **0**
* **Event Preservation Rate:** **100.0%** (**Zero events lost**, 1-to-1 cardinality strictly maintained)

---

## 2. Statistical Distributions & Environmental Context

### A. Thermal Radiative Metrics (M3)
* **Mean Fire Radiative Power (MW):** 5.24 MW (median: 3.75 MW)
* **Maximum Observed FRP:** 1333.95 MW
* **Mean Event Lifespan:** 0.17 hours (max: 1.75 hours)
* **Mean Detections / Cluster:** 1.91 detections

### B. Population Demographics (WorldPop 100m)
* **Mean Population at Event Cell:** **3.18 persons**
* **Mean Population in 1km Buffer:** **1385.62 persons**
* **Mean Population in 5km Buffer:** **30609.7 persons**
* **Mean Population Density (1km):** **441.06 persons / km²**

### C. Conservation & Protected Areas (WDPA)
* **Events Inside Protected Area Polygons:** **1,465**
* **Events Within 1km of Protected Area:** **1,477**
* **Events Within 5km of Protected Area:** **2,083**

### D. Industrial Facility Proximity (OSM)
* **Events Near Power Plants (<2km):** **35,406**
* **Events Near Factories (<2km):** **21,863**
* **Events Near Refineries (<5km):** **2,074**
* **Events Near Mines (<5km):** **479**
* **Events Near Quarries (<3km):** **52,031**
* **Events Near Subtransmission Substations (<2km):** **69,809**

### E. Infrastructure Network Proximity (OSM)
* **Mean Distance to Major Road:** **74.62 km**
* **Mean Distance to Railway:** **119.81 km**
* **Mean Distance to High-Voltage Line:** **98.23 km**
* **Mean Distance to Airport:** **96.39 km**

### F. Land Cover Composition (ESA WorldCover 10m)
* **Cropland:** 450,173 events
* **Tree cover:** 323,521 events
* **Grassland:** 113,651 events
* **Built-up:** 32,138 events
* **Shrubland:** 30,520 events
* **Bare / sparse vegetation:** 29,964 events
* **NoData:** 11,041 events
* **Permanent water bodies:** 4,870 events
* **Mangroves:** 539 events
* **Herbaceous wetland:** 314 events
* **Moss and lichen:** 157 events
* **Snow and ice:** 3 events

---

## 3. Data Lineage & Provenance
* **M3 Thermal Events:** `data/processed/events/events_v0_1.parquet`
* **Population Model:** WorldPop 2025 India 100m (`data/processed/population/population_india_100m.tif`)
* **Conservation Areas:** UNEP-WCMC WDPA Sep 2026 (`data/processed/protected_areas/protected_areas_india.gpkg`)
* **Industrial & Infrastructure Networks:** OpenStreetMap India (`data/processed/osm/osm_india.gpkg`)
* **Land Cover Surface:** ESA WorldCover 10m 2021 v200 (`data/raw/worldcover/india/`)
