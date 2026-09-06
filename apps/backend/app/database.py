"""
Database connection management for ThermoTrace.
Uses asyncpg connection pool when PostGIS is available,
falls back to JSON file when the database is unavailable.
"""
import os
import json
import asyncpg
from typing import Optional

_pool: Optional[asyncpg.Pool] = None
_db_available = True

DB_CONFIG = {
    "user": os.getenv("DB_USER", "thermotrace"),
    "password": os.getenv("DB_PASSWORD", "thermopassword"),
    "database": os.getenv("DB_NAME", "thermotrace"),
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "5432")),
}

FALLBACK_JSON = os.path.join(os.path.dirname(__file__), "..", "firms_data.json")


async def get_pool() -> Optional[asyncpg.Pool]:
    """Get or create the connection pool."""
    global _pool, _db_available
    if not _db_available:
        return None
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(
                min_size=2,
                max_size=10,
                **DB_CONFIG,
            )
        except Exception as e:
            print(f"[DB] Could not connect to PostGIS: {e}")
            _db_available = False
            return None
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def load_fallback_events() -> list:
    """Load events from the cached JSON when the DB is not available."""
    if os.path.exists(FALLBACK_JSON):
        try:
            with open(FALLBACK_JSON, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []
