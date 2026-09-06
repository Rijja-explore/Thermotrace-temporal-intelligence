import json
import urllib.request
import urllib.parse
import os
import pandas as pd
from typing import Dict, Any, List, Optional

STAC_API_URL = "https://earth-search.aws.element84.com/v1/search"
OUTPUT_EVIDENCE_PATH = "ml/data/sentinel2_acquired_evidence.json"
CANDIDATE_BATCH_PATH = "ml/data/ground_truth_investigation_batch_v1.csv"

def fetch_sentinel2_stac_items(lat: float, lon: float, start_time: str, buffer_days: int = 5) -> List[Dict[str, Any]]:
    """
    Queries Element84 Earth Search STAC API for Sentinel-2 L2A scenes around target coordinates and date.
    """
    dt = pd.to_datetime(start_time)
    start_date = (dt - pd.Timedelta(days=buffer_days)).strftime("%Y-%m-%dT00:00:00Z")
    end_date = (dt + pd.Timedelta(days=buffer_days)).strftime("%Y-%m-%dT23:59:59Z")
    
    # 0.05 degree bounding box (~5km)
    bbox = [lon - 0.025, lat - 0.025, lon + 0.025, lat + 0.025]
    
    payload = {
        "collections": ["sentinel-2-l2a"],
        "bbox": bbox,
        "datetime": f"{start_date}/{end_date}",
        "limit": 5
    }
    
    req = urllib.request.Request(
        STAC_API_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json", "User-Agent": "ThermoTrace-STAC-Client/1.0"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                return data.get("features", [])
    except Exception as e:
        print(f"Error fetching STAC items for lat={lat}, lon={lon}: {e}")
        
    return []

def run_stac_evidence_acquisition(limit_events: int = 15):
    """
    Runs automated Sentinel-2 evidence acquisition for candidate events.
    """
    if not os.path.exists(CANDIDATE_BATCH_PATH):
        raise FileNotFoundError(f"Candidate batch file not found: {CANDIDATE_BATCH_PATH}")
        
    df_candidates = pd.read_csv(CANDIDATE_BATCH_PATH)
    events_to_query = df_candidates.head(limit_events)
    
    results = []
    print(f"Starting Sentinel-2 STAC acquisition for top {len(events_to_query)} events...")
    
    for idx, row in events_to_query.iterrows():
        event_id = row['event_id']
        lat = float(row['centroid_lat'])
        lon = float(row['centroid_lon'])
        start_time = str(row['start_time'])
        
        print(f"[{idx+1}/{len(events_to_query)}] Querying STAC for event {event_id} at ({lat:.4f}, {lon:.4f})...")
        items = fetch_sentinel2_stac_items(lat, lon, start_time)
        
        scene_info = []
        for item in items:
            props = item.get("properties", {})
            assets = item.get("assets", {})
            scene_info.append({
                "scene_id": item.get("id"),
                "datetime": props.get("datetime"),
                "cloud_cover": props.get("eo:cloud_cover"),
                "thumbnail_url": assets.get("thumbnail", {}).get("href"),
                "visual_url": assets.get("visual", {}).get("href"),
                "s3_href": assets.get("red", {}).get("href")
            })
            
        evidence_status = "STAC_SCENES_FOUND" if scene_info else "NO_SCENE_AVAILABLE"
        results.append({
            "event_id": event_id,
            "centroid_lat": lat,
            "centroid_lon": lon,
            "start_time": start_time,
            "stac_evidence_status": evidence_status,
            "scenes_found": len(scene_info),
            "scenes": scene_info
        })
        
    os.makedirs(os.path.dirname(OUTPUT_EVIDENCE_PATH), exist_ok=True)
    with open(OUTPUT_EVIDENCE_PATH, "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"Acquisition complete! Saved Sentinel-2 evidence metadata for {len(results)} events to {OUTPUT_EVIDENCE_PATH}")
    return results

if __name__ == "__main__":
    run_stac_evidence_acquisition(limit_events=10)
