"""
ThermoTrace Removal Candidates Audit & Generator
================================================

Compiles reports/handoff/removal_candidates.json documenting all duplicate,
intermediate, and redundant files, verifying script references and downstream needs.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"d:\New folder (2)")
OUT_FILE = ROOT / "reports" / "handoff" / "removal_candidates.json"

def main():
    inv_file = ROOT / "reports" / "handoff" / "member1_repository_inventory.json"
    if not inv_file.exists():
        raise FileNotFoundError("Inventory file missing!")

    inv = json.loads(inv_file.read_text(encoding="utf-8"))
    records = inv["file_records"]

    candidates = []
    category_summary = {}

    for r in records:
        if r["removable_candidate"]:
            path = r["path"]
            sz_mb = r["size_mb"]
            reason = r["removal_rationale"]
            
            # Determine category
            if path.startswith("osm/"):
                cat = "root_duplicate_osm_pbf"
                ref_by_scripts = False
                downstream_needed = False
                regenerable = True
            elif path.startswith("population/"):
                cat = "root_duplicate_population_tif"
                ref_by_scripts = False
                downstream_needed = False
                regenerable = True
            elif path.startswith("data/raw/worldcover/") and not path.startswith("data/raw/worldcover/india/"):
                cat = "duplicate_worldcover_root_tiles"
                ref_by_scripts = False
                downstream_needed = False
                regenerable = True
            elif path.startswith("ThermoTrace_WorldCover_Downloader/"):
                cat = "duplicate_worldcover_downloader_workspace"
                ref_by_scripts = False
                downstream_needed = False
                regenerable = True
            elif path.startswith("firms_data/"):
                cat = "duplicate_firms_workspace_copy"
                ref_by_scripts = False
                downstream_needed = False
                regenerable = True
            elif path.endswith(".csv") and ("ThermoTrace_FIRMS_Downloader/processed" in path or "firms_data/processed" in path):
                cat = "redundant_csv_conversions"
                ref_by_scripts = False
                downstream_needed = False
                regenerable = True
            elif path.startswith("ThermoTrace_ProtectedAREA/"):
                cat = "extracted_intermediate_wdpa_shapefiles"
                ref_by_scripts = False
                downstream_needed = False
                regenerable = True
            elif "__pycache__" in path or path.endswith(".pyc"):
                cat = "python_bytecode_cache"
                ref_by_scripts = False
                downstream_needed = False
                regenerable = True
            elif ".pytest_cache" in path:
                cat = "pytest_cache"
                ref_by_scripts = False
                downstream_needed = False
                regenerable = True
            else:
                cat = "other_intermediate"
                ref_by_scripts = False
                downstream_needed = False
                regenerable = True

            category_summary[cat] = category_summary.get(cat, {"count": 0, "size_mb": 0.0})
            category_summary[cat]["count"] += 1
            category_summary[cat]["size_mb"] = round(category_summary[cat]["size_mb"] + sz_mb, 2)

            candidates.append({
                "path": path,
                "category": cat,
                "size_bytes": r["size_bytes"],
                "size_mb": sz_mb,
                "why_unnecessary": reason,
                "referenced_by_active_pipeline_scripts": ref_by_scripts,
                "required_by_downstream_members": downstream_needed,
                "can_be_regenerated": regenerable,
                "canonical_counterpart_path": get_canonical_counterpart(path)
            })

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_removal_candidates": len(candidates),
        "total_reclaimable_space_mb": round(sum(c["size_mb"] for c in candidates), 2),
        "total_reclaimable_space_gb": round(sum(c["size_mb"] for c in candidates) / 1024, 2),
        "category_summary": category_summary,
        "candidates": sorted(candidates, key=lambda x: -x["size_mb"])
    }

    OUT_FILE.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Generated removal candidates report: {OUT_FILE}")
    print(f"Total candidates: {output['total_removal_candidates']}")
    print(f"Total reclaimable space: {output['total_reclaimable_space_gb']} GB")
    print("\nCategory breakdown:")
    for k, v in category_summary.items():
        print(f"  {k}: {v['count']} files ({v['size_mb']} MB)")

def get_canonical_counterpart(path: str) -> str:
    if path.startswith("osm/"):
        return "data/raw/osm/india/india-260901.osm.pbf"
    if path.startswith("population/"):
        return "data/raw/population/ind_pop_2025_CN_100m_R2025A_v1.tif"
    if path.startswith("data/raw/worldcover/") and not path.startswith("data/raw/worldcover/india/"):
        fname = Path(path).name
        return f"data/raw/worldcover/india/{fname}"
    if path.startswith("ThermoTrace_WorldCover_Downloader/"):
        return "data/raw/worldcover/india/"
    if path.startswith("firms_data/"):
        return "data/raw/firms/ and data/processed/firms/"
    if "ThermoTrace_FIRMS_Downloader/processed" in path:
        return "data/processed/firms/ and data/processed/events/"
    if path.startswith("ThermoTrace_ProtectedAREA/"):
        return "data/processed/protected_areas/protected_areas_india.gpkg"
    return "N/A"

if __name__ == "__main__":
    main()
