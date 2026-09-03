# ThermoTrace - FIRMS Layer-0 Data Quality Summary
**Pipeline Module**: `ThermoTrace.M1.FIRMS_ETL` | **Version**: `1.1.0` (FIRMS CANONICAL v1.1)  
**Execution Timestamp**: `2026-09-02T18:10:17.150131+00:00`  
**Duration**: `34.94s`

---

## 1. Executive Ingestion Summary
- **Total Raw Files Ingested**: `147`
- **Total Combined Rows**: `1,908,698`
- **Canonical Rows Retained**: `1,908,697`
- **Duplicates Removed**: `1`
- **Invalid Coordinate Rows**: `0`

## 2. Sensor & Temporal Distribution
- **Date Range**: `2025-09-02` to `2026-09-02`
- **NOAA-20 (J1) Detections**: `972,823`
- **NOAA-21 (J2) Detections**: `935,874`
- **Pass Indicator**: Day: `1,396,268` | Night: `512,429`

## 3. Spatial Extent (India Processing Window)
- **Bounding Box**: Longitude `[68.1, 97.4]`, Latitude `[6.5, 35.7]`
- **Observed Extent**: Lon `[68.10002, 97.4]`, Lat `[6.50425, 35.69986]`
- **Inside India BBox**: `1,908,697` (100.0%)
- **Outside India BBox**: `0` (0.0%)

## 4. Confidence Breakdown
- **Nominal (`n`)**: `1,520,487` (79.66%)
- **Low (`l`)**: `333,369` (17.47%)
- **High (`h`)**: `54,841` (2.87%)

## 5. Radiative Power (FRP) Profile (MW)
- **Min**: `0.0` MW
- **Max**: `1333.949951171875` MW
- **Median**: `3.9700000286102295` MW
- **Mean**: `7.014699935913086` MW
- **Standard Deviation**: `16.411800384521484` MW

## 6. Audit & Canonical Integrity
- Canonical records are indexed with unique deterministic SHA-256 `detection_id` keys.
- Multi-sensor observations (N20 vs N21) are strictly isolated and preserved.
- Raw CSV files remain 100% immutable and untouched.
