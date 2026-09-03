"""
ThermoTrace Final Pre-Git QA Validation Engine
==============================================

Verifies all 20 pre-Git validation requirements and produces
reports/handoff/final_handoff_validation.json.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
import subprocess

ROOT = Path(r"d:\New folder (2)")
OUT_FILE = ROOT / "reports" / "handoff" / "final_handoff_validation.json"

def run_qa_checks():
    checks = {}

    # 1. Core Parquet Datasets
    checks["firms_canonical_exists"] = (ROOT / "data/processed/firms/firms_india_canonical.parquet").exists()
    checks["events_v0_1_exists"] = (ROOT / "data/processed/events/events_v0_1.parquet").exists()
    checks["event_detection_links_exists"] = (ROOT / "data/processed/events/event_detection_links.parquet").exists()
    checks["event_features_v1_exists"] = (ROOT / "data/processed/features/event_features_v1.parquet").exists()
    checks["event_features_v2_exists"] = (ROOT / "data/processed/features/event_features_v2.parquet").exists()

    # 2. Canonical Geospatial Layers
    checks["osm_canonical_exists"] = (ROOT / "data/processed/osm/osm_india.gpkg").exists()
    checks["population_canonical_exists"] = (ROOT / "data/processed/population/population_india_100m.tif").exists()
    checks["worldcover_canonical_exists"] = (ROOT / "data/processed/worldcover/worldcover_india_10m.tif").exists()
    checks["wdpa_canonical_exists"] = (ROOT / "data/processed/protected_areas/protected_areas_india.gpkg").exists()

    # 3. Documentation & Manifests
    checks["root_readme_complete"] = (ROOT / "README.md").exists() and (ROOT / "README.md").stat().st_size > 1000
    checks["data_readme_complete"] = (ROOT / "data/README.md").exists()
    checks["handoff_readme_complete"] = (ROOT / "reports/handoff/README.md").exists()
    checks["data_manifest_yaml_complete"] = (ROOT / "data/data_manifest.yaml").exists()
    checks["cloud_manifest_json_complete"] = (ROOT / "reports/handoff/cloud_data_manifest.json").exists()
    checks["downstream_requirements_complete"] = (ROOT / "reports/handoff/downstream_data_requirements.md").exists()

    # 4. Schemas and Reports
    checks["v1_schema_exists"] = (ROOT / "reports/features/event_features_v1_schema.json").exists()
    checks["v2_schema_exists"] = (ROOT / "reports/features/event_features_v2_schema.json").exists()
    checks["firms_report_exists"] = (ROOT / "reports/firms/firms_quality_report.json").exists()
    checks["events_report_exists"] = (ROOT / "reports/events/eventization_quality_report.json").exists()

    # 5. Raw Data Immutability
    checks["raw_osm_intact"] = (ROOT / "data/raw/osm/india/india-260901.osm.pbf").stat().st_size == 1705764974
    checks["raw_population_intact"] = (ROOT / "data/raw/population/ind_pop_2025_CN_100m_R2025A_v1.tif").stat().st_size == 778106191
    checks["raw_worldcover_91_tiles_intact"] = len(list((ROOT / "data/raw/worldcover/india").glob("*.tif"))) == 91
    checks["raw_wdpa_intact"] = (ROOT / "data/raw/protected_areas/WDPA_WDOECM_Sep2026_Public_IND_shp_2.zip").stat().st_size == 1188472

    # 6. Safety & Git Staging Guardrails
    checks["no_temporary_part_files"] = len(list(ROOT.rglob("*.part"))) == 0
    checks["no_secrets_or_env_staged"] = not (ROOT / ".env").exists()
    
    # 7. Test Suite Status
    try:
        res = subprocess.run(["pytest", "tests/", "-q"], cwd=str(ROOT), capture_output=True, text=True, timeout=60)
        checks["all_74_tests_passing"] = (res.returncode == 0) and ("74 passed" in res.stdout)
    except Exception as e:
        checks["all_74_tests_passing"] = False

    all_passed = all(checks.values())

    report = {
        "validation_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_checks_evaluated": len(checks),
        "total_checks_passed": sum(1 for v in checks.values() if v),
        "all_checks_passed": all_passed,
        "qa_status": "PASS" if all_passed else "FAIL",
        "detailed_checks": checks
    }

    OUT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Generated QA Validation: {OUT_FILE}")
    print(f"Passed: {report['total_checks_passed']} / {report['total_checks_evaluated']} checks")
    print(f"Status: {report['qa_status']}")

if __name__ == "__main__":
    run_qa_checks()
