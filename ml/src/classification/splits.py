import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from typing import Tuple

def random_split(df: pd.DataFrame, test_size=0.2, random_state=42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    return train_test_split(df, test_size=test_size, random_state=random_state)

def chronological_split(df: pd.DataFrame, date_col='start_time', test_ratio=0.2) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df_sorted = df.sort_values(date_col)
    split_idx = int(len(df_sorted) * (1 - test_ratio))
    return df_sorted.iloc[:split_idx], df_sorted.iloc[split_idx:]

def unseen_facility_split(df: pd.DataFrame, facility_id_col='nearest_facility_id', test_ratio=0.2, random_state=42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    # Extract non-null facilities
    valid_mask = df[facility_id_col].notna() & (df[facility_id_col] != "")
    facilities = df.loc[valid_mask, facility_id_col].unique()
    
    if len(facilities) == 0:
        # If no facility IDs exist, fallback to random split
        return random_split(df, test_size=test_ratio, random_state=random_state)
        
    # Split the facilities deterministically
    train_fac, test_fac = train_test_split(facilities, test_size=test_ratio, random_state=random_state)
    
    # Guarantee mathematically that no intersection exists
    intersection = set(train_fac).intersection(set(test_fac))
    if intersection:
        raise ValueError("Leakage detected: train and test facilities overlap")
        
    # Match events to train/test facilities
    train_df = df[df[facility_id_col].isin(train_fac)].copy()
    test_df = df[df[facility_id_col].isin(test_fac)].copy()
    
    # unmatched events (NaN facility IDs) are strictly routed to train
    unmatched_df = df[~valid_mask].copy()
    train_df = pd.concat([train_df, unmatched_df])
    
    return train_df, test_df
