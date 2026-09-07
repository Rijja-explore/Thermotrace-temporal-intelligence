# ThermoTrace — Complete Project & Prototype Guide

**SIH Problem Statement 26162** · AI-Based Detection and Classification of Industrial Fires and Persistent Thermal Sources Using NASA FIRMS, OSM & Satellite Data

---

## What is ThermoTrace?

ThermoTrace is an **Explainable Facility-Aware Thermal Intelligence and Abnormal-Event Monitoring System**. It uses NASA FIRMS satellite data (MODIS & VIIRS) to detect, classify, and explain industrial thermal events — fires, abnormal flaring, and persistent heat sources — across India's industrial zones.

**Core novelty:** It does not just detect — it **explains why** the AI made each decision (SHAP, counterfactuals, LSTM attention), and **auto-dispatches email alerts** to `rijja2310119@ssn.edu.in` when critical events are detected.

---

## Login Page

**Shown when:** Not authenticated (page refresh = re-login required)

**Credentials:** Username `admin` · Password `admin` (any other combination = Access Denied)

| Element | Description |
|---------|-------------|
| Brand logo | Animated radar ring background, satellite SVG |
| Username field | Text input, autofocus |
| Password field | Password type |
| Sign In button | Cyan gradient; shows "Authenticating…" spinner + "Access Granted" on success |
| Error banner | Red banner on wrong credentials |
| Demo hint | "Demo credentials: admin / admin" |
| System badges | NASA FIRMS Live · XAI Engine v2 · SIH26162 |

---

## Command Center (Dashboard)

**Nav:** Command Center

| Component | Description |
|-----------|-------------|
| **KPI Strip** | 5 cards: Total Anomalies, Industrial Sources, Persistent Sources, Abnormal Events, High-Risk Alerts |
| **Map Toolbar** | Time range (7D/30D/90D), Region filter, Status filter, Class filter, Search, Pipeline modal button |
| **MapView** | Leaflet map with color-coded dots. 🔴 Fire · 🟡 Industrial · 🟢 Agricultural · 🟣 Unknown · 🔵 Normal. Animated ring on selected event |
| **Event Panel** | Side panel on dot click — ID, classification, risk score, facility, "Investigate →" |
| **Alert Rail** | Right column: priority queue of critical + high alerts, sorted by severity |
| **Pipeline Modal** | 7-layer NASA pipeline expandable view |

---

## Event Investigations

**Nav:** Event Investigations

| Component | Description |
|-----------|-------------|
| **Split layout** | Left = map zoomed to event, Right = analyst workspace |
| **Score Cards** | Classification Confidence · Industrial Likelihood · Operational Risk (each 0–100, with "Explain" breakdown) |
| **Evidence Timeline** | Horizontal timeline: first detection → persistence window → satellite passes |
| **Thermal Fingerprint Chart** | 30-day FRP bar chart vs baseline. Red = anomalous days |
| **Evidence Grid** | Cards: Facility Proximity · Land Cover · Persistence · Spatial Stability · Conflicts · Data Gaps |
| **XAI Panel (inline)** | Always visible SHAP + Counterfactual + Temporal Attention tabs |
| **🤖 XAI Deep Drill** | Opens full Explainability Drawer side panel |
| **Compare** | Compare two events side-by-side |
| **What-If Simulator** | Navigate to simulator pre-loaded with this event |
| **Report** | PDF-style report preview modal |
| **Analyst Action Bar** | Verify / Escalate / Dismiss / Reclassify buttons |
| **Data Provenance** | Sensor, model version, data source, acquisition date |

---

## Incident Scenario Modeler & Threat Simulator

**Nav:** Scenario Modeler

Parameter sliders (FRP, persistence, wind, proximity, inversion) → live updated risk score + hazard radius + plume dispersion. Preset industrial incident scenarios (Jamnagar Bleed, Ratnagiri Gas Surge, etc.). Automated SOP execution sequences (FGRS diversion, perimeter deluge, evacuation advisories). Auto-dispatches email notifications if simulated risk ≥ 75. Exportable GeoAI incident briefing JSON dossiers.

---

## Methodology & Intelligence Pipeline

**Nav:** Methodology

Full multi-layer architectural view:
- **Interactive Layer-by-Layer Pipeline**: 7-stage interactive visualization from raw NASA satellite orbits to calibrated alerts.
- **Data Source Registry**: Specifications for NASA FIRMS (MODIS/VIIRS), ESA WorldCover 10m, OpenStreetMap facility footprints, GADM boundaries, and ground truth datasets.
- **Feature Engineering Breakdown**: 4 feature pillars (Raw Thermal, Temporal Windows, Land Cover Fractions, Industrial Context Proximity).
- **Calibrated Uncertainty & Confidence Scale**: Explicit confidence thresholds (Confirmed ≥ 85%, Probable 70–84%, Possible 55–69%, Requires Verification 40–54%, Unknown < 40%).
- **Documented System Limitations**: Transparent edge cases (cloud mask thresholds, sensor resolution, agricultural overlap).

---

## Alert Center

**Nav:** Alert Center

Filterable table of all alerts by severity/status/region/date. Click any row for detail. CSV export.

---

## Facilities

**Nav:** Facilities

Industrial facility registry (OSM: refineries, steel, mining, power). Each facility has thermal history chart and linked events list.

---

## Thermal Analytics

**Nav:** Thermal Analytics

Confusion matrix · F1 per class · SHAP global importance · Ablation study table · Calibration curve.

---

## Data Reduction — Live Map Demo ⭐

**Nav:** Data Reduction

Interactive step-by-step geospatial demonstration using the **real Leaflet India map canvas** showing **raw NASA FIRMS detections across India collapsing down to 5 critical verified industrial events** through 5 processing stages.

| Stage | Input | Retained | What happens |
|-------|-------|----------|--------------|
| 1 — Raw FIRMS | — | ~100+ | All MODIS/VIIRS thermal pixels across India (refineries, noise, ag fires, glint) |
| 2 — Quality Filter | ~100+ | ~60 | Remove low-confidence (<25MW), cloud-masked, solar glint, and noise pixels |
| 3 — Clustering | ~60 | ~25 | DBSCAN groups proximate detections within 500m into event clusters |
| 4 — Geo Fusion | ~25 | ~10 | Cross-reference with OSM industrial facility footprints & ESA land cover |
| 5 — ML + XAI | ~10 | 5 | XGBoost+BiLSTM classifies critical risk; SHAP explains; auto-email dispatched |

Controls: Next / Prev / Direct Stage Click / Auto-Play toggle. Live animated markers transition colors (orange → yellow → cyan → purple → red) and remove noise dynamically. At Stage 5, emergency email alert is automatically dispatched to `rijja2310119@ssn.edu.in`.

---

## XAI Panel — Explainable AI

### Tab 1: SHAP Features
Animated bar chart. Click any row to expand feature explanation.

| Feature | SHAP | Impact |
|---------|------|--------|
| FRP Surge (340 MW, +4.2σ) | +0.34 | ↑ RISK |
| Persistence (80%, 24/30 days) | +0.28 | ↑ RISK |
| Facility Proximity (180m) | +0.22 | ↑ RISK |
| Nighttime Ratio (68%) | +0.16 | ↑ RISK |
| Land Cover (88% Industrial) | +0.12 | ↑ RISK |
| Wind Dispersion (25 km/h SW) | −0.06 | ↓ RISK |

### Tab 2: Counterfactuals (DiCE)
"What would flip the classification?" — 3 scenarios with conditions, feasibility, and outcome delta.

### Tab 3: Temporal Attention
30-day LSTM attention heatmap — red peaks = days the model focused on. Bidirectional LSTM (128 units) with scaled dot-product attention.

---

## Email Alert System

- **Auto-trigger:** Data Reduction Demo Stage 5
- **Recipient:** `rijja2310119@ssn.edu.in`
- **Content:** Event ID, FRP (MW), Risk Score, Hazard Radius, Mitigation directive, link to Command Center
- **Backend:** `apps/backend/app/api/notifications.py` — Python smtplib
- **Configure:** Set `SMTP_USER`, `SMTP_PASSWORD` in `.env` for real delivery

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React 18 + TypeScript + Vite |
| Styling | Vanilla CSS (custom dark design system) |
| Maps | Leaflet.js |
| Animation | Canvas API (custom) |
| Backend | FastAPI (Python 3.11) |
| ML | XGBoost + BiLSTM (PyTorch) |
| XAI | SHAP TreeExplainer + DiCE |
| Data | NASA FIRMS, ESA WorldCover 10m, OpenStreetMap |
| Email | Python smtplib / SMTP |

---

## Key Novelty vs Competitors

| Feature | ThermoTrace | Typical Fire Detection |
|---------|-------------|----------------------|
| Explains each AI decision | ✅ SHAP + DiCE + LSTM Attention | ❌ Black-box |
| Shows data reduction pipeline | ✅ Animated 847→3 demo | ❌ Hidden |
| Temporal persistence analysis | ✅ 30-day LSTM window | ❌ Single-pass |
| Facility-aware context | ✅ OSM + ESA fusion | ❌ None |
| Auto-email on detection | ✅ SMTP dispatch | ❌ Manual |
| Counterfactual mitigation | ✅ Operator-actionable | ❌ None |

---

*ThermoTrace · SIH26162 · 2026*
