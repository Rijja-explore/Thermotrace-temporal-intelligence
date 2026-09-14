# 🌐 ThermoTrace Frontend — Analyst Mission Control

> React 19 + TypeScript + Vite web client for the ThermoTrace Industrial Thermal Intelligence Platform (SIH 26162).

---

## 🏛️ End-to-End Operational Architecture

```text
              NASA SATELLITES
                    ↓
             NASA FIRMS NRT
                    ↓
        ┌──────────────────────┐
        │  RAW HOTSPOT DATA    │
        └──────────┬───────────┘
                   ↓
           QUALITY FILTER
                   ↓
             DBSCAN CLUSTER
                   ↓
       OSM + WORLDCOVER GIS
                   ↓
        ┌─────────────────────┐
        │  THERMOTRACE AI     │
        │                     │
        │ Persistence         │
        │ Facility Baseline   │
        │ Z-score / MAD       │
        │ Temporal / LSTM     │
        │ HGB Classification  │
        └──────────┬──────────┘
                   ↓
            INTELLIGENCE FUSION
                   ↓
          RISK + HAZARD + PLUME
                   ↓
             COMMAND CENTER
                   ↓
             INVESTIGATION
                   ↓
        ANALYST MAKES DECISION
                   ↓
       ┌───────────┴──────────┐
       ↓                      ↓
    No dispatch          Dispatch Report
                              ↓
                       Complete Report
                              ↓
                 thermotrace.india@gmail.com
```

---

## 🚀 Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment
Create a `.env` file in `apps/frontend/`:
```env
VITE_API_BASE=https://thermotrace-temporal-intelligence.onrender.com
```
*(Or use `http://localhost:8000` when running backend locally).*

### 3. Start Development Server
```bash
npm run dev
```

### 4. Build for Production
```bash
npm run build
```

---

## 📑 Application Structure (8 Canonical Pages)

- **`src/pages/`**:
  - `Dashboard.tsx`: **1. Command Center** (`/command-center`) — Near-Real-Time (NRT) KPI metrics strip, interactive Leaflet map, and priority alert rail.
  - `EventInvestigation.tsx`: **2. Investigations** (`/investigation/:id`) — Single-event deep-dive triage, Sentinel-2 imagery, 90-day FRP time series, and SHAP XAI breakdown.
  - `WhatIfSimulator.tsx`: **3. Scenario Modeler** (`/scenario-modeler`) — Interactive physics simulation with API 521 radiant heat exclusion zones and Gaussian plume dispersion.
  - `DataReductionVisualizer.tsx`: **4. Data Reduction** (`/data-reduction`) — 5-stage interactive reduction visualizer demonstrating raw FIRMS telemetry reduction.
  - `Alerts.tsx`: **5. Alert Center** (`/alert-center`) — Prioritized incident feed with threat badges and state-level filtering.
  - `FacilityProfile.tsx`: **6. Facilities** (`/facilities`) — Registered industrial asset catalog with baseline $\mu$, standard deviation $\sigma$, and operating envelopes.
  - `Analytics.tsx`: **7. Analytics** (`/analytics`) — Aggregate temporal intelligence, diurnal day/night ratios, and ML validation performance.
  - `Methodology.tsx`: **8. Methodology** (`/methodology`) — Mathematical formulation & scientific documentation.
- **`src/components/`**:
  - `MapView.tsx`: Leaflet mapping component with custom styling & vector state boundaries.
  - `EventPanel.tsx`: Side drawer for rapid anomaly inspection.
  - `ui/`: Reusable cards, modal dialogs, scorebars, and timeline visualizers.
- **`src/services/`**:
  - `api.ts`: Centralized HTTP client connecting to FastAPI backend endpoints.
  - `alertEmail.ts`: Analyst-controlled report dispatch client to `thermotrace.india@gmail.com`.
  - `AuthContext.tsx`: Single Analyst persona authentication context (`analyst / analyst`).
