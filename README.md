# 🔥 ThermoTrace — AI-Based Industrial Thermal Intelligence Platform

> **SIH 2026 Prototype** | *Operational GeoAI Intelligence Layer above NASA FIRMS (Problem Statement SIH26162)*

---

## 📌 Executive Concept & Core Philosophy

NASA FIRMS provides satellite thermal anomaly / active-fire observations from VIIRS and MODIS instruments. However, **a thermal anomaly is NOT automatically an industrial fire or a wildfire**. Industrial flares, refineries, steel plants, cement kilns, and agricultural burning produce distinct thermal signatures that require tailored operational responses.

**ThermoTrace** implements a unified, near-real-time GeoAI pipeline combining spatial context, sequential temporal learning, dynamic facility baselines, human-in-the-loop analyst verification, and multi-tier notification routing:

```
NASA FIRMS (VIIRS / MODIS NRT)
        ↓
Near-Real-Time Ingestion & Quality Filtering
        ↓
Spatiotemporal DBSCAN Clustering & Geospatial Fusion
        ↓
Feature Engineering (Spatial + Temporal Sequences)
        ↓
 ┌───────────────────────────┬───────────────────────────┐
 │ HistGradientBoosting (HGB)│ LSTM Temporal Engine      │
 │ "WHAT & WHERE"            │ "HOW IT EVOLVES OVER TIME"│
 └─────────────┬─────────────┴─────────────┬─────────────┘
               └─────────────┬─────────────┘
                             ↓
                 AI Fusion Layer (HGB + LSTM)
                             ↓
              90-Day Rolling Facility Baseline
                             ↓
                 Temporal Escalation State
      (STABLE → WATCH → ESCALATING → CRITICAL_ESCALATION)
                             ↓
                    Risk Engine (API 521)
                             ↓
             XAI & Plume Dispersion Assessment
                             ↓
                 Unified Incident Dossier
                             ↓
           Human Analyst Investigation Workflow
               (Review Evidence → Audit Log)
                             ↓
              ┌──────────────┴──────────────┐
              ▼                             ▼
      REJECT / RECLASSIFY                CONFIRM
              │                             │
              │                             ▼
              │                   Official Notification
              │                 (rijja2310119@ssn.edu.in)
              ▼                             ▼
        Verified Analyst Ground-Truth Dataset
                             ↓
      Closed-Loop Continuous Learning & Validation Gate
```

---

## 🧠 Hybrid AI Architecture (HGB + LSTM)

- **HistGradientBoosting (HGB)**: Evaluates land-cover, spatial proximity, and contextual features $\to$ *"WHAT and WHERE the event is"*.
- **LSTM Temporal Engine**: Processes observation sequences $(t_1 \to t_n)$ to model rate-of-change, acceleration, and thermal trends $\to$ *"HOW the event evolves over time"*.
- **AI Fusion Layer**: Fuses spatial probabilities ($P_{\text{HGB}}$), sequential temporal scores ($S_{\text{LSTM}}$), and rolling 90-day facility baseline deviations ($Z = \frac{\text{FRP} - \mu}{\sigma}$).

### Standardized 4-Stage Temporal State Machine:
$$\text{STABLE} \longrightarrow \text{WATCH} \longrightarrow \text{ESCALATING} \longrightarrow \text{CRITICAL\_ESCALATION}$$

---

## 👥 Role-Based Access Control (RBAC) & Standard Accounts

| Role | Standard User Account | Operational Scope |
| :--- | :--- | :--- |
| **ANALYST** | `anagesh2410198@ssn.edu.in` | Event investigation, HGB+LSTM telemetry review, XAI, incident confirmation/rejection, ground-truth labeling |
| **OFFICIAL** | `rijja2310119@ssn.edu.in` | Official emergency alerts, confirmed incident dossiers, radiant hazard ($350\text{ m}$) & plume dispersion zones, SOP directives |
| **ADMIN** | `admin@thermotrace.gov.in` | User management, continuous learning validation gate, poller controls, security audit trail |

*Default Evaluation Password:* `ThermoTrace2026!`

---

## 📬 Centralized Notification Routing Matrix

| Severity Level | Trigger Condition | Primary Recipient | Format |
| :--- | :--- | :--- | :--- |
| 🟢 **NORMAL** | $Z < 0.8$, Stable | Dashboard Only | Telemetry Card |
| 🟡 **WATCH** | $0.8 \le Z < 2.0$ | Dashboard Monitoring | Status Badge |
| 🟠 **HIGH** | $Z \ge 2.0$ or Escalating | `anagesh2410198@ssn.edu.in` (Analyst) | Detailed Investigation Brief |
| 🔴 **CRITICAL** | $Z \ge 3.0$ + Critical Escalation | `anagesh2410198@ssn.edu.in` + `rijja2310119@ssn.edu.in` | Incident Dossier |
| 🚨 **CONFIRMED** | Analyst Human Verification | `rijja2310119@ssn.edu.in` (Official) | Official Emergency Response Directive |

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python:** 3.11+ (PyTorch, scikit-learn, FastAPI, uvicorn)
- **Node.js:** 18+ / npm 10+

### 1. Installation

```bash
# Clone repository
git clone https://github.com/Rijja-explore/Thermotrace-temporal-intelligence.git
cd Thermotrace-temporal-intelligence

# Install Python backend dependencies
pip install -r apps/backend/requirements.txt

# Install React frontend dependencies
cd apps/frontend
npm install
cd ../..
```

### 2. Running Locally

**Terminal 1 — Start FastAPI Backend (Port 8000):**
```bash
python -m uvicorn apps.backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Start React Frontend (Port 3000 / 5173):**
```bash
cd apps/frontend
npm run dev
```

Open your browser at `http://localhost:3000` or `http://localhost:5173`.

---

## 🧪 Comprehensive Verification Suite

Run end-to-end subsystem verification:
```bash
python scratch/test_adaptive_upgrade.py
```

---

## 📄 Authors & Acknowledgements
Developed by the **ThermoTrace Team** for SIH 2026.
Addressing Industrial Safety, Remote Sensing Geospatial Intelligence, and Remote Disaster Monitoring.
