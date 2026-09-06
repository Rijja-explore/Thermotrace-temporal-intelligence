# Imagery and Evidence Capability Audit

## 1. Existing Imagery/Data Sources
An exhaustive scan of the repository (`data/` directories, environment variables, python dependencies, and source code) was performed for satellite imagery capabilities (Sentinel, Landsat, MODIS, STAC, Earth Engine, Planet, etc.).

## 2. Actual vs Theoretical Access
- **Satellite Optical/SAR Imagery (Sentinel, Landsat, Planet, Earth Engine)**: **No capability (Category D)**. The repository contains absolutely no API clients, credentials, dependencies (e.g., `earthengine-api`, `pystac`, `sentinelhub`), or scripts capable of retrieving historical satellite imagery.
- **Population & Landcover Data**: **Actually downloaded local data (Category A)**. The project relies on static `rasterio` usage to read locally downloaded population and ESA WorldCover GeoTIFFs. These are static contextual maps, not dynamic historical imagery.
- **FIRMS Thermal Data**: **Actually downloaded local data (Category A)**. Pre-processed Parquet files contain the thermal anomaly records.

## 3. Temporal Coverage (Imagery)
- **NOT AVAILABLE**. Since there are no dynamic imagery retrieval capabilities, we cannot query historical imagery for the 40-event pilot dates.

## 4. Spatial Coverage & Resolution (Imagery)
- **NOT AVAILABLE**.

## 5. Available Spectral/Thermal Information (Imagery)
- **NOT AVAILABLE**.

## 6. Whether Historical Imagery Can Be Retrieved for the Pilot Dates
- **NOT AVAILABLE**. No capability exists to query or retrieve imagery around an individual FIRMS event.

## 7. Existing FIRMS Temporal Capabilities
The existing ThermoTrace FIRMS dataset does provide robust temporal information:
- **Source satellites**: VIIRS (NOAA-20, NOAA-21, Suomi NPP) and MODIS.
- **Acquisition timestamps**: Exact `start_time` and `end_time`.
- **Observations**: Total `detection_count`, `duration_hours`, and multi-satellite confirmation flags.
- **Spatial clustering & Recurrence**: Explicit measurement of historical detections at the same coordinates (`events_previous_30d`, etc.).
*(Note: This provides excellent evidence-triangulation context, but it remains ThermoTrace internal data and is NOT independent ground truth.)*

## 8. Existing External Evidence/API Capabilities
- **NOT AVAILABLE**. The repository has no configured APIs (e.g., News APIs, Web Search integration scripts) for automated independent verification. The only external data sources are static pre-downloaded OSM, Population, and Landcover datasets.

## 9. What is Genuinely Possible for Each Taxonomy Class
With the current repository capabilities (strictly static OSM/Landcover context + FIRMS thermal history):
- **wildfire/forest fire**: NOT POSSIBLE to independently verify. We only know if it occurred in a static forest pixel.
- **agricultural burning**: NOT POSSIBLE to independently verify. We only know if it occurred in a static cropland pixel.
- **mining/quarry activity**: NOT POSSIBLE to independently verify. We only know if it occurred near a static OSM quarry polygon.
- **persistent industrial thermal source**: NOT POSSIBLE to independently verify. We only know if there is high FIRMS temporal recurrence near an OSM facility.
- **industrial fire/abnormal event**: NOT POSSIBLE to independently verify. We only know if an acute (low recurrence) thermal event occurred near an OSM facility.

## 10. What is NOT Possible
It is impossible to achieve independent semantic ground-truth verification for any event. We cannot distinguish an agricultural fire next to a factory from a factory fire, nor can we distinguish an active mining burn from a wildfire encroaching on a quarry.

## 11. Specific Blockers
The absolute blocker is the absence of an independent, dynamic visual or spectral verification layer (e.g., STAC API integration for Sentinel-2/Landsat-8) that can retrieve cloud-free imagery before and after an event to inspect burn scars, active flares, or agricultural clearing.

## 12. Audit of the Previous 12-Event Artifacts
The previous batch investigation produced non-Unknown classes (`persistent_industrial_source` and `mining_or_other_industrial_activity`). A review confirms these proposals were generated using:
- `events_previous_30d`
- `near_power_plant`, `near_factory`, `near_refinery`, `near_substation`
- `near_mine`, `near_quarry`

**Explicit Statement**: These are strictly ThermoTrace contextual features and are NOT independent semantic evidence. They were improperly used as deterministic thresholds to simulate a ground-truth investigation.

## 13. Recommended Next Implementation Step
Implement a dynamic STAC (SpatioTemporal Asset Catalog) client or Earth Engine integration capable of querying historical Sentinel-2 or Landsat imagery bounding boxes centered on an `event_id`'s coordinates and date, allowing for independent visual evidence verification.

---

**IMPLEMENT_MISSING_EVIDENCE_LAYER**
