"""
Shared test fixtures and helpers for ThermoTrace temporal intelligence tests.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Make sure src/ is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from thermotrace_temporal.schemas import Observation


def make_obs(
    obs_id: str,
    lat: float = 19.123,
    lon: float = 73.456,
    dt: datetime = datetime(2026, 1, 15, 8, 0, 0),
    frp: float | None = 50.0,
    confidence: float | None = 90.0,
    facility_id: str | None = "FAC-001",
    facility_type: str | None = "refinery",
    facility_distance_km: float | None = 0.5,
    landcover_class: str | None = "industrial",
    satellite: str = "NOAA-20",
    sensor: str = "VIIRS",
) -> Observation:
    return Observation(
        observation_id=obs_id,
        latitude=lat,
        longitude=lon,
        timestamp_utc=dt,
        frp=frp,
        confidence=confidence,
        facility_id=facility_id,
        facility_type=facility_type,
        facility_distance_km=facility_distance_km,
        landcover_class=landcover_class,
        satellite=satellite,
        sensor=sensor,
        source="TEST",
    )


def make_obs_list(
    n: int,
    base_dt: datetime = datetime(2026, 1, 10, 8, 0, 0),
    interval_hours: float = 24.0,
    frp_base: float | None = 50.0,
    **kwargs,
) -> list[Observation]:
    """Create n observations evenly spaced in time."""
    obs = []
    for i in range(n):
        dt = base_dt + timedelta(hours=i * interval_hours)
        frp = (frp_base + i) if frp_base is not None else None
        obs.append(make_obs(f"OBS-{i:04d}", dt=dt, frp=frp, **kwargs))
    return obs
