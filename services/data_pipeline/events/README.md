# ThermoTrace - Spatiotemporal Event Engine (Module M3)

The **Event Engine** converts Layer-0 NASA FIRMS VIIRS detections into coherent, traceable, spatiotemporal thermal event objects (`event_id`).

---

## 1. Scientific Definition & Operational Boundary

> [!IMPORTANT]
> **Scientific Limitation:**
> An event object in ThermoTrace represents strictly:
> **"FIRMS detections grouped by spatiotemporal proximity."**
> 
> It does **NOT** mean:
> - A confirmed fire
> - An industrial incident
> - A facility event
> - An accident or explosion
> 
> Semantic, industrial, or incident interpretations require downstream evidence from M2 (Classification/Filtering) and M4/M5 (OSM/WorldCover/Temporal Baseline intelligence).

---

## 2. Pipeline Inputs & Outputs

### Input
- Canonical FIRMS Parquet: `processed/firms_india_canonical.parquet` (1,908,697 detections, 2025-09-02 to 2026-09-02).
- Read-only ingestion: Canonical FIRMS data is never modified.

### Outputs
- **Canonical Events Parquet**: `processed/events/events_v0_1.parquet`
- **Canonical Events CSV**: `processed/events/events_v0_1.csv`
- **Event-Detection Link Table**: `processed/events/event_detection_links.parquet`
- **Quality Reports**:
  - `reports/events/eventization_quality_report.json`
  - `reports/events/eventization_quality_summary.md`

---

## 3. Core Algorithm & Chaining Prevention

### Two-Tier Spatiotemporal Linkage
Detections $A$ and $B$ are merged into the same event if and only if:
1. **Spatial Proximity**: $\text{dist\_km}(A, B) \le \text{SPATIAL\_RADIUS\_KM}$ (Default: `1.0 km`)
2. **Temporal Proximity**: $|t_A - t_B| \le \text{TEMPORAL\_WINDOW\_HOURS}$ (Default: `6.0 hours`)

### Scalable Sliding-Window Indexing ($O(N \log N)$)
Rather than constructing an intractable $O(N^2)$ pairwise distance matrix over 1.9M detections:
- Detections are sorted chronologically.
- A 48-hour sliding window with a step of $(48 - \text{window\_hours})$ slices the timeline.
- Within each slice, a 2D Euclidean KDTree over local metric coordinates (km) performs fast neighbor searches.
- Temporal differences are evaluated, and valid pairs are passed to a **Bounded Union-Find** structure.

### Chaining Prevention Engine
To prevent spatial stepping-stone chaining (e.g. A connects to B, B connects to C, spanning 50 km) or runaway multi-week temporal percolation:
- **Bounded Disjoint Set Union**:
  Before merging sets $S_1$ and $S_2$:
  - Checks if combined duration exceeds `MAX_EVENT_DURATION_HOURS` (`48.0 hours`).
  - Checks if combined spatial bounding diameter exceeds `MAX_EVENT_DIAMETER_KM` (`15.0 km`).
  - If exceeded, the merge is **rejected** and logged as a prevented chaining occurrence.
- Resulting events are tagged with quality flags:
  - `NORMAL`: Standard spatiotemporal cluster
  - `SINGLE_DETECTION`: Isolated point detection
  - `LARGE_SPATIAL_SPREAD`: Cluster diameter $> 10\text{ km}$
  - `LONG_TEMPORAL_SPREAD`: Cluster duration $> 24\text{ hours}$

---

## 4. Parameter Sensitivity Benchmark

Empirical evaluation on a representative peak-season sample of 132,420 detections (April 2026):

| Spatial Radius | Temporal Window | Total Events | Median Size | Max Size | % Singletons | Max Duration | Observations |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1.0 km** | **3.0 h** | 56,469 | 1.0 | 134 | 56.73% | 1.72 h | Multi-sensor agreement within same pass. |
| **1.0 km** | **6.0 h** | 56,469 | 1.0 | 134 | 56.73% | 1.72 h | **Initial Recommended Baseline**: Identical to 3h because VIIRS passes are ~50 min apart. |
| **1.0 km** | **12.0 h** | 50,650 | 1.0 | 620 | 57.41% | 133.47 h | Connects morning and night passes, causing multi-day temporal chaining. |
| **2.0 km** | **6.0 h** | 48,520 | 1.0 | 215 | 53.84% | 1.72 h | Moderate spatial expansion within single pass. |
| **2.0 km** | **12.0 h** | 42,123 | 1.0 | 2,427 | 55.29% | 134.23 h | Significant cross-day and spatial chaining. |
| **5.0 km** | **6.0 h** | 33,533 | 2.0 | 994 | 48.87% | 1.72 h | Excessive spatial merging across independent nearby fires/facilities. |

---

## 5. Event Data Model & Schemas

### `events_v0_1.parquet`
```
event_id                      : String (e.g. TT-EVT-00000001, deterministic)
start_time                    : ISO-8601 UTC string (e.g. 2025-09-02T06:48:00)
end_time                      : ISO-8601 UTC string (e.g. 2025-09-02T06:50:00)
duration_hours                : Float32 (elapsed hours between start and end)
centroid_lat                  : Float64 (mean detection latitude)
centroid_lon                  : Float64 (mean detection longitude)
spatial_extent_km             : Float32 (bounding diameter, 0.0 for singletons)
detection_count               : Int32 (total detections in event)
unique_satellite_count        : Int8 (1 or 2)
satellites                    : String ('N20', 'N21', or 'N20,N21')
max_frp_mw                    : Float32 (peak Fire Radiative Power)
mean_frp_mw                   : Float32 (average Fire Radiative Power)
median_frp_mw                 : Float32 (median Fire Radiative Power)
sum_frp_mw                    : Float32 (cumulative Fire Radiative Power)
max_bright_ti4                : Float32 (peak I-4 brightness temp in Kelvin)
mean_bright_ti4               : Float32 (mean I-4 brightness temp in Kelvin)
max_bright_ti5                : Float32 (peak I-5 brightness temp in Kelvin)
mean_bright_ti5               : Float32 (mean I-5 brightness temp in Kelvin)
day_detection_count           : Int32 (count of day-pass detections)
night_detection_count         : Int32 (count of night-pass detections)
confidence_high_count         : Int32 (count of high-confidence detections)
confidence_nominal_count      : Int32 (count of nominal-confidence detections)
confidence_low_count          : Int32 (count of low-confidence detections)
source_product_count          : Int8 (distinct source products)
event_quality                 : String (NORMAL, SINGLE_DETECTION, LARGE_SPATIAL_SPREAD, LONG_TEMPORAL_SPREAD)
```

### `event_detection_links.parquet`
```
event_id                      : String (Foreign key to events_v0_1)
detection_id                  : String (Foreign key to firms_india_canonical)
```

---

## 6. Execution Instructions

Run full pipeline with default parameters and sensitivity benchmarking:
```powershell
python data_pipeline/events/build_events.py
```

Run with custom parameters:
```powershell
python data_pipeline/events/build_events.py --spatial-radius-km 1.5 --temporal-window-hours 4.0 --skip-sensitivity
```
