import os
import time
from datetime import date, timedelta
from io import StringIO
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

# -----------------------------
# ThermoTrace FIRMS Downloader
# -----------------------------
# Downloads India VIIRS NOAA-20 and NOAA-21 data in 5-day chunks.
# For each date range, it automatically chooses Standard Processing (SP)
# when available, otherwise Near Real-Time (NRT).
#
# IMPORTANT:
# - Put your NEW FIRMS MAP_KEY in .env
# - Do NOT commit .env to GitHub.
# - This script intentionally does NOT contain your key.

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
RAW_DIR = ROOT / "raw" if (ROOT / "raw").exists() else ROOT / "data" / "raw" / "firms"
MANIFEST = RAW_DIR / "download_manifest.csv"

MAP_KEY = os.getenv("FIRMS_MAP_KEY")

# India bounding box: west, south, east, north
INDIA_BBOX = "68.1,6.5,97.4,35.7"

# Default one-year window ending today.
END_DATE = date.today()
START_DATE = END_DATE - timedelta(days=365)

SENSORS = {
    "noaa20": ("VIIRS_NOAA20_SP", "VIIRS_NOAA20_NRT"),
    "noaa21": ("VIIRS_NOAA21_SP", "VIIRS_NOAA21_NRT"),
}

API_BASE = "https://firms.modaps.eosdis.nasa.gov/api"


def require_key():
    if not MAP_KEY or "PASTE_YOUR" in MAP_KEY or "YOUR_NEW_KEY" in MAP_KEY:
        raise SystemExit(
            "FIRMS_MAP_KEY is missing or unconfigured in .env. "
            "Please update the .env file with your valid NASA FIRMS MAP_KEY."
        )


def get_availability():
    """Return FIRMS availability table for all products."""
    url = f"{API_BASE}/data_availability/csv/{MAP_KEY}/ALL"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return pd.read_csv(StringIO(r.text))


def availability_dict(df):
    result = {}
    for _, row in df.iterrows():
        result[row["data_id"]] = (
            pd.to_datetime(row["min_date"]).date(),
            pd.to_datetime(row["max_date"]).date(),
        )
    return result


def choose_source(day_start, day_end, sp_id, nrt_id, avail):
    """
    Prefer SP if the COMPLETE chunk is covered by SP.
    Otherwise use NRT if the COMPLETE chunk is covered by NRT.
    Otherwise return None.
    """
    for source in (sp_id, nrt_id):
        if source not in avail:
            continue
        min_d, max_d = avail[source]
        if min_d <= day_start and day_end <= max_d:
            return source
    return None


def chunks(start, end, size=5):
    current = start
    while current <= end:
        chunk_end = min(current + timedelta(days=size - 1), end)
        yield current, chunk_end
        current = chunk_end + timedelta(days=1)


def download_chunk(source, start, end, sensor_name):
    day_range = (end - start).days + 1
    date_str = start.isoformat()

    url = (
        f"{API_BASE}/area/csv/{MAP_KEY}/{source}/"
        f"{INDIA_BBOX}/{day_range}/{date_str}"
    )

    print(f"[DOWNLOAD] {sensor_name} | {source} | {start} -> {end}")

    r = requests.get(url, timeout=180)
    r.raise_for_status()

    text = r.text.strip()
    if not text:
        print("  -> empty response")
        return None

    df = pd.read_csv(StringIO(text))
    if df.empty:
        print("  -> 0 records")
        return df

    df["source_product"] = source
    df["downloaded_at_utc"] = pd.Timestamp.utcnow().isoformat()
    df["query_start"] = start.isoformat()
    df["query_end"] = end.isoformat()

    return df


def main():
    require_key()
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print(f"ThermoTrace FIRMS collection")
    print(f"Window: {START_DATE} -> {END_DATE}")
    print(f"Area: India bbox {INDIA_BBOX}")
    print("Sensors: NOAA-20 + NOAA-21")
    print()

    availability = get_availability()
    avail = availability_dict(availability)

    all_manifest = []

    for sensor_name, (sp_id, nrt_id) in SENSORS.items():
        sensor_dir = RAW_DIR / sensor_name
        sensor_dir.mkdir(parents=True, exist_ok=True)

        for start, end in chunks(START_DATE, END_DATE, size=5):
            source = choose_source(start, end, sp_id, nrt_id, avail)

            if source is None:
                print(
                    f"[SKIP] {sensor_name} {start}->{end}: "
                    "no single SP/NRT product covers the full chunk."
                )
                all_manifest.append({
                    "sensor": sensor_name,
                    "start": start,
                    "end": end,
                    "source": None,
                    "status": "unavailable",
                    "records": 0,
                })
                continue

            filename = f"{sensor_name}_{start}_{end}_{source}.csv"
            path = sensor_dir / filename

            # Resume-friendly: don't download a file that already exists.
            if path.exists() and path.stat().st_size > 0:
                print(f"[SKIP] already exists: {path.name}")
                try:
                    existing = pd.read_csv(path)
                    n = len(existing)
                except Exception:
                    n = -1
                all_manifest.append({
                    "sensor": sensor_name,
                    "start": start,
                    "end": end,
                    "source": source,
                    "status": "existing",
                    "records": n,
                    "file": str(path.relative_to(ROOT)),
                })
                continue

            try:
                df = download_chunk(source, start, end, sensor_name)

                if df is None:
                    records = 0
                else:
                    df.to_csv(path, index=False)
                    records = len(df)

                print(f"  -> saved {records} records to {path}")

                all_manifest.append({
                    "sensor": sensor_name,
                    "start": start,
                    "end": end,
                    "source": source,
                    "status": "downloaded",
                    "records": records,
                    "file": str(path.relative_to(ROOT)),
                })

            except requests.HTTPError as e:
                print(f"[ERROR] HTTP error: {e}")
                all_manifest.append({
                    "sensor": sensor_name,
                    "start": start,
                    "end": end,
                    "source": source,
                    "status": "http_error",
                    "records": 0,
                    "error": str(e),
                })
            except Exception as e:
                print(f"[ERROR] {e}")
                all_manifest.append({
                    "sensor": sensor_name,
                    "start": start,
                    "end": end,
                    "source": source,
                    "status": "error",
                    "records": 0,
                    "error": str(e),
                })

            # Be gentle with the service and transaction limit.
            time.sleep(1.0)

    manifest_df = pd.DataFrame(all_manifest)
    manifest_df.to_csv(MANIFEST, index=False)
    print(f"Manifest written: {MANIFEST}")

    # Run Canonical Layer-0 ETL Pipeline
    from data_pipeline.firms.canonical_etl import run_pipeline
    output_dir = ROOT / "processed" if (ROOT / "processed").exists() else ROOT / "data" / "processed" / "firms"
    reports_dir = ROOT / "reports" if (ROOT / "reports").exists() else ROOT / "data" / "reports" / "firms"
    run_pipeline(
        raw_dir=RAW_DIR,
        output_dir=output_dir,
        reports_dir=reports_dir,
    )


if __name__ == "__main__":
    main()
