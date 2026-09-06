from pathlib import Path
import pandas as pd


def load_csv(path):
    """Load a CSV file into a pandas DataFrame."""
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    return pd.read_csv(path)


def save_csv(dataframe, path):
    """Save a DataFrame to CSV, creating the parent folder if needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(path, index=False)


def validate_unique_ids(dataframe, column):
    """Check that an ID column contains no missing or duplicate values."""
    if dataframe[column].isna().any():
        raise ValueError(f"Missing values found in {column}.")

    if dataframe[column].duplicated().any():
        raise ValueError(f"Duplicate values found in {column}.")

    return True


def observation_days(start_time, end_time):
    """Return the number of calendar days between two timestamps."""
    start_time = pd.to_datetime(start_time)
    end_time = pd.to_datetime(end_time)

    return (end_time - start_time).days + 1