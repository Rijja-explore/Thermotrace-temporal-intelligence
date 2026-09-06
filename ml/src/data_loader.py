import pandas as pd
from pathlib import Path

def load_v2_features(filepath: str | Path) -> pd.DataFrame:
    """Loads the canonical event_features_v2 dataset and performs sanity checks."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Feature dataset not found at {path}")
    
    df = pd.read_parquet(path)
    
    if "event_id" not in df.columns:
        raise ValueError("Critical column 'event_id' missing from feature dataset.")
        
    if not df["event_id"].is_unique:
        raise ValueError("Duplicate event_ids detected in the canonical dataset.")
        
    return df
