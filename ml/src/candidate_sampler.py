import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
from src.feature_schema import FeatureSchemaValidator
import hashlib

class CandidateSampler:
    def __init__(self, df: pd.DataFrame, schema_validator: FeatureSchemaValidator, seed: int = 42):
        self.df = df
        self.schema_validator = schema_validator
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        
    def filter_leakage_features(self, df_subset: pd.DataFrame) -> pd.DataFrame:
        """Removes features excluded by schema."""
        approved_cols = []
        # Exclude event_id temporarily for validation since we need it in the dataset,
        # but the validator rejects it as a feature.
        # For the candidate feature file, we must exclude the leakage features.
        
        # We need to manually identify approved columns from the dataset.
        for col in df_subset.columns:
            if col == 'event_id':
                approved_cols.append(col)
                continue
            try:
                self.schema_validator.validate_features([col])
                approved_cols.append(col)
            except ValueError:
                pass # Excluded
        return df_subset[approved_cols].copy()
        
    def get_stratified_sample(self, n_target: int = 400) -> pd.DataFrame:
        candidates = []
        
        # We want to identify specific strata and select events from them.
        # Create a spatial grid to prevent geographic domination
        df_work = self.df.copy()
        df_work['grid_lat'] = df_work['centroid_lat'].round(0)
        df_work['grid_lon'] = df_work['centroid_lon'].round(0)
        df_work['spatial_grid'] = df_work['grid_lat'].astype(str) + "_" + df_work['grid_lon'].astype(str)
        
        # Define quantiles safely
        frp_q75 = df_work['max_frp_mw'].quantile(0.75) if 'max_frp_mw' in df_work.columns else 10.0
        
        # Define groups
        def get_col(col_name, default_val):
            if col_name in df_work.columns:
                return df_work[col_name]
            return pd.Series([default_val] * len(df_work), index=df_work.index)
            
        groups = {
            "high_frp_no_facility": df_work[
                (get_col('max_frp_mw', 0) > frp_q75) & 
                (get_col('distance_to_facility_km', 10) > 5.0)
            ],
            "low_frp_near_facility": df_work[
                (get_col('max_frp_mw', 10) <= frp_q75) & 
                (get_col('distance_to_facility_km', 10) <= 2.0)
            ],
            "persistent_non_industrial": df_work[
                (get_col('duration_hours', 0) > 2.0) & 
                (get_col('builtup_fraction_1km', 1) < 0.1)
            ],
            "recurrent_weak_context": df_work[
                (get_col('events_previous_30d', 0) > 3) & 
                (get_col('distance_to_facility_km', 10) > 5.0)
            ],
            "forest_near_infra": df_work[
                (get_col('forest_fraction_1km', 0) > 0.5) & 
                ((get_col('distance_to_major_road_km', 10) < 1.0) | (get_col('distance_to_power_line_km', 10) < 1.0))
            ],
            "cropland_near_infra": df_work[
                (get_col('cropland_fraction_1km', 0) > 0.5) & 
                ((get_col('distance_to_major_road_km', 10) < 1.0) | (get_col('distance_to_power_line_km', 10) < 1.0))
            ],
            "isolated_high_confidence": df_work[
                (get_col('events_previous_30d', 1) == 0) & 
                (get_col('detection_count', 0) > 3)
            ],
            "random_baseline": df_work.copy()
        }
        
        sampled_ids = set()
        per_group_target = n_target // len(groups)
        max_per_grid = 3
        
        for group_name, group_df in groups.items():
            # Exclude already sampled
            group_df = group_df[~group_df['event_id'].isin(sampled_ids)].copy()
            if group_df.empty:
                continue
                
            # Shuffle randomly
            group_df = group_df.sample(frac=1, random_state=self.seed)
            
            # Select while respecting max per grid
            grid_counts = {}
            group_selected = []
            
            for _, row in group_df.iterrows():
                grid = row['spatial_grid']
                if grid_counts.get(grid, 0) < max_per_grid:
                    group_selected.append(row)
                    grid_counts[grid] = grid_counts.get(grid, 0) + 1
                    sampled_ids.add(row['event_id'])
                
                if len(group_selected) >= per_group_target:
                    break
                    
            # Add to total candidates
            if group_selected:
                sel_df = pd.DataFrame(group_selected)
                sel_df['sampling_stratum'] = group_name
                sel_df['sampling_reason'] = f"Sampled from {group_name}"
                sel_df['sampling_batch'] = "batch_001"
                candidates.append(sel_df)
                
        final_candidates = pd.concat(candidates, ignore_index=True)
        # Ensure exact required size if possible
        if len(final_candidates) > n_target:
            final_candidates = final_candidates.sample(n=n_target, random_state=self.seed).reset_index(drop=True)
            
        return final_candidates

    def generate_batch(self, out_csv: Path, out_parquet: Path, n_target: int = 400):
        print("Sampling candidates...")
        candidates = self.get_stratified_sample(n_target)
        
        # Prepare CSV for reviewers
        csv_cols = [
            "event_id", "start_time", "end_time", "centroid_lat", "centroid_lon",
            "max_frp_mw", "duration_hours", "sampling_stratum",
            "label", "reviewer_1", "reviewer_2", "final_label",
            "evidence_urls", "evidence_type", "notes", "label_confidence", "label_date", "label_version"
        ]
        
        # Add empty label columns
        label_cols = ["label", "reviewer_1", "reviewer_2", "final_label", "evidence_urls", "evidence_type", "notes", "label_confidence", "label_date", "label_version"]
        for c in label_cols:
            candidates[c] = ""
            
        # Ensure only columns that exist are output
        valid_csv_cols = [c for c in csv_cols if c in candidates.columns]
        csv_df = candidates[valid_csv_cols]
        csv_df.to_csv(out_csv, index=False)
        
        # Prepare Parquet for features (No Leakage)
        feature_df = self.filter_leakage_features(candidates)
        # Retain sampling metadata as per requirements, but note they aren't ML features.
        for meta_col in ["sampling_stratum", "sampling_reason", "sampling_batch"]:
            if meta_col in candidates.columns:
                feature_df[meta_col] = candidates[meta_col]
                
        feature_df.to_parquet(out_parquet, index=False)
        
        print(f"Generated {len(candidates)} candidates.")
        return candidates
