import json
import sys
import os

TAXONOMY = [
    "persistent_industrial_source",
    "industrial_fire_or_abnormal_event",
    "wildfire_or_forest_fire",
    "agricultural_burning",
    "mining_or_other_industrial_activity",
    "unknown_requires_verification"
]

CONFIDENCE_CHOICES = ["HIGH", "MEDIUM", "LOW"]

def review_assignments(assignment_file_path):
    if not os.path.exists(assignment_file_path):
        print(f"Error: Assignment file not found: {assignment_file_path}")
        return

    with open(assignment_file_path, "r") as f:
        assignments = json.load(f)

    print(f"\n========================================================")
    print(f" THERMOTRACE HUMAN VERIFICATION PILOT V2 — REVIEW TOOL")
    print(f" Loaded {len(assignments)} assignments from: {assignment_file_path}")
    print(f"========================================================\n")

    unreviewed = [i for i, a in enumerate(assignments) if a.get("assigned_label") is None]
    print(f"Status: {len(assignments) - len(unreviewed)} / {len(assignments)} reviewed ({len(unreviewed)} pending)\n")

    if not unreviewed:
        print("All events in this assignment set have been reviewed!")
        return

    for idx in unreviewed:
        item = assignments[idx]
        feats = item.get("source_features", {})
        
        print(f"--------------------------------------------------------")
        print(f"Event ID    : {item.get('event_id')}")
        print(f"Coordinates : Lat {item.get('latitude')}, Lon {item.get('longitude')}")
        print(f"Timestamp   : {item.get('timestamp')}")
        print(f"AI Suggest  : {item.get('ai_assisted_suggestion')} (Conf: {item.get('ai_assisted_confidence')})")
        print(f"Thermal Ev  : max_frp={feats.get('max_frp_mw')} MW, duration={feats.get('duration_hours')} hrs")
        print(f"Temporal Ev : active_days_30d={feats.get('active_days_previous_30d')}, events_30d={feats.get('events_previous_30d')}")
        print(f"Land Cover  : forest={feats.get('forest_fraction_1km')}, cropland={feats.get('cropland_fraction_1km')}, builtup={feats.get('builtup_fraction_1km')}")
        print(f"Infra Ev    : dist_facility={feats.get('distance_to_facility_km')} km, refinery={feats.get('near_refinery')}, factory={feats.get('near_factory')}, mine={feats.get('near_mine')}, quarry={feats.get('near_quarry')}")
        print(f"--------------------------------------------------------")
        print("Select Class Label:")
        for i, cat in enumerate(TAXONOMY, 1):
            print(f"  [{i}] {cat}")
        print("  [S] Skip for now")
        print("  [Q] Save and Quit")
        
        if not sys.stdin.isatty():
            print("Non-interactive terminal detected. Run tool interactively in terminal.")
            break

        choice = input("\nEnter choice [1-6, S, Q]: ").strip().upper()
        if choice == 'Q':
            print("Quitting review session.")
            break
        elif choice == 'S':
            print("Skipped event.\n")
            continue
        elif choice in ['1', '2', '3', '4', '5', '6']:
            chosen_label = TAXONOMY[int(choice) - 1]
            
            # Confidence
            print("\nSelect Confidence:")
            print("  [1] HIGH  [2] MEDIUM  [3] LOW")
            conf_choice = input("Enter confidence choice [1-3]: ").strip()
            conf_map = {'1': 'HIGH', '2': 'MEDIUM', '3': 'LOW'}
            chosen_conf = conf_map.get(conf_choice, 'MEDIUM')
            
            # Notes
            notes = input("\nEnter supporting evidence notes: ").strip()
            
            item["assigned_label"] = chosen_label
            item["annotator_confidence"] = chosen_conf
            item["evidence_notes"] = notes
            item["status"] = "completed"
            
            with open(assignment_file_path, "w") as f:
                json.dump(assignments, f, indent=2)
            print(f"--> Saved verification for {item.get('event_id')} as '{chosen_label}' ({chosen_conf})\n")
        else:
            print("Invalid input. Skipping.\n")

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "ml/data/ground_truth/human_verified/pilot_v2/annotator_1_assignments.json"
    review_assignments(path)
