# 🔥 ThermoTrace — Explainable Geospatial & Temporal Intelligence Platform

> **Smart India Hackathon (SIH 2026)** | *Operational GeoAI Intelligence Layer above NASA FIRMS (Problem Statement SIH26162)*  
> **Repository**: [Thermotrace-temporal-intelligence](https://github.com/Rijja-explore/Thermotrace-temporal-intelligence) | **Live Demo**: [https://thermotrace.vercel.app](https://thermotrace.vercel.app)

---

## 📌 1. Project Overview & Problem Statement

NASA FIRMS provides near-real-time satellite thermal anomaly and active fire detections from **VIIRS** (`VNP14IMGTDL`, `VJ114IMGTDL` at 375m resolution) and **MODIS** (`MCD14DL` at 1km resolution). However, in an operational industrial setting:

> **A thermal anomaly is NOT automatically an accidental fire or wildfire.**  
> Industrial refineries, petrochemical complexes, blast furnaces, and cement kilns generate persistent thermal signatures (routine flaring, furnace exhaust) that trigger thousands of false emergency alarms every day.

**ThermoTrace** solves this challenge by implementing a **99.98% Data Reduction Pipeline** and a **4-Engine Decision Intelligence Suite** that differentiates:
1. **Normal Permitted Operations** (routine flare baselines, regulated industrial exhaust).
2. **Abnormal Industrial Runaways** (explosions, uncontrolled flaring surges, pipeline ruptures).
3. **Environmental Fires** (stubble burning, agricultural clearing, forest wildfires).

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

## 🧠 2. Detailed Machine Learning Architecture & Models

ThermoTrace employs an ensemble of specialized machine learning models and statistical baselines rather than a single black-box classifier:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                               MACHINE LEARNING SUITE                             │
├──────────────────────────────────────────────────────────────────────────────────┤
│ 1. Engine 1: Persistent Source Random Forest / Gradient Boosting Classifier     │
│ 2. Engine 2: Rolling 90-Day Non-Parametric & Robust Gaussian Baseline Engine    │
│ 3. Engine 3: Multi-Task PyTorch Recurrent LSTM Neural Network (`ThermalLSTM`)   │
│ 4. Engine 4: Histogram-Based Gradient Boosting Decision Tree (`HistGradient`)   │
│ 5. Adaptive Retraining Gate: Closed-Loop Continuous Feedback Learner             │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 🔹 Engine 1: Persistent Source ML Fingerprint (`persistent_fingerprint.py`)
- **Core Question**: *"Does this spatial location behave like an established industrial asset?"*
- **Model Type**: Supervised Random Forest Classifier trained on verified industrial registries (OSM, CPCB, Ministry of Petroleum).
- **Extracted Behavioral Features**:
  - **Detection Frequency ($f_{\text{det}}$)**: $\frac{\text{Detections in 90 days}}{\text{Total Satellite Passes}}$ (Refineries typically $>0.85$).
  - **Centroid Spatial Drift ($\Delta d_{\text{centroid}}$)**: Standard deviation of observed coordinate jitter (Flare stacks $< 50\text{m}$; wildfires $> 1.2\text{km}$).
  - **Day/Night Thermal Ratio ($R_{\text{D/N}}$)**: Ratio of daytime to night-time FRP (Industrial operations run 24/7 with $R_{\text{D/N}} \in [0.8, 1.2]$; agricultural fires concentrate in daytime).
  - **Cadence Regularity ($\text{CV}_{\Delta t}$)**: Coefficient of variation between consecutive observations.
  - **Infrastructure Polygon Containment**: Distance to boundary and containment in heavy industrial zones.
- **Output**: Calibrated persistence probability $P_{\text{pers}} \in [0.0, 1.0]$.

---

### 🔹 Engine 2: Rolling 90-Day Facility Baseline (`baseline.py`)
- **Core Question**: *"Is the observed thermal output normal for this specific industrial facility?"*
- **Model Type**: Dynamic rolling statistical baseline with outlier suppression (Median Absolute Deviation - MAD).
- **Mathematical Formulations**:
  $$\text{Standard } Z\text{-Score} = \frac{\text{FRP}_{\text{observed}} - \mu_{90d}}{\sigma_{90d}}$$
  $$\text{Robust } Z_{\text{MAD}} = \frac{\text{FRP}_{\text{observed}} - \text{Median}_{90d}}{1.4826 \times \text{MAD}_{90d}}$$
- **Operational Logic**:
  - $Z < +2.5\sigma$: **Normal Baseline Flaring** (Operational Alarm Suppressed).
  - $+2.5\sigma \le Z < +4.0\sigma$: **Elevated Operational Thermal Activity** (Analyst Watchlist).
  - $Z \ge +4.0\sigma$: **Statistically Significant Thermal Excursion** (Critical Escalation).

---

### 🔹 Engine 3: Sequential PyTorch LSTM Temporal Engine (`lstm_temporal.py`)
- **Core Question**: *"Is the thermal trajectory accelerating or escalating across sequential satellite passes?"*
- **Model Architecture**:
  - **Class**: `ThermalLSTMModel(nn.Module)`
  - **Input Dimensions**: 10-dimensional sequential feature vector per satellite pass:
    ```python
    [
        0: FRP (Normalized MW),
        1: Brightness Temperature T4 (K),
        2: Spectral Differential ΔT31 (T4 - T11 K),
        3: dFRP/dt (Velocity / 1st derivative),
        4: d²FRP/dt² (Acceleration / 2nd derivative),
        5: 90-Day Persistence Ratio,
        6: Day/Night Pass Flag (0: Night, 1: Day),
        7: Distance to Nearest Facility (km),
        8: Baseline Z-Score,
        9: Daily Pass Frequency
    ]
    ```
  - **Network Topology**:
    - 2-Layer Bidirectional/Unidirectional LSTM (`hidden_size=32`, `dropout=0.15`).
    - **Dual Output Heads**:
      1. **Classification Head**: 4-State Escalation State Machine: `[STABLE, WATCH, ESCALATING, CRITICAL_ESCALATION]`.
      2. **Regression Head**: Autoregressive Next-Pass FRP Predictor ($T+24\text{h}$, $T+48\text{h}$ forecasted MW).

---

### 🔹 Engine 4: Contextual HistGradientBoosting Classifier (`models.py`)
- **Core Question**: *"What is the environmental, infrastructure, and geospatial classification of this event?"*
- **Active Model**: `M4-B_HistGradientBoosting_v1.26.0-Adaptive`
- **Trained Framework**: Scikit-Learn `HistGradientBoostingClassifier`
- **6-Class Operational Taxonomy**:
  1. `persistent_industrial_source` (Refinery flare stack, steel smelter kiln, industrial chimney).
  2. `industrial_fire_or_abnormal_event` (Accidental refinery fire, chemical tank blaze, flare surge).
  3. `wildfire_or_forest_fire` (Vegetation, scrub, or canopy wildfire).
  4. `agricultural_burning` (Crop residue / stubble burning).
  5. `mining_or_other_industrial_activity` (Coal seam fire, open cast mine, slag heap).
  6. `unknown_requires_verification` (Ambiguous thermal anomaly).
- **Champion Model Evaluation Metrics**:
  - **Accuracy**: **95.65%**
  - **Weighted F1-Score**: **0.9357**
  - **Macro F1-Score**: **0.7400**
  - **Industrial Recall**: **75.00%**
  - **Agricultural & Wildfire Precision**: **100.00%**

---

### 🔹 Hybrid Multimodal Decision Fusion (`model_fusion.py`)
The 4 engines are fused into a **Unified Composite Operational Risk Score ($0 - 100$)**:

$$\text{Risk Score} = 100 \times \left( w_1 \cdot \text{Score}_{\text{HGB}} + w_2 \cdot \text{Score}_{\text{Baseline}} + w_3 \cdot \text{Score}_{\text{LSTM}} + w_4 \cdot \text{Score}_{\text{Physics}} \right)$$

Where:
- $w_{\text{baseline}} = 0.30$ (Facility Baseline Deviation)
- $w_{\text{lstm}} = 0.25$ (Temporal Acceleration & Trajectory)
- $w_{\text{persistent}} = 0.25$ (Learned Industrial Fingerprint)
- $w_{\text{hgb}} = 0.20$ (Contextual Spatial Classifier)

---

### 🔹 Closed-Loop Adaptive Continuous Retraining Gate (`retraining_gate.py`)
- When an analyst confirms or reclassifies an anomaly in the console, the event is sealed with PBKDF2 cryptographic audit hashes and appended to the ground-truth ledger (`data/feedback/analyst_feedback.json`).
- Automated retraining triggers periodically on candidate models.
- **Promotion Safety Gate**: A candidate model is **ONLY promoted** to the active champion registry if:
  1. $\text{Validation Macro-F1} \ge 0.82$.
  2. Industrial classification recall does not regress.
  3. All automated unit and regression tests pass.
- If a promoted model regresses in production, an automated **Rollback Gate** restores the previous champion artifact in $<100\text{ms}$.

---

## ⚡ 3. Physics-Based Consequence & Plume Modeling

When an industrial anomaly is flagged, ThermoTrace executes deterministic engineering consequence models:

```
                  ┌──────────────────────────────────────────────┐
                  │          CONSEQUENCE MODELING SUITE          │
                  └──────────────────────┬───────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ↓                                               ↓
     [API 521 Thermal Radiation]                    [Atmospheric Gaussian Plume]
     Radiant heat flux cordons:                     Downwind toxic/smoke corridor:
     - 4.73 kW/m² (Personnel safety)                - Pasquill-Gifford dispersion
     - 9.46 kW/m² (Equipment threshold)             - Wind vector & atmospheric stability
     - 37.5 kW/m² (Structural hazard)               - Downwind corridor distance (km)
```

1. **API 521 Radiant Heat Flux Contours**:
   - Computes radiant heat intensity $q = \frac{\tau \cdot F \cdot Q}{4 \pi R^2}$ to calculate safety perimeters:
     - **Outer Perimeter ($4.73\,\text{kW/m}^2$)**: Escape boundary for personnel without protective gear.
     - **Intermediate Perimeter ($9.46\,\text{kW/m}^2$)**: Emergency crew operational threshold with protective suits.
     - **Inner Perimeter ($37.5\,\text{kW/m}^2$)**: Structural damage risk to neighboring storage tanks.
2. **Gaussian Atmospheric Plume Dispersion**:
   - Ingests wind vectors ($u\,\text{m/s}$, wind bearing) and Pasquill-Gifford atmospheric stability classes (A–F) to project downwind smoke and toxic corridor footprints.
3. **Demographic Exposure & Critical Infrastructure Intersection**:
   - Intersects plume footprints with High-Resolution Settlement Layer (HRSL) population rasters and OpenStreetMap infrastructure polygons to compute:
     - Residential population exposed within impact corridor.
     - Proximity to high-voltage power transmission lines, gas pipelines, schools, and hospitals.

---

## 🖥️ 4. Analyst Mission Control Platform Modules

The frontend interface is organized into **8 canonical Analyst intelligence pages**:

| Module | Route | Purpose & Core Capabilities |
| :--- | :--- | :--- |
| **1. Command Center** | `/command-center` | Primary mission control dashboard: Near-Real-Time (NRT) KPI strip, interactive Leaflet map, filters, facility overlays, and quick event inspection. |
| **2. Investigations** | `/investigation/:id` | Deep-dive triage dossier: Sentinel-2 optical imagery, 90-day FRP time series, SHAP/XAI explanations, and human-in-the-loop audit actions. |
| **3. Scenario Modeler** | `/scenario-modeler` | Interactive physics simulator: API 521 radiant heat exclusion zones ($q = \frac{\tau \eta Q}{4 \pi R^2}$), Gaussian plume corridors, and sector SOP sequences. |
| **4. Data Reduction** | `/data-reduction` | 5-Stage interactive reduction visualizer demonstrating telemetry reduction from raw FIRMS scan pixels down to verified critical alarms. |
| **5. Alert Center** | `/alert-center` | Prioritized incident queue: severity badges (CRITICAL / HIGH / MEDIUM), geographic filters, and investigation routing. |
| **6. Facilities** | `/facilities` | Industrial asset catalog: baseline FRP ($\mu$), standard deviation ($\sigma$), normal operating envelope, and historical flaring metrics. |
| **7. Analytics** | `/analytics` | System-wide intelligence analytics: temporal distributions, diurnal day/night ratios, regional risk breakdown, and model evaluation metrics. |
| **8. Methodology** | `/methodology` | Mathematical formulation & scientific documentation: NASA FIRMS NRT ingestion, DBSCAN clustering, OSM GIS fusion, and API 521 physics. |

---

## 🔐 5. Single Analyst Authentication (SIH Demo Mode)

ThermoTrace uses a unified **Lead Thermal Analyst** persona for operational efficiency and SIH defense:

- **Role**: `ANALYST` (Full access to all 8 mission control pages, AI explanations, and dispatch tools)
- **Default Username**: `analyst`
- **Default Password**: `analyst`
- **Official Dispatch Target**: `thermotrace.india@gmail.com`

---

## 📬 5. Centralized Notification & Mail Dispatch Engine

All approved incident reports, emergency alerts, and PDF dossiers are routed through a resilient dual-mode dispatch pipeline:

- **Central Dispatch Email**: `thermotrace.india@gmail.com`
- **Supported Dispatch Protocols**:
  1. **HTTPS Mail API (Port 443 via Resend / `RESEND_API_KEY`)**: 100% immune to cloud firewall and port-blocking restrictions.
  2. **SMTP IPv4 Dispatch (Ports 587 STARTTLS & 465 SSL)**: Enforces explicit IPv4 address resolution to prevent Linux/Docker IPv6 `[Errno 101] Network is unreachable` routing issues.
- **Audit Logging**: Every outgoing message records message ID, timestamp, recipient, delivery state, and full HTML dossier in an immutable dispatch ledger.

---

## 🛠️ 6. Technology Stack

### Backend
- **Language**: Python 3.11+
- **Web API Framework**: FastAPI, Uvicorn, Pydantic v2
- **Machine Learning & Math**: PyTorch, Scikit-learn, NumPy, Pandas, Joblib
- **Geospatial Processing**: Shapely, GeoPandas, PyProj, Rasterio
- **PDF Generation**: ReportLab
- **Security & Auth**: PBKDF2-HMAC-SHA256 password hashing, RBAC token system

### Frontend
- **Framework**: React 19, TypeScript, Vite
- **Mapping**: Leaflet, React-Leaflet, Esri Dark Canvas Tiles
- **Icons & Styling**: Lucide React, Modern Glassmorphism CSS Design Tokens
- **State Management**: React Hooks, Context API

### Infrastructure & Deployment
- **Backend Hosting**: Render (FastAPI Web Service)
- **Frontend Hosting**: Vercel (Single Page Application)
- **Containerization**: Docker, Docker Compose

---

## 🚀 7. Local Development & Setup Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Git

### 1. Clone Repository
```bash
git clone https://github.com/Rijja-explore/Thermotrace-temporal-intelligence.git
cd Thermotrace-temporal-intelligence
```

### 2. Backend Setup
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt   # Or install fastapi uvicorn scikit-learn torch reportlab pydantic

# Launch Backend API
uvicorn apps.backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
*The interactive Swagger documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).*

### 3. Frontend Setup
```bash
cd apps/frontend
npm install
npm run dev
```
*The frontend will launch at [http://localhost:5173](http://localhost:5173).*

---

## ⚙️ 8. Environment Variables Reference

Create a `.env` file in the root or configure these variables in your deployment dashboard (Render / Vercel):

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `VITE_API_BASE` | `https://thermotrace-temporal-intelligence.onrender.com` | Backend API URL for frontend client |
| `RESEND_API_KEY` | *(Optional)* | API key for HTTPS email delivery over Port 443 |
| `MAIL_USERNAME` | `thermotrace.india@gmail.com` | Gmail SMTP username / sender account |
| `MAIL_PASSWORD` | *(Google App Password)* | 16-character Google App Password for SMTP |
| `MAIL_HOST` | `smtp.gmail.com` | SMTP server hostname |
| `MAIL_PORT` | `587` (or `465`) | SMTP server port |
| `MAIL_FROM` | `thermotrace.india@gmail.com` | Sender header address |
| `MAIL_TO` | `thermotrace.india@gmail.com` | Default recipient for approved intelligence reports |

---

## 🧪 9. Verification & Automated Test Suite

Run the full automated test suite covering unit tests, ML pipelines, API endpoints, and continuous learning gates:

```bash
# Run all pytest suites
pytest tests/ -v

# Run ML adaptive retraining & evaluation tests
python scripts/evaluate.py
python scripts/test_adaptive_upgrade.py
python scripts/test_dispatch.py
```

---

## 👥 10. Contributors & License

- **Project Lead & Development**: Rijja H ([rijja.softwaredev@gmail.com](mailto:rijja.softwaredev@gmail.com))
- **Team**: ThermoTrace Intelligence Systems (SIH 2026)
- **License**: MIT License
