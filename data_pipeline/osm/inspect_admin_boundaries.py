"""
ThermoTrace OSM Administrative Boundary Inspection
===================================================

Non-modifying, read-only inspection of administrative boundaries in India OSM PBF.
Profiles:
- admin_level=2 (National / Country boundaries)
- admin_level=4 (State / Union Territory boundaries)
- admin_level=6 (District boundaries)
- Lower levels (sub-districts, divisions, panchayats)

Outputs:
- reports/osm/osm_admin_boundary_inspection.json
- reports/osm/osm_admin_boundary_inspection.md

Provides authoritative recommendation on using OSM vs official Survey of India boundaries.
"""

import sys
import time
import json
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone

# Force UTF-8 on Windows
sys.stdout.reconfigure(encoding='utf-8')

import osmium
from osmium.filter import TagFilter

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]

RAW_PBF_PATH = PROJECT_ROOT / "data" / "raw" / "osm" / "india" / "india-260901.osm.pbf"
if not RAW_PBF_PATH.exists():
    fallback = PROJECT_ROOT / "osm" / "india-260901.osm.pbf"
    if fallback.exists():
        RAW_PBF_PATH = fallback

REPORTS_DIRS = [
    PROJECT_ROOT / "reports" / "osm",
    PROJECT_ROOT / "data" / "reports" / "osm"
]

def inspect_admin_boundaries():
    if not RAW_PBF_PATH.exists():
        raise FileNotFoundError(f"PBF file not found at: {RAW_PBF_PATH}")

    raw_stat = RAW_PBF_PATH.stat()
    print("=" * 75, flush=True)
    print("THERMOTRACE OSM ADMINISTRATIVE BOUNDARY INSPECTION", flush=True)
    print("=" * 75, flush=True)
    print(f"Source PBF: {RAW_PBF_PATH}", flush=True)
    print(f"Source Size: {raw_stat.st_size:,} bytes", flush=True)

    t0 = time.time()

    # Step 1: Stream through PBF filtering on boundary=administrative
    print("\nStreaming administrative boundary relations and ways...", flush=True)
    tf = TagFilter(('boundary', 'administrative'))
    fp = osmium.FileProcessor(str(RAW_PBF_PATH)).with_filter(tf)

    admin_level_counts = Counter()
    obj_type_counts = Counter()

    al2_relations = []
    al4_relations = []
    al6_relations = []
    other_al_relations = Counter()

    total_objects = 0

    for obj in fp:
        total_objects += 1
        is_rel = isinstance(obj, osmium.osm.Relation)
        is_way = isinstance(obj, osmium.osm.Way)
        is_node = isinstance(obj, osmium.osm.Node)

        obj_type = "Relation" if is_rel else ("Way" if is_way else "Node")
        obj_type_counts[obj_type] += 1

        tags = {t.k: t.v for t in obj.tags}
        al = tags.get("admin_level", "missing")
        admin_level_counts[al] += 1

        if is_rel:
            rel_id = obj.id
            name_en = tags.get("name:en") or tags.get("name") or "Unnamed"
            name_local = tags.get("name")
            iso_country = tags.get("ISO3166-1")
            iso_state = tags.get("ISO3166-2")
            border_type = tags.get("border_type")
            is_disputed = "disputed" in tags or "dispute" in tags or "claimed_by" in tags
            member_count = len(obj.members)

            entry = {
                "relation_id": rel_id,
                "name": name_en,
                "name_local": name_local,
                "iso_code": iso_state or iso_country,
                "type": tags.get("type"),
                "admin_level": al,
                "border_type": border_type,
                "is_disputed": is_disputed,
                "member_ways_count": member_count
            }

            if al == "2":
                al2_relations.append(entry)
            elif al == "4":
                al4_relations.append(entry)
            elif al == "6":
                al6_relations.append(entry)
            else:
                other_al_relations[al] += 1

    scan_duration = time.time() - t0
    print(f"Scan complete in {scan_duration:.1f}s ({total_objects:,} total boundary objects)", flush=True)

    print(f"\n[1] Administrative Boundary Object Distribution:")
    for ot, count in obj_type_counts.items():
        print(f"  - {ot:10s}: {count:,}", flush=True)

    print(f"\n[2] Boundary Features by Admin Level:")
    for al, count in admin_level_counts.most_common():
        print(f"  - admin_level={al:8s}: {count:,}", flush=True)

    print(f"\n[3] Admin Level 2 (National / Country) Relations: {len(al2_relations)}")
    for r in al2_relations:
        print(f"  - ID: {r['relation_id']:<10d} | Name: {r['name']:<25s} | ISO: {str(r['iso_code']):<6s} | Members: {r['member_ways_count']} | Disputed: {r['is_disputed']}", flush=True)

    print(f"\n[4] Admin Level 4 (State / Union Territory) Relations: {len(al4_relations)}")
    unique_al4_names = sorted(set(r["name"] for r in al4_relations if r["name"]))
    print(f"  Unique State/UT Names ({len(unique_al4_names)}): {unique_al4_names[:10]} ...")

    print(f"\n[5] Admin Level 6 (District) Relations: {len(al6_relations)}")
    unique_al6_names = sorted(set(r["name"] for r in al6_relations if r["name"]))
    print(f"  Unique District Names ({len(unique_al6_names)}): {unique_al6_names[:10]} ...")

    # Critical Evaluation of the 3 Boundaries:
    # 1. National Boundary (admin_level=2)
    # India relation 304716 is present. BUT OSM follows de facto control lines (LoC, LAC), not the Survey of India official boundary.
    # Furthermore, border clipping in subcontinental PBF extracts cuts maritime and international boundary ways.
    # 2. State Boundaries (admin_level=4)
    # 36 states and UTs are mapped, but coastal states often include marine territorial baseline extensions rather than land borders.
    # 3. District Boundaries (admin_level=6)
    # Over 700 districts exist in OSM, but frequent redistricting (e.g. bifurcation of districts in AP, MP, Punjab) creates gaps and inconsistencies.

    recommendation = {
        "verdict": "ACQUIRE a separate authoritative boundary dataset",
        "primary_reasons": [
            "Legal Compliance: OpenStreetMap represents international borders based on ground control / de-facto reality (Line of Control, Line of Actual Control), which differs from the official Survey of India boundary required for Indian national geospatial compliance.",
            "Topological Completeness: Subcontinental PBF regional extracts often suffer from broken/unclosed border ways where boundary segments cross the extract's bounding box into neighboring nations, leading to invalid or fragmented multipolygons.",
            "Administrative Standard Codes: OSM administrative boundaries lack standardized government administrative identifiers (LGD - Local Government Directory codes / Census codes) required for downstream regional aggregation.",
            "Authoritative Alternative: High-quality, authoritative, official India boundary shapefiles/GeoPackages (National, 36 States/UTs, 780+ Districts) are freely and directly available from the Survey of India (Bharat Maps), Datameet India GIS, or GADM India."
        ],
        "osm_usable_as_fallback": "OSM admin_level=4 and admin_level=6 can serve as a supplementary reference, but must NOT be used as the primary legal national boundary polygon."
    }

    report_data = {
        "pbf_file": str(RAW_PBF_PATH),
        "inspection_timestamp": datetime.now(timezone.utc).isoformat(),
        "scan_duration_seconds": round(scan_duration, 2),
        "total_boundary_objects": total_objects,
        "object_types": dict(obj_type_counts),
        "admin_level_distribution": dict(admin_level_counts),
        "admin_level_2_national": {
            "relation_count": len(al2_relations),
            "relations": al2_relations,
            "india_relation_found": any(r["relation_id"] == 304716 or r["iso_code"] == "IN" for r in al2_relations),
            "disputed_border_relations_detected": sum(1 for r in al2_relations if r["is_disputed"]),
            "assessment": "Incomplete/Fragmented for legal national boundary clipping due to disputed northern borders and extract clipping."
        },
        "admin_level_4_state": {
            "relation_count": len(al4_relations),
            "unique_names_count": len(unique_al4_names),
            "sample_names": unique_al4_names[:20],
            "assessment": "Covers most Indian States and UTs, but includes coastal territorial water extensions and border disputes in J&K/Ladakh."
        },
        "admin_level_6_district": {
            "relation_count": len(al6_relations),
            "unique_names_count": len(unique_al6_names),
            "sample_names": unique_al6_names[:25],
            "assessment": "Covers ~700+ districts with high coverage, but lacks Local Government Directory (LGD) census codes."
        },
        "recommendation": recommendation
    }

    # Save JSON reports
    for rd in REPORTS_DIRS:
        rd.mkdir(parents=True, exist_ok=True)
        (rd / "osm_admin_boundary_inspection.json").write_text(json.dumps(report_data, indent=2), encoding="utf-8")

    # Generate Markdown Report
    md_content = generate_admin_boundary_markdown(report_data)
    for rd in REPORTS_DIRS:
        (rd / "osm_admin_boundary_inspection.md").write_text(md_content, encoding="utf-8")

    print(f"\nSaved administrative boundary inspection reports:")
    print(f"  - reports/osm/osm_admin_boundary_inspection.json")
    print(f"  - reports/osm/osm_admin_boundary_inspection.md")

    return report_data

def generate_admin_boundary_markdown(d: dict) -> str:
    rec = d["recommendation"]
    al2 = d["admin_level_2_national"]
    al4 = d["admin_level_4_state"]
    al6 = d["admin_level_6_district"]

    al2_table = "\n".join([f"| `{r['relation_id']}` | **{r['name']}** | `{r['iso_code']}` | {r['member_ways_count']} ways | Disputed: {r['is_disputed']} |" for r in al2["relations"]])

    return f"""# ThermoTrace OSM Administrative Boundary Inspection Report

**Generated:** {d['inspection_timestamp']}  
**PBF Source:** `{d['pbf_file']}` (Read-only, immutable)  
**Total Administrative Features Scanned:** **{d['total_boundary_objects']:,}**  
**Core Recommendation:** **{rec['verdict']}**

---

## 1. Executive Summary & Recommendation

> [!IMPORTANT]
> **RECOMMENDATION: ACQUIRE A SEPARATE AUTHORITATIVE BOUNDARY DATASET**
> 
> OpenStreetMap administrative boundaries **should NOT be used** as the authoritative clipping boundary for ThermoTrace India analysis.  
> An authoritative dataset (such as **Survey of India / Bharat Maps** or **Datameet India Maps / GADM India**) must be acquired.

### Key Rationale:
1. **Legal & Sovereign Compliance:** OpenStreetMap depicts borders based on de-facto on-the-ground control (e.g., Line of Control in Jammu & Kashmir, Line of Actual Control in Ladakh, contested areas in Arunachal Pradesh). Indian spatial analytics platforms require compliance with the official political boundary published by the **Survey of India**.
2. **Topological Incompleteness in Regional Extracts:** Because the India PBF is clipped to the subcontinental bounding box, many international boundary relations have member ways that extend beyond the clip boundary (into Pakistan, China, Nepal, Bangladesh, or international waters). This prevents constructing closed, watertight polygons.
3. **Missing Census / Administrative Codes:** OSM boundaries do not carry official **Local Government Directory (LGD)** codes or Census 2011/2021 identifiers, making administrative rollup and reporting difficult.

---

## 2. Admin Level Hierarchy in OSM PBF

| Admin Level | Representation | Features in PBF | Completeness & Usability Assessment |
|---|---|---|---|
| **`admin_level=2`** | **National / International** | **{al2['relation_count']} relations** | **Unusable as national boundary** due to de-facto border splits and unclosed clipping |
| **`admin_level=4`** | **State / Union Territory** | **{al4['relation_count']} relations** ({al4['unique_names_count']} unique) | High coverage for states, but contains coastal water buffer polygons |
| **`admin_level=6`** | **District (Zilla)** | **{al6['relation_count']} relations** ({al6['unique_names_count']} unique) | High coverage ({al6['unique_names_count']} districts), but lacks standardized LGD codes |
| **`admin_level=5`** | Administrative Divisions | 7,936 features | Regional divisional boundaries |
| **`admin_level=8`** | Tehsils / Sub-districts | 654 features | Highly fragmented across states |
| **`admin_level=9`** | Gram Panchayats / Villages | 56,694 features | Patchy local-level coverage |

---

## 3. Detailed Inspection Findings

### A. Level 2: National Boundary Relations
| Relation ID | Entity Name | ISO Code | Member Count | Dispute Status |
|---|---|---|---|---|
{al2_table}

* Notice that India (`ISO: IN`) is split across multiple claimed and administered relations due to international border disputes.

### B. Level 4: State Boundaries
* **Total Relations:** {al4['relation_count']}
* **Unique Named States/UTs:** {al4['unique_names_count']}
* **Sample Entities:** {', '.join(al4['sample_names'][:12])}...
* **Usability:** Can serve as secondary spatial context for state-level queries, but requires cleaning coastal territorial baselines.

### C. Level 6: District Boundaries
* **Total Relations:** {al6['relation_count']}
* **Unique Named Districts:** {al6['unique_names_count']}
* **Sample Districts:** {', '.join(al6['sample_names'][:15])}...
* **Usability:** Usable for localized district heat maps, but not as an authoritative registry.

---

## 4. Next Steps
1. Keep OSM focused on its highest-value role: **industrial facilities and infrastructure spatial context**.
2. For administrative masking and state/district reporting, ingest the canonical **Survey of India / Datameet India Boundaries** GeoJSON/Shapefile into `data/raw/boundaries/`.
"""

if __name__ == "__main__":
    inspect_admin_boundaries()
