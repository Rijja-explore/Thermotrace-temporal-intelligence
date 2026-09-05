"""
Events API — list, search, detail, and analyst actions.
Falls back to JSON-based mock data when PostGIS is unavailable.
"""
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
import os

router = APIRouter()

# ═══════════════════════════════════════════
# MOCK DATA (used when DB is unavailable)
# ═══════════════════════════════════════════
MOCK_EVENTS = [
    {
        "event_id": "TT-IND-00427",
        "geometry": {"lat": 19.0760, "lon": 72.8777},
        "time_window": {"start": "2026-01-01T00:00:00Z", "end": "2026-01-30T23:59:59Z"},
        "observations": [{"frp": 42.5, "satellite": "VIIRS_SNPP", "acq_date": "2026-01-15"}, {"frp": 38.2, "satellite": "MODIS", "acq_date": "2026-01-20"}],
        "facility_context": {"nearby_refinery_km": 0.43, "name": "Mumbai Refinery Complex", "land_cover": "Industrial", "population_within_5km": 125000},
        "landcover_context": {"primary": "Industrial", "secondary": "Urban"},
        "temporal_features": {"baseline_frp_mean": 35.4, "baseline_frp_std": 8.2, "current_frp": 42.5, "deviation_sigma": 0.87, "detection_count_30d": 24, "persistence_ratio": 0.8},
        "classification": {"class": "Persistent industrial source", "confidence": 87},
        "scores": {"industrial_likelihood": 87, "operational_risk": 72},
        "evidence": ["24 detections / 30 days", "Stable centroid drift < 50m", "Facility proximity 0.43 km", "Night-time thermal persistence", "FRP consistent with refinery flaring"],
        "status": "requires_verification",
        "data_version": "demo-2026-01",
        "model_version": "hybrid-v1"
    },
    {
        "event_id": "TT-IND-00512",
        "geometry": {"lat": 22.5726, "lon": 88.3639},
        "time_window": {"start": "2026-02-10T00:00:00Z", "end": "2026-02-28T23:59:59Z"},
        "observations": [{"frp": 85.3, "satellite": "VIIRS_NOAA20", "acq_date": "2026-02-15"}],
        "facility_context": {"nearby_refinery_km": 2.1, "name": "Kolkata Industrial Zone", "land_cover": "Urban/Industrial", "population_within_5km": 340000},
        "landcover_context": {"primary": "Urban", "secondary": "Industrial"},
        "temporal_features": {"baseline_frp_mean": 12.1, "baseline_frp_std": 4.5, "current_frp": 85.3, "deviation_sigma": 16.27, "detection_count_30d": 8, "persistence_ratio": 0.27},
        "classification": {"class": "Anomalous Heat Signature", "confidence": 92},
        "scores": {"industrial_likelihood": 45, "operational_risk": 89},
        "evidence": ["Sudden temperature spike +180%", "High contrast with surroundings", "No scheduled maintenance", "Population exposure high"],
        "status": "critical_alert",
        "data_version": "demo-2026-01",
        "model_version": "hybrid-v1"
    },
    {
        "event_id": "TT-IND-00678",
        "geometry": {"lat": 13.0827, "lon": 80.2707},
        "time_window": {"start": "2026-03-01T00:00:00Z", "end": "2026-03-15T23:59:59Z"},
        "observations": [{"frp": 28.1, "satellite": "VIIRS_SNPP", "acq_date": "2026-03-05"}],
        "facility_context": {"nearby_refinery_km": 0.08, "name": "Chennai Petrochemical Complex", "land_cover": "Industrial Zone", "population_within_5km": 45000},
        "landcover_context": {"primary": "Industrial Zone", "secondary": "Coastal"},
        "temporal_features": {"baseline_frp_mean": 25.0, "baseline_frp_std": 5.0, "current_frp": 28.1, "deviation_sigma": 0.62, "detection_count_30d": 15, "persistence_ratio": 0.5},
        "classification": {"class": "Scheduled Flaring", "confidence": 95},
        "scores": {"industrial_likelihood": 98, "operational_risk": 20},
        "evidence": ["Matches flaring schedule", "Expected thermal footprint", "Facility operator confirmed", "Regular maintenance cycle"],
        "status": "monitored",
        "data_version": "demo-2026-01",
        "model_version": "hybrid-v1"
    },
    {
        "event_id": "TT-IND-00901",
        "geometry": {"lat": 26.8467, "lon": 80.9462},
        "time_window": {"start": "2026-01-20T00:00:00Z", "end": "2026-01-25T23:59:59Z"},
        "observations": [{"frp": 15.2, "satellite": "MODIS", "acq_date": "2026-01-22"}],
        "facility_context": {"nearby_refinery_km": 12.5, "name": "N/A", "land_cover": "Agricultural", "population_within_5km": 8000},
        "landcover_context": {"primary": "Agricultural", "secondary": "Rural"},
        "temporal_features": {"baseline_frp_mean": 8.0, "baseline_frp_std": 6.0, "current_frp": 15.2, "deviation_sigma": 1.2, "detection_count_30d": 5, "persistence_ratio": 0.17},
        "classification": {"class": "Agricultural Burning", "confidence": 78},
        "scores": {"industrial_likelihood": 5, "operational_risk": 55},
        "evidence": ["Seasonal pattern match", "Agricultural land cover", "Low industrial likelihood", "Widespread spatial pattern"],
        "status": "requires_verification",
        "data_version": "demo-2026-01",
        "model_version": "hybrid-v1"
    },
    {
        "event_id": "TT-IND-01102",
        "geometry": {"lat": 28.6139, "lon": 77.2090},
        "time_window": {"start": "2026-04-10T00:00:00Z", "end": "2026-04-14T23:59:59Z"},
        "observations": [{"frp": 22.0, "satellite": "VIIRS_NOAA21", "acq_date": "2026-04-12"}],
        "facility_context": {"nearby_refinery_km": 5.5, "name": "Delhi NCR Zone", "land_cover": "Urban", "population_within_5km": 500000},
        "landcover_context": {"primary": "Urban", "secondary": "Mixed"},
        "temporal_features": {"baseline_frp_mean": 5.0, "baseline_frp_std": 3.0, "current_frp": 22.0, "deviation_sigma": 5.67, "detection_count_30d": 3, "persistence_ratio": 0.1},
        "classification": {"class": "Unknown Subsurface Heat", "confidence": 65},
        "scores": {"industrial_likelihood": 30, "operational_risk": 60},
        "evidence": ["Diffused heat signature", "No surface structure correlated", "Subsurface investigation recommended", "Moderate risk level"],
        "status": "investigating",
        "data_version": "demo-2026-01",
        "model_version": "hybrid-v1"
    }
]


def _load_firms_json() -> list:
    """Attempt to load live FIRMS data from the fetcher output."""
    json_path = os.path.join(os.path.dirname(__file__), "..", "..", "firms_data.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                data = json.load(f)
            if data:
                return data
        except Exception as e:
            print(f"[events] Failed to read firms_data.json: {e}")
    return []


def _get_all_events() -> list:
    """Return live FIRMS data if loaded, otherwise fall back to demo events."""
    firms = _load_firms_json()
    if firms:
        return firms
    return MOCK_EVENTS


# ═══════════════════════════════════════════
# API ROUTES
# ═══════════════════════════════════════════

def _get_event_region(e: dict) -> str:
    """Determine event region accurately from metadata or event ID."""
    if e.get("region"):
        return e["region"]
    if e.get("event_id", "").startswith("TT-IND-"):
        return "India"
    return "Global"


def _filter_by_region(events: list, region: str) -> list:
    """
    Filter events by region.
    - 'All': returns all events.
    - 'India': returns all Indian events.
    - 'Global': returns events outside India.
    - Specific State/District: returns matching Indian events.
    """
    if not region or region.lower() == "all":
        return events

    target = region.strip().lower()

    if target == "india":
        return [e for e in events if _get_event_region(e).lower() == "india"]
    elif target in ("global", "world", "international"):
        return [e for e in events if _get_event_region(e).lower() != "india"]
    else:
        # Check specific Indian state, district, or facility name
        return [
            e for e in events
            if _get_event_region(e).lower() == "india" and (
                target in e.get("facility_context", {}).get("state", "").lower() or
                target in e.get("facility_context", {}).get("district", "").lower() or
                target in e.get("facility_context", {}).get("name", "").lower()
            )
        ]



@router.get("/")
async def list_events(
    status: Optional[str] = Query(None, description="Filter by status"),
    risk_min: Optional[int] = Query(None, description="Min operational risk"),
    event_class: Optional[str] = Query(None, description="Filter by classification class"),
    region: str = Query("India", description="Region filter: India, Global, or All"),
    limit: int = Query(500, le=5000),
    offset: int = Query(0, ge=0),
):
    """List thermal events with optional filters. Defaults to India region."""
    events = _get_all_events()
    events = _filter_by_region(events, region)

    if status:
        events = [e for e in events if e.get("status") == status]
    if risk_min is not None:
        events = [e for e in events if (e.get("scores", {}).get("operational_risk", 0)) >= risk_min]
    if event_class:
        events = [e for e in events if event_class.lower() in (e.get("classification", {}).get("class", "")).lower()]

    total = len(events)
    paginated = events[offset:offset + limit]

    return {"total": total, "offset": offset, "limit": limit, "region": region, "events": paginated}


@router.get("/summary")
async def events_summary(
    region: str = Query("India", description="Region filter: India, Global, or All"),
):
    """Dashboard summary statistics, filtered by region."""
    events = _filter_by_region(_get_all_events(), region)
    total = len(events)
    critical = len([e for e in events if e.get("scores", {}).get("operational_risk", 0) >= 80])
    high = len([e for e in events if 60 <= e.get("scores", {}).get("operational_risk", 0) < 80])
    industrial = len([e for e in events if e.get("scores", {}).get("industrial_likelihood", 0) >= 70])
    persistent = len([e for e in events if e.get("temporal_features", {}).get("persistence_ratio", 0) >= 0.5])
    abnormal = len([e for e in events if e.get("temporal_features", {}).get("deviation_sigma", 0) >= 3.0])
    unknown = len([e for e in events if "unknown" in (e.get("classification", {}).get("class", "")).lower()])
    requires_verification = len([e for e in events if e.get("status") == "requires_verification"])

    by_status = {}
    for e in events:
        s = e.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1

    return {
        "total": total,
        "critical": critical,
        "high": high,
        "industrial": industrial,
        "persistent": persistent,
        "abnormal": abnormal,
        "unknown": unknown,
        "requires_verification": requires_verification,
        "by_status": by_status,
        "region": region,
    }


@router.get("/live-status")
async def live_status():
    """Check the freshness and source metadata of currently loaded FIRMS satellite data."""
    events = _load_firms_json()
    if not events:
        return {"status": "no_data", "is_live": False, "total": 0}

    india_events = [e for e in events if e.get("region") == "India"]
    dates = sorted(list({obs.get("acq_date") for e in events for obs in e.get("observations", [])}))
    sats = sorted(list({obs.get("satellite") for e in events for obs in e.get("observations", [])}))

    return {
        "status": "active_live",
        "is_live": True,
        "source": "NASA FIRMS (EOSDIS) Near-Real-Time Active Fire Feeds",
        "satellites": sats,
        "acquisition_dates": dates,
        "total_canonical_events": len(events),
        "india_events": len(india_events),
        "global_events": len(events) - len(india_events),
        "update_frequency": "Every 3-4 hours as satellites complete polar overpasses",
    }


@router.post("/sync")
async def sync_live_firms():
    """Trigger an instant pull of the latest 24h satellite detections from NASA FIRMS."""
    try:
        import sys
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
        import fetch_live_data
        count = fetch_live_data.fetch_and_save_all()
        return {
            "status": "success",
            "message": f"Successfully ingested {count} live satellite events from NASA FIRMS",
            "total": count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch live FIRMS data: {str(e)}")


@router.get("/{event_id}")
async def get_event(event_id: str):
    """Get detailed information for a single event."""
    for event in _get_all_events():
        if event.get("event_id") == event_id:
            return event
    raise HTTPException(status_code=404, detail=f"Event {event_id} not found")


class AnalystAction(BaseModel):
    action: str  # confirm, reject, reclassify
    new_status: Optional[str] = None
    new_class: Optional[str] = None
    notes: Optional[str] = None
    analyst: str = "demo-analyst"


@router.post("/{event_id}/action")
async def event_action(event_id: str, body: AnalystAction):
    """
    Record an analyst decision on an event.
    In a real system this updates PostGIS; here we update the in-memory mock.
    """
    for event in MOCK_EVENTS:
        if event.get("event_id") == event_id:
            old_status = event["status"]
            if body.action == "confirm":
                event["status"] = "confirmed"
            elif body.action == "reject":
                event["status"] = "rejected"
            elif body.action == "reclassify":
                if body.new_class:
                    event["classification"]["class"] = body.new_class
                if body.new_status:
                    event["status"] = body.new_status
                else:
                    event["status"] = "reclassified"
            else:
                event["status"] = body.new_status or event["status"]

            return {
                "success": True,
                "event_id": event_id,
                "old_status": old_status,
                "new_status": event["status"],
                "action": body.action,
                "analyst": body.analyst,
                "notes": body.notes,
            }

    raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
