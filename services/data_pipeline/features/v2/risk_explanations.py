"""
ThermoTrace Feature Engineering V2: Risk Explanations Engine
============================================================

Derives human-interpretable primary, secondary, and tertiary risk reason tags
explaining the underlying physical and contextual drivers of each thermal event.
"""

import numpy as np
import pandas as pd

def extract_v2_risk_explanations(
    df: pd.DataFrame,
    risk_df: pd.DataFrame,
    land_df: pd.DataFrame,
    infra_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Generates risk_reason_1, risk_reason_2, and risk_reason_3 indicating the top
    contributing contextual risk factors for the event.
    """
    n_events = len(df)
    
    # Candidate reason scores matrix
    # Order of evaluation:
    # 0: HIGH_THERMAL_INTENSITY
    # 1: REPEATED_ACTIVITY
    # 2: HIGH_POPULATION_EXPOSURE
    # 3: NEAR_PROTECTED_AREA
    # 4: NEAR_INDUSTRIAL_FACILITY
    # 5: NEAR_POWER_INFRASTRUCTURE
    # 6: FOREST_DOMINANT_LANDCOVER
    # 7: TRANSPORT_CORRIDOR_PROXIMITY
    
    thermal_comp = risk_df["thermal_risk_component"].values
    rec_comp = risk_df["recurrence_component"].values
    exp_comp = risk_df["exposure_risk_component"].values
    cons_comp = risk_df["conservation_risk_component"].values
    ind_comp = risk_df["industrial_context_component"].values
    power_score = infra_df["power_infrastructure_proximity"].values
    forest_frac = land_df["forest_exposure_score"].values
    corridor = infra_df["transport_corridor_flag"].values

    # Reason candidate priority weights
    candidates = np.stack([
        np.where(thermal_comp >= 40.0, thermal_comp, -1.0),
        np.where(rec_comp >= 25.0, rec_comp * 1.2, -1.0),
        np.where(exp_comp >= 35.0, exp_comp * 1.1, -1.0),
        np.where(cons_comp >= 40.0, cons_comp * 1.3, -1.0),
        np.where(ind_comp >= 40.0, ind_comp, -1.0),
        np.where(power_score >= 40.0, power_score, -1.0),
        np.where(forest_frac >= 50.0, forest_frac, -1.0),
        np.where(corridor, 35.0, -1.0)
    ], axis=1) # shape: (n_events, 8)

    labels = [
        "HIGH_THERMAL_INTENSITY",
        "REPEATED_ACTIVITY",
        "HIGH_POPULATION_EXPOSURE",
        "NEAR_PROTECTED_AREA",
        "NEAR_INDUSTRIAL_FACILITY",
        "NEAR_POWER_INFRASTRUCTURE",
        "FOREST_DOMINANT_LANDCOVER",
        "TRANSPORT_CORRIDOR_PROXIMITY"
    ]

    # Find top 3 reasons by descending candidate weight
    # Argsort gives ascending, so we flip
    top_indices = np.argsort(-candidates, axis=1)[:, :3]

    reasons_1 = []
    reasons_2 = []
    reasons_3 = []

    for i in range(n_events):
        row_c = candidates[i]
        idxs = top_indices[i]
        
        r1 = labels[idxs[0]] if row_c[idxs[0]] > 0 else "BASELINE_MONITORING"
        r2 = labels[idxs[1]] if row_c[idxs[1]] > 0 else "NONE"
        r3 = labels[idxs[2]] if row_c[idxs[2]] > 0 else "NONE"

        reasons_1.append(r1)
        reasons_2.append(r2)
        reasons_3.append(r3)

    return pd.DataFrame({
        "risk_reason_1": pd.Series(reasons_1, index=df.index, dtype="string"),
        "risk_reason_2": pd.Series(reasons_2, index=df.index, dtype="string"),
        "risk_reason_3": pd.Series(reasons_3, index=df.index, dtype="string")
    }, index=df.index)
