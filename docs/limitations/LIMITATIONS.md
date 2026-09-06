# ThermoTrace System Limitations & Scientific Scope

1. **Pixel Spatial Resolution (375m / 1km):**
   NASA VIIRS 375m and MODIS 1km observations represent thermal anomaly footprints across hundreds of square meters. ThermoTrace provides facility and area-level attribution, not pipe or valve-level sub-meter pinpointing.

2. **Cloud & Smoke Contamination:**
   Heavy cloud cover, monsoonal precipitation, or thick smoke plumes attenuate thermal radiance, resulting in missing observations or lower satellite detection confidence.

3. **Ground Truth Labels:**
   Ground truth labels for industrial thermal events remain derived or analyst-verified. Where ground truth is unavailable or ambiguous, ThermoTrace assigns `unknown_requires_verification` rather than forcing an artificial prediction.

4. **Satellite Overpass Timing:**
   Sun-synchronous satellite orbits (e.g. VIIRS ~1:30 AM/PM local time) produce discrete revisit snapshots rather than continuous 24/7 video monitoring.

5. **Configurable Scoring Weights:**
   Weights in `config/weights.yaml` and thresholds in `config/thresholds.yaml` represent operational starting points and must be empirically calibrated for specific industrial deployment regions.
