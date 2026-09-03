# ThermoTrace - Layer-0 NASA FIRMS Canonical ETL Pipeline (Person 1 / M1)

This module implements the **Layer-0 NASA FIRMS Ingestion, Cleaning, Normalization, Validation, and Canonical Export Pipeline** for the SIH project **ThermoTrace**.

It transforms raw VIIRS active fire observations (NOAA-20 / JPSS-1 and NOAA-21 / JPSS-2) over India into an auditable, explainable, canonical detection dataset ready for downstream ThermoTrace modules (M2–M5).

---

## 1. What the Pipeline Does

- **Discovers and inspects** raw FIRMS CSV chunk files without modifying them.
- **Normalizes disparate schemas**: Seamlessly handles differences between Standard Processing (SP) with the `type` column and Near Real-Time (NRT) products without `type`.
- **Standardizes temporal data**: Parses `acq_date` and zero-padded `acq_time` into standard ISO-8601 UTC `acq_datetime` (`YYYY-MM-DDTHH:MM:00`) without fabricating timezone offsets.
- **Validates spatial & numeric attributes**: Enforces physical WGS84 bounds, sets an operational `within_india_bbox` boolean flag (`[68.1, 6.5, 97.4, 35.7]`), and validates Fire Radiative Power (`frp >= 0`).
- **Preserves categorical confidence**: Retains raw categorical confidence (`l`, `n`, `h`) while providing a documented ordinal index `confidence_numeric` for downstream filtering.
- **Conservative deduplication**: Eliminates true duplicate records within the same sensor while strictly isolating and preserving multi-sensor observations (N20 and N21 are never treated as duplicates).
- **Generates deterministic detection IDs**: Computes reproducible SHA-256 detection IDs (`DET_{sat}_{date}_{hash[:12]}`) that remain 100% reproducible across reruns.
- **Produces audit-grade reports**: Writes machine-readable JSON reports and human-readable Markdown summaries.
- **Exports canonical datasets**: Writes compressed Parquet and CSV outputs.

---

## 2. Input Data & Raw Schemas

Raw CSV files reside under `data/raw/firms/` (with support for both `noaa20`/`noaa21` and `j1`/`j2` subdirectories).

Raw files exhibit two schema variants:
1. **Standard Processing (SP)**: 19 columns including `type` (0.0=vegetation, 1.0=volcano, 2.0=static land, 3.0=offshore), `version` as `2`.
2. **Near Real-Time (NRT)**: 18 columns, lacks `type` (stored as null), `version` as `2.0NRT`.

### Raw Data Immutability
All raw CSV chunk files under `data/raw/firms/` are strictly read-only. The pipeline never modifies, overwrites, or deletes raw input files.

---

## 3. Canonical Schema & Data Dictionary

| Canonical Field | Type | Raw Source Field | Description / Rules |
| :--- | :--- | :--- | :--- |
| `detection_id` | `string` | *(Computed)* | Deterministic SHA-256 hash: `DET_{sat}_{date}_{hash[:12]}`. Stable across runs. |
| `latitude` | `float64` | `latitude` | Validated WGS84 latitude (`-90.0 <= lat <= 90.0`). |
| `longitude` | `float64` | `longitude` | Validated WGS84 longitude (`-180.0 <= lon <= 180.0`). |
| `acq_datetime` | `string` | `acq_date` + `acq_time` | ISO-8601 UTC timestamp: `YYYY-MM-DDTHH:MM:00`. |
| `acq_date` | `string` | `acq_date` | Original acquisition date (`YYYY-MM-DD`). |
| `acq_time` | `string` | `acq_time` | 4-character zero-padded string `HHMM` (e.g., `0531`). |
| `satellite` | `string` | `satellite` | Sensor satellite platform: `N20` (NOAA-20 / J1) or `N21` (NOAA-21 / J2). |
| `instrument` | `string` | `instrument` | Sensor instrument: `VIIRS`. |
| `daynight` | `string` | `daynight` | Solar pass indicator: `D` (Day) or `N` (Night). |
| `confidence` | `string` | `confidence` | Original FIRMS categorical confidence: `l` (low), `n` (nominal), `h` (high). |
| `confidence_numeric` | `float32` | *(Computed)* | Ordinal index (`l`=0.3, `n`=0.6, `h`=0.9). *Not a calibrated ML probability.* |
| `bright_ti4` | `float32` | `bright_ti4` | VIIRS I-4 channel brightness temperature (Kelvin). |
| `bright_ti5` | `float32` | `bright_ti5` | VIIRS I-5 channel brightness temperature (Kelvin). |
| `frp` | `float32` | `frp` | Fire Radiative Power (MW). Validated non-negative. |
| `scan_km` | `float32` | `scan` | Across-track pixel footprint dimension in km. |
| `track_km` | `float32` | `track` | Along-track pixel footprint dimension in km. |
| `hotspot_type` | `Int8` (null) | `type` | Classification code from SP: 0=veg, 1=volcano, 2=static land, 3=offshore. Null in NRT. |
| `firms_version` | `string` | `version` | FIRMS collection version string (e.g. `'2'`, `'2.0NRT'`). |
| `source` | `string` | `source_product` | Source product identifier (e.g., `'VIIRS_NOAA20_SP'`, `'VIIRS_NOAA21_NRT'`). |
| `within_india_bbox` | `boolean` | *(Computed)* | `True` if within `[68.1 <= lon <= 97.4, 6.5 <= lat <= 35.7]`, else `False`. |
| `quality_flag` | `string` | *(Computed)* | Audit flag: `'VALID'`, `'SUSPICIOUS_FRP_ZERO'`, `'INVALID_COORDS'`, etc. |
| `downloaded_at_utc` | `string` | `downloaded_at_utc` | Timestamp of ingestion for provenance and auditing. |

---

## 4. Processing & Validation Rules

### Coordinate Validation
- Physical validity: `-90.0 <= latitude <= 90.0` and `-180.0 <= longitude <= 180.0`.
- Violations are flagged with `quality_flag = 'INVALID_COORDS'` (never silently discarded).
- Operational India Bounding Box: `within_india_bbox` is flagged `True`/`False`. Records outside the bbox are preserved.

### Numeric Validation
- `frp`: Must be non-negative. Records with `frp == 0.0` are flagged `SUSPICIOUS_FRP_ZERO`; records with `frp < 0` are flagged `INVALID_FRP_NEGATIVE`.
- Missing numbers are never arbitrarily imputed.

### Confidence Normalization
- The original FIRMS categorical confidence string (`'l'`, `'n'`, `'h'`) is strictly preserved.
- `confidence_numeric` maps `'l' -> 0.3`, `'n' -> 0.6`, `'h' -> 0.9`. 
- **Scientific Notice**: This is an ordinal sorting index for downstream filtering, NOT a Bayesian or calibrated ML probability of an industrial fire. Low-confidence detections are NOT deleted.

### Conservative Deduplication
- Records are identified as duplicate only if they share identical:
  `(satellite, acq_datetime, latitude, longitude, scan_km, track_km)`.
- Detections from different satellites (e.g., N20 and N21 observing the same location at close times) are **strictly preserved** for multi-sensor agreement analysis.
- First occurrence is retained deterministically.

### Deterministic Detection ID
- `detection_id` is derived via SHA-256:
  `DET_{satellite}_{acq_date_nodash}_{SHA256(satellite|instrument|datetime|lat|lon|bt4|frp)[:12]}`
- 100% reproducible and unique.
- **Important**: `detection_id` is NOT an `event_id` or cluster ID. Event clustering belongs to M3.

---

## 5. Directory Structure & Outputs

```
firms_data/
├── raw/
│   ├── j1/ (or noaa20/)      <- Raw immutable CSV chunks
│   ├── j2/ (or noaa21/)      <- Raw immutable CSV chunks
│   └── download_manifest.csv <- Download manifest
├── processed/
│   ├── firms_india_canonical.csv     (360 MB)
│   └── firms_india_canonical.parquet (67 MB)
├── reports/
│   ├── firms_quality_report.json    (Comprehensive metrics)
│   ├── firms_quality_summary.md     (Human-readable summary)
│   └── firms_schema_report.json     (Raw schema audit)
└── data_pipeline/
    └── firms/
        ├── canonical_etl.py     <- Main production ETL script
        ├── ingest_firms_year.py <- NASA FIRMS chunk downloader
        └── README.md            <- Documentation
```

---

## 6. How to Run the Pipeline

### Run Full Pipeline
From the project root:
```bash
python data_pipeline/firms/canonical_etl.py
```

### Custom Path Arguments (Optional)
```bash
python data_pipeline/firms/canonical_etl.py \
  --raw-dir data/raw/firms \
  --output-dir data/processed/firms \
  --reports-dir data/reports/firms
```

### Run Unit & Integration Tests
```bash
python -m pytest tests/test_firms_etl.py -v
```

---

## 7. Limitations & Scientific Boundaries (Person 1 Scope)

> [!CAUTION]
> **FIRMS Detections are Thermal Anomalies, NOT Facility Confirmations:**
> FIRMS detections represent satellite-measured radiometric temperature anomalies (sub-pixel active combustion or elevated heat emitters). They are **not** proof of an industrial fire, nor do they identify a specific building or plant.

Downstream ThermoTrace modules will contextualize detections:
- **M2**: Multi-sensor spatial joins (Copernicus WorldCover land cover, WDPA protected areas, OSM industrial facility masks, WorldPop population density).
- **M3**: Spatiotemporal clustering and event aggregation into `event_id`s.
- **M4**: Industrial baseline persistence scoring and false-positive suppression (flaring, slag pits, brick kilns, agricultural stubble).
- **M5**: Sentinel-2 / Landsat high-resolution optical/SWIR confirmation, plume detection, and API delivery.

**Explicitly Out of Scope for M1:**
- DO NOT perform spatial/temporal clustering.
- DO NOT classify events as industrial vs wildfire vs agricultural.
- DO NOT assign facility or building names.
- DO NOT calculate historical baselines or anomaly scores.
- DO NOT delete low-confidence detections.
