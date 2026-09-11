"""
Closed-Loop Adaptive Intelligence — Analyst Feedback Collector.
Captures human-in-the-loop audit decisions and builds the verified ground-truth dataset for retraining.
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger("thermotrace.feedback")

FEEDBACK_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "feedback")
FEEDBACK_FILE = os.path.join(FEEDBACK_DIR, "analyst_feedback.json")


def _ensure_storage():
    os.makedirs(FEEDBACK_DIR, exist_ok=True)
    if not os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "schema_version": "1.0",
                "last_updated_utc": datetime.now(timezone.utc).isoformat(),
                "total_feedbacks": 0,
                "verified_ground_truth": []
            }, f, indent=2)


def record_analyst_decision(
    event_id: str,
    action: str,  # 'CONFIRM' | 'REJECT' | 'RECLASSIFY'
    analyst_id: str,
    original_label: str,
    corrected_label: str,
    confidence: float,
    notes: Optional[str] = None,
    features: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Log an analyst's ground-truth verification into the closed-loop dataset.
    """
    _ensure_storage()
    now_utc = datetime.now(timezone.utc).isoformat()

    entry = {
        "feedback_id": f"FB-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{event_id[:8]}",
        "event_id": event_id,
        "action": action,
        "analyst_id": analyst_id,
        "original_label": original_label,
        "corrected_label": corrected_label,
        "confidence": confidence,
        "notes": notes or "Analyst audit validation",
        "features": features or {},
        "timestamp_utc": now_utc,
        "used_in_retraining": False,
    }

    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        data["verified_ground_truth"].append(entry)
        data["total_feedbacks"] = len(data["verified_ground_truth"])
        data["last_updated_utc"] = now_utc

        with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return {"status": "RECORDED", "entry": entry, "total_feedback_samples": data["total_feedbacks"]}
    except Exception as e:
        logger.error("Failed to store analyst feedback: %s", e)
        return {"status": "ERROR", "message": str(e)}


def get_feedback_statistics() -> Dict[str, Any]:
    """Returns feedback metrics and readiness for scheduled retraining."""
    _ensure_storage()
    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        records = data.get("verified_ground_truth", [])
        unprocessed = [r for r in records if not r.get("used_in_retraining", False)]

        confirms = sum(1 for r in records if r.get("action") == "CONFIRM")
        rejects = sum(1 for r in records if r.get("action") == "REJECT")
        reclassifies = sum(1 for r in records if r.get("action") == "RECLASSIFY")

        return {
            "total_verified_events": len(records),
            "unprocessed_for_retraining": len(unprocessed),
            "confirm_count": confirms,
            "reject_count": rejects,
            "reclassify_count": reclassifies,
            "retraining_recommended": len(unprocessed) >= 5,
            "last_updated_utc": data.get("last_updated_utc"),
        }
    except Exception as e:
        return {"error": str(e), "total_verified_events": 0}
