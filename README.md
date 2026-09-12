# 🔥 ThermoTrace — AI-Based Industrial Thermal Intelligence Platform

> **SIH 2026 Prototype** | *Operational GeoAI Intelligence Layer above NASA FIRMS (Problem Statement SIH26162)*

---

## 📌 Executive Concept & Core Philosophy

NASA FIRMS provides satellite thermal anomaly / active-fire observations from VIIRS (VNP14IMGTDL, VJ114IMGTDL) and MODIS (MCD14DL) instruments. However, **a thermal anomaly is NOT automatically an accidental industrial fire or a wildfire**. Industrial flares, refineries, steel plants, cement kilns, and agricultural burning produce distinct thermal signatures that require tailored operational responses.

**ThermoTrace** implements a unified, near-real-time GeoAI pipeline that solves this problem using a **4-Engine Decision Intelligence Architecture**:

```text
                                 NASA FIRMS NRT
                             (VIIRS / MODIS Passes)
                                       ↓
                        Spatiotemporal DBSCAN Clustering
                                       ↓
                          Multi-Feature Engineering
                                       ↓
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                       THERMOTRACE 4-ENGINE AI PIPELINE                    │
 ├─────────────────────────┬───────────────────────────┬─────────────────────┤
 │ Engine 1: Persistent ML │ Engine 2: 90D Baseline    │ Engine 3: LSTM      │
 │ "WHAT TYPE OF SOURCE?"  │ "IS IT ABNORMAL HERE?"    │ "IS IT ESCALATING?" │
 │ Evaluates recurrence,   │ 90-Day facility rolling   │ Sequential pass     │
 │ drift, day/night ratio  │ distribution (Z-score)    │ dynamics & slope    │
 └────────────┬────────────┴─────────────┬─────────────┴──────────┬──────────┘
              │                          │                        │
              └──────────────────────────┼────────────────────────┘
                                         │
                        ┌────────────────┴────────────────┐
                        │ Engine 4: Contextual HGB        │
                        │ Spatial/Land-Cover Signature    │
                        └────────────────┬────────────────┘
                                         ↓
                        Hybrid Decision Fusion Engine
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ↓                                ↓                                ↓
 [Normal Flaring]               [Abnormal Runaway]             [Wildfire / Agri]
 High P_pers + Normal Z         High P_pers + Surge Z          Low P_pers + Natural Land
 → ROUTINE MONITORING           → CRITICAL INCIDENT            → ENVIRONMENTAL ALERT
 (Suppressed Alarm)                      │
                                         ↓
                        Radiant Hazard & Plume Modeling
                          (API 521 Thermal Contours)
                                         ↓
                            Unified Incident Dossier
                                         ↓
                        Human Analyst Verification
                           (Review → Audit Log)
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
            REJECT / RECLASSIFY                            CONFIRM
                    │                                         │
                    │                                         ▼
                    │                              Approved Report & PDF Dossier
                    │                              (thermotrace.india@gmail.com)
                    ▼                                         ▼
              Verified Analyst Ground-Truth Dataset (Closed-Loop)
                                         ↓
              Candidate Retraining & Validation Gate (Macro F1 ≥ 0.82)
                                         ↓
              Controlled Candidate-Model Promotion (Model Registry)
```

---

## 🧠 The 4-Engine AI Story

Instead of using one model to answer all questions or relying on brittle manual thresholds, ThermoTrace assigns clear division of concerns:

| Engine | Technical Subsystem | Core Question Answered | Key Indicators & Math |
| :--- | :--- | :--- | :--- |
| **Engine 1** | **Persistent Source ML Fingerprinter** | *"What type of behavioural source is this?"* | Detection frequency ($>85\%$), Centroid drift ($<50\text{m}$), Day/Night symmetry ($>0.70$), OSM polygon containment $\to P_{\text{persistent}} \in [0.0, 1.0]$ |
| **Engine 2** | **Rolling 90-Day Facility Baseline** | *"Is the current intensity statistically abnormal for this facility?"* | Historical operating envelope $\to Z = \frac{\text{FRP} - \mu_{90d}}{\sigma_{90d}}$ and robust $Z_{\text{MAD}}$ |
| **Engine 3** | **Sequential PyTorch LSTM** | *"Is the thermal trajectory accelerating / escalating over time?"* | Multi-pass hidden state sequence $\to \text{STABLE} \to \text{WATCH} \to \text{ESCALATING} \to \text{CRITICAL\_ESCALATION}$ ($\frac{d\text{FRP}}{dt}, \frac{d^2\text{FRP}}{dt^2}$) |
| **Engine 4** | **Contextual HistGradientBoosting** | *"What is the environmental and infrastructure context?"* | Distance to facility, high-voltage lines, pipelines, land-cover fractions ($P_{\text{HGB}}$ across 6-class operational taxonomy) |

### Implemented 6-Class Operational Taxonomy:
1. `persistent_industrial_source` (Refinery flare stack, steel smelter kiln, industrial chimney)
2. `industrial_fire_or_abnormal_event` (Accidental industrial explosion, tank farm blaze, uncontrolled flare surge)
3. `wildfire_or_forest_fire` (Vegetation, scrub, or canopy wildfire)
4. `agricultural_burning` (Stubble / crop residue burning)
5. `mining_or_other_industrial_activity` (Coal seam, open cast mining, slag heaps)
6. `unknown_requires_verification` (Ambiguous thermal signature requiring analyst inspection)

---

### 🎤 Championship Jury Viva Defense: "Why Both LSTM and Z-Score Baseline?"

> **Jury Question:** *"If you have an LSTM, why do you still need a Z-score baseline? Doesn't the LSTM detect anomalies?"*

**Team Defense:**
> *"Yes — our LSTM absolutely detects abnormal behavior! The important distinction is **what kind of abnormal** each subsystem detects.*
>
> *Suppose a refinery normally behaves like: `80 → 85 → 82 → 88 → 84 → 86 MW`. The LSTM learns this sequence pattern. When it observes `82 → 85 → 90 → 120 → 180 MW`, it recognizes that the trajectory has changed dramatically from normal and flags temporal escalation.*
>
> *However, there are two distinct meanings of 'abnormal' in operational remote sensing: **temporal trajectory abnormality** vs **facility-relative baseline abnormality**."*

#### Comparative Intelligence Matrix:

| Question / Operational Need | Sequential PyTorch LSTM | Facility 90-Day Baseline (Z-score) |
| :--- | :--- | :--- |
| **Is the pattern changing unusually?** | ✅ **Excellent** | ⚠️ Limited |
| **Is FRP suddenly increasing?** | ✅ **Yes** | ✅ **Yes** |
| **Is the current value unusual for this facility?** | ✅ Can learn pattern | ✅ **Very direct empirical anchor** |
| **Does the sequence look like previous incidents?** | ✅ **Yes** | ❌ No |
| **Is 150 MW normal for this specific refinery?** | ⚠️ Depends on training distribution | ✅ **Excellent ($Z = \frac{150 - \mu}{\sigma}$)** |
| **Predict what happens next (24h/48h)?** | ✅ **Excellent (Forecast Corridor)** | ❌ No |
| **Detect multi-pass escalation velocity?** | ✅ **Excellent ($\frac{d\text{FRP}}{dt}, \frac{d^2\text{FRP}}{dt^2}$)** | ⚠️ Limited |
| **Explain deviation from facility's historical mean?** | ⚠️ Latent hidden representations | ✅ **Mathematically certified $\pm Z\sigma$** |

#### The Two-Refineries Problem (Why Baseline is Essential):

```text
Refinery A (Small Regional Plant):
  Normal FRP = 20–30 MW
  Current Observed = 100 MW  →  Z = +14.2σ  [CRITICAL DISASTER]

Refinery B (Jamnagar Mega Complex):
  Normal FRP = 90–120 MW
  Current Observed = 100 MW  →  Z = +0.2σ   [ROUTINE NORMAL FLARING]
```

> *"An LSTM trained globally could see **100 MW as normal** because it has seen many large facilities operating around 100 MW. But ThermoTrace must answer: **'Is 100 MW abnormal for THIS specific facility?'** The Facility Baseline resolves this instantly.*
>
> *Therefore, we don't use one model to answer three different questions:*
> 1. *The **Persistent ML Model** tells us whether the source behaves like a stationary industrial stack.*
> 2. *The **Facility Baseline** tells us whether the current intensity is statistically abnormal for this specific plant.*
> 3. *The **Sequential LSTM** tells us whether the thermal behavior is escalating over time.*
>
> *Fusing all three produces an explainable, false-alarm-free decision intelligence layer."*

---

## 🔑 1-Click Role Accounts & Notification Routing

## 🔑 Single Analyst Login & Central Report Destination

ThermoTrace provides a unified single-role **Analyst Intelligence Platform** for SIH Demo Mode with PBKDF2-HMAC-SHA256 authentication:

### Credentials & Report Destination:

| Role | Username | Password | Central Report Destination | Scope & Permissions |
| :--- | :--- | :--- | :--- | :--- |
| 🔬 **Analyst** | `analyst` | `analyst` *(or `ThermoTrace2026!`)* | `thermotrace.india@gmail.com` | Lead Thermal Analyst — Full access to the entire platform: Incident investigation, 4-engine AI dossier review, XAI explanations, physical hazard contours, simulation SOPs, and 1-click PDF report approval dispatched directly to `thermotrace.india@gmail.com`. |

---

## 📬 Intelligence Report & Notification Routing Matrix

| Severity Level | Trigger Condition | Primary Recipient | Format |
| :--- | :--- | :--- | :--- |
| 🟢 **NORMAL** | $P_{\text{pers}} \ge 0.60$, $Z < 1.8$, LSTM Stable | Dashboard Monitoring | Suppressed Alarm (Routine Telemetry) |
| 🟡 **WATCH** | $0.8 \le Z < 1.8$ | Dashboard Monitoring | Status Advisory Badge |
| 🟠 **HIGH** | $Z \ge 1.8$ or Escalating | `thermotrace.india@gmail.com` | Detailed Investigation Brief |
| 🔴 **CRITICAL** | $Z \ge 3.0$ + Critical Escalation | `thermotrace.india@gmail.com` | Critical Incident Dossier |
| 🚨 **CONFIRMED** | Analyst Approval / SOP Execution | `thermotrace.india@gmail.com` | Official Incident Directive & Attached PDF Dossier |

---

## 🔄 Complete End-to-End Operational Flow

```text
[Step 1: Near-Real-Time Telemetry Ingestion]
 NASA FIRMS VIIRS & MODIS NRT passes ingested with deduplication and quality filtering.
 Hotspots clustered spatially via Haversine DBSCAN into composite thermal events.

[Step 2: 4-Engine Multi-Modal AI Evaluation]
 • Engine 1 computes P(persistent) = 0.99 (Confirms stationary refinery flare).
 • Engine 2 computes Facility Baseline Z-score = +13.95σ (Spike from 82 MW to 340 MW).
 • Engine 3 PyTorch LSTM computes Trajectory = CRITICAL_ESCALATION (+92.5 MW/pass).
 • Engine 4 HGB classifies spatial signature = Industrial Fire / Flare Surge (94% conf).

[Step 3: Decision Fusion & Threat Tiering]
 Hybrid fusion layer synthesizes the 4 engines:
 → Final Assessment: ABNORMAL_INDUSTRIAL_EVENT [CRITICAL].
 → Routes Critical Investigation Dossier to Analyst Central Feed (thermotrace.india@gmail.com).

[Step 4: Physical Hazard & Plume Modeling]
 • Radiant Heat Contour: R = 350m at 4.7 kW/m² (API 521 escape threshold).
 • Plume Dispersion: Gaussian downwind dispersion extending along wind vector.
 • Population Exposure: Surrounding residential buffer estimation.

[Step 5: Human-in-the-Loop Analyst Verification & Approval]
 Analyst logs into Console (`analyst`/`analyst`), reviews multi-spectral imagery, XAI explanations, and clicks CONFIRM / APPROVE.
 An immutable audit record is logged: ACTION: CONFIRMED by Lead Thermal Analyst.

[Step 6: Direct Report Approval & PDF Dispatch]
 Complete incident dossier & formatted PDF report dispatched directly to thermotrace.india@gmail.com.
 Response SOP triggered: FGRS diversion, boundary deluge curtain, and emergency standby directives.

[Step 7: Closed-Loop Continuous Learning Gate]
 Confirmed audit sample is added to the ground-truth training set.
 Continuous learning gate triggers candidate evaluation:
 Macro F1 >= 0.82 gate threshold → Candidate model registered in model_registry.json for controlled deployment.
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python:** 3.11+ (PyTorch, scikit-learn, FastAPI, uvicorn)
- **Node.js:** 18+ / npm 10+

### 1. Backend Setup & Test
```bash
# Run continuous learning validation suite (Tests all 16 ML retraining & gate criteria)
python scratch/test_continuous_learning.py

# Run verification suite (Tests all 6 subsystems & 4 AI engines)
python scratch/test_full_system.py

# Run FastAPI backend
cd apps/backend
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup & Build
```bash
cd apps/frontend
npm install
npm run build
npm run dev
```

---

## 🏛️ Project Structure

```text
Thermotrace-temporal-intelligence/
├── apps/
│   ├── backend/                     # FastAPI backend (Auth, Intelligence, Notifications, NRT)
│   └── frontend/                    # Vite + React + Tailwind + TypeScript Dashboard
├── services/
│   ├── classification/
│   │   ├── persistent_fingerprint.py # Engine 1: Learned Persistent Source ML Fingerprint
│   │   ├── baseline.py              # Engine 2: 90-Day Rolling Facility Baseline
│   │   ├── lstm_temporal.py         # Engine 3: Sequential PyTorch LSTM Engine
│   │   ├── models.py                # Engine 4: Contextual HistGradientBoosting
│   │   ├── model_fusion.py          # Unified 4-Engine Decision Intelligence Fusion Layer
│   │   ├── retraining_gate.py       # Closed-loop validation gate & genuine ML retraining
│   │   └── feedback_collector.py    # Human-in-the-loop ground truth collector
│   ├── data_pipeline/               # NASA FIRMS NRT poller and ingestion
│   └── temporal_intelligence/       # Clustering, physical hazard & plume dispersion
├── scratch/
│   ├── test_continuous_learning.py  # 16-point forensic continuous learning test suite
│   ├── test_full_system.py          # Master verification test suite
│   └── test_api_flow.py             # End-to-end REST API validation test
└── README.md                        # Documentation & Architecture Guide
```
