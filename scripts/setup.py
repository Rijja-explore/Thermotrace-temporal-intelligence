"""
Setup & Environment Verification Script for ThermoTrace.
"""
import sys
import os
import subprocess

REQUIRED_PACKAGES = [
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("pydantic", "pydantic"),
    ("scikit-learn", "sklearn"),
    ("joblib", "joblib"),
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("scipy", "scipy"),
    ("pyyaml", "yaml")
]

def check_environment():
    print("=== ThermoTrace System Environment Check ===")
    print(f"Python Version: {sys.version}")
    
    missing = []
    for pip_name, import_name in REQUIRED_PACKAGES:
        try:
            __import__(import_name)
            print(f"  [OK] {pip_name} is installed")
        except ImportError:
            print(f"  [MISSING] {pip_name} is MISSING")
            missing.append(pip_name)

    if missing:
        print(f"\nMissing packages detected: {missing}")
        print(f"Installing missing packages via pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
        print("Installation complete.")
    else:
        print("\nAll required core dependencies are installed and operational.")

if __name__ == "__main__":
    check_environment()
