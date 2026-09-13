# 🌐 ThermoTrace Frontend — Analyst Mission Control

> React 19 + TypeScript + Vite web client for the ThermoTrace Industrial Thermal Intelligence Platform.

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

## 📑 Application Structure

- **`src/pages/`**:
  - `Dashboard.tsx`: Executive KPI & threat tier distribution overview.
  - `ThermalMap.tsx`: Dark Canvas Leaflet map with satellite anomaly markers & API 521 perimeters.
  - `EventInvestigation.tsx`: Deep-dive investigation view with spectral analysis & evidence ledger.
  - `AIIntelligence.tsx`: 4-Engine model inspector, XAI feature attributions, and PyTorch LSTM trajectories.
  - `WhatIfSimulator.tsx`: Interactive hazard & Gaussian plume dispersion simulation workbench.
  - `ReportsView.tsx`: 19-Section intelligence report management & PDF dispatch console.
  - `DataReductionVisualizer.tsx`: 5-Stage interactive 99.98% noise filtration visualizer.
- **`src/components/`**:
  - `MapView.tsx`: Leaflet mapping component with custom styling & vector state boundaries.
  - `EventPanel.tsx`: Side drawer for rapid anomaly inspection.
  - `ui/`: Reusable cards, modal dialogs, scorebars, and timeline visualizers.
- **`src/services/`**:
  - `api.ts`: Centralized HTTP client connecting to FastAPI backend endpoints.
  - `alertEmail.ts`: Client-side notification and email dispatch helpers.
