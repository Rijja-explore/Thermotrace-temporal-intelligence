"""
schemas.py – Pydantic data models for ThermoTrace Temporal Intelligence.

All input/output data contracts are defined here.
These schemas are shared across modules and used for validation.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class AnomalyLevel(str, Enum):
    NORMAL = "normal"
    WATCH = "watch"
    ABNORMAL = "abnormal"
    SEVERE = "severe"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertType(str, Enum):
    NEW_INDUSTRIAL_EVENT = "NEW_INDUSTRIAL_EVENT"
    PERSISTENT_SOURCE = "PERSISTENT_SOURCE"
    ABNORMAL_INCREASE = "ABNORMAL_INCREASE"
    HIGH_OPERATIONAL_RISK = "HIGH_OPERATIONAL_RISK"
    UNKNOWN_REQUIRES_VERIFICATION = "UNKNOWN_REQUIRES_VERIFICATION"
    NONE = "NONE"


class AlertPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    NONE = "NONE"


class AlertStatus(str, Enum):
    NEW = "NEW"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    INVESTIGATING = "INVESTIGATING"
    CLOSED = "CLOSED"


class HistoryQuality(str, Enum):
    GOOD = "good"
    MODERATE = "moderate"
    POOR = "poor"
    INSUFFICIENT = "insufficient"


# ---------------------------------------------------------------------------
# Input Observation
# ---------------------------------------------------------------------------

class Observation(BaseModel):
    """
    Normalised thermal observation from Person 1 (data-ingestion pipeline).
    All fields are optional except observation_id, latitude, longitude, timestamp_utc.
    """

    observation_id: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    timestamp_utc: datetime

    # Fire radiative power (MW) – may be absent for low-quality detections
    frp: Optional[float] = Field(default=None, ge=0.0)
    # Detection confidence 0–100
    confidence: Optional[float] = Field(default=None, ge=0.0, le=100.0)

    satellite: Optional[str] = None
    sensor: Optional[str] = None
    source: Optional[str] = None

    facility_id: Optional[str] = None
    facility_type: Optional[str] = None
    facility_distance_km: Optional[float] = Field(default=None, ge=0.0)
    landcover_class: Optional[str] = None

    @field_validator("timestamp_utc", mode="before")
    @classmethod
    def parse_timestamp(cls, v: Any) -> datetime:
        if isinstance(v, datetime):
            return v
        try:
            from dateutil import parser as dateutil_parser
            dt = dateutil_parser.parse(str(v))
            # Ensure timezone-naive for internal processing
            if dt.tzinfo is not None:
                import pytz  # type: ignore[import-untyped]
                dt = dt.astimezone(pytz.utc).replace(tzinfo=None)
            return dt
        except Exception as exc:
            raise ValueError(f"Cannot parse timestamp '{v}': {exc}") from exc

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Thermal Event
# ---------------------------------------------------------------------------

class ThermalEvent(BaseModel):
    """Represents a cluster of spatially and temporally proximate observations."""

    event_id: str
    cluster_id: int
    observation_ids: list[str]
    centroid_latitude: float
    centroid_longitude: float
    start_time: datetime
    end_time: datetime
    observation_count: int
    duration_hours: float
    spatial_extent_km: float

    # FRP statistics across the event
    frp_mean: Optional[float] = None
    frp_max: Optional[float] = None
    frp_min: Optional[float] = None
    frp_std: Optional[float] = None

    # Source metadata
    satellites: list[str] = Field(default_factory=list)
    sensors: list[str] = Field(default_factory=list)
    facility_id: Optional[str] = None
    facility_type: Optional[str] = None
    facility_distance_km: Optional[float] = None
    landcover_class: Optional[str] = None


# ---------------------------------------------------------------------------
# Temporal Features
# ---------------------------------------------------------------------------

class TemporalWindow(BaseModel):
    """Temporal feature set for a specific look-back window."""

    window_days: int
    window_label: str  # e.g. "7d", "30d", "90d"
    start: Optional[datetime] = None
    end: Optional[datetime] = None

    detection_count: int = 0
    active_days: int = 0
    monitored_days: int = 0
    persistence_ratio: Optional[float] = None  # None if monitored_days == 0

    duration_hours_total: float = 0.0

    frp_mean: Optional[float] = None
    frp_median: Optional[float] = None
    frp_max: Optional[float] = None
    frp_min: Optional[float] = None
    frp_std: Optional[float] = None
    frp_p90: Optional[float] = None
    frp_p95: Optional[float] = None

    spatial_extent_km: Optional[float] = None
    spatial_stability_score: Optional[float] = None  # 0–100

    detection_frequency: Optional[float] = None  # detections per day
    days_since_last_detection: Optional[float] = None

    # Distribution metadata
    day_count: int = 0
    night_count: int = 0
    hour_distribution: dict[int, int] = Field(default_factory=dict)
    weekday_count: int = 0
    weekend_count: int = 0
    sensor_distribution: dict[str, int] = Field(default_factory=dict)


class TemporalFeatures(BaseModel):
    """All temporal features for an event or facility window."""

    event_id: Optional[str] = None
    facility_id: Optional[str] = None
    analysis_end: Optional[datetime] = None

    window_7d: TemporalWindow
    window_30d: TemporalWindow
    window_90d: TemporalWindow


# ---------------------------------------------------------------------------
# Spatial Stability
# ---------------------------------------------------------------------------

class SpatialStability(BaseModel):
    centroid_lat: float
    centroid_lon: float
    mean_distance_km: float
    max_distance_km: float
    radius_km: float
    stability_score: float  # 0–100; higher = more stable


# ---------------------------------------------------------------------------
# Facility Thermal Fingerprint
# ---------------------------------------------------------------------------

class FacilityFingerprint(BaseModel):
    """Historical thermal behaviour summary for a facility."""

    facility_id: str
    facility_type: Optional[str] = None
    observation_count: int
    active_days: int
    baseline_start: Optional[datetime] = None
    baseline_end: Optional[datetime] = None

    normal_detection_frequency: Optional[float] = None
    normal_frp_mean: Optional[float] = None
    normal_frp_median: Optional[float] = None
    normal_frp_std: Optional[float] = None
    normal_frp_p90: Optional[float] = None
    normal_frp_p95: Optional[float] = None
    normal_active_hours: Optional[dict[int, float]] = None  # hour -> proportion
    normal_spatial_extent: Optional[float] = None

    history_quality: HistoryQuality = HistoryQuality.INSUFFICIENT


# ---------------------------------------------------------------------------
# Baseline
# ---------------------------------------------------------------------------

class Baseline(BaseModel):
    """Baseline statistics computed from historical data (no current-period leakage)."""

    available: bool
    facility_id: Optional[str] = None
    baseline_period_start: Optional[datetime] = None
    baseline_period_end: Optional[datetime] = None

    frp_mean: Optional[float] = None
    frp_median: Optional[float] = None
    frp_std: Optional[float] = None
    frp_upper_quantile: Optional[float] = None
    frp_lower_quantile: Optional[float] = None

    detection_frequency: Optional[float] = None
    active_days_ratio: Optional[float] = None
    spatial_extent_mean: Optional[float] = None

    history_count: int = 0
    history_quality: HistoryQuality = HistoryQuality.INSUFFICIENT
    notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Deviation (current vs baseline)
# ---------------------------------------------------------------------------

class Deviation(BaseModel):
    frp_deviation: Optional[float] = None
    frp_deviation_percent: Optional[float] = None
    frequency_deviation: Optional[float] = None
    frequency_deviation_percent: Optional[float] = None
    active_day_deviation: Optional[float] = None
    spatial_deviation: Optional[float] = None
    notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Anomaly
# ---------------------------------------------------------------------------

class AnomalyResult(BaseModel):
    anomaly_score: float  # 0–100
    anomaly_level: AnomalyLevel
    reasons: list[str] = Field(default_factory=list)
    component_scores: dict[str, float] = Field(default_factory=dict)
    data_quality_notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Industrial Likelihood
# ---------------------------------------------------------------------------

class IndustrialLikelihood(BaseModel):
    score: float  # 0–100
    requires_verification: bool
    component_scores: dict[str, float] = Field(default_factory=dict)
    evidence_for: list[str] = Field(default_factory=list)
    evidence_against: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Operational Risk
# ---------------------------------------------------------------------------

class OperationalRisk(BaseModel):
    risk_score: float  # 0–100
    risk_level: RiskLevel
    score_confidence: str  # "full", "partial", "minimal"
    available_components: list[str] = Field(default_factory=list)
    missing_components: list[str] = Field(default_factory=list)
    component_contributions: dict[str, float] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

class EvidenceBundle(BaseModel):
    evidence_for: list[str] = Field(default_factory=list)
    evidence_against: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Alert
# ---------------------------------------------------------------------------

class Alert(BaseModel):
    alert_id: str
    event_id: Optional[str] = None
    facility_id: Optional[str] = None
    alert_type: AlertType
    priority: AlertPriority
    reason: str
    risk_score: float
    anomaly_score: float
    industrial_likelihood: float
    created_at: datetime
    recommended_action: str
    status: AlertStatus = AlertStatus.NEW


# ---------------------------------------------------------------------------
# Canonical Pipeline Output
# ---------------------------------------------------------------------------

class LocationInfo(BaseModel):
    latitude: float
    longitude: float


class TimeWindow(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None


class FacilityInfo(BaseModel):
    facility_id: Optional[str] = None
    facility_type: Optional[str] = None
    distance_km: Optional[float] = None


class PipelineOutput(BaseModel):
    """
    Canonical JSON-compatible output for the ThermoTrace temporal intelligence pipeline.
    Consumed by Person 2 (ML features) and Person 4 (API/frontend).
    """

    event_id: str
    location: LocationInfo
    time_window: TimeWindow
    temporal_features: dict[str, Any]  # Serialised TemporalFeatures
    facility: FacilityInfo
    baseline: dict[str, Any]  # Serialised Baseline
    deviation: dict[str, Any]  # Serialised Deviation
    anomaly: dict[str, Any]  # Serialised AnomalyResult
    industrial_likelihood: dict[str, Any]  # Serialised IndustrialLikelihood
    operational_risk: dict[str, Any]  # Serialised OperationalRisk
    alert: dict[str, Any]  # Serialised Alert
    evidence: dict[str, Any]  # Serialised EvidenceBundle
    recommendation: str
    metadata: dict[str, str]

    def to_json_dict(self) -> dict[str, Any]:
        """Return a fully JSON-serialisable dictionary."""
        import json

        def default(o: Any) -> Any:
            if isinstance(o, datetime):
                return o.isoformat()
            if isinstance(o, Enum):
                return o.value
            raise TypeError(f"Object of type {type(o)} is not JSON serialisable")

        raw = self.model_dump()
        # Round-trip through JSON to coerce enums, datetimes etc.
        return json.loads(json.dumps(raw, default=default))
