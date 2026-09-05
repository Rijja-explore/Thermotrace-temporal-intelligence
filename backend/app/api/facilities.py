"""
Facilities API — industrial facility lookup and proximity search across India and globally.
"""
from fastapi import APIRouter, Query
from typing import Optional
import math

router = APIRouter()

# Comprehensive industrial facilities across India (Refineries, Petrochemicals, Steel Plants, Coal Basins)
FACILITIES = [
    # ── Refineries & Petrochemicals ──
    {"facility_id": 1, "name": "Jamnagar Refinery Complex", "facility_type": "Oil Refinery & Petrochemical", "lat": 22.4707, "lon": 70.0577, "capacity": "1,240,000 bpd", "operator": "Reliance Industries", "state": "Gujarat"},
    {"facility_id": 2, "name": "Vadinar Refinery", "facility_type": "Oil Refinery", "lat": 22.4200, "lon": 69.7200, "capacity": "400,000 bpd", "operator": "Nayara Energy", "state": "Gujarat"},
    {"facility_id": 3, "name": "Hazira Industrial & Steel Complex", "facility_type": "Petrochemical, LNG & Integrated Steel", "lat": 21.1054, "lon": 72.6458, "capacity": "10.0 MTPA Steel / Petrochem", "operator": "ArcelorMittal Nippon Steel (AM/NS), Reliance, ONGC, L&T", "state": "Gujarat"},
    {"facility_id": 4, "name": "Dahej Petroleum & Chemical Zone (PCPIR)", "facility_type": "Petrochemical & Chemical Complex", "lat": 21.7080, "lon": 72.5830, "capacity": "Mega Petrochem Park", "operator": "ONGC, OPaL, Petronet LNG", "state": "Gujarat"},
    {"facility_id": 5, "name": "Koyali Refinery (Vadodara)", "facility_type": "Oil Refinery & Petrochemical", "lat": 22.3619, "lon": 73.1360, "capacity": "274,000 bpd", "operator": "IOCL", "state": "Gujarat"},
    {"facility_id": 6, "name": "Mumbai Refinery Complex", "facility_type": "Oil Refinery", "lat": 19.0100, "lon": 72.8800, "capacity": "300,000 bpd", "operator": "BPCL / HPCL / RCF", "state": "Maharashtra"},
    {"facility_id": 7, "name": "Panipat Refinery", "facility_type": "Oil Refinery & Petrochemical", "lat": 29.3909, "lon": 76.9635, "capacity": "300,000 bpd", "operator": "IOCL", "state": "Haryana"},
    {"facility_id": 8, "name": "Mathura Refinery", "facility_type": "Oil Refinery", "lat": 27.4924, "lon": 77.6737, "capacity": "160,000 bpd", "operator": "IOCL", "state": "Uttar Pradesh"},
    {"facility_id": 9, "name": "Chennai Petrochemical Complex (Manali)", "facility_type": "Petrochemical & Refinery", "lat": 13.1650, "lon": 80.3020, "capacity": "210,000 bpd", "operator": "CPCL", "state": "Tamil Nadu"},
    {"facility_id": 10, "name": "Mangalore Refinery (MRPL)", "facility_type": "Oil Refinery", "lat": 12.9912, "lon": 74.8385, "capacity": "300,000 bpd", "operator": "MRPL (ONGC)", "state": "Karnataka"},
    {"facility_id": 11, "name": "Kochi Refinery", "facility_type": "Oil Refinery & Petrochemical", "lat": 9.9674, "lon": 76.3530, "capacity": "310,000 bpd", "operator": "BPCL", "state": "Kerala"},
    {"facility_id": 12, "name": "Visakhapatnam Refinery", "facility_type": "Oil Refinery", "lat": 17.6868, "lon": 83.2185, "capacity": "166,000 bpd", "operator": "HPCL", "state": "Andhra Pradesh"},
    {"facility_id": 13, "name": "Paradip Refinery Complex", "facility_type": "Oil Refinery & Petrochemical", "lat": 20.2882, "lon": 86.6433, "capacity": "300,000 bpd", "operator": "IOCL", "state": "Odisha"},
    {"facility_id": 14, "name": "Haldia Refinery Complex", "facility_type": "Oil Refinery & Petrochemical", "lat": 22.0620, "lon": 88.0640, "capacity": "150,000 bpd", "operator": "IOCL / Haldia Petrochem", "state": "West Bengal"},
    {"facility_id": 15, "name": "Barauni Refinery", "facility_type": "Oil Refinery", "lat": 25.4670, "lon": 85.9870, "capacity": "120,000 bpd", "operator": "IOCL", "state": "Bihar"},
    {"facility_id": 16, "name": "Bina Refinery", "facility_type": "Oil Refinery", "lat": 24.1750, "lon": 78.1880, "capacity": "156,000 bpd", "operator": "BPCL", "state": "Madhya Pradesh"},
    {"facility_id": 17, "name": "Bhatinda Refinery (HMEL)", "facility_type": "Oil Refinery", "lat": 30.1250, "lon": 74.9350, "capacity": "230,000 bpd", "operator": "HMEL", "state": "Punjab"},
    {"facility_id": 18, "name": "Bongaigaon Refinery", "facility_type": "Petrochemical & Refinery", "lat": 26.4780, "lon": 90.5600, "capacity": "50,000 bpd", "operator": "IOCL", "state": "Assam"},
    {"facility_id": 19, "name": "Numaligarh Refinery", "facility_type": "Oil Refinery", "lat": 26.5920, "lon": 93.7530, "capacity": "60,000 bpd", "operator": "NRL", "state": "Assam"},
    {"facility_id": 20, "name": "Digboi Refinery", "facility_type": "Heritage Oil Refinery", "lat": 27.3820, "lon": 95.6260, "capacity": "13,000 bpd", "operator": "IOCL", "state": "Assam"},

    # ── Integrated Steel Plants ──
    {"facility_id": 21, "name": "JSW Steel Vijayanagar Works", "facility_type": "Integrated Steel Plant (Largest in India)", "lat": 15.1850, "lon": 76.6750, "capacity": "12.0 MTPA", "operator": "JSW Steel", "state": "Karnataka"},
    {"facility_id": 22, "name": "Tata Steel Jamshedpur Works", "facility_type": "Integrated Steel Plant", "lat": 22.7800, "lon": 86.2000, "capacity": "11.0 MTPA", "operator": "Tata Steel", "state": "Jharkhand"},
    {"facility_id": 23, "name": "Tata Steel Kalinganagar", "facility_type": "Integrated Steel Plant", "lat": 20.9650, "lon": 86.0120, "capacity": "8.0 MTPA", "operator": "Tata Steel", "state": "Odisha"},
    {"facility_id": 24, "name": "SAIL Bokaro Steel Plant", "facility_type": "Integrated Steel Plant", "lat": 23.6693, "lon": 86.1511, "capacity": "4.5 MTPA", "operator": "SAIL", "state": "Jharkhand"},
    {"facility_id": 25, "name": "SAIL Bhilai Steel Plant", "facility_type": "Integrated Steel Plant", "lat": 21.1890, "lon": 81.3850, "capacity": "7.0 MTPA", "operator": "SAIL", "state": "Chhattisgarh"},
    {"facility_id": 26, "name": "SAIL Rourkela Steel Plant", "facility_type": "Integrated Steel Plant", "lat": 22.2280, "lon": 84.8700, "capacity": "4.5 MTPA", "operator": "SAIL", "state": "Odisha"},
    {"facility_id": 27, "name": "SAIL Durgapur Steel Plant", "facility_type": "Integrated Steel Plant", "lat": 23.5130, "lon": 87.3120, "capacity": "2.2 MTPA", "operator": "SAIL", "state": "West Bengal"},
    {"facility_id": 28, "name": "SAIL IISCO Steel Plant (Burnpur)", "facility_type": "Integrated Steel Plant", "lat": 23.6700, "lon": 86.9400, "capacity": "2.5 MTPA", "operator": "SAIL", "state": "West Bengal"},
    {"facility_id": 29, "name": "RINL Visakhapatnam Steel Plant", "facility_type": "Integrated Steel Plant", "lat": 17.6330, "lon": 83.1830, "capacity": "7.3 MTPA", "operator": "Rashtriya Ispat Nigam Ltd", "state": "Andhra Pradesh"},
    {"facility_id": 30, "name": "JSPL Raigarh Steel Plant", "facility_type": "Integrated Steel & Power Plant", "lat": 21.9100, "lon": 83.3900, "capacity": "3.6 MTPA", "operator": "Jindal Steel & Power", "state": "Chhattisgarh"},
    {"facility_id": 31, "name": "JSPL Angul Steel Complex", "facility_type": "Integrated Steel & Power Plant", "lat": 20.8400, "lon": 85.1000, "capacity": "6.0 MTPA", "operator": "Jindal Steel & Power", "state": "Odisha"},

    # ── Major Coal Basins & Mining Thermal Belts ──
    {"facility_id": 32, "name": "Jharia - Dhanbad Coalfield Basin", "facility_type": "Opencast Coal Mining & Underground Colliery Fires", "lat": 23.7500, "lon": 86.4200, "capacity": "Mega Coalfield", "operator": "Bharat Coking Coal Ltd (BCCL)", "state": "Jharkhand"},
    {"facility_id": 33, "name": "Raniganj - Asansol Coalfield Basin", "facility_type": "Coal Mining & Colliery Belt", "lat": 23.6200, "lon": 87.0800, "capacity": "Coal Basin", "operator": "Eastern Coalfields Ltd (ECL)", "state": "West Bengal"},
    {"facility_id": 34, "name": "Korba Coal & Super Thermal Power Basin", "facility_type": "Opencast Coal Mining & Super Thermal Power", "lat": 22.3600, "lon": 82.7200, "capacity": "SECL Mining / 2600MW NTPC", "operator": "SECL / NTPC", "state": "Chhattisgarh"},
    {"facility_id": 35, "name": "Singrauli Coal & Power Basin", "facility_type": "Opencast Coal Mining & Power Hub", "lat": 24.1900, "lon": 82.6700, "capacity": "Energy Capital of India", "operator": "NCL / NTPC", "state": "Madhya Pradesh"},
    {"facility_id": 36, "name": "Talcher Coalfield & Thermal Basin", "facility_type": "Coal Mining & Super Thermal Power", "lat": 20.9500, "lon": 85.2200, "capacity": "Mega Coal Reserve", "operator": "Mahanadi Coalfields Ltd (MCL)", "state": "Odisha"},
    {"facility_id": 37, "name": "Ib Valley Coalfield", "facility_type": "Opencast Coal Mining Basin", "lat": 21.8500, "lon": 83.9200, "capacity": "Coal Basin", "operator": "Mahanadi Coalfields Ltd (MCL)", "state": "Odisha"},
    {"facility_id": 38, "name": "Ramagundam Godavari Coalfield Basin", "facility_type": "Coal Mining & Super Thermal Power", "lat": 18.7600, "lon": 79.5200, "capacity": "SCCL Mining / NTPC 2600MW", "operator": "SCCL / NTPC", "state": "Telangana"},
    {"facility_id": 39, "name": "Neyveli Lignite Mining & Power Complex", "facility_type": "Open Cast Lignite Mines & Thermal Power", "lat": 11.6000, "lon": 79.4800, "capacity": "3000MW Power / Mining", "operator": "NLC India Ltd", "state": "Tamil Nadu"},

    # ── High-Tech Manufacturing, Auto & Chemical Corridors ──
    {"facility_id": 40, "name": "Sriperumbudur - Oragadam Industrial Corridor", "facility_type": "Automotive, Electronics & Heavy Manufacturing", "lat": 12.8700, "lon": 79.9400, "capacity": "SIPCOT Industrial Hub", "operator": "SIPCOT Industrial Park", "state": "Tamil Nadu"},
    {"facility_id": 41, "name": "Sivakasi Fireworks & Industrial Cluster", "facility_type": "Fireworks, Matches & Chemical Cluster", "lat": 9.4500, "lon": 77.7900, "capacity": "Pyrotechnic & Chemical Hub", "operator": "Sivakasi Industrial Association", "state": "Tamil Nadu"},
    {"facility_id": 42, "name": "Chakan - Talegaon Auto Industrial Belt", "facility_type": "Automotive & Heavy Engineering Hub", "lat": 18.7500, "lon": 73.8500, "capacity": "Auto Corridor", "operator": "MIDC Pune", "state": "Maharashtra"},
    {"facility_id": 43, "name": "Sanand Industrial Estate (GIDC)", "facility_type": "Automotive & Engineering Hub", "lat": 23.0100, "lon": 72.3800, "capacity": "Auto Hub", "operator": "GIDC Gujarat", "state": "Gujarat"},
    {"facility_id": 44, "name": "Bhiwadi - Dharuhera Industrial Cluster", "facility_type": "Manufacturing & Chemical Hub", "lat": 28.2100, "lon": 76.8600, "capacity": "Industrial Belt", "operator": "RIICO / HSIIDC", "state": "Rajasthan"},
]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in kilometres."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def find_nearest_facility(lat: float, lon: float, max_radius_km: float = 25.0) -> Optional[dict]:
    """Find the nearest facility within max_radius_km."""
    best = None
    min_dist = max_radius_km
    for f in FACILITIES:
        d = haversine_km(lat, lon, f["lat"], f["lon"])
        if d <= min_dist:
            min_dist = d
            best = {**f, "distance_km": round(d, 2)}
    return best


@router.get("/")
async def list_facilities(
    facility_type: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
):
    """List all known industrial facilities."""
    result = FACILITIES
    if facility_type:
        result = [f for f in result if facility_type.lower() in f["facility_type"].lower()]
    if state:
        result = [f for f in result if state.lower() in f.get("state", "").lower()]
    return {"total": len(result), "facilities": result}


@router.get("/nearby")
async def nearby_facilities(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius_km: float = Query(25.0, description="Search radius in km"),
):
    """Find facilities within a given radius of a point."""
    results = []
    for f in FACILITIES:
        dist = haversine_km(lat, lon, f["lat"], f["lon"])
        if dist <= radius_km:
            results.append({**f, "distance_km": round(dist, 2)})
    results.sort(key=lambda x: x["distance_km"])
    return {"total": len(results), "radius_km": radius_km, "facilities": results}


@router.get("/{facility_id}")
async def get_facility(facility_id: int):
    """Get details for a specific facility."""
    for f in FACILITIES:
        if f["facility_id"] == facility_id:
            return f
    return {"error": "Facility not found"}
