"""
ThermoTrace 4-Engine Hybrid AI Fusion Layer.
Combines:
  - Engine 1: Learned Persistent Source ML Fingerprint (WHAT TYPE OF SOURCE IS THIS?)
  - Engine 2: Rolling 90-Day Facility Baseline Deviation / Z-score (IS IT ABNORMAL HERE?)
  - Engine 3: Sequential PyTorch LSTM Temporal Engine (IS IT ESCALATING?)
  - Engine 4: Contextual HistGradientBoosting Classifier (GENERAL SPATIAL/LAND-COVER CLASSIFICATION)

Architectural Division of Concerns:
  - Engine 1 determines whether the multi-feature fingerprint behaves like a persistent industrial source (flares, kilns, smelters).
  - Engine 2 determines whether the current thermal intensity is statistically abnormal relative to the facility's learned 90-day baseline.
  - Engine 3 determines whether the multi-pass satellite trajectory is accelerating/surging over time.
  - Engine 4 determines the contextual classification probability vector across environmental & industrial classes.
"""

from typing import Dict, Any, List, Optional
import numpy as np


class HybridAIFusionLayer:
    """
    Unified 4-Engine Decision Intelligence Fusion Layer.
    Fuses persistent fingerprint probabilities, baseline z-scores, sequential LSTM trends,
    and contextual classifier outputs into a unified Composite Risk Index and Threat Tier.
    """

    def __init__(
        self,
        weight_persistent_ml: float = 0.25,
        weight_facility_baseline: float = 0.30,
        weight_lstm_temporal: float = 0.25,
        weight_hgb_contextual: float = 0.20
    ):
        total = weight_persistent_ml + weight_facility_baseline + weight_lstm_temporal + weight_hgb_contextual
        self.w_pers = weight_persistent_ml / total
        self.w_base = weight_facility_baseline / total
        self.w_lstm = weight_lstm_temporal / total
        self.w_hgb = weight_hgb_contextual / total

    def fuse_event_intelligence(
        self,
        hgb_prediction: Dict[str, Any],
        lstm_prediction: Dict[str, Any],
        baseline_stats: Dict[str, Any],
        current_frp: float,
        persistent_prediction: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes unified 4-engine multimodal fusion.

        Parameters
        ----------
        hgb_prediction : Dict[str, Any]
            Output of Engine 4 (Contextual HGB Classifier: label, confidence).
        lstm_prediction : Dict[str, Any]
            Output of Engine 3 (PyTorch Sequential LSTM: escalation_state, slope, temporal_risk).
        baseline_stats : Dict[str, Any]
            Output of Engine 2 (Facility 90-Day Baseline: mean_frp, std_frp).
        current_frp : float
            Current satellite pass Fire Radiative Power (MW).
        persistent_prediction : Dict[str, Any], optional
            Output of Engine 1 (Persistent Source ML: persistence_probability, category).
        """
        # 1. Engine 1: Persistent Source ML Fingerprint
        if persistent_prediction is None:
            from services.classification.persistent_fingerprint import persistent_fingerprinter
            persistent_prediction = persistent_fingerprinter.predict_persistence({
                "mean_frp_mw": current_frp,
                "distance_to_facility_km": baseline_stats.get("distance_to_facility_km", 0.2),
                "detection_frequency": baseline_stats.get("daily_detection_frequency", 0.85),
                "day_night_ratio": baseline_stats.get("day_night_ratio", 0.70),
                "persistence_ratio_90d": baseline_stats.get("persistence_pct", 80.0) / 100.0,
            })

        p_persistent = float(persistent_prediction.get("persistence_probability", 0.85))
        pers_category = persistent_prediction.get("persistence_category", "PERSISTENT")

        # 2. Engine 2: Facility 90-Day Baseline Deviation (Z-score)
        base_mean = float(baseline_stats.get("mean_frp", baseline_stats.get("rolling_frp_mean", 80.0)))
        base_std = max(1.0, float(baseline_stats.get("std_frp", baseline_stats.get("rolling_frp_std", 18.0))))
        z_score = (current_frp - base_mean) / base_std
        # Standardized baseline abnormality score [0.0 - 1.0]
        baseline_anomaly_score = min(1.0, max(0.0, z_score / 5.0))

        # 3. Engine 3: Sequential PyTorch LSTM Temporal Dynamics
        escalation_state = lstm_prediction.get("escalation_state", "STABLE")
        temporal_risk = float(lstm_prediction.get("temporal_risk_score", 30.0))
        slope = float(lstm_prediction.get("frp_trend_slope_mw_per_pass", lstm_prediction.get("trend_slope_mw_per_day", 0.0)))
        temporal_anomaly_signal = temporal_risk / 100.0

        # 4. Engine 4: Contextual HistGradientBoosting Spatial/Land-Cover
        hgb_label = hgb_prediction.get("label", "industrial_flaring")
        hgb_conf = float(hgb_prediction.get("confidence", 0.85))
        is_industrial_type = any(term in hgb_label.lower() for term in ["industrial", "refinery", "plant", "flare"])
        spatial_anomaly_signal = hgb_conf if is_industrial_type else (hgb_conf * 0.4)

        # 5. Core 4-Engine Decision Synthesis
        # Normal Persistent Source Case:
        # High persistence probability (looks like a flare), but Z-score is normal (within operating bounds) and LSTM is stable.
        is_normal_persistent_source = (
            p_persistent >= 0.60 and
            z_score <= 1.8 and
            escalation_state in ["STABLE", "NORMAL"]
        )

        # Abnormal Persistent Source Case (e.g. flare runaway or blast furnace failure):
        # High persistence probability, but Z-score is extreme (+3.0σ) OR LSTM shows critical escalation.
        is_abnormal_persistent_event = (
            p_persistent >= 0.60 and
            (z_score >= 3.0 or escalation_state == "CRITICAL_ESCALATION" or (z_score >= 2.0 and escalation_state == "ESCALATING"))
        )

        if is_normal_persistent_source:
            # Suppress false alarms on routine industrial operations
            composite_risk_index = round(min(30.0, max(5.0, 15.0 + (z_score * 5.0))), 1)
            threat_tier = "NORMAL"
            operational_status = "ROUTINE_MONITORING"
            final_assessment = "NORMAL_PERSISTENT_INDUSTRIAL_SOURCE"
            decision_rationale = (
                f"Engine 1 confirmed persistent industrial source (P_pers={round(p_persistent*100)}%). "
                f"Engine 2 verified thermal intensity is within normal 90-day operating baseline (Z={round(z_score, 2)}σ, μ={base_mean} MW). "
                f"Engine 3 confirmed stable temporal dynamics ({escalation_state}). Routine monitoring maintained."
            )
        elif is_abnormal_persistent_event:
            # Critical emergency: Persistent stack exhibiting major thermal surge
            composite_risk_index = round(min(100.0, max(75.0, 70.0 + (z_score * 2.0) + (temporal_anomaly_signal * 15.0))), 1)
            threat_tier = "CRITICAL"
            operational_status = "REQUIRES_VERIFICATION"
            final_assessment = "ABNORMAL_INDUSTRIAL_EVENT"
            decision_rationale = (
                f"Engine 1 confirmed persistent industrial source (P_pers={round(p_persistent*100)}%). "
                f"Engine 2 detected severe baseline anomaly (Z=+{round(z_score, 2)}σ above {base_mean} MW mean). "
                f"Engine 3 detected critical temporal escalation ({escalation_state}, slope +{round(slope,1)} MW/pass). "
                f"High-priority incident dossier dispatched for analyst verification."
            )
        else:
            # Standard multi-weighted risk calculation
            composite_risk_index = (
                (self.w_pers * p_persistent * 100.0) +
                (self.w_base * baseline_anomaly_score * 100.0) +
                (self.w_lstm * temporal_anomaly_signal * 100.0) +
                (self.w_hgb * spatial_anomaly_signal * 100.0)
            )
            composite_risk_index = round(min(100.0, max(5.0, composite_risk_index)), 1)

            if composite_risk_index >= 70.0 or z_score >= 3.5:
                threat_tier = "CRITICAL"
                operational_status = "REQUIRES_VERIFICATION"
                final_assessment = "HIGH_SEVERITY_THERMAL_EVENT"
            elif composite_risk_index >= 50.0 or z_score >= 1.8 or escalation_state == "ESCALATING":
                threat_tier = "HIGH"
                operational_status = "WATCH"
                final_assessment = "ELEVATED_THERMAL_ANOMALY"
            elif composite_risk_index >= 30.0 or z_score >= 0.8:
                threat_tier = "WATCH"
                operational_status = "MONITORING"
                final_assessment = "MODERATE_THERMAL_ACTIVITY"
            else:
                threat_tier = "NORMAL"
                operational_status = "NORMAL"
                final_assessment = "TRANSIENT_OR_BACKGROUND_ACTIVITY"

            decision_rationale = (
                f"Integrated 4-engine assessment: Engine 1 P_pers={round(p_persistent*100)}%, "
                f"Engine 2 Z={round(z_score, 2)}σ, Engine 3 State={escalation_state}, "
                f"Engine 4 Class={hgb_label} ({round(hgb_conf*100)}% conf)."
            )

        return {
            "fusion_architecture": "ThermoTrace 4-Engine Decision Intelligence Pipeline",
            "four_engines": {
                "engine_1_persistent_ml": {
                    "persistence_probability": p_persistent,
                    "persistence_category": pers_category,
                    "role": "Identifies long-term behavioural fingerprint (WHAT TYPE OF SOURCE?)"
                },
                "engine_2_facility_baseline": {
                    "baseline_mean_mw": base_mean,
                    "baseline_std_mw": base_std,
                    "deviation_z": round(z_score, 2),
                    "role": "Determines statistical abnormality relative to 90-day facility envelope (IS IT ABNORMAL HERE?)"
                },
                "engine_3_lstm_temporal": {
                    "escalation_state": escalation_state,
                    "temporal_anomaly_score": float(lstm_prediction.get("temporal_anomaly_score", 0.30)),
                    "escalation_probability": float(lstm_prediction.get("escalation_probability", 0.25)),
                    "trend_slope_mw_per_pass": round(slope, 1),
                    "acceleration_mw_per_pass2": float(lstm_prediction.get("frp_acceleration_mw_per_pass2", 0.0)),
                    "prediction_error_mw": float(lstm_prediction.get("prediction_error_mw", 0.0)),
                    "temporal_risk_score": temporal_risk,
                    "role": "Determines multi-pass trajectory, acceleration & autoregressive error (IS IT ESCALATING?)"
                },
                "engine_4_hgb_contextual": {
                    "label": hgb_label,
                    "confidence": round(hgb_conf, 3),
                    "role": "Evaluates macro spatial, infrastructure, and land-cover signatures"
                }
            },
            "weights": {
                "engine_1_persistent_ml": round(self.w_pers, 2),
                "engine_2_facility_baseline": round(self.w_base, 2),
                "engine_3_lstm_temporal": round(self.w_lstm, 2),
                "engine_4_hgb_contextual": round(self.w_hgb, 2)
            },
            "threat_tier": threat_tier,
            "operational_status": operational_status,
            "final_assessment": final_assessment,
            "composite_risk_index": composite_risk_index,
            "baseline_deviation_z": round(z_score, 2),
            "temporal_escalation_state": escalation_state,
            "persistence_probability": p_persistent,
            "explainable_fusion_dossier": decision_rationale
        }


# Global 4-engine hybrid fusion layer instance
hybrid_fusion_layer = HybridAIFusionLayer()
