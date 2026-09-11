import urllib.request
import json

payload = {
    "recipient_name": "Rijja (Lead Incident Commander)",
    "recipient_email": "official@thermotrace.gov.in",
    "recipient_phone": "+919876543210",
    "channels": ["EMAIL", "SMS"],
    "event_id": "TT-CASE-001",
    "facility_name": "Jamnagar Mega Refinery Complex",
    "frp_mw": 340.0,
    "risk_score": 84.0,
    "threat_tier": "CRITICAL"
}

req = urllib.request.Request(
    "http://localhost:8000/api/notifications/dispatch",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req) as response:
        print(response.read().decode("utf-8"))
except Exception as e:
    print(f"Error: {e}")
