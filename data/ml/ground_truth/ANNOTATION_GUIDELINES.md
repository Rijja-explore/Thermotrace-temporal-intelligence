# ThermoTrace Ground Truth Annotation Guidelines

## Overview
This document provides standard operating procedures and evidence criteria for human domain experts annotating thermal anomaly events across the 6-class taxonomy for SIH26162 (NTRO).

---

## The 6-Class Taxonomy

1. **`persistent_industrial_source`**:
   - **Positive Evidence**: Proximity ($\le 2.0$ km) to registered industrial plant/refinery AND high temporal recurrence ($>10$ active detection days in 30 days).
   - **Negative Evidence**: Single isolated thermal detection with zero prior historical recurrence.
   - **Rule**: Facility proximity *alone* is NOT proof of an industrial source.

2. **`industrial_fire_or_abnormal_event`**:
   - **Positive Evidence**: Extreme FRP intensity spike ($>150$ MW) near industrial facility/refinery, accompanied by news/incident report corroboration.
   - **Negative Evidence**: Low-FRP transient agricultural stubble burn.

3. **`mining_or_other_industrial_activity`**:
   - **Positive Evidence**: Location within active OSM mine/quarry boundary + spatial stability over time.
   - **Negative Evidence**: Deep forest vegetation cover with zero proximity to mining concessions.

4. **`wildfire_or_forest_fire`**:
   - **Positive Evidence**: Mapped forest cover fraction ($>0.4$), large spatial footprint ($>2$ km²), away from industrial facilities.
   - **Negative Evidence**: Urban/industrial built-up land cover.

5. **`agricultural_burning`**:
   - **Positive Evidence**: Cropland cover fraction ($>0.4$), seasonal timing (post-harvest), short duration ($<6$ hours).
   - **Negative Evidence**: Continuous multi-month flare activity.

6. **`unknown_requires_verification`**:
   - **Usage**: Mandatory when evidence is conflicting, cloud-covered, or insufficient to prove a specific semantic class. Never force uncertain events.
