# 🎯 ThermoTrace Judging Demonstration Guide

> **SIH 2026 Live Demo Script**  
> *Follow this exact step-by-step walkthrough during judging evaluation.*

---

## 🚀 System Startup Commands

```bash
# 1. Start Backend API
python -m uvicorn apps.backend.app.main:app --host 0.0.0.0 --port 8000

# 2. Start Frontend UI
cd apps/frontend && npm run dev
```

Open Browser at: `http://localhost:3000`

---

## 📋 28-Step End-to-End Judge Demonstration Flow

| Step | Action | Expected UI Output & Verification |
| :--- | :--- | :--- |
| **1** | Open App (`http://localhost:3000`) | Header displays "THERMOTRACE" with green "SYSTEM ACTIVE" status badge. |
| **2** | View Command Dashboard | Dashboard loads central dark-theme GIS map with thermal events & facilities across India. |
| **3** | Inspect Summary Counters | Metric cards display Total Detections, Critical Events, Industrial Sources, and High Risk. |
| **4** | View Industrial Facilities Layer | Blue rectangular markers appear on map representing refineries, steel plants, and coal basins. |
| **5** | Select Event `TT-CASE-001` | Map zooms to **Jamnagar Refinery Complex**. Side panel opens with event details. |
| **6** | Click "Investigate Event" | Navigates to **Event Investigation HERO Page** (Split Map + Intelligence Panel). |
| **7** | Inspect Facility Context | Displays "Jamnagar Mega Refinery & Petrochemical Complex", 120m distance, Refineries type. |
| **8** | Inspect Land Cover | Displays "Industrial Built-up (78.5%)". |
| **9** | Inspect Event History | Temporal features card displays 34 active days / 30-day window, 112 detections / 90d. |
| **10** | Inspect Persistence Score | High persistence ratio (0.80) verified. |
| **11** | Inspect Facility Fingerprint | Displays normal baseline range (35–55 MW), current FRP (128.5 MW), and fingerprint quality. |
| **12** | Inspect Normal vs Current | Current FRP is within expected operational flaring envelope. |
| **13** | Inspect Anomaly Score | Displays **18.5 / 100** (NORMAL / Non-abnormal operating state). |
| **14** | Inspect Industrial Likelihood | Displays **96.5 / 100** (VERY HIGH industrial attribution). |
| **15** | Inspect Operational Risk | Displays **28.4 / 100** (LOW operational risk). |
| **16** | Open Evidence Panel | Displays Explainable Evidence Engine section. |
| **17** | Review Evidence FOR | Shows 4 positive factors (112 detections, 120m proximity, 78.5% industrial landcover, multi-sensor agreement). |
| **18** | Review Evidence AGAINST | Shows "Thermal intensity is within normal operating baseline envelope". |
| **19** | Review Data Limitations | Displays zero cloud contamination flags. |
| **20** | Review AI Probabilities | AI Probability breakdown shows **persistent_industrial_source (94.2%)**. |
| **21** | Select Case 2 (`TT-CASE-002`) | Opens **Punjab Stubble Burning** case. |
| **22** | Compare Natural/Agri Case | Shows 89.4% Cropland cover, 14.2 km distance from facility, low persistence (0.14), classified as **agricultural_burning (91.5%)**. |
| **23** | Select Case 3 (`TT-CASE-003`) | Opens **Ramgarh Mining Belt** ambiguous case. |
| **24** | Inspect UNKNOWN State | System displays **unknown_requires_verification (38.0%)**. Explains sparse observation + cloud obstruction. |
| **25** | Perform Analyst Action | Click "🔄 Reclassify", select `mining_or_other_industrial_activity`, enter rationale, submit. Status updates to `RECLASSIFIED`. |
| **26** | Open Alert Centre | Click "Alert Centre" in header. Table displays active alerts ordered by critical/high/medium priority. |
| **27** | Export Incident PDF / HTML | Click "Export Incident PDF / HTML" on `TT-CASE-001`. Opens branded incident report in new tab. |
| **28** | View AI Evaluation Page | Click "AI Evaluation" in header. Displays 7-model benchmark matrix (M4-B Winner: 70.0% Acc, 0.5879 F1) & ablation gains. |

---

## 🔒 Offline Demo Guarantee

All demonstration cases (`TT-CASE-001`, `TT-CASE-002`, `TT-CASE-003`) use cached local payloads in `backend/firms_data.json` and fallback JSON services. **The application will run 100% reliably without active internet connection.**
