"""
ThermoTrace Feature Engineering I/O Utilities
=============================================

Memory-safe I/O utilities for reading and writing Parquet, GeoPackage, and JSON datasets.
"""

from pathlib import Path
import json
import pandas as pd
import pyarrow.parquet as pq

def read_parquet_safe(file_path: Path, columns: list = None) -> pd.DataFrame:
    """Reads a Parquet file safely with optional column projection."""
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"Parquet file not found at: {p}")
    return pd.read_parquet(p, columns=columns)

def write_parquet_safe(df: pd.DataFrame, file_path: Path, compression: str = "snappy"):
    """Writes a DataFrame to Parquet with directory creation and Snappy compression."""
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(p, index=False, compression=compression)

def save_json_safe(data: dict, file_path: Path, indent: int = 2):
    """Saves a dictionary as formatted JSON with UTF-8 encoding."""
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=indent), encoding="utf-8")
