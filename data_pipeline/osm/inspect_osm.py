"""
Inspect India OpenStreetMap PBF for ThermoTrace Industrial Context and Infrastructure Analysis.

This script performs a non-modifying, read-only inspection of the raw OSM PBF file.
It inspects:
1. File metadata (size, replication timestamp, generator)
2. Header bounding box (geographic coverage)
3. Object counts and tag occurrence distributions relevant to industrial facilities and infrastructure
4. Geometry types (points, lines, polygons/multipolygons)
5. Data quality metrics (missing names, missing operators, tag coverage)
"""

import sys
import time
import json
from pathlib import Path
from collections import Counter
import osmium
from osmium.filter import KeyFilter

# Ensure UTF-8 output on Windows console
sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]

# Path to raw PBF (immutable)
PBF_PATH = PROJECT_ROOT / "data" / "raw" / "osm" / "india" / "india-260901.osm.pbf"
if not PBF_PATH.exists():
    fallback = PROJECT_ROOT / "osm" / "india-260901.osm.pbf"
    if fallback.exists():
        PBF_PATH = fallback

# Normalization mapping for facilities
def classify_facility(tags):
    """
    Classifies an OSM feature into normalized facility categories per ThermoTrace spec.
    Returns (category, is_facility)
    """
    landuse = tags.get("landuse")
    industrial = tags.get("industrial")
    power = tags.get("power")
    man_made = tags.get("man_made")
    amenity = tags.get("amenity")
    building = tags.get("building")
    craft = tags.get("craft")

    # 1. Power
    if power == "plant" or industrial == "power":
        return "POWER_PLANT", True
    if power == "substation":
        return "SUBSTATION", True
    if power == "generator":
        return "POWER_PLANT", True

    # 2. Refinery & Oil/Gas
    if industrial in ("refinery", "oil", "gas") or man_made in ("refinery", "petroleum_well", "oil_well", "gas_well"):
        if industrial == "refinery" or man_made == "refinery":
            return "REFINERY", True
        return "OIL_GAS", True

    # 3. Chemical
    if industrial == "chemical":
        return "CHEMICAL_PLANT", True

    # 4. Steel / Metallurgy
    if industrial in ("steel", "metallurgy", "metal", "iron") or craft == "metalworking":
        return "STEEL_PLANT", True

    # 5. Cement
    if industrial == "cement":
        return "CEMENT_PLANT", True

    # 6. Storage
    if man_made in ("storage_tank", "silo", "gasometer") or tags.get("content") in ("fuel", "oil", "gas", "chemicals"):
        return "STORAGE_FACILITY", True

    # 7. Mining & Quarry
    if landuse == "quarry" or tags.get("mine") is not None or man_made == "mineshaft":
        return "QUARRY" if landuse == "quarry" else "MINE", True

    # 8. Waste Processing
    if (amenity in ("waste_disposal", "waste_transfer_station", "recycling")
        or landuse == "landfill"
        or man_made in ("wastewater_plant", "waste_disposal")):
        return "WASTE_PROCESSING", True

    # 9. Warehouse
    if building == "warehouse" or industrial == "warehouse":
        return "WAREHOUSE", True

    # 10. Factory / Manufacturing
    if (industrial in ("factory", "manufacturing")
        or building in ("factory", "manufacture")
        or man_made == "works"):
        return "FACTORY", True

    # 11. Industrial Area
    if landuse == "industrial":
        return "INDUSTRIAL_AREA", True

    # 12. Other specific industrial tags
    if industrial or building == "industrial":
        return "OTHER_INDUSTRIAL", True

    return None, False


# Normalization mapping for infrastructure
def classify_infrastructure(tags):
    """
    Classifies an OSM feature into normalized infrastructure categories per ThermoTrace spec.
    Returns (category, is_infra)
    """
    power = tags.get("power")
    pipeline = tags.get("pipeline")
    man_made = tags.get("man_made")
    railway = tags.get("railway")
    highway = tags.get("highway")
    aeroway = tags.get("aeroway")
    harbour = tags.get("harbour")
    port = tags.get("port")
    landuse = tags.get("landuse")

    # 1. Power lines
    if power in ("line", "minor_line", "cable"):
        return "POWER_LINE", True
    if power == "substation":
        return "SUBSTATION", True
    if power in ("plant", "generator"):
        return "POWER_PLANT", True

    # 2. Pipelines
    if pipeline or man_made == "pipeline":
        return "PIPELINE", True

    # 3. Railways
    if railway in ("rail", "narrow_gauge", "light_rail", "yard", "subway", "monorail"):
        return "RAILWAY", True

    # 4. Major Roads
    if highway in ("motorway", "trunk", "primary", "secondary", "tertiary",
                   "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link"):
        return "MAJOR_ROAD", True

    # 5. Airports
    if aeroway in ("aerodrome", "runway", "taxiway", "helipad", "apron"):
        return "AIRPORT", True

    # 6. Ports & Harbours
    if harbour or port or landuse == "port" or tags.get("industrial") == "port":
        return "PORT", True

    return None, False


def run_inspection(pbf_path: Path):
    if not pbf_path.exists():
        raise FileNotFoundError(f"OSM PBF file not found at: {pbf_path}")

    file_size_bytes = pbf_path.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)
    file_size_gb = file_size_bytes / (1024 * 1024 * 1024)

    print("=" * 70, flush=True)
    print("THERMOTRACE OSM PBF PRE-EXTRACTION INSPECTION", flush=True)
    print("=" * 70, flush=True)
    print(f"File Path: {pbf_path}", flush=True)
    print(f"File Size: {file_size_bytes:,} bytes ({file_size_mb:.2f} MiB / {file_size_gb:.3f} GiB)", flush=True)

    # 1. Inspect Header
    reader = osmium.io.Reader(str(pbf_path))
    header = reader.header()
    box = header.box()
    bbox = None
    if box.valid():
        bbox = {
            "min_lon": round(box.bottom_left.lon, 6),
            "min_lat": round(box.bottom_left.lat, 6),
            "max_lon": round(box.top_right.lon, 6),
            "max_lat": round(box.top_right.lat, 6)
        }
        print(f"Geographic Extent (BBOX): [{bbox['min_lon']}, {bbox['min_lat']}] to [{bbox['max_lon']}, {bbox['max_lat']}]", flush=True)
    else:
        print("Geographic Extent: BBOX not present in header", flush=True)

    header_meta = {}
    for key in ["osmosis_replication_timestamp", "timestamp", "generator"]:
        try:
            val = header.get(key)
            if val:
                header_meta[key] = val
                print(f"PBF Header {key}: {val}", flush=True)
        except Exception:
            pass
    reader.close()

    # 2. Inspect with KeyFilter
    print("\nScanning objects matching industrial facility and infrastructure keys...", flush=True)
    keys_to_filter = [
        "landuse", "industrial", "power", "man_made", "amenity",
        "building", "craft", "pipeline", "railway", "highway", "aeroway", "harbour", "port"
    ]
    kf = KeyFilter(*keys_to_filter)
    fp = osmium.FileProcessor(str(pbf_path)).with_filter(kf)

    total_scanned = 0
    t0 = time.time()

    # Metrics
    fac_counts = Counter()
    fac_geoms = Counter()  # point, polygon, line
    fac_named = 0
    fac_with_operator = 0
    fac_total = 0

    infra_counts = Counter()
    infra_geoms = Counter()
    infra_named = 0
    infra_total = 0

    # Tag breakdowns
    fac_tags_seen = Counter()
    infra_tags_seen = Counter()

    for obj in fp:
        total_scanned += 1
        tags = {t.k: t.v for t in obj.tags}

        is_node = isinstance(obj, osmium.osm.Node)
        is_way = isinstance(obj, osmium.osm.Way)
        is_rel = isinstance(obj, osmium.osm.Relation)

        # Facility classification
        fac_cat, is_fac = classify_facility(tags)
        if is_fac:
            fac_total += 1
            fac_counts[fac_cat] += 1
            if "name" in tags:
                fac_named += 1
            if "operator" in tags:
                fac_with_operator += 1

            if is_node:
                fac_geoms["point"] += 1
            elif is_way:
                if obj.is_closed():
                    fac_geoms["polygon"] += 1
                else:
                    fac_geoms["line"] += 1
            elif is_rel:
                rel_type = tags.get("type")
                if rel_type == "multipolygon":
                    fac_geoms["polygon"] += 1
                else:
                    fac_geoms["relation"] += 1

            for k in ("landuse", "industrial", "power", "man_made", "amenity", "building"):
                if k in tags:
                    fac_tags_seen[f"{k}={tags[k]}"] += 1

        # Infrastructure classification
        infra_cat, is_infra = classify_infrastructure(tags)
        if is_infra:
            infra_total += 1
            infra_counts[infra_cat] += 1
            if "name" in tags:
                infra_named += 1

            if is_node:
                infra_geoms["point"] += 1
            elif is_way:
                if obj.is_closed() and infra_cat in ("PORT", "AIRPORT", "SUBSTATION", "POWER_PLANT"):
                    infra_geoms["polygon"] += 1
                else:
                    infra_geoms["line"] += 1
            elif is_rel:
                rel_type = tags.get("type")
                if rel_type == "multipolygon":
                    infra_geoms["polygon"] += 1
                else:
                    infra_geoms["relation"] += 1

            for k in ("power", "pipeline", "railway", "highway", "aeroway"):
                if k in tags:
                    infra_tags_seen[f"{k}={tags[k]}"] += 1

        if total_scanned % 1_000_000 == 0:
            elapsed = time.time() - t0
            print(f"  Processed {total_scanned:,} candidate objects ({elapsed:.1f}s, {total_scanned/elapsed:,.0f} obj/s)...", flush=True)

    scan_duration = time.time() - t0
    print(f"\nScan completed in {scan_duration:.2f} seconds ({total_scanned / max(scan_duration, 0.001):,.0f} obj/s)", flush=True)

    # Summary Report
    print("\n" + "=" * 70, flush=True)
    print("INSPECTION RESULTS SUMMARY", flush=True)
    print("=" * 70, flush=True)
    print(f"Total Filtered Objects Scanned: {total_scanned:,}", flush=True)
    print(f"\n1. INDUSTRIAL FACILITIES IDENTIFIED: {fac_total:,}", flush=True)
    print("   Geometry Distribution:")
    for geom_type, count in fac_geoms.items():
        print(f"     - {geom_type.capitalize():10s}: {count:,} ({count/fac_total*100:.1f}%)", flush=True)
    print("   Category Breakdown:")
    for cat, count in fac_counts.most_common():
        print(f"     - {cat:20s}: {count:,} ({count/fac_total*100:.1f}%)", flush=True)
    print(f"   Name Completeness:     {fac_named:,} / {fac_total:,} ({fac_named/fac_total*100:.1f}%)")
    print(f"   Operator Completeness: {fac_with_operator:,} / {fac_total:,} ({fac_with_operator/fac_total*100:.1f}%)")
    print(f"   Missing Name:          {fac_total - fac_named:,} ({(fac_total - fac_named)/fac_total*100:.1f}%)")

    print(f"\n2. INFRASTRUCTURE FEATURES IDENTIFIED: {infra_total:,}", flush=True)
    print("   Geometry Distribution:")
    for geom_type, count in infra_geoms.items():
        print(f"     - {geom_type.capitalize():10s}: {count:,} ({count/infra_total*100:.1f}%)", flush=True)
    print("   Category Breakdown:")
    for cat, count in infra_counts.most_common():
        print(f"     - {cat:20s}: {count:,} ({count/infra_total*100:.1f}%)", flush=True)
    print(f"   Name Completeness:     {infra_named:,} / {infra_total:,} ({infra_named/infra_total*100:.1f}%)")

    print("\n3. TOP AVAILABLE FACILITY TAGS:")
    for tag, count in fac_tags_seen.most_common(20):
        print(f"     - {tag:30s}: {count:,}")

    print("\n4. TOP AVAILABLE INFRASTRUCTURE TAGS:")
    for tag, count in infra_tags_seen.most_common(20):
        print(f"     - {tag:30s}: {count:,}")

    # Write inspection JSON
    summary_data = {
        "pbf_file": str(pbf_path),
        "file_size_bytes": file_size_bytes,
        "file_size_mb": round(file_size_mb, 2),
        "file_size_gb": round(file_size_gb, 3),
        "geographic_extent_bbox": bbox,
        "metadata": header_meta,
        "scan_duration_seconds": round(scan_duration, 2),
        "candidate_objects_scanned": total_scanned,
        "facilities": {
            "total_count": fac_total,
            "geometries": dict(fac_geoms),
            "categories": dict(fac_counts),
            "with_name": fac_named,
            "with_operator": fac_with_operator,
            "missing_name": fac_total - fac_named,
            "top_tags": dict(fac_tags_seen.most_common(30))
        },
        "infrastructure": {
            "total_count": infra_total,
            "geometries": dict(infra_geoms),
            "categories": dict(infra_counts),
            "with_name": infra_named,
            "missing_name": infra_total - infra_named,
            "top_tags": dict(infra_tags_seen.most_common(30))
        }
    }

    # Save to both reports directories
    for report_dir in [PROJECT_ROOT / "reports" / "osm", PROJECT_ROOT / "data" / "reports" / "osm"]:
        report_dir.mkdir(parents=True, exist_ok=True)
        out_file = report_dir / "osm_inspection_summary.json"
        out_file.write_text(json.dumps(summary_data, indent=2), encoding="utf-8")
        print(f"\nInspection summary JSON saved to: {out_file}", flush=True)

    return summary_data


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else PBF_PATH
    run_inspection(target)
