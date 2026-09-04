import os
import argparse
import pandas as pd
import numpy as np
import json
from src.classification.candidate_acquisition import CandidateAcquisition

def main():
    parser = argparse.ArgumentParser(description="Build candidate acquisition batch for ground truth annotation.")
    parser.add_argument("--sample-size", type=int, default=1000, help="Target candidate sample size.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic sampling.")
    parser.add_argument("--input-file", type=str, default="data/processed/features/event_features_v2.parquet", help="Path to input features parquet.")
    parser.add_argument("--output-file", type=str, default="ml/data/ground_truth/candidate_pool_v1.json", help="Path to output candidates JSON.")
    args = parser.parse_args()

    print(f"Loading event population from {args.input_file}...")
    df = pd.read_parquet(args.input_file)
    print(f"Loaded {len(df)} total events.")

    print(f"Generating candidate batch of size {args.sample_size} (seed={args.seed})...")
    batch = CandidateAcquisition.generate_batch(df, batch_size=args.sample_size, random_seed=args.seed)
    
    # Merge with coordinates and start_time for annotation convenience
    merged_batch = batch.merge(df[['event_id', 'centroid_lat', 'centroid_lon', 'start_time', 'max_frp_mw', 'distance_to_facility_km']], on="event_id")

    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
    records = merged_batch.to_dict(orient="records")
    
    with open(args.output_file, "w") as f:
        json.dump(records, f, indent=2)

    print(f"Successfully saved {len(records)} candidates to {args.output_file}")

if __name__ == "__main__":
    main()
