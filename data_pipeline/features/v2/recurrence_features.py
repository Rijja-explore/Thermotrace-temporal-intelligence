"""
ThermoTrace Feature Engineering V2: Recurrence & Historical Thermal Activity
============================================================================

Computes leak-free historical recurrence indicators across 7-day, 30-day,
and 90-day backward horizons within a localized 0.05-degree spatial neighborhood.

Zero Temporal Leakage Guarantee:
For event timestamp T, strictly events with timestamp < T are evaluated.
"""

import numpy as np
import pandas as pd

def extract_v2_recurrence_features(df: pd.DataFrame, cell_size_deg: float = 0.05) -> pd.DataFrame:
    """
    Computes historical event counts, cumulative FRP, active days, and time since previous event.
    Guarantees zero data leakage by sorting chronologically and restricting windows to t < T.
    """
    n_total = len(df)
    
    # 1. Parse timestamps and compute epoch days
    dt_series = pd.to_datetime(df["start_time"])
    epoch_days = dt_series.values.astype("datetime64[s]").astype(np.float64) / 86400.0
    
    # 2. Local spatial cell indices (~5.5km grid)
    cell_x = np.floor(df["centroid_lon"].values / cell_size_deg).astype(np.int32)
    cell_y = np.floor(df["centroid_lat"].values / cell_size_deg).astype(np.int32)
    
    # 3. Sort chronologically
    sort_order = np.argsort(epoch_days)
    inv_sort = np.empty_like(sort_order)
    inv_sort[sort_order] = np.arange(n_total)
    
    sorted_days = epoch_days[sort_order]
    sorted_frp = df["sum_frp_mw"].values[sort_order].astype(np.float32)
    sorted_cx = cell_x[sort_order]
    sorted_cy = cell_y[sort_order]
    
    # Output arrays (in sorted order)
    ev_7d = np.zeros(n_total, dtype=np.int32)
    ev_30d = np.zeros(n_total, dtype=np.int32)
    ev_90d = np.zeros(n_total, dtype=np.int32)
    frp_7d = np.zeros(n_total, dtype=np.float32)
    frp_30d = np.zeros(n_total, dtype=np.float32)
    frp_90d = np.zeros(n_total, dtype=np.float32)
    act_7d = np.zeros(n_total, dtype=np.int16)
    act_30d = np.zeros(n_total, dtype=np.int16)
    act_90d = np.zeros(n_total, dtype=np.int16)
    time_since_prev = np.full(n_total, 9999.0, dtype=np.float32)
    
    # Group by cell using compound key
    cell_keys = (sorted_cy.astype(np.int64) << 32) | (sorted_cx.astype(np.int64) & 0xFFFFFFFF)
    
    # Efficient contiguous grouping
    # Because events are sorted by time, find group indices
    sorted_cell_idx = np.argsort(cell_keys, kind="stable")
    sorted_by_cell_keys = cell_keys[sorted_cell_idx]
    
    # Unique cell boundaries
    diff_mask = np.concatenate(([True], sorted_by_cell_keys[1:] != sorted_by_cell_keys[:-1], [True]))
    cell_boundaries = np.where(diff_mask)[0]
    
    for b_i in range(len(cell_boundaries) - 1):
        c_start = cell_boundaries[b_i]
        c_end = cell_boundaries[b_i + 1]
        if c_end - c_start <= 1:
            continue
            
        grp_order = sorted_cell_idx[c_start:c_end]
        # Sort group chronologically
        grp_order = grp_order[np.argsort(sorted_days[grp_order])]
        
        t_vals = sorted_days[grp_order]
        f_vals = sorted_frp[grp_order]
        cal_days = np.floor(t_vals).astype(np.int32)
        frp_cumsum = np.concatenate(([0.0], np.cumsum(f_vals)))
        k = len(grp_order)
        
        for i in range(1, k):
            target_pos = grp_order[i]
            t_cur = t_vals[i]
            time_since_prev[target_pos] = (t_cur - t_vals[i-1]) * 24.0
            
            # 7d
            s7 = np.searchsorted(t_vals[:i], t_cur - 7.0, side="left")
            ev_7d[target_pos] = i - s7
            frp_7d[target_pos] = frp_cumsum[i] - frp_cumsum[s7]
            act_7d[target_pos] = len(np.unique(cal_days[s7:i]))
            
            # 30d
            s30 = np.searchsorted(t_vals[:i], t_cur - 30.0, side="left")
            ev_30d[target_pos] = i - s30
            frp_30d[target_pos] = frp_cumsum[i] - frp_cumsum[s30]
            act_30d[target_pos] = len(np.unique(cal_days[s30:i]))
            
            # 90d
            s90 = np.searchsorted(t_vals[:i], t_cur - 90.0, side="left")
            ev_90d[target_pos] = i - s90
            frp_90d[target_pos] = frp_cumsum[i] - frp_cumsum[s90]
            act_90d[target_pos] = len(np.unique(cal_days[s90:i]))
            
    # Unsort back to original DataFrame index
    return pd.DataFrame({
        "events_previous_7d": ev_7d[inv_sort],
        "events_previous_30d": ev_30d[inv_sort],
        "events_previous_90d": ev_90d[inv_sort],
        "frp_previous_7d": frp_7d[inv_sort],
        "frp_previous_30d": frp_30d[inv_sort],
        "frp_previous_90d": frp_90d[inv_sort],
        "active_days_previous_7d": act_7d[inv_sort],
        "active_days_previous_30d": act_30d[inv_sort],
        "active_days_previous_90d": act_90d[inv_sort],
        "time_since_previous_event_hours": time_since_prev[inv_sort]
    }, index=df.index)
