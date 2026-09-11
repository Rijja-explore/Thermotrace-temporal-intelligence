"""
ThermoTrace Hybrid AI Fusion Layer.
Combines HistGradientBoosting (Spatial/Contextual) + LSTM (Temporal Evolution) + 90-Day Facility Baseline.

Architectural Paradigm:
- HGB: Evaluates spatial land-cover, facility proximity, and contextual features -> "WHAT and WHERE".
- LSTM: Evaluates sequential pass dynamics, acceleration, and trend slope -> "HOW IT EVOLVES".
- 90-Day Baseline: Computes statistical deviation against learned historical operating envelope -> "WHAT IS NORMAL".
"""
from typing import Dict, Any, List, Optional
import numpy as np


class HybridAIFusionLayer:
    """
    Weighted and Explainable Decision Fusion Layer.
    Fuses spatial classification probabilities, temporal escalation states, and baseline deviations.
    """
    def __init__(
        self,
        weight_hgb_spatial: float = 0.45,
        weight_lstm_temporal: float = 0.35,
        weight_facility_baseline: float = 0.20
    ):
        # Configurable and documented fusion weights
        total = weight_hgb_spatial + weight_lstm_temporal + weight_facility_baseline
        self.w_hgb = weight_hgb_spatial / total
        self.w_lstm = weight_lstm_temporal / total
        self.w_base = weight_facility_baseline / total

    def fuse_event_intelligence(
        self,
        hgb_prediction: Dict[str, Any],
        lstm_prediction: Dict[str, Any],
        baseline_stats: Dict[str, Any],
        current_frp: float
    ) -> Dict[str, Any]:
        """
        Executes unified multimodal fusion across spatial, temporal, and baseline subsystems.
        """
        # 1. Spatial / Contextual Score from HGB
        hgb_label = hgb_prediction.get("label", "unknown_requires_verification")
        hgb_conf = float(hgb_prediction.get("confidence", 0.70))
        is_industrial_type = "industrial" in hgb_label.lower()

        # 2. Temporal Escalation Score from LSTM
        escalation_state = lstm_prediction.get("escalation_state", "STABLE")
        temporal_risk = float(lstm_prediction.get("temporal_risk_score", 30.0))
        slope = float(lstm_prediction.get("frp_trend_slope_mw_per_pass", 0.0))

        # 3. Facility Baseline Deviation (Z-score)
        base_mean = float(baseline_stats.get("mean_frp", baseline_stats.get("rolling_frp_mean", 80.0)))
        base_std = max(1.0, float(baseline_stats.get("std_frp", baseline_stats.get("rolling_frp_std", 18.0))))
        z_score = (current_frp - base_mean) / base_std

        # Standardized baseline abnormality score [0 - 1.0]
        baseline_anomaly_score = min(1.0, max(0.0, z_score / 6.0))

        # 4. Multimodal Fusion Calculation
        # Normalize HGB confidence for abnormal events
        spatial_anomaly_signal = hgb_conf if is_industrial_type else (hgb_conf * 0.5)
        temporal_anomaly_signal = temporal_risk / 100.0

        composite_risk_index = (
            (self.w_hgb * spatial_anomaly_signal * 100.0) +
            (self.w_lstm * temporal_anomaly_signal * 100.0) +
            (self.w_base * baseline_anomaly_score * 100.0)
        )
        composite_risk_index = round(min(100.0, max(5.0, composite_risk_index)), 1)

        # 5. Standardized Severity / Threat Tier Mapping
        if composite_risk_index >= 75.0 or (z_score >= 3.5 and escalation_state == "CRITICAL_ESCALATION"):
            threat_tier = "CRITICAL"
            operational_status = "REQUIRES_VERIFICATION"
        elif composite_risk_index >= 55.0 or z_score >= 2.0 or escalation_state == "ESCALATING":
            threat_tier = "HIGH"
            operational_status = "WATCH"
        elif composite_risk_index >= 35.0 or z_score >= 1.0:
            threat_tier = "WATCH"
            operational_status = "MONITORING"
        else:
            threat_tier = "NORMAL"
            operational_status = "NORMAL"

        return {
            "fusion_architecture": "Hybrid HGB (Spatial) + LSTM (Temporal) + Rolling 90D Baseline",
            "weights": {
                "hgb_spatial_context": round(self.w_hgb, 2),
                "lstm_temporal_evolution": round(self.w_lstm, 2),
                "facility_baseline_deviation": round(self.w_base, 2),
            },
            "threat_tier": threat_tier,
            "operational_status": operational_status,
            "composite_risk_index": composite_risk_index,
            "temporal_escalation_state": escalation_state,
            "baseline_deviation_z": round(z_score, 2),
            "hgb_classification": {
                "label": hgb_label,
                "confidence": round(hgb_conf, 3),
                "role_summary": "Identified industrial facility spatial context and land-cover signatures."
            },
            "lstm_temporal_intelligence": {
                "state": escalation_state,
                "trend_slope_mw_per_pass": slope,
                "temporal_risk": temporal_risk,
                "role_summary": "Modeled multi-pass thermal trajectory and acceleration."
            },
            "explainable_fusion_dossier": (
                f"Combined HGB spatial classification ({hgb_label}, {round(hgb_conf*100)}% conf) "
                f"with LSTM temporal dynamics ({escalation_state}, {round(slope,1)} MW/pass) "
                f"and 90-day facility baseline deviation (+{round(z_score,2)}σ). "
                f"Operational risk index computed at {composite_risk_index}/100 [{threat_tier}]."
            )
        }


# Global fusion layer instance
hybrid_fusion_layer = HybridAIFusionLayer()
