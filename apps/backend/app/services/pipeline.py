import csv
import json
import urllib.request
import asyncio
import datetime
import uuid
import asyncpg
import os

# ─── ALL FIRMS SATELLITE SOURCES (Direct CSV Downloads) ───
# Multiple satellites = better temporal coverage over India
FIRMS_SOURCES = {
    "MODIS_C6.1": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_Global_24h.csv",
    "VIIRS_SNPP_C2": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_Global_24h.csv",
    "VIIRS_NOAA20_C2": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_Global_24h.csv",
    "VIIRS_NOAA21_C2": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-21-viirs-c2/csv/J2_VIIRS_C2_Global_24h.csv",
}

FALLBACK_JSON_PATH = os.path.join(os.path.dirname(__file__), "backend", "firms_data.json")


def parse_confidence(confidence_raw):
    """Handle both MODIS (0-100 int) and VIIRS ('low'/'nominal'/'high') confidence formats."""
    if isinstance(confidence_raw, str):
        c = confidence_raw.strip().lower()
        if c in ('h', 'high'):
            return 95
        elif c in ('n', 'nominal'):
            return 50
        elif c in ('l', 'low'):
            return 20
        else:
            try:
                return int(c)
            except ValueError:
                return 50
    try:
        return int(confidence_raw)
    except (ValueError, TypeError):
        return 50


def fetch_single_source(sat_name, url):
    """Fetch and parse data from a single FIRMS satellite CSV source."""
    events = []
    try:
        print(f"  ↳ Downloading {sat_name}...")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=90) as response:
            lines = [line.decode('utf-8') for line in response.readlines()]

        reader = csv.DictReader(lines)

        for row in reader:
            try:
                lat = float(row['latitude'])
                lon = float(row['longitude'])
                acq_date = row['acq_date']
                acq_time = row['acq_time']
                frp = float(row.get('frp', 0))
                conf_score = parse_confidence(row.get('confidence', '50'))

                dt_str = f"{acq_date}T{acq_time[:2]}:{acq_time[2:]}:00Z"

                event = {
                    "event_id": f"TT-FIRMS-{str(uuid.uuid4())[:8].upper()}",
                    "satellite": sat_name,
                    "geometry": {"lat": lat, "lon": lon},
                    "time_window": {"start": dt_str, "end": dt_str},
                    "observations": [{"frp": frp, "satellite": sat_name}],
                    "facility_context": {},
                    "landcover_context": {},
                    "temporal_features": {},
                    "classification": {"class": "FIRMS Thermal Anomaly", "confidence": conf_score},
                    "scores": {"industrial_likelihood": 0, "operational_risk": int(min(100, frp / 10))},
                    "evidence": [f"Satellite: {sat_name}", f"FRP: {frp} MW", f"Confidence: {conf_score}%"],
                    "status": "requires_verification",
                    "data_version": f"firms-{sat_name.lower()}-24h",
                    "model_version": "raw"
                }
                events.append(event)
            except Exception:
                continue

        print(f"    ✓ {sat_name}: {len(events)} detections")
    except Exception as e:
        print(f"    ✗ {sat_name} failed: {e}")

    return events


async def fetch_firms_data():
    """Fetch fire data from ALL FIRMS satellite sources and merge."""
    print("Fetching FIRMS data from ALL satellites...")
    all_events = []

    for sat_name, url in FIRMS_SOURCES.items():
        sat_events = fetch_single_source(sat_name, url)
        all_events.extend(sat_events)

    print(f"\n  Total detections across all satellites: {len(all_events)}")
    return all_events


async def save_to_db(events):
    try:
        # Use environment variables with fallbacks to defaults
        import os
        db_user = os.getenv("DB_USER", "thermotrace")
        db_password = os.getenv("DB_PASSWORD", "thermopassword")
        db_name = os.getenv("DB_NAME", "thermotrace")
        db_host = os.getenv("DB_HOST", "127.0.0.1")
        
        conn = await asyncpg.connect(user=db_user, password=db_password, database=db_name, host=db_host)
        # For full implementation we would insert using ST_MakePoint and JSONB
        print("Connected to DB, inserting data...")
        for ev in events:
            # Simplified insert - skipping conflict handling for brevity in demo script
            await conn.execute('''
                INSERT INTO events (event_id, lat, lon, geom, time_start, time_end, status, classification, scores, evidence)
                VALUES ($1, $2, $3, ST_SetSRID(ST_MakePoint($3, $2), 4326), $4, $5, $6, $7::jsonb, $8::jsonb, $9::jsonb)
                ON CONFLICT (event_id) DO NOTHING
            ''', ev['event_id'], ev['geometry']['lat'], ev['geometry']['lon'],
                 datetime.datetime.fromisoformat(ev['time_window']['start'].replace('Z', '+00:00')),
                 datetime.datetime.fromisoformat(ev['time_window']['end'].replace('Z', '+00:00')),
                 ev['status'], json.dumps(ev['classification']), json.dumps(ev['scores']), json.dumps(ev['evidence']))
        await conn.close()
        print("Successfully saved to database.")
    except Exception as e:
        print(f"Database not available ({e}), falling back to local JSON file.")
        with open(FALLBACK_JSON_PATH, "w") as f:
            json.dump(events, f, indent=2)
        print(f"Saved {len(events)} events to {FALLBACK_JSON_PATH}")


async def run_pipeline():
    events = await fetch_firms_data()
    # Filter only nominal/high confidence events
    high_conf = [e for e in events if e['classification']['confidence'] >= 50]
    print(f"Filtering to high confidence: {len(high_conf)} events (from {len(events)} total).")
    # No artificial 500-event cap — let the frontend handle rendering limits
    await save_to_db(high_conf)

if __name__ == "__main__":
    asyncio.run(run_pipeline())
