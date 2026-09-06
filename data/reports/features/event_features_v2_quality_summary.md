# ThermoTrace Feature Engineering V2 Executive Summary

**Execution Timestamp:** 2026-09-03T10:36:57.741350+00:00  
**Pipeline Version:** 2.0.0  
**Status:** **PASS**  
**Canonical Output Dataset:** `D:\New folder (2)\data\processed\features\event_features_v2.parquet` (210.97 MB, 144 features, 996,891 events)

---

## 1. Cardinality & Data Preservation
* **Input V1 Events:** **996,891**
* **Output V2 Events:** **996,891**
* **Unique Event IDs:** **996,891**
* **Duplicate Event IDs:** **0**
* **Preservation Rate:** **100.0%** (Zero events lost, 1-to-1 cardinality strictly preserved)
* **Features:** 65 V1 features preserved + **79 V2 features added** = **144 Total Features**.

---

## 2. ThermoTrace Explainable Baseline Risk Engine

> [!NOTE]
> This baseline risk engine provides an objective, transparent, and rule-based benchmark combining physical thermal intensity, demographic exposure, environmental fuel load, conservation proximity, industrial facilities, and recurrence. It is an engineering baseline and not a scientifically validated probability of wildfire.

### A. Risk Distribution Across India (996,891 Events)
* **Mean Baseline Risk Score:** **25.39 / 100** (Median: 24.04, Max: 75.03)
* **Risk Categorization Breakdown:**
  * **LOW:** 698,500 events (70.1%)
  * **MODERATE:** 297,205 events (29.8%)
  * **HIGH:** 1,186 events (0.1%)

### B. Risk Component Averages (0 – 100 Scale)
* **Thermal Risk Component:** **25.18** (FRP magnitude and cluster persistence)
* **Exposure Risk Component:** **33.93** (Population density within 1km/5km)
* **Environmental Risk Component:** **30.03** (Vegetative fuel load from ESA WorldCover)
* **Conservation Risk Component:** **0.2** (Proximity to official WDPA protected areas)
* **Industrial Context Component:** **17.93** (OSM facility proximity)
* **Infrastructure Context Component:** **32.14** (Roads, rail, power lines, pipelines)
* **Recurrence Component:** **43.73** (Leak-free 30-day historical thermal activity)

### C. Top Primary Risk Drivers
* **REPEATED_ACTIVITY:** 380,623 events
* **HIGH_POPULATION_EXPOSURE:** 234,366 events
* **FOREST_DOMINANT_LANDCOVER:** 187,012 events
* **BASELINE_MONITORING:** 114,804 events
* **HIGH_THERMAL_INTENSITY:** 36,022 events

---

## 3. Data Lineage & Provenance
* **Base Input Table:** `data/processed/features/event_features_v1.parquet` (65 canonical columns)
* **FIRMS Detections & M3 Clusters:** `data/processed/events/events_v0_1.parquet`
* **Population Demographics:** WorldPop 2025 India 100m (`data/processed/population/population_india_100m.tif`)
* **Conservation Network:** UNEP-WCMC WDPA Sep 2026 (`data/processed/protected_areas/protected_areas_india.gpkg`)
* **Industrial & Infrastructure Networks:** OpenStreetMap India (`data/processed/osm/osm_india.gpkg`)
* **Land Cover Classification:** ESA WorldCover 10m 2021 v200 (`data/raw/worldcover/india/`)
