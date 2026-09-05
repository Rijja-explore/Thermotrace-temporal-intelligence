# ThermoTrace - Temporal Intelligence Platform

![ThermoTrace](https://img.shields.io/badge/Status-Live_Data_Active-brightgreen)
![Tech Stack](https://img.shields.io/badge/Stack-React_|_FastAPI_|_Cesium_|_Python-blue)

ThermoTrace is a comprehensive GIS Platform, Backend API, and Product UI designed to ingest, monitor, and classify thermal anomalies globally using live NASA FIRMS (Fire Information for Resource Management System) data. 

This platform sits as an intelligence layer above raw satellite detections, providing:
1. **Context**: Overlaying active fires and thermal detections on industrial facilities and infrastructure using Google Photorealistic 3D Tiles.
2. **Classification**: Distinguishing between natural wildfires, persistent industrial sources, and high-risk abnormal events.
3. **Analyst Workflow**: A command dashboard for analysts to investigate evidence, verify risks, and generate incident reports.

## 🌟 Key Features

- **Live 24h NASA Ingestion**: Automatically fetches, geocodes, and clusters real-time global thermal detections from MODIS and VIIRS satellites.
- **3D GIS Dashboard**: An interactive web globe powered by Cesium and Google 3D Tiles to visualize heat signatures and facility proximities in full 3D space.
- **Temporal Fingerprinting**: Analyzes a 30-day thermal baseline to detect deviations and anomalies that could indicate operational risk or disasters.
- **Automated Evidence Collection**: Generates human-readable evidence factors (e.g., "High thermal intensity spike", "Landscape Classification: Forest Reserve").
- **Incident Reporting**: Allows analysts to generate printable, structured incident reports directly from the UI without needing a terminal or notebooks.

## 🛠 Tech Stack

### Frontend (`/frontend`)
- **Framework**: React 18 with Vite
- **Language**: TypeScript
- **GIS/Mapping**: CesiumJS (with Google Photorealistic 3D Tiles)
- **Styling**: Tailwind CSS / Custom Vanilla CSS (Dark Glassmorphism UI)
- **Charts**: Recharts (for temporal baseline analysis)

### Backend (`/backend`)
- **Framework**: FastAPI (Python 3.12+)
- **Data Ingestion**: Custom pipeline for NASA FIRMS CSV parsing, DBScan spatial clustering, and temporal analysis.
- **Data Storage**: JSON / PostGIS (schema provided)
- **Deployment**: Docker Compose ready

## 🚀 Getting Started

### 1. Live Data Ingestion
The system relies on live data from NASA. To start the continuous background ingestion loop (which updates the database every hour):

```bash
python fetch_live_data.py
```

### 2. Run the Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
The API documentation will be available at `http://localhost:8000/docs`.

### 3. Run the Frontend (React)
```bash
cd frontend
npm install
npm run dev
```
Navigate to `http://localhost:5173` to access the Command Dashboard.

## 📂 Repository Structure

```
├── fetch_live_data.py       # Background daemon for LIVE NASA FIRMS data pull & clustering
├── backend/                 # FastAPI Application
│   ├── app/main.py          # API entrypoint
│   ├── app/api/             # Routes (events, facilities, alerts, reports)
│   └── app/services/        # Pipeline & temporal logic
├── frontend/                # React Vite Application
│   ├── src/pages/           # Dashboard, Event Investigation, Alerts
│   ├── src/components/      # MapView (Cesium), EventPanel, TimelineChart
│   └── src/index.css        # Core design system and animations
├── database/                # PostGIS schema and seed scripts
└── docker-compose.yml       # Production deployment config
```

## 🎯 Definition of Done

This system serves as a judge-friendly investigation platform. An analyst or judge can open the web application, select a live thermal event on the 3D globe, inspect facility context, review classification evidence and historical risk, make an analyst decision, and generate an incident report—all entirely through the UI.
