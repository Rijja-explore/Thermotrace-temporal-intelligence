"""
Health Check Script — Verifies backend API server health status.
"""
import sys
import urllib.request
import json

def check_health(url="http://localhost:8000/api/health"):
    print(f"Checking health status at {url}...")
    try:
        req = urllib.request.urlopen(url, timeout=5)
        if req.status == 200:
            data = json.loads(req.read().decode('utf-8'))
            print("[OK] System Healthy:")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"[ERROR] Health check returned HTTP status {req.status}")
            return False
    except Exception as e:
        print(f"[ERROR] Health check failed: {e}")
        return False

if __name__ == "__main__":
    success = check_health()
    sys.exit(0 if success else 1)
