# Evidence Access Alternatives Audit

## 1. Local Data Inspection
An exhaustive scan of the repository was performed to locate any locally cached satellite imagery or metadata. 
- **Sentinel-2/Landsat/MODIS/VIIRS Imagery**: 0 files found.
- **GeoTIFF/JP2/NetCDF Products**: 0 files found (excluding the static landcover/population data).
- **STAC caches / precomputed indices**: None exist in the workspace.

## 2. Alternative Public Metadata Endpoints Tested
A test was executed against the **Microsoft Planetary Computer STAC API** (`https://planetarycomputer.microsoft.com/api/stac/v1/search`) querying the `landsat-c2-l2` collection for event `TT-EVT-00141704` across the temporal window `2025-11-24` to `2025-12-22`.
- **Result**: `FAILED`
- **Exact Exception**: `requests.exceptions.ConnectionError: ('Connection aborted.', ConnectionResetError(10054, 'An existing connection was forcibly closed by the remote host', None, 10054, None))`
- **Conclusion**: The environment blocks HTTPS requests to all tested public APIs (Earth Search, Planetary Computer), not just a single provider.

## 3. Metadata Access vs Image Asset Access
- **METADATA_ACCESS**: `FAILED` (Network blocked)
- **IMAGE_ASSET_ACCESS**: `FAILED` (Cannot even retrieve metadata to find URLs)
- **LOCAL_IMAGE_PROCESSING**: `FAILED` (No local imagery exists)

## 4. Existing Local/Network Configuration
A check of the environment variables and configuration revealed:
- No proxy configurations (e.g., `HTTP_PROXY`, `HTTPS_PROXY`) are set.
- No cloud credentials (AWS, GCP, Azure) are configured.
- No authentication tokens for STAC catalogues exist.
The environment is operating in a closed sandbox without egress proxy configuration or credential injection.

## 5. External-Evidence Fallback
An alternative to satellite imagery is authoritative public reporting (e.g., government disaster reports, official facility incident logs, reliable news). 
**Requirements for fallback evidence**:
- **Source Type**: Must be a verified independent authority (government, fire department, company press release, reputable news organization).
- **Provenance Fields Required**: 
  - `evidence_source_url` (must be accessible and durable)
  - `evidence_publish_date`
  - `evidence_publisher` (e.g., "Reuters", "Bihar State Disaster Management Authority")
  - `evidence_summary_quote`
**Limitation**: As proven in previous batches, this fallback is effectively useless for minor agricultural burns, small routine flares, or remote forest fires, as these rarely generate indexed news or public incident reports.

## 6. Decision Matrix

| Evidence route | Metadata accessible? | Asset/data accessible? | Reproducible here? | Independent of FIRMS? | Suitable for semantic verification? |
| -------------- | -------------------- | ---------------------- | ------------------ | --------------------- | ----------------------------------- |
| **Local Satellite Imagery** | NO | NO | YES (if it existed) | YES | YES |
| **Element84 STAC (Sentinel-2)** | NO (Blocked) | NO | NO | YES | YES |
| **Planetary Computer STAC (Landsat)** | NO (Blocked) | NO | NO | YES | YES |
| **Web News/Incident Reports** | NO (Blocked/Unreliable) | NO | NO | YES | PARTIAL (Only major events) |
| **ThermoTrace Context (Recurrence, OSM)** | YES | YES | YES | NO (It is FIRMS-derived/static) | NO |

## 7. Critical Methodological Conclusion
**A. What the current environment can support**
The current environment strictly supports processing of locally cached static data (OSM proximities, WorldCover fractions, Population) and internal ThermoTrace FIRMS statistics (recurrence, FRP).

**B. What requires a different execution environment**
Any automated independent semantic verification (via satellite STAC APIs or programmatic web scraping) requires an execution environment with open HTTPS egress to public catalog endpoints and appropriate cloud credentials.

**C. What evidence can legitimately be used for semantic labels**
Only independent, external data—such as visual confirmation of a burn scar via Sentinel-2, or an official documented incident report—can be legitimately used to assign semantic silver labels like `wildfire_or_forest_fire` or `industrial_fire_or_abnormal_event`. 

**D. What remains impossible to establish**
It remains scientifically impossible to establish the ground-truth semantic class of any thermal event in this environment. It is strictly prohibited to turn ThermoTrace-derived heuristics (e.g., `events_previous_30d > 10` or `near_power_plant == True`) into semantic labels. Proximity is context, not causation.

---

**NO_USABLE_INDEPENDENT_EVIDENCE_ACCESS**
