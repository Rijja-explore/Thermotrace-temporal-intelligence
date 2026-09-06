from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from .api import events, facilities, alerts, reports

app = FastAPI(
    title="ThermoTrace Backend API",
    description="Explainable Geospatial Intelligence for Industrial Thermal Anomalies",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(facilities.router, prefix="/api/facilities", tags=["facilities"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])


@app.get("/health")
@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "thermotrace-api",
        "version": "1.0.0",
        "engine": "thermotrace-temporal-v1.0",
        "model": "M4-B_HistGradientBoosting_v1.0"
    }
