# Pilot 001 AI Class Diversity Investigation (Batch 001)

## Objective
To test the AI-assisted evidence workflow by investigating exactly 12 events sampled across 6 diverse contextual strata. The goal is to determine if the methodology can successfully propose defensible, evidence-backed AI-assisted silver labels across multiple taxonomy classes.

## Candidate Selection
The 12 events were contextually selected for investigation using strictly factual filters (e.g. `forest_fraction_1km > 0.8`, `events_previous_30d > 10`, `near_quarry = True`). No synthetic risk scores or heuristic flags were used. The first 5 events from the previous batch were completely excluded. 

## Investigation & Evidence Summary

### Stratum 1: Strong industrial/persistent-source context (2 events)
- **Selection**: High recurrence (10+ events in previous 30 days) combined with proximity to an industrial facility.
- **Sources Investigated**: Searched for exact coordinates, nearest settlement, and facility type. No relevant public evidence was found using the searches performed. Historical satellite imagery not independently inspected in this investigation.
- **Proposed Label**: `persistent_industrial_source`
- **Confidence**: `low`
- **Alternatives**: `industrial_fire_or_abnormal_event` (Rejected: duration/recurrence is too high for an accident).
- **Sufficiency**: While external news is absent, the triangulation of independent OSM facility boundaries combined with extreme localized temporal recurrence provides indirect but plausible support for a persistent industrial process (flare/furnace).

### Stratum 2: Strong agricultural-burning context (2 events)
- **Selection**: High cropland fraction (>80%).
- **Sources Investigated**: Extensive searches performed for local agricultural fires. No relevant public evidence was found using the searches performed. Historical satellite imagery not independently inspected.
- **Proposed Label**: `unknown_requires_verification`
- **Confidence**: `low`
- **Alternatives**: `agricultural_burning` vs `wildfire_or_forest_fire`
- **Sufficiency**: The strict evidence rule prohibits claiming agricultural burning solely from land-cover fractions. Without news or satellite verification, it remains Unknown.

### Stratum 3: Strong forest/wildfire context (2 events)
- **Selection**: High forest fraction (>80%) and low recurrence.
- **Sources Investigated**: Searched for forest fires in the state/district. No relevant public evidence was found using the searches performed. Historical satellite imagery not independently inspected.
- **Proposed Label**: `unknown_requires_verification`
- **Confidence**: `low`
- **Alternatives**: `wildfire_or_forest_fire` vs `agricultural_burning`
- **Sufficiency**: The strict evidence rule prohibits claiming wildfire solely from forest fractions. Without external verification, it remains Unknown.

### Stratum 4: Strong mining/quarry/industrial-activity context (2 events)
- **Selection**: Direct proximity to a registered mine or quarry.
- **Sources Investigated**: Searched for local mining activity/fires. No relevant public evidence was found using the searches performed. Historical satellite imagery not independently inspected.
- **Proposed Label**: `mining_or_other_industrial_activity`
- **Confidence**: `low`
- **Alternatives**: `wildfire_or_forest_fire`
- **Sufficiency**: The triangulation of exact OSM quarry boundaries with localized thermal detections provides indirect but plausible support for mining-related burning (e.g. waste burning or blasting).

### Stratum 5: Strong industrial-fire/abnormal-event context (2 events)
- **Selection**: Proximity to industrial facilities but zero recurrence in the previous 30 days (implying abnormal/singular event).
- **Sources Investigated**: Searched for facility fires/explosions. No relevant public evidence was found using the searches performed. Historical satellite imagery not independently inspected.
- **Proposed Label**: `unknown_requires_verification`
- **Confidence**: `low`
- **Alternatives**: `industrial_fire_or_abnormal_event` vs `agricultural_burning`
- **Sufficiency**: A single thermal detection near a factory could be an accident, but it could equally be an agricultural fire in an adjacent field. Without news verification, it must remain Unknown.

### Stratum 6: Intentionally ambiguous events (2 events)
- **Selection**: No nearby industrial facilities, mixed land cover (<40% forest, <40% crop).
- **Sources Investigated**: No relevant public evidence was found using the searches performed.
- **Proposed Label**: `unknown_requires_verification`
- **Confidence**: `low`
- **Alternatives**: Multiple competing hypotheses.
- **Sufficiency**: Insufficient evidence.

## Investigation Statistics
- **Total Investigated**: 12
- **Proposed labels by class**:
  - `unknown_requires_verification`: 8
  - `persistent_industrial_source`: 2
  - `mining_or_other_industrial_activity`: 2
- **Number Unknown**: 8
- **Number High Confidence**: 0
- **Number Medium Confidence**: 0
- **Number Low Confidence**: 12
- **Number with at least two independent evidence sources**: 0
- **Number supported primarily by ThermoTrace context**: 12

## Workflow Decision

**REVISE_INVESTIGATION_METHOD**

**Reasoning**: The current investigation methodology relies almost exclusively on web searches for indexed English-language news articles and incident logs. Because the vast majority of rural and routine thermal anomalies (e.g. agricultural fires, minor forest fires, typical industrial flares) do not generate indexed digital news, the workflow fails to produce evidence for them. Without access to an independent, automated satellite imagery verification tool to visually confirm agricultural clearing or forest burn scars, the AI investigator is forced to either incorrectly use ThermoTrace context as ground truth (violating the rules) or classify almost everything as `unknown_requires_verification`. To successfully generate a multi-class silver dataset, the AI workflow must be augmented with a tool capable of querying and inspecting historical satellite imagery for visual evidence triangulation.
