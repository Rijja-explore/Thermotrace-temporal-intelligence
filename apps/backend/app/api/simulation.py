"""
What-If Scenario Simulation & Counterfactual Threat Modelling Engine.
Calculates thermal radiation hazard envelopes, weather-driven dispersion cones,
operational risk scores, and mitigation SOP effectiveness.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import math

router = APIRouter()

class WhatIfSimulationRequest(BaseModel):
    event_id: Optional[str] = "TT-CASE-001"
    facility_name: Optional[str] = "Jamnagar Mega Refinery Complex"
    baseline_frp: float = Field(122.5, description="Historical normal FRP in MW")
    simulated_frp: float = Field(280.0, description="Simulated FRP thermal spike in MW")
    duration_hours: float = Field(12.0, description="Simulated persistence duration")
    wind_speed_kmh: float = Field(25.0, description="Wind speed in km/h")
    wind_direction_deg: float = Field(220.0, description="Wind direction (degrees)")
    population_distance_km: float = Field(2.5, description="Distance to nearest residential zone")
    atmospheric_inversion: bool = Field(False, description="Thermal inversion trapping plume")
    # Mitigation Measures
    mitigation_fgrs: bool = Field(False, description="Flare Gas Recovery System active (-45% FRP)")
    mitigation_deluge: bool = Field(False, description="Water / Nitrogen Deluge active (-30% radiation)")
    mitigation_esd: bool = Field(False, description="Emergency Shutdown ESD-1 (-60% baseline deviation)")
    mitigation_evac: bool = Field(False, description="Evacuation / Shelter-in-Place triggered")
    mitigation_uav: bool = Field(False, description="High-res drone UAV dispatched for ground confirmation")

class WhatIfSimulationResponse(BaseModel):
    baseline_risk_score: float
    simulated_risk_score: float
    mitigated_risk_score: float
    risk_level: str
    effective_frp: float
    frp_deviation_pct: float
    thermal_hazard_radius_m: float  # 4.7 kW/m2 threshold
    public_safety_radius_m: float   # 1.6 kW/m2 threshold
    plume_dispersion_length_km: float
    population_threat_index: float
    anomaly_probability: float
    mitigation_impact_pct: float
    recommended_sop: List[Dict[str, Any]]
    counterfactual_deltas: Dict[str, Any]


def calculate_simulation(req: WhatIfSimulationRequest) -> Dict[str, Any]:
    # 1. Calculate effective FRP after active mitigations
    effective_frp = req.simulated_frp
    frp_reduction_pct = 0.0

    if req.mitigation_fgrs:
        frp_reduction_pct += 45.0
    if req.mitigation_deluge:
        frp_reduction_pct += 25.0
    if req.mitigation_esd:
        frp_reduction_pct += 35.0

    # Cap mitigation reduction at 85%
    frp_reduction_pct = min(85.0, frp_reduction_pct)
    effective_frp = max(req.baseline_frp * 0.5, req.simulated_frp * (1.0 - frp_reduction_pct / 100.0))

    # FRP deviation vs baseline
    base_frp = max(1.0, req.baseline_frp)
    frp_dev_pct = ((effective_frp - base_frp) / base_frp) * 100.0
    raw_frp_dev_pct = ((req.simulated_frp - base_frp) / base_frp) * 100.0

    # 2. Thermal radiation hazard envelope (Point source approximation: q = eta * Q / (4 * pi * r^2))
    # Radiative fraction ~0.25 to 0.35 for industrial flaring
    rad_fraction = 0.30
    # Q in kW = FRP_MW * 1000
    q_kw = effective_frp * 1000.0 * rad_fraction
    
    # Radius for 4.7 kW/m2 (Threshold for pain/blisters within 20s):
    # r = sqrt(q_kw / (4 * pi * 4.7))
    r_4_7 = math.sqrt(max(10.0, q_kw / (4.0 * math.pi * 4.7)))
    # Radius for 1.6 kW/m2 (Safe public continuous exposure limit):
    r_1_6 = math.sqrt(max(20.0, q_kw / (4.0 * math.pi * 1.6)))

    # Wind tilt impact on hazard envelope
    wind_factor = 1.0 + (req.wind_speed_kmh / 80.0) * 0.4
    hazard_radius_m = round(r_4_7 * wind_factor, 1)
    safety_radius_m = round(r_1_6 * wind_factor, 1)

    # 3. Downwind Plume Dispersion Length (Gaussian puff approximation)
    inversion_multiplier = 1.65 if req.atmospheric_inversion else 1.0
    plume_length_km = round(
        (req.wind_speed_kmh * 0.08 + math.sqrt(effective_frp) * 0.15) * inversion_multiplier,
        2
    )

    # 4. Population Threat Index
    dist_km = max(0.1, req.population_distance_km)
    pop_threat = min(100.0, ((hazard_radius_m / 1000.0) / dist_km) * 100.0 * (1.5 if req.atmospheric_inversion else 1.0))
    if req.mitigation_evac:
        pop_threat *= 0.25  # Evacuation reduces human vulnerability significantly

    # 5. Risk Scores (0-100)
    # Baseline Risk (assuming normal baseline FRP)
    baseline_risk = min(100.0, max(15.0, (req.baseline_frp / 150.0) * 35.0))

    # Raw Simulated Risk (without mitigations)
    raw_intensity_score = min(50.0, (req.simulated_frp / 250.0) * 45.0)
    persistence_score = min(25.0, (req.duration_hours / 24.0) * 25.0)
    raw_pop_score = min(25.0, (1.0 / max(0.5, req.population_distance_km)) * 12.0)
    simulated_risk_score = round(min(100.0, raw_intensity_score + persistence_score + raw_pop_score), 1)

    # Mitigated Risk Score (with active mitigations)
    mitigated_intensity = min(50.0, (effective_frp / 250.0) * 45.0)
    mitigated_persistence = min(25.0, (req.duration_hours / (48.0 if req.mitigation_esd else 24.0)) * 25.0)
    mitigated_pop = min(25.0, pop_threat * 0.25)
    mitigated_risk_score = round(min(100.0, mitigated_intensity + mitigated_persistence + mitigated_pop), 1)

    # Risk level categorization
    if mitigated_risk_score >= 75.0:
        risk_level = "CRITICAL"
    elif mitigated_risk_score >= 50.0:
        risk_level = "HIGH"
    elif mitigated_risk_score >= 30.0:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Overall mitigation impact %
    mitigation_impact = round(max(0.0, ((simulated_risk_score - mitigated_risk_score) / max(1.0, simulated_risk_score)) * 100.0), 1)

    # Anomaly probability
    anomaly_prob = round(min(0.999, max(0.12, 0.50 + (frp_dev_pct / 400.0))), 3)

    # 6. Recommended SOP Checklist Playbook
    sop_steps = [
        {
            "step": 1,
            "title": "Automated Satellite Re-triangulation & Sensor Cross-Check",
            "agency": "ThermoTrace Space Ops",
            "status": "COMPLETED" if req.mitigation_uav else "RECOMMENDED",
            "action": "Cross-reference VIIRS day/night passes with Sentinel-2 SWIR band 12 to rule out optical flare artifacts.",
            "urgency": "IMMEDIATE"
        },
        {
            "step": 2,
            "title": "Facility Control Room Telemetry & FGRS Verification",
            "agency": "Plant Safety Division",
            "status": "ACTIVE" if req.mitigation_fgrs else "PENDING",
            "action": f"Direct plant operators to divert excess hydrocarbon stream to Flare Gas Recovery Unit (target: -{frp_reduction_pct:.0f}% thermal load).",
            "urgency": "CRITICAL" if simulated_risk_score >= 50 else "STANDARD"
        },
        {
            "step": 3,
            "title": "High-Pressure Deluge & Vapor Dispersion Deployment",
            "agency": "Industrial Fire Safety & Hazmat",
            "status": "ACTIVE" if req.mitigation_deluge else "STANDBY",
            "action": f"Engage water curtain injection around perimeter. Current 4.7 kW/m² hazard envelope: {hazard_radius_m}m.",
            "urgency": "CRITICAL" if hazard_radius_m > 300 else "ELEVATED"
        },
        {
            "step": 4,
            "title": "Inter-Agency Regulatory & District Notification",
            "agency": "CPCB / State Pollution Control Board & NDRF",
            "status": "ACTIVE" if req.mitigation_evac else "ADVISORY",
            "action": f"Issue advisory to communities within {req.population_distance_km:.1f}km downwind (azimuth {req.wind_direction_deg}°).",
            "urgency": "HIGH" if pop_threat >= 40 else "ROUTINE"
        }
    ]

    return {
        "baseline_risk_score": round(baseline_risk, 1),
        "simulated_risk_score": simulated_risk_score,
        "mitigated_risk_score": mitigated_risk_score,
        "risk_level": risk_level,
        "effective_frp": round(effective_frp, 1),
        "frp_deviation_pct": round(frp_dev_pct, 1),
        "thermal_hazard_radius_m": hazard_radius_m,
        "public_safety_radius_m": safety_radius_m,
        "plume_dispersion_length_km": plume_length_km,
        "population_threat_index": round(pop_threat, 1),
        "anomaly_probability": anomaly_prob,
        "mitigation_impact_pct": mitigation_impact,
        "recommended_sop": sop_steps,
        "counterfactual_deltas": {
            "frp_delta_mw": round(effective_frp - req.baseline_frp, 1),
            "risk_delta_pts": round(mitigated_risk_score - baseline_risk, 1),
            "hazard_radius_delta_m": round(hazard_radius_m - (math.sqrt(req.baseline_frp * 1000 * 0.3 / (4 * math.pi * 4.7))), 1)
        }
    }


@router.post("/what-if", response_model=WhatIfSimulationResponse)
async def run_what_if_simulation(req: WhatIfSimulationRequest):
    """Execute counterfactual thermal intelligence simulation."""
    res = calculate_simulation(req)
    return res


@router.get("/presets")
async def get_simulation_presets():
    """Retrieve pre-configured industrial scenario presets."""
    return {
        "presets": [
            {
                "preset_id": "PRESET-JAMNAGAR-BLOWOUT",
                "name": "Jamnagar Refinery — Uncontrolled Flare Surge & Inversion",
                "description": "High-pressure thermal blowout during atmospheric night inversion near major petrochemical storage.",
                "facility_name": "Jamnagar Mega Refinery Complex",
                "baseline_frp": 122.5,
                "simulated_frp": 340.0,
                "duration_hours": 18.0,
                "wind_speed_kmh": 12.0,
                "wind_direction_deg": 195.0,
                "population_distance_km": 1.8,
                "atmospheric_inversion": True
            },
            {
                "preset_id": "PRESET-HAZIRA-GASLEAK",
                "name": "Hazira Chemical Belt — High-Wind Gas Dispersion",
                "description": "Volatile gas flaring with gusting winds directed toward nearby coastal settlement.",
                "facility_name": "Hazira Petrochemical & Fertilizer Hub",
                "baseline_frp": 65.0,
                "simulated_frp": 195.0,
                "duration_hours": 6.0,
                "wind_speed_kmh": 45.0,
                "wind_direction_deg": 280.0,
                "population_distance_km": 0.9,
                "atmospheric_inversion": False
            },
            {
                "preset_id": "PRESET-PUNJAB-AGRI",
                "name": "Punjab Border — Crop Residue Fire Spread vs Reserve",
                "description": "Transient high-intensity agricultural burning expanding toward protected forest buffer.",
                "facility_name": "Barnala Rural Agricultural Sector",
                "baseline_frp": 15.0,
                "simulated_frp": 85.0,
                "duration_hours": 3.0,
                "wind_speed_kmh": 22.0,
                "wind_direction_deg": 310.0,
                "population_distance_km": 4.2,
                "atmospheric_inversion": False
            }
        ]
    }
