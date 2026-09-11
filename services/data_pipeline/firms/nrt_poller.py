"""
NASA FIRMS Near-Real-Time Ingestion Poller & Deduplicator.
Ensures observations are uniquely indexed and dispatches new clusters into the intelligence pipeline.
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Set
from .firms_client import FIRMSClient

logger = logging.getLogger("thermotrace.nrt_poller")


class NRTPoller:
    def __init__(self, client: FIRMSClient = None):
        self.client = client or FIRMSClient()
        self.seen_observation_keys: Set[str] = set()
        self.ingested_count: int = 0
        self.last_poll_time: Optional[datetime] = None
        self._init_cache()

    def _init_cache(self):
        """Pre-populate deduplication keys from local storage."""
        cache_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "apps", "backend", "firms_data.json")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    items = data if isinstance(data, list) else data.get("observations", [])
                    for item in items:
                        key = self._generate_key(item)
                        self.seen_observation_keys.add(key)
            except Exception:
                pass

    def _generate_key(self, obs: Dict[str, Any]) -> str:
        lat = round(float(obs.get("latitude", obs.get("lat", 0.0))), 4)
        lon = round(float(obs.get("longitude", obs.get("lon", 0.0))), 4)
        acq_date = obs.get("acq_date", "")
        acq_time = str(obs.get("acq_time", ""))
        satellite = obs.get("satellite", "")
        return f"{lat}_{lon}_{acq_date}_{acq_time}_{satellite}"

    def poll_and_deduplicate(self) -> Dict[str, Any]:
        """
        Polls NASA FIRMS NRT sources, filters duplicates, and returns fresh observations.
        """
        self.last_poll_time = datetime.now(timezone.utc)
        raw_observations = self.client.fetch_area_nrt()
        new_records: List[Dict[str, Any]] = []

        for obs in raw_observations:
            key = self._generate_key(obs)
            if key not in self.seen_observation_keys:
                self.seen_observation_keys.add(key)
                new_records.append(obs)

        self.ingested_count += len(new_records)

        return {
            "poll_timestamp_utc": self.last_poll_time.isoformat(),
            "raw_received_count": len(raw_observations),
            "new_unique_observations": len(new_records),
            "total_seen_keys": len(self.seen_observation_keys),
            "telemetry": self.client.get_pipeline_telemetry(),
            "new_observations": new_records,
        }


# Global poller instance
nrt_poller = NRTPoller()
