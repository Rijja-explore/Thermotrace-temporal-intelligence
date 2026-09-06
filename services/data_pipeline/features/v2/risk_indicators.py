"""
ThermoTrace Feature Engineering V2: Explainable Baseline Risk Engine
===================================================================

Computes multi-dimensional risk components and synthesizes the unified
ThermoTrace Explainable Baseline Risk Score (0-100) and risk severity tiers.
"""

import numpy as np
import pandas as pd

def extract_v2_risk_indicators(
    df: pd.DataFrame,
    thermal_df: pd.DataFrame,
    pop_df: pd.DataFrame,
    land_df: pd.DataFrame,
    cons_df: pd.DataFrame,
    ind_df: pd.DataFrame,
    infra_df: pd.DataFrame,
    rec_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Computes 7 transparent risk component scores (0-100), the overall baseline risk score,
    and categorical risk levels (LOW, MODERATE, HIGH, CRITICAL).
    """
    # 1. Thermal Risk Component (0 - 100)
    # Log max FRP (~6 for 400MW) * 12 + persistence * 28
    log_max = thermal_df["log_max_frp"].values
    persistence = thermal_df["thermal_persistence_indicator"].values
    thermal_comp = np.clip(log_max * 12.0 + persistence * 28.0, 0.0, 100.0).astype(np.float32)

    # 2. Exposure Risk Component (0 - 100)
    exposure_comp = pop_df["population_exposure_score"].values.astype(np.float32)

    # 3. Environmental Risk Component (0 - 100)
    env_comp = land_df["environmental_sensitivity_score"].values.astype(np.float32)

    # 4. Conservation Risk Component (0 - 100)
    cons_comp = cons_df["conservation_sensitivity_score"].values.astype(np.float32)

    # 5. Industrial Context Component (0 - 100)
    ind_comp = ind_df["industrial_proximity_score"].values.astype(np.float32)

    # 6. Infrastructure Context Component (0 - 100)
    infra_comp = infra_df["infrastructure_context_score"].values.astype(np.float32)

    # 7. Recurrence Component (0 - 100)
    ev_30d = rec_df["events_previous_30d"].values
    frp_30d = rec_df["frp_previous_30d"].values
    rec_comp = np.clip(ev_30d * 8.0 + (frp_30d / 20.0), 0.0, 100.0).astype(np.float32)

    # Composite Baseline Risk Score (0.0 to 100.0)
    # Weights: Thermal (25%), Exposure (20%), Environmental (15%), Conservation (15%),
    #          Industrial (10%), Infrastructure (5%), Recurrence (10%)
    baseline_score = (
        0.25 * thermal_comp +
        0.20 * exposure_comp +
        0.15 * env_comp +
        0.15 * cons_comp +
        0.10 * ind_comp +
        0.05 * infra_comp +
        0.10 * rec_comp
    ).astype(np.float32)
    baseline_score = np.clip(baseline_score, 0.0, 100.0)

    # Categorical Risk Levels
    conditions = [
        baseline_score < 30.0,
        (baseline_score >= 30.0) & (baseline_score < 60.0),
        (baseline_score >= 60.0) & (baseline_score < 80.0),
        baseline_score >= 80.0
    ]
    choices = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    risk_level = pd.Series(np.select(conditions, choices, default="LOW"), index=df.index, dtype="string")

    return pd.DataFrame({
        "thermal_risk_component": thermal_comp,
        "exposure_risk_component": exposure_comp,
        "environmental_risk_component": env_comp,
        "conservation_risk_component": cons_comp,
        "industrial_context_component": ind_comp,
        "infrastructure_context_component": infra_comp,
        "recurrence_component": rec_comp,
        "baseline_risk_score": baseline_score,
        "baseline_risk_level": risk_level
    }, index=df.index)
