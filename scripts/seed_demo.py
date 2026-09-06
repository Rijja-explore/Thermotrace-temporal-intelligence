"""
Seed Demo Data Script — Populates cached offline dataset and seed database records.
"""
import json
import os
import sys

# Ensure root paths are in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from apps.backend.app.api.events import DEMO_EVENTS

def seed_demo_data():
    print("=== ThermoTrace Demo Data Seeding ===")
    target_json = os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "firms_data.json")
    
    with open(target_json, "w", encoding="utf-8") as f:
        json.dump(DEMO_EVENTS, f, indent=2)
        
    print(f"Successfully seeded {len(DEMO_EVENTS)} demo events into {os.path.abspath(target_json)}")

if __name__ == "__main__":
    seed_demo_data()
