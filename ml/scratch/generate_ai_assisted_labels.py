import json
import os
import pandas as pd
import numpy as np

CANDIDATES_PATH = "ml/data/ground_truth/candidate_pool_v1.json"
POPULATION_PATH = "data/processed/features/event_features_v2.parquet"
OUTPUT_DIR = "ml/data/ground_truth/ai_assisted"
OUTPUT_LABELS_JSON = os.path.join(OUTPUT_DIR, "ai_assisted_labels_v1.json")
OUTPUT_SUMMARY_MD = os.path.join("ml/reports", "ai_assisted_label_summary_v1.md")
OUTPUT_PRIORITY_JSON = os.path.join(OUTPUT_DIR, "human_review_priority_v1.json")

def generate_ai_assisted_labels():
    print(f"Loading 1,500 candidates from {CANDIDATES_PATH}...")
    with open(CANDIDATES_PATH, "r") as f:
        candidates = json.load(f)
        
    df_cand = pd.DataFrame(candidates)
    df_pop = pd.read_parquet(POPULATION_PATH)
    
    # Merge candidates with full features
    df = df_cand[['event_id', 'acquisition_stratum']].merge(df_pop, on="event_id")
    
    ai_labels = []
    
    for idx, row in df.iterrows():
        event_id = str(row['event_id'])
        max_frp = float(row.get('max_frp_mw', 0.0) or 0.0)
        duration_hrs = float(row.get('duration_hours', 0.0) or 0.0)
        events_30d = float(row.get('events_previous_30d', 0.0) or 0.0)
        active_days = float(row.get('active_days_previous_30d', 0.0) or 0.0)
        forest_frac = float(row.get('forest_fraction_1km', 0.0) or 0.0)
        crop_frac = float(row.get('cropland_fraction_1km', 0.0) or 0.0)
        builtup_frac = float(row.get('builtup_fraction_1km', 0.0) or 0.0)
        dist_fac = float(row.get('distance_to_facility_km', 999.0) if row.get('distance_to_facility_km') is not None else 999.0)
        
        near_refinery = bool(row.get('near_refinery', False))
        near_factory = bool(row.get('near_factory', False))
        near_mine = bool(row.get('near_mine', False))
        near_quarry = bool(row.get('near_quarry', False))
        
        thermal_ev = []
        temporal_ev = []
        landcover_ev = []
        infra_ev = []
        
        if max_frp > 0: thermal_ev.append(f"max_frp_mw={max_frp:.1f}")
        if duration_hrs > 0: thermal_ev.append(f"duration_hours={duration_hrs:.1f}")
        if active_days > 0: temporal_ev.append(f"active_days_30d={active_days}")
        if events_30d > 0: temporal_ev.append(f"events_30d={events_30d}")
        if forest_frac > 0.1: landcover_ev.append(f"forest_frac={forest_frac:.2f}")
        if crop_frac > 0.1: landcover_ev.append(f"cropland_frac={crop_frac:.2f}")
        if builtup_frac > 0.1: landcover_ev.append(f"builtup_frac={builtup_frac:.2f}")
        if dist_fac < 10.0: infra_ev.append(f"dist_facility_km={dist_fac:.2f}")
        if near_mine or near_quarry: infra_ev.append(f"mine_quarry_flag=True")
        if near_refinery or near_factory: infra_ev.append(f"factory_refinery_flag=True")
        
        # Rule-based evidence evaluation
        label = "unknown_requires_verification"
        confidence = "LOW"
        requires_review = True
        reasoning = ""
        
        # 1. Persistent Industrial Source (Facility proximity AND high recurrence/active days)
        if dist_fac <= 2.0 and active_days >= 10.0:
            label = "persistent_industrial_source"
            if active_days >= 15.0 and builtup_frac >= 0.2:
                confidence = "HIGH"
                requires_review = False
            else:
                confidence = "MEDIUM"
                requires_review = True
            reasoning = f"Facility distance {dist_fac:.2f}km <= 2km with {active_days} active days in 30d."
            
        # 2. Industrial Fire / Abnormal Event (Refinery/factory or high builtup + extreme FRP)
        elif (near_refinery or near_factory or builtup_frac >= 0.3) and max_frp >= 150.0:
            label = "industrial_fire_or_abnormal_event"
            if max_frp >= 250.0:
                confidence = "HIGH"
                requires_review = False
            else:
                confidence = "MEDIUM"
                requires_review = True
            reasoning = f"High FRP {max_frp:.1f}MW near refinery/factory/builtup context."
            
        # 3. Mining or Other Industrial Activity (Mine/Quarry flag + facility or builtup proximity)
        elif (near_mine or near_quarry) and (dist_fac <= 3.0 or builtup_frac > 0.1):
            label = "mining_or_other_industrial_activity"
            confidence = "MEDIUM"
            requires_review = True
            reasoning = f"Near active mine/quarry with facility distance {dist_fac:.2f}km."
            
        # 4. Wildfire / Forest Fire (High forest cover + away from facility)
        elif forest_frac >= 0.4 and dist_fac > 2.0:
            label = "wildfire_or_forest_fire"
            if forest_frac >= 0.6 and max_frp >= 50.0:
                confidence = "HIGH"
                requires_review = False
            else:
                confidence = "MEDIUM"
                requires_review = True
            reasoning = f"Dominant forest cover ({forest_frac:.2f}) away from facilities ({dist_fac:.2f}km)."
            
        # 5. Agricultural Burning (High cropland cover + transient duration + away from facility)
        elif crop_frac >= 0.4 and active_days < 5.0 and dist_fac > 2.0:
            label = "agricultural_burning"
            if crop_frac >= 0.6 and active_days <= 2.0:
                confidence = "HIGH"
                requires_review = False
            else:
                confidence = "MEDIUM"
                requires_review = True
            reasoning = f"Dominant cropland cover ({crop_frac:.2f}) with transient active days ({active_days})."
            
        # 6. Unknown / Conflicting
        else:
            label = "unknown_requires_verification"
            confidence = "LOW"
            requires_review = True
            reasoning = f"Insufficient or conflicting evidence (frp={max_frp:.1f}, dist_fac={dist_fac:.2f}km, forest={forest_frac:.2f}, crop={crop_frac:.2f})."
            
        ai_labels.append({
            "event_id": event_id,
            "ai_assisted_label": label,
            "ai_confidence": confidence,
            "evidence_used": {
                "thermal": thermal_ev,
                "temporal": temporal_ev,
                "land_cover": landcover_ev,
                "infrastructure": infra_ev
            },
            "reasoning_summary": reasoning,
            "requires_human_review": requires_review,
            "max_frp_mw": max_frp
        })
        
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_LABELS_JSON, "w") as f:
        json.dump(ai_labels, f, indent=2)
        
    # Generate Ranked Human Review Priority List
    # Priority order: 1. LOW confidence, 2. Unknown label, 3. requires_human_review=True, 4. high FRP
    priority_list = sorted(
        ai_labels,
        key=lambda x: (
            0 if x['ai_confidence'] == "LOW" else 1,
            0 if x['ai_assisted_label'] == "unknown_requires_verification" else 1,
            0 if x['requires_human_review'] else 1,
            -x['max_frp_mw']
        )
    )
    
    with open(OUTPUT_PRIORITY_JSON, "w") as f:
        json.dump(priority_list, f, indent=2)
        
    print(f"AI-assisted labeling complete! {len(ai_labels)} records saved to {OUTPUT_LABELS_JSON}")
    print(f"Human review priority list ({len(priority_list)} records) saved to {OUTPUT_PRIORITY_JSON}")

if __name__ == "__main__":
    generate_ai_assisted_labels()
