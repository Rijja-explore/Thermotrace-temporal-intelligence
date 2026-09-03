# ThermoTrace - Event Engine v0.1 Quality Summary
**Engine Module**: `ThermoTrace.M3.EventEngine` | **Version**: `0.1.0`  
**Executed At**: `2026-09-02T19:00:49.527227+00:00` | **Duration**: `203.41s`

---

## 1. Executive Summary
- **Total Input Detections**: `1,908,697`
- **Total Spatiotemporal Events**: `996,891`
- **Single-Detection Events**: `645,771` (64.78%)
- **Multi-Detection Events**: `351,120` (35.22%)
- **Detections in Multi-Events**: `66.17%`
- **Unassigned Detections**: `0` (100% assigned)

## 2. Event Dimensions & Statistics
- **Detections per Event**: Median: `1.0` | Max: `263`
- **Event Duration**: Median: `0.0h` | Max: `1.75h`
- **Spatial Extent**: Median: `0.0 km` | Max: `14.710000038146973 km`
- **Dual-Sensor (N20 + N21) Events**: `184,429`

## 3. Configuration Parameters
- **Spatial Radius**: `1.0 km`
- **Temporal Window**: `6.0 hours`
- **Max Event Duration**: `48.0 hours`
- **Max Event Diameter**: `15.0 km`

## 4. Parameter Sensitivity Benchmark Table
| Spatial Radius | Temporal Window | Total Events | Median Size | Max Size | % Singletons | Max Duration |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1.0 km | 3.0 h | 56,465 | 1.0 | 134 | 56.74% | 1.72 h |
| 1.0 km | 6.0 h | 56,465 | 1.0 | 134 | 56.74% | 1.72 h |
| 1.0 km | 12.0 h | 50,847 | 1.0 | 222 | 57.21% | 47.4 h |
| 2.0 km | 6.0 h | 48,539 | 1.0 | 142 | 53.81% | 1.72 h |
| 2.0 km | 12.0 h | 42,528 | 1.0 | 240 | 54.76% | 47.4 h |
| 5.0 km | 6.0 h | 35,022 | 2.0 | 155 | 47.25% | 1.72 h |

---
*Note: Event objects represent localized spatiotemporal detection clusters. They are not confirmed industrial incidents or facility assignments.*
