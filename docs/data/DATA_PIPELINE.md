# ThermoTrace Data Pipeline Architecture

## Data Sources & ETL

1. **NASA FIRMS Active Fire / Thermal Anomaly Data:**
   - **Satellites:** VIIRS (Suomi-NPP 375m, NOAA-20 375m, NOAA-21 375m) and MODIS (Terra/Aqua 1km).
   - **Ingestion:** Hourly/daily ingestion script (`canonical_etl.py`).
   - **Cleaning:** Validates latitude [-90, 90], longitude [-180, 180], confidence scores (>0), FRP intensity (>0 MW), and filters duplicate acquisition timestamps within 50 meters.

2. **OpenStreetMap (OSM) Industrial Infrastructure:**
   - **Extracts:** Refineries, petrochemical complexes, steel plants, coal mines, power stations, chemical plants, quarries.
   - **Proximity Calculation:** Computes Haversine distance from thermal centroid to nearest industrial asset.

3. **ESA WorldCover Land Cover (10m Resolution):**
   - **Fractions:** Calculates urban/built-up, forest, cropland, and water body percentage coverage within 100m, 500m, and 1000m buffer zones around thermal centroids.

4. **Spatiotemporal Event Clustering (DBSCAN):**
   - **Spatial Epsilon:** 2.0 km (Haversine metric).
   - **Temporal Window:** 24 hours.
   - **Output:** Unique deterministic `event_id` grouping observation sequences over time.
