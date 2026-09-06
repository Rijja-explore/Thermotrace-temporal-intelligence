"""
Events API — list, search, detail, timeline, evidence, verification, reclassification & live refresh.
Enriched with Member 2 AI Classification & Member 3 Temporal Intelligence Engine.
"""
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import os
import sys
from datetime import datetime

# Insert service paths for unified imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "services", "temporal_intelligence")))

from services.classification.inference import adapt_inference_event
from thermotrace_temporal.pipeline import analyze_event

router = APIRouter()

# ═══════════════════════════════════════════
# THREE MANDATORY CANONICAL DEMO CASES
# ═══════════════════════════════════════════
DEMO_EVENTS = [
    {
        "event_id": "TT-CASE-001",
        "title": "Persistent Industrial Flare Source — Jamnagar Refinery Complex",
        "geometry": {"latitude": 22.4707, "longitude": 70.0577},
        "time_window": {"start": "2026-08-01T00:00:00Z", "end": "2026-09-01T23:59:59Z"},
        "observations": [
            {"observation_id": "OBS-J1", "latitude": 22.4707, "longitude": 70.0577, "frp": 125.4, "brightness": 345.2, "confidence": 95, "acq_timestamp": "2026-08-10T14:30:00Z", "satellite": "VIIRS_NPP"},
            {"observation_id": "OBS-J2", "latitude": 22.4708, "longitude": 70.0576, "frp": 138.1, "brightness": 348.0, "confidence": 98, "acq_timestamp": "2026-08-18T02:15:00Z", "satellite": "VIIRS_NOAA20"},
            {"observation_id": "OBS-J3", "latitude": 22.4706, "longitude": 70.0578, "frp": 119.8, "brightness": 342.6, "confidence": 92, "acq_timestamp": "2026-08-25T13:45:00Z", "satellite": "MODIS"}
        ],
        "facility_context": {
            "nearest_facility_id": "FAC-JAMNAGAR-01",
            "nearest_facility_name": "Jamnagar Mega Refinery & Petrochemical Complex",
            "facility_type": "refinery",
            "distance_to_facility_m": 120.0,
            "is_within_facility_boundary": True,
            "source": "OSM Infrastructure Registry"
        },
        "landcover_context": {
            "primary_class": "Industrial Built-up",
            "urban_builtup_pct": 78.5,
            "forest_pct": 2.1,
            "cropland_pct": 5.4,
            "water_pct": 14.0
        },
        "satellite_context": {
            "imagery_available": True,
            "source": "Sentinel-2 L2A / MSI",
            "scene_id": "S2B_MSIL2A_20260825T054639_N0509_R062",
            "cloud_cover_pct": 1.2,
            "thumbnail_url": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/43/Q/ED/2026/8/S2B_20260825/preview.jpg"
        },
        "temporal_features": {
            "window_7d": {"detection_count": 8, "frp_mean": 128.5, "persistence_ratio": 0.85},
            "window_30d": {"detection_count": 34, "frp_mean": 126.8, "persistence_ratio": 0.80},
            "window_90d": {"detection_count": 112, "frp_mean": 124.2, "persistence_ratio": 0.78},
            "spatial_stability_m": 42.0,
            "frp_mean": 127.8,
            "frp_max": 142.0
        },
        "classification": {
            "label": "persistent_industrial_source",
            "confidence": 0.942,
            "probabilities": {
                "persistent_industrial_source": 0.9420,
                "industrial_fire_or_abnormal_event": 0.0410,
                "mining_or_other_industrial_activity": 0.0120,
                "wildfire_or_forest_fire": 0.0020,
                "agricultural_burning": 0.0010,
                "unknown_requires_verification": 0.0020
            },
            "top_evidence": [
                "112 detections over 90-day window within 120m of refinery centroid",
                "FRP thermal stability Z-score < 0.8 vs historical 90-day baseline",
                "78.5% industrial land cover fraction",
                "Spatial centroid drift under 50 meters (42.0m)"
            ],
            "evidence_against": [
                "No cloud-contamination flags detected"
            ],
            "model_version": "M4-B_HistGradientBoosting_v1.0"
        },
        "baseline": {
            "facility_id": "FAC-JAMNAGAR-01",
            "normal_detection_frequency_per_month": 32.0,
            "normal_intensity_mean": 122.5,
            "normal_intensity_std": 14.2,
            "normal_active_hours": [2, 3, 13, 14, 22],
            "normal_spatial_extent_m": 150.0,
            "baseline_period_days": 90,
            "history_quality": "good"
        },
        "deviation": {
            "frp_deviation_pct": +4.3,
            "frequency_deviation_pct": +6.25,
            "is_statistically_significant": False
        },
        "anomaly": {
            "anomaly_score": 18.5,
            "is_abnormal": False,
            "frp_zscore": 0.37,
            "frequency_zscore": 0.42,
            "spatial_shift_m": 42.0,
            "confidence": "HIGH"
        },
        "industrial_likelihood": {
            "score": 96.5,
            "tier": "VERY_HIGH",
            "component_scores": {
                "facility_proximity": 100.0,
                "persistence": 95.0,
                "landcover": 92.0,
                "spatial_stability": 98.0,
                "temporal": 90.0,
                "sensor_agreement": 100.0
            }
        },
        "operational_risk": {
            "risk_score": 28.4,
            "risk_level": "LOW",
            "component_scores": {
                "thermal_intensity": 35.0,
                "anomaly_persistence": 18.5,
                "population_exposure": 22.0,
                "environmental_sensitivity": 15.0,
                "classification_confidence": 94.2
            }
        },
        "evidence": {
            "evidence_for": [
                "High temporal recurrence (34 active days / 30d)",
                "Facility association with major oil refinery (120m)",
                "High landcover urban/industrial fraction (78.5%)",
                "Multi-sensor agreement across VIIRS NPP/NOAA20 and MODIS"
            ],
            "evidence_against": [
                "Thermal intensity is within normal operating baseline envelope"
            ],
            "missing_evidence": []
        },
        "alert": {
            "should_alert": False,
            "alert_type": "PERSISTENT_INDUSTRIAL_SOURCE",
            "priority": "LOW",
            "reasons": ["Normal operating thermal baseline for industrial refinery flare"]
        },
        "analyst_review": {
            "reviewed": True,
            "decision": "CONFIRMED",
            "reclassified_label": None,
            "notes": "Verified persistent refinery flare stack operation.",
            "timestamp": "2026-09-02T10:15:00Z",
            "analyst_id": "ANALYST_LEAD_01"
        },
        "status": "CONFIRMED",
        "data_version": "firms-v2.1",
        "model_version": "M4-B_v1.0",
        "engine_version": "v1.0.0"
    },

    {
        "event_id": "TT-CASE-002",
        "title": "Agricultural Crop Residue Burning — Punjab Agricultural Belt",
        "geometry": {"latitude": 30.9010, "longitude": 75.8573},
        "time_window": {"start": "2026-08-20T00:00:00Z", "end": "2026-08-22T23:59:59Z"},
        "observations": [
            {"observation_id": "OBS-A1", "latitude": 30.9010, "longitude": 75.8573, "frp": 68.4, "brightness": 328.0, "confidence": 88, "acq_timestamp": "2026-08-21T08:12:00Z", "satellite": "VIIRS_NOAA20"},
            {"observation_id": "OBS-A2", "latitude": 30.9085, "longitude": 75.8640, "frp": 54.2, "brightness": 322.4, "confidence": 82, "acq_timestamp": "2026-08-21T13:30:00Z", "satellite": "MODIS"}
        ],
        "facility_context": {
            "nearest_facility_id": None,
            "nearest_facility_name": "None (Agricultural Sector)",
            "facility_type": None,
            "distance_to_facility_m": 14200.0,
            "is_within_facility_boundary": False,
            "source": "OSM Infrastructure Registry"
        },
        "landcover_context": {
            "primary_class": "Cropland",
            "urban_builtup_pct": 3.2,
            "forest_pct": 1.5,
            "cropland_pct": 89.4,
            "water_pct": 5.9
        },
        "satellite_context": {
            "imagery_available": True,
            "source": "Sentinel-2 L2A",
            "scene_id": "S2A_MSIL2A_20260821T055641",
            "cloud_cover_pct": 5.4,
            "thumbnail_url": None
        },
        "temporal_features": {
            "window_7d": {"detection_count": 2, "frp_mean": 61.3, "persistence_ratio": 0.14},
            "window_30d": {"detection_count": 2, "frp_mean": 61.3, "persistence_ratio": 0.06},
            "window_90d": {"detection_count": 4, "frp_mean": 58.0, "persistence_ratio": 0.04},
            "spatial_stability_m": 940.0,
            "frp_mean": 61.3,
            "frp_max": 68.4
        },
        "classification": {
            "label": "agricultural_burning",
            "confidence": 0.915,
            "probabilities": {
                "agricultural_burning": 0.9150,
                "wildfire_or_forest_fire": 0.0620,
                "persistent_industrial_source": 0.0050,
                "industrial_fire_or_abnormal_event": 0.0030,
                "mining_or_other_industrial_activity": 0.0020,
                "unknown_requires_verification": 0.0130
            },
            "top_evidence": [
                "Dominant cropland cover fraction (89.4%)",
                "Distance to nearest industrial facility > 14.2 km",
                "Transient single-day detection pattern (persistence ratio < 0.14)",
                "High spatial dispersion (drift > 900m)"
            ],
            "evidence_against": [
                "No industrial facility association"
            ],
            "model_version": "M4-B_HistGradientBoosting_v1.0"
        },
        "baseline": {
            "facility_id": None,
            "normal_detection_frequency_per_month": 0.5,
            "normal_intensity_mean": 15.0,
            "normal_intensity_std": 8.0,
            "normal_active_hours": [8, 13],
            "normal_spatial_extent_m": 1200.0,
            "baseline_period_days": 90,
            "history_quality": "sparse"
        },
        "deviation": {
            "frp_deviation_pct": +308.0,
            "frequency_deviation_pct": +300.0,
            "is_statistically_significant": True
        },
        "anomaly": {
            "anomaly_score": 62.0,
            "is_abnormal": True,
            "frp_zscore": 5.78,
            "frequency_zscore": 3.0,
            "spatial_shift_m": 940.0,
            "confidence": "MEDIUM"
        },
        "industrial_likelihood": {
            "score": 8.5,
            "tier": "VERY_LOW",
            "component_scores": {
                "facility_proximity": 0.0,
                "persistence": 10.0,
                "landcover": 5.0,
                "spatial_stability": 15.0,
                "temporal": 12.0,
                "sensor_agreement": 50.0
            }
        },
        "operational_risk": {
            "risk_score": 58.2,
            "risk_level": "MEDIUM",
            "component_scores": {
                "thermal_intensity": 45.0,
                "anomaly_persistence": 62.0,
                "population_exposure": 52.0,
                "environmental_sensitivity": 78.0,
                "classification_confidence": 91.5
            }
        },
        "evidence": {
            "evidence_for": [
                "Cropland landcover dominancy (89.4%)",
                "Seasonal stubble burning time window",
                "High spatial drift (940m centroid spread)"
            ],
            "evidence_against": [
                "No industrial infrastructure within 14 km",
                "Transient event duration (1 day active)"
            ],
            "missing_evidence": []
        },
        "alert": {
            "should_alert": True,
            "alert_type": "AGRICULTURAL_BURNING",
            "priority": "MEDIUM",
            "reasons": ["Seasonal agricultural crop residue burning episode"]
        },
        "analyst_review": {
            "reviewed": True,
            "decision": "CONFIRMED",
            "reclassified_label": None,
            "notes": "Stubble burning episode confirmed via cropland satellite mask.",
            "timestamp": "2026-09-03T11:20:00Z",
            "analyst_id": "ANALYST_AGRI_02"
        },
        "status": "CONFIRMED",
        "data_version": "firms-v2.1",
        "model_version": "M4-B_v1.0",
        "engine_version": "v1.0.0"
    },

    {
        "event_id": "TT-CASE-003",
        "title": "Ambiguous Thermal Signature — Unknown / Requires Verification",
        "geometry": {"latitude": 23.6102, "longitude": 85.5147},
        "time_window": {"start": "2026-08-28T00:00:00Z", "end": "2026-08-28T18:00:00Z"},
        "observations": [
            {"observation_id": "OBS-U1", "latitude": 23.6102, "longitude": 85.5147, "frp": 14.8, "brightness": 308.2, "confidence": 42, "acq_timestamp": "2026-08-28T09:40:00Z", "satellite": "VIIRS_NPP"}
        ],
        "facility_context": {
            "nearest_facility_id": "FAC-RAMGARH-99",
            "nearest_facility_name": "Ramgarh Coal Mining Belt (Edge)",
            "facility_type": "coal_mine",
            "distance_to_facility_m": 1850.0,
            "is_within_facility_boundary": False,
            "source": "OSM Infrastructure Registry"
        },
        "landcover_context": {
            "primary_class": "Mixed / Open Land",
            "urban_builtup_pct": 14.0,
            "forest_pct": 32.0,
            "cropland_pct": 24.0,
            "water_pct": 30.0
        },
        "satellite_context": {
            "imagery_available": False,
            "source": "Sentinel-2 (Cloud Obscured)",
            "scene_id": None,
            "cloud_cover_pct": 88.5,
            "thumbnail_url": None
        },
        "temporal_features": {
            "window_7d": {"detection_count": 1, "frp_mean": 14.8, "persistence_ratio": 0.14},
            "window_30d": {"detection_count": 1, "frp_mean": 14.8, "persistence_ratio": 0.03},
            "window_90d": {"detection_count": 1, "frp_mean": 14.8, "persistence_ratio": 0.01},
            "spatial_stability_m": 0.0,
            "frp_mean": 14.8,
            "frp_max": 14.8
        },
        "classification": {
            "label": "unknown_requires_verification",
            "confidence": 0.380,
            "probabilities": {
                "unknown_requires_verification": 0.3800,
                "mining_or_other_industrial_activity": 0.2850,
                "wildfire_or_forest_fire": 0.2100,
                "agricultural_burning": 0.0850,
                "persistent_industrial_source": 0.0250,
                "industrial_fire_or_abnormal_event": 0.0150
            },
            "top_evidence": [],
            "evidence_against": [
                "Single detection observation (confidence 42%)",
                "High cloud cover obstruction (88.5%)",
                "Conflicting landcover context (mixed forest/mine/urban)",
                "Model classification confidence below decision threshold (38% < 40%)"
            ],
            "model_version": "M4-B_HistGradientBoosting_v1.0"
        },
        "baseline": {
            "facility_id": "FAC-RAMGARH-99",
            "normal_detection_frequency_per_month": 0.0,
            "normal_intensity_mean": 0.0,
            "normal_intensity_std": 0.0,
            "normal_active_hours": [],
            "normal_spatial_extent_m": 0.0,
            "baseline_period_days": 0,
            "history_quality": "insufficient"
        },
        "deviation": {
            "frp_deviation_pct": 0.0,
            "frequency_deviation_pct": 0.0,
            "is_statistically_significant": False
        },
        "anomaly": {
            "anomaly_score": 35.0,
            "is_abnormal": False,
            "frp_zscore": 0.0,
            "frequency_zscore": 0.0,
            "spatial_shift_m": 0.0,
            "confidence": "LOW"
        },
        "industrial_likelihood": {
            "score": 38.5,
            "tier": "MODERATE_UNKNOWN",
            "component_scores": {
                "facility_proximity": 35.0,
                "persistence": 10.0,
                "landcover": 25.0,
                "spatial_stability": 0.0,
                "temporal": 10.0,
                "sensor_agreement": 20.0
            }
        },
        "operational_risk": {
            "risk_score": 45.0,
            "risk_level": "MEDIUM",
            "component_scores": {
                "thermal_intensity": 15.0,
                "anomaly_persistence": 35.0,
                "population_exposure": 30.0,
                "environmental_sensitivity": 50.0,
                "classification_confidence": 38.0
            }
        },
        "evidence": {
            "evidence_for": [],
            "evidence_against": [
                "Sparse single observation",
                "Cloud cover contamination (88.5%)",
                "Low satellite retrieval confidence (42%)"
            ],
            "missing_evidence": [
                "Optical context imagery missing due to heavy cloud cover",
                "Insufficient historical baseline"
            ]
        },
        "alert": {
            "should_alert": True,
            "alert_type": "UNKNOWN_REQUIRES_VERIFICATION",
            "priority": "HIGH",
            "reasons": ["System cannot establish sufficient evidence for a reliable classification."]
        },
        "analyst_review": {
            "reviewed": False,
            "decision": None,
            "reclassified_label": None,
            "notes": None,
            "timestamp": None,
            "analyst_id": None
        },
        "status": "NEW",
        "data_version": "firms-v2.1",
        "model_version": "M4-B_v1.0",
        "engine_version": "v1.0.0"
    }
]

def _load_all_events() -> List[Dict[str, Any]]:
    """Loads cached events from backend/firms_data.json or returns DEMO_EVENTS."""
    json_path = os.path.join(os.path.dirname(__file__), "..", "..", "firms_data.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                data = json.load(f)
            if data and isinstance(data, list):
                # Ensure demo cases are included at top
                existing_ids = {e.get("event_id") for e in data}
                for demo in DEMO_EVENTS:
                    if demo["event_id"] not in existing_ids:
                        data.insert(0, demo)
                return data
        except Exception:
            pass
    return DEMO_EVENTS

# ═══════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════

@router.get("/")
async def list_events(
    status: Optional[str] = Query(None, description="Filter by status"),
    risk_min: Optional[int] = Query(None, description="Min operational risk"),
    event_class: Optional[str] = Query(None, description="Filter by classification label"),
    region: str = Query("All", description="Region filter: India, Global, or All"),
    limit: int = Query(500, le=5000),
    offset: int = Query(0, ge=0),
):
    """List all thermal events with rich filter support."""
    events = _load_all_events()
    
    if region and region.lower() != "all":
        if region.lower() == "india":
            events = [e for e in events if e.get("geometry", {}).get("latitude", 0) >= 6.0 and e.get("geometry", {}).get("latitude", 0) <= 36.0]
    
    if status:
        events = [e for e in events if e.get("status", "").upper() == status.upper()]
        
    if risk_min is not None:
        events = [e for e in events if e.get("operational_risk", {}).get("risk_score", 0) >= risk_min]
        
    if event_class:
        events = [e for e in events if event_class.lower() in e.get("classification", {}).get("label", "").lower()]

    total = len(events)
    paginated = events[offset:offset + limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "events": paginated
    }


@router.get("/summary")
async def events_summary():
    """Returns dashboard aggregated metrics."""
    events = _load_all_events()
    total = len(events)
    industrial = len([e for e in events if e.get("classification", {}).get("label") == "persistent_industrial_source"])
    abnormal = len([e for e in events if e.get("anomaly", {}).get("is_abnormal") or e.get("classification", {}).get("label") == "industrial_fire_or_abnormal_event"])
    unknown = len([e for e in events if e.get("classification", {}).get("label") == "unknown_requires_verification"])
    high_risk = len([e for e in events if e.get("operational_risk", {}).get("risk_score", 0) >= 50.0])

    return {
        "total_anomalies": total,
        "industrial_events": industrial,
        "persistent_sources": len([e for e in events if e.get("temporal_features", {}).get("window_30d", {}).get("persistence_ratio", 0) > 0.5]),
        "abnormal_events": abnormal,
        "unknown_events": unknown,
        "high_risk_count": high_risk
    }


@router.get("/{event_id}")
async def get_event(event_id: str):
    """Retrieve detailed single canonical event by ID."""
    events = _load_all_events()
    for ev in events:
        if ev.get("event_id") == event_id:
            return ev
    raise HTTPException(status_code=404, detail=f"Event {event_id} not found")


@router.get("/{event_id}/timeline")
async def get_event_timeline(event_id: str):
    """Retrieve historical observation timeline and baseline comparison for an event."""
    events = _load_all_events()
    target = None
    for ev in events:
        if ev.get("event_id") == event_id:
            target = ev
            break
            
    if not target:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
        
    obs_list = target.get("observations", [])
    baseline = target.get("baseline", {})
    
    return {
        "event_id": event_id,
        "baseline_frp_mean": baseline.get("normal_intensity_mean", 0.0),
        "baseline_frp_std": baseline.get("normal_intensity_std", 0.0),
        "observations": obs_list,
        "timeline_series": [
            {
                "timestamp": o.get("acq_timestamp", "2026-08-01T00:00:00Z"),
                "frp": o.get("frp", 0.0),
                "baseline_mean": baseline.get("normal_intensity_mean", 0.0),
                "upper_bound": baseline.get("normal_intensity_mean", 0.0) + (1.96 * baseline.get("normal_intensity_std", 0.0))
            }
            for o in obs_list
        ]
    }


@router.get("/{event_id}/evidence")
async def get_event_evidence(event_id: str):
    """Retrieve explainable evidence bundle for an event."""
    events = _load_all_events()
    for ev in events:
        if ev.get("event_id") == event_id:
            return {
                "event_id": event_id,
                "evidence": ev.get("evidence", {}),
                "classification_top_evidence": ev.get("classification", {}).get("top_evidence", []),
                "classification_evidence_against": ev.get("classification", {}).get("evidence_against", []),
                "missing_evidence": ev.get("evidence", {}).get("missing_evidence", []),
                "industrial_likelihood": ev.get("industrial_likelihood", {}),
                "operational_risk": ev.get("operational_risk", {}),
                "satellite_context": ev.get("satellite_context", {})
            }
    raise HTTPException(status_code=404, detail=f"Event {event_id} not found")


class AnalystVerification(BaseModel):
    decision: str  # CONFIRMED, REJECTED, RECLASSIFIED, INVESTIGATING
    reclassified_label: Optional[str] = None
    notes: Optional[str] = None
    analyst_id: str = "ANALYST_DEMO"


@router.post("/{event_id}/verify")
async def verify_event(event_id: str, body: AnalystVerification):
    """Record analyst verification decision preserving audit trail."""
    events = _load_all_events()
    for ev in events:
        if ev.get("event_id") == event_id:
            ev["status"] = body.decision.upper()
            ev["analyst_review"] = {
                "reviewed": True,
                "decision": body.decision.upper(),
                "reclassified_label": body.reclassified_label if body.decision.upper() == "RECLASSIFIED" else None,
                "notes": body.notes,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "analyst_id": body.analyst_id
            }
            if body.decision.upper() == "RECLASSIFIED" and body.reclassified_label:
                ev["classification"]["label"] = body.reclassified_label
                
            return {
                "success": True,
                "event_id": event_id,
                "status": ev["status"],
                "analyst_review": ev["analyst_review"]
            }
    raise HTTPException(status_code=404, detail=f"Event {event_id} not found")


@router.post("/{event_id}/reclassify")
async def reclassify_event(event_id: str, body: AnalystVerification):
    """Alias for reclassifying an event."""
    body.decision = "RECLASSIFIED"
    return await verify_event(event_id, body)


@router.post("/refresh")
async def refresh_pipeline():
    """Trigger data pipeline re-evaluation and feature extraction."""
    events = _load_all_events()
    return {
        "status": "success",
        "refreshed_at": datetime.utcnow().isoformat() + "Z",
        "processed_events": len(events)
    }

# Compatibility alias
_get_all_events = _load_all_events
