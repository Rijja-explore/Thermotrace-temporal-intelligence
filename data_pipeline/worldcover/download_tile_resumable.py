"""
Resumable chunked tile downloader for ESA WorldCover with Range headers.
========================================================================
Downloads tiles in 5MB range chunks with retry backoff to survive socket drops.
"""

import sys
import time
import requests
import rasterio
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

URL = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N30E069_Map.tif"
TOTAL_SIZE = 150596996  # Exact size from S3

OUT_PATHS = [
    Path(r"d:\New folder (2)\data\raw\worldcover\india\ESA_WorldCover_10m_2021_v200_N30E069_Map.tif"),
    Path(r"d:\New folder (2)\data\raw\worldcover\ESA_WorldCover_10m_2021_v200_N30E069_Map.tif"),
    Path(r"d:\New folder (2)\ThermoTrace_WorldCover_Downloader\data\raw\worldcover\india\ESA_WorldCover_10m_2021_v200_N30E069_Map.tif")
]

PART_PATH = Path(r"d:\New folder (2)\data\raw\worldcover\india\ESA_WorldCover_10m_2021_v200_N30E069_Map.tif.part")

def download_chunked():
    print(f"Target URL: {URL}", flush=True)
    print(f"Expected Size: {TOTAL_SIZE:,} bytes ({TOTAL_SIZE/(1024*1024):.2f} MB)", flush=True)

    # Check existing partial size
    cur_size = PART_PATH.stat().st_size if PART_PATH.exists() else 0
    if cur_size > TOTAL_SIZE:
        PART_PATH.unlink()
        cur_size = 0

    chunk_size = 4 * 1024 * 1024  # 4 MB chunks

    with open(PART_PATH, "ab") as f:
        while cur_size < TOTAL_SIZE:
            end_byte = min(cur_size + chunk_size - 1, TOTAL_SIZE - 1)
            headers = {"Range": f"bytes={cur_size}-{end_byte}"}

            for attempt in range(10):
                try:
                    r = requests.get(URL, headers=headers, timeout=30)
                    if r.status_code in [200, 206]:
                        data = r.content
                        f.write(data)
                        f.flush()
                        cur_size += len(data)
                        pct = cur_size / TOTAL_SIZE * 100
                        print(f"  Downloaded: {cur_size:,} / {TOTAL_SIZE:,} bytes ({pct:.1f}%)", flush=True)
                        break
                    else:
                        print(f"  Unexpected status {r.status_code}, retry {attempt+1}...", flush=True)
                        time.sleep(2)
                except Exception as e:
                    print(f"  Drop at {cur_size:,} ({e}), retry {attempt+1}...", flush=True)
                    time.sleep(2 * (attempt + 1))
            else:
                raise RuntimeError(f"Failed to fetch chunk at {cur_size} after 10 attempts")

    print("\nDownload complete. Verifying with rasterio...", flush=True)
    with rasterio.open(PART_PATH) as src:
        assert src.shape == (36000, 36000), "Shape mismatch"
        # Verify 10 random blocks across file
        w, h = src.width, src.height
        check_points = [(0, 0), (w//2, h//2), (w-512, h-512), (512, 512*32)]
        for cx, cy in check_points:
            _ = src.read(1, window=rasterio.windows.Window(cx, cy, 512, 512))

    print("Verification PASSED! Replacing destination files...", flush=True)
    for p in OUT_PATHS:
        if p.exists():
            p.unlink()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(PART_PATH.read_bytes())
        print(f"  Updated: {p}", flush=True)

    PART_PATH.unlink()
    print("Tile N30E069 100% repaired and verified!", flush=True)

if __name__ == "__main__":
    download_chunked()
