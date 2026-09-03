"""
ThermoTrace Cloud Restoration Utility
=====================================

Provides instructions and helper logic for downloading and placing
large datasets from the official ThermoTrace Google Drive storage folder.
"""

from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = PROJECT_ROOT / "reports" / "handoff" / "cloud_data_manifest.json"

def main():
    print("=" * 80)
    print("THERMOTRACE CLOUD ASSET RESTORATION GUIDE")
    print("=" * 80)
    
    if not MANIFEST_PATH.exists():
        print(f"Error: Manifest not found at {MANIFEST_PATH}")
        return

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    cloud_url = manifest.get("cloud_root_url", "https://drive.google.com/drive/folders/1orP0iv660wOhkpOB2NPIj_ZzxUoMvzKe?usp=sharing")

    print(f"\nOfficial Cloud Repository (Google Drive):\n  {cloud_url}\n")
    print("Available Large Geospatial Assets:")
    for ds in manifest.get("datasets", []):
        print(f"\n* Dataset: {ds['dataset_id']} ({ds['size_mb']} MB)")
        print(f"  Cloud Destination: {ds['cloud_package_path']}")
        print(f"  Local Restore Path: {ds['local_source_path']}")
        print(f"  Expected SHA-256: {ds['sha256']}")
        print(f"  Instructions: {ds['restoration_instructions']}")

    print("\n" + "=" * 80)
    print("To verify integrity after manual download, run:")
    print("  python data_pipeline/handoff/verify_handoff_checksums.py")
    print("=" * 80)

if __name__ == "__main__":
    main()
