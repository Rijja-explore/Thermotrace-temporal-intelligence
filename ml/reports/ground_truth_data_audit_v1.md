# Ground-Truth Data Audit Report — Person 2 AI/ML

## 1. Executive Summary & Inventory
- **Total Discovered Thermal Events**: 996,891 events in `data/processed/features/event_features_v2.parquet`.
- **Total Usable Feature Columns**: 144 columns (47 safe `APPROVED_FEATURES` for ML training, 42 excluded leakage/synthetic risk fields).
- **Current Verified Ground-Truth Labels**: **0 verified production labels**. (Existing 100-event dataset is strictly identified as `mock_ground_truth`).
- **Primary Objective**: Build a candidate acquisition and human-verification framework to acquire human-verified ground-truth labels across the 6-class taxonomy.

---

## 2. Missingness Analysis across Key Fields (996,891 Events)
| Feature Field Group | Column Name | Missingness (%) | Data Quality Assessment |
| :--- | :--- | :---: | :--- |
| **Identifiers** | `event_id` | `0.0%` | Complete unique string keys (`TT-EVT-XXXXX`) |
| **Spatial Coordinates** | `centroid_lat`, `centroid_lon` | `0.0%` | Complete subcontinent coverage [5°N-38°N, 65°E-100°E] |
| **Timestamps** | `start_time` | `0.0%` | ISO 8601 strings spanning 2024-2026 |
| **Thermal FRP** | `max_frp_mw`, `mean_frp_mw` | `0.0%` | Complete numeric detection statistics (MW) |
| **Temporal Recurrence** | `events_previous_30d`, `active_days_previous_30d` | `0.0%` | Complete leak-free historical lookbacks |
| **Land Cover Fractions** | `forest_fraction_1km`, `cropland_fraction_1km`, `builtup_fraction_1km` | `0.0%` | Complete 10m ESA WorldCover aggregations |
| **Infrastructure Context**| `distance_to_facility_km`, `near_refinery`, `near_mine` | `0.0%` | Complete OSM spherical spatial index queries |

---

## 3. Available Feature Groups & Candidate Signals

1. **Thermal Intensity & Spread**:
   - `max_frp_mw`, `sum_frp_mw`, `spatial_extent_km`, `duration_hours`, `detection_count`.
2. **Temporal Recurrence & Persistence**:
   - `events_previous_7d`, `events_previous_30d`, `events_previous_90d`, `active_days_previous_30d`.
3. **Land Cover Context**:
   - `forest_fraction_1km`, `cropland_fraction_1km`, `builtup_fraction_1km`, `grassland_fraction_1km`, `natural_land_fraction`.
4. **Industrial Infrastructure Proximity**:
   - `distance_to_facility_km`, `near_power_plant`, `near_factory`, `near_refinery`, `near_mine`, `near_quarry`.

---

## 4. Ground-Truth Acquisition & Human Verification Protocol

* **Fields Requiring External Verification**:
  - Optical satellite imagery (Sentinel-2 L2A / Landsat) pre-and-post event.
  - Independent incident reporting logs (FSI wildfire notices, CPCB industrial permits).
* **Review Priority Strata**:
  - `likely_persistent_industrial`
  - `likely_industrial_abnormal`
  - `likely_wildfire`
  - `likely_agricultural_burning`
  - `likely_mining_activity`
  - `ambiguous_insufficient_evidence`
