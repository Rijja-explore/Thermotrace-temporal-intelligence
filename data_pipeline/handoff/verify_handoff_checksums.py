"""
ThermoTrace Handoff Checksum Verifier
=====================================

Validates the cryptographic SHA-256 integrity of all canonical and raw datasets.
Can be executed by any team member after cloning or downloading from cloud storage.
"""

import sys
import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = PROJECT_ROOT / "reports" / "handoff" / "cloud_data_manifest.json"

EXPECTED_CHECKSUMS = {
    "data/processed/firms/firms_india_canonical.parquet": "aa1bd287ca31db8c05548355fe13ee79f22838fdc367fa488d24ef9a683f1ab9",
    "data/processed/events/events_v0_1.parquet": "be8ec5dc76843e2a995b80bc141e2dd035801e60916f34001fe327a8ad43c989",
    "data/processed/events/event_detection_links.parquet": "e3bd37aee5ec5c252cd2ffc44d8b3ae37b67ea39fb644a458b8f0d8d18f4e327",
    "data/processed/features/event_features_v1.parquet": "3a865e2f37177d7a784d36a1f2dfe0d39c04f1dbf08d4669430fad62d152d594",
    "data/processed/features/event_features_v2.parquet": "b27b63333d29e72dccb0ad999664289de6d86a4a50ef1d4a5aba11ed58f5b1cc",
    "data/processed/osm/osm_india.gpkg": "0555c3d021427a59bde4fab7f84f2d92598b3dbb674be59c1cec42fc058690c8",
    "data/processed/population/population_india_100m.tif": "cfb1d2434430902e405d68ba720ee9f6f8f96c2bc4955a5982616af5e4736a79",
    "data/processed/protected_areas/protected_areas_india.gpkg": "ecbcd4697ee22cdb64e6ed700712d27c193ff983202cfd178bfd7ef9d905e340",
    "data/processed/worldcover/worldcover_india_10m.tif": "c5c62163351ad7ee6653f20cf9ee7d6ebb3927167c9842e172f46101cf13f720",
    "data/raw/osm/india/india-260901.osm.pbf": "5c65b1e536cccd140a947a97fe51a45475b2bab32d12a7b7821048881e49b678",
    "data/raw/population/ind_pop_2025_CN_100m_R2025A_v1.tif": "f5717c622d79052d4aacf0f67365165575855ba8059375b5d87ea655ed26fa53"
}

def verify_file(rel_path: str, expected_hash: str) -> bool:
    target = PROJECT_ROOT / rel_path
    if not target.exists():
        print(f"[-] MISSING: {rel_path}")
        return False
    
    h = hashlib.sha256()
    with open(target, "rb") as f:
        while chunk := f.read(16 * 1024 * 1024):
            h.update(chunk)
    actual_hash = h.hexdigest()

    if actual_hash == expected_hash:
        print(f"[+] VERIFIED: {rel_path} ({round(target.stat().st_size / (1024**2), 2)} MB)")
        return True
    else:
        print(f"[!] MISMATCH: {rel_path}")
        print(f"    Expected: {expected_hash}")
        print(f"    Actual:   {actual_hash}")
        return False

def main():
    print("=" * 80)
    print("THERMOTRACE DATA INTEGRITY VERIFIER")
    print("=" * 80)
    all_ok = True
    for rel_path, exp_hash in EXPECTED_CHECKSUMS.items():
        if not verify_file(rel_path, exp_hash):
            all_ok = False
    
    print("=" * 80)
    if all_ok:
        print("[SUCCESS] 100% of checked datasets match their expected SHA-256 signatures!")
        sys.exit(0)
    else:
        print("[WARNING] One or more datasets failed integrity checks.")
        sys.exit(1)

if __name__ == "__main__":
    main()
