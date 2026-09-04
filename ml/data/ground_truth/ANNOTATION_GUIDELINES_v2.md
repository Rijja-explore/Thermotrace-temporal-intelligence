# ThermoTrace Human Annotation Guidelines (v2.0)

## 1. Overview & Objective
This document provides formal domain expert guidelines for manually annotating thermal anomaly candidate events across the Indian subcontinent for **SIH26162: AI-Based Detection and Classification of Industrial Fires and Persistent Thermal Sources (NTRO)**.

---

## 2. The 6-Class Taxonomy & Evidence Criteria

### Class 1: `persistent_industrial_source`
- **Definition**: Continuous or highly recurring operational thermal emissions from active industrial infrastructure (e.g. oil refinery flares, steel mill furnaces, cement kilns).
- **Positive Evidence**:
  - Distance to mapped facility $\le 2.0$ km AND 30-day active detection days $\ge 10$.
  - Mapped built-up / industrial land cover fraction $\ge 0.3$.
  - High spatial stability (centroid position varies $<500$ meters across observations).
- **Negative Evidence**:
  - Transient single-day anomaly in dense forest cover.
- **Confounding Cases & Unknown Trigger**:
  - Facility proximity *alone* is NOT proof of an industrial source. If recurrence is zero and built-up land cover is absent, mark as `unknown_requires_verification`.

### Class 2: `industrial_fire_or_abnormal_event`
- **Definition**: Catastrophic or non-routine thermal fire events occurring within industrial facilities or chemical storage complexes.
- **Positive Evidence**:
  - FRP intensity spike ($>150$ MW) located $\le 1.0$ km from industrial infrastructure.
  - Corroborating independent news or incident log records.
- **Negative Evidence**:
  - Low FRP ($<15$ MW) stubble burning in open cropland.
- **Confounding Cases & Unknown Trigger**:
  - High FRP in mixed urban/forest interfaces without verified industrial facility records.

### Class 3: `mining_or_other_industrial_activity`
- **Definition**: Thermal anomalies associated with open-pit coal/metal mining, slag heap smoldering, or quarry extraction.
- **Positive Evidence**:
  - Location within or adjacent to active OSM mine/quarry boundary.
  - Multi-day recurrence with moderate FRP (20–100 MW).
- **Negative Evidence**:
  - Pure agricultural land cover with zero mining infrastructure.

### Class 4: `wildfire_or_forest_fire`
- **Definition**: Uncontrolled vegetation fires burning in natural forest or woodland ecosystems.
- **Positive Evidence**:
  - Mapped forest fraction $\ge 0.4$ and natural land fraction $\ge 0.7$.
  - Large spatial extent ($>1.5$ km²) and multi-pixel detection spread.
  - Facility distance $>5.0$ km.
- **Negative Evidence**:
  - Spatial location inside a refinery or steel plant complex.

### Class 5: `agricultural_burning`
- **Definition**: Seasonal crop residue / stubble burning in agricultural fields.
- **Positive Evidence**:
  - Cropland cover fraction $\ge 0.4$.
  - Short duration ($<6$ hours) and low active days ($<3$ days in 30d).
  - Seasonal alignment (post-monsoon wheat/rice harvest windows).
- **Negative Evidence**:
  - Multi-month continuous thermal emissions.

### Class 6: `unknown_requires_verification`
- **Usage**: Mandatory whenever available evidence is sparse, contradictory, or insufficient to prove one of the 5 semantic classes.
- **Rule**: **Never force uncertain events into a semantic class**.

---

## 3. Human Annotation Confidence Scale

- **`HIGH`**: Multiple independent evidence categories (e.g. high cropland fraction + short duration + satellite visual proof) unanimously support the label without contradiction.
- **`MEDIUM`**: Evidence strongly favors one class, but slight ambiguity exists (e.g. cropland/forest boundary).
- **`LOW`**: Weak or sparse evidence. Annotators should strongly consider assigning `unknown_requires_verification`.

---

## 4. Double-Annotation & Adjudication Protocol

1. **Initial Double Annotation**: A subset of 150–300 candidates is assigned independently to Annotator A and Annotator B.
2. **Disagreement Preservation**: Both Annotator A and B original records are preserved immutably.
3. **Senior Adjudication Queue**: Disagreements trigger an adjudication record where a senior reviewer evaluates cited evidence and records `adjudicated_label` and `adjudication_reason`.
