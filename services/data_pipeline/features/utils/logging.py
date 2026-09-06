"""
ThermoTrace Feature Engineering Logging Utility
===============================================
"""

import sys
import time

def log_progress(step: str, detail: str = ""):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{timestamp}] [INFO] {step}"
    if detail:
        msg += f" - {detail}"
    print(msg, flush=True)

def log_stage_header(title: str):
    bar = "=" * 80
    print(f"\n{bar}\n{title}\n{bar}", flush=True)
