"""
Reports API — generate incident reports for events.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from .events import _get_all_events
from datetime import datetime

router = APIRouter()


def _build_report_html(event: dict) -> str:
    """Generate a self-contained HTML incident report."""
    eid = event.get("event_id", "N/A")
    classification = event.get("classification", {})
    scores = event.get("scores", {})
    facility = event.get("facility_context", {})
    temporal = event.get("temporal_features", {})
    evidence_list = event.get("evidence", [])
    obs = event.get("observations", [])

    evidence_items = "".join(f"<li>{e}</li>" for e in evidence_list)
    obs_rows = "".join(
        f"<tr><td>{o.get('satellite','N/A')}</td><td>{o.get('frp','N/A')} MW</td><td>{o.get('acq_date','N/A')}</td></tr>"
        for o in obs
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>ThermoTrace Incident Report — {eid}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Inter',sans-serif; background:#0a0e1a; color:#e0e6f0; padding:40px; }}
  .report {{ max-width:800px; margin:0 auto; background:linear-gradient(145deg,#111827,#1a2332); border:1px solid #2d3748; border-radius:16px; padding:40px; }}
  .header {{ text-align:center; margin-bottom:32px; border-bottom:1px solid #2d3748; padding-bottom:24px; }}
  .header h1 {{ font-size:28px; font-weight:700; background:linear-gradient(135deg,#f97316,#ef4444); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
  .header p {{ color:#8896ab; margin-top:8px; }}
  .badge {{ display:inline-block; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600; }}
  .badge-critical {{ background:rgba(239,68,68,0.2); color:#ef4444; border:1px solid rgba(239,68,68,0.3); }}
  .badge-high {{ background:rgba(249,115,22,0.2); color:#f97316; border:1px solid rgba(249,115,22,0.3); }}
  .badge-medium {{ background:rgba(234,179,8,0.2); color:#eab308; border:1px solid rgba(234,179,8,0.3); }}
  .badge-low {{ background:rgba(34,197,94,0.2); color:#22c55e; border:1px solid rgba(34,197,94,0.3); }}
  .section {{ margin:24px 0; }}
  .section h2 {{ font-size:18px; font-weight:600; color:#94a3b8; margin-bottom:12px; text-transform:uppercase; letter-spacing:1px; }}
  .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
  .card {{ background:rgba(255,255,255,0.03); border:1px solid #2d3748; border-radius:12px; padding:16px; }}
  .card .label {{ font-size:12px; color:#64748b; text-transform:uppercase; letter-spacing:0.5px; }}
  .card .value {{ font-size:20px; font-weight:600; margin-top:4px; }}
  table {{ width:100%; border-collapse:collapse; margin-top:8px; }}
  th, td {{ padding:10px 12px; text-align:left; border-bottom:1px solid #2d3748; font-size:14px; }}
  th {{ color:#64748b; font-weight:500; text-transform:uppercase; font-size:12px; }}
  ul {{ list-style:none; padding:0; }}
  ul li {{ padding:8px 0; border-bottom:1px solid rgba(45,55,72,0.5); font-size:14px; }}
  ul li::before {{ content:'✓ '; color:#22c55e; font-weight:bold; }}
  .footer {{ margin-top:32px; padding-top:16px; border-top:1px solid #2d3748; text-align:center; color:#64748b; font-size:12px; }}
  @media print {{ body {{ background:#fff; color:#1a1a1a; }} .report {{ border:1px solid #ddd; background:#fff; }} }}
</style>
</head>
<body>
<div class="report">
  <div class="header">
    <h1>🔥 THERMOTRACE INCIDENT REPORT</h1>
    <p>Event {eid} &bull; Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
  </div>

  <div class="section">
    <h2>Classification</h2>
    <div class="grid">
      <div class="card">
        <div class="label">Event Class</div>
        <div class="value">{classification.get('class','N/A')}</div>
      </div>
      <div class="card">
        <div class="label">Confidence</div>
        <div class="value">{classification.get('confidence','N/A')}%</div>
      </div>
    </div>
  </div>

  <div class="section">
    <h2>Risk Scores</h2>
    <div class="grid">
      <div class="card">
        <div class="label">Industrial Likelihood</div>
        <div class="value" style="color:#a855f7">{scores.get('industrial_likelihood','N/A')}</div>
      </div>
      <div class="card">
        <div class="label">Operational Risk</div>
        <div class="value" style="color:#ef4444">{scores.get('operational_risk','N/A')}</div>
      </div>
    </div>
  </div>

  <div class="section">
    <h2>Facility Context</h2>
    <div class="grid">
      <div class="card">
        <div class="label">Nearest Facility</div>
        <div class="value">{facility.get('name','N/A')}</div>
      </div>
      <div class="card">
        <div class="label">Distance</div>
        <div class="value">{facility.get('nearby_refinery_km','N/A')} km</div>
      </div>
      <div class="card">
        <div class="label">Land Cover</div>
        <div class="value">{facility.get('land_cover','N/A')}</div>
      </div>
      <div class="card">
        <div class="label">Population (5 km)</div>
        <div class="value">{facility.get('population_within_5km','N/A'):,}</div>
      </div>
    </div>
  </div>

  <div class="section">
    <h2>Thermal History</h2>
    <div class="grid">
      <div class="card">
        <div class="label">Baseline FRP (mean ± σ)</div>
        <div class="value">{temporal.get('baseline_frp_mean','?')} ± {temporal.get('baseline_frp_std','?')} MW</div>
      </div>
      <div class="card">
        <div class="label">Current FRP</div>
        <div class="value">{temporal.get('current_frp','?')} MW</div>
      </div>
      <div class="card">
        <div class="label">Deviation</div>
        <div class="value">{temporal.get('deviation_sigma','?')}σ</div>
      </div>
      <div class="card">
        <div class="label">Detections (30d)</div>
        <div class="value">{temporal.get('detection_count_30d','?')}</div>
      </div>
    </div>
  </div>

  <div class="section">
    <h2>Observations</h2>
    <table>
      <thead><tr><th>Satellite</th><th>FRP</th><th>Date</th></tr></thead>
      <tbody>{obs_rows if obs_rows else '<tr><td colspan="3">No observations recorded</td></tr>'}</tbody>
    </table>
  </div>

  <div class="section">
    <h2>Evidence Factors</h2>
    <ul>{evidence_items if evidence_items else '<li>No evidence factors recorded</li>'}</ul>
  </div>

  <div class="section">
    <h2>Recommended Action</h2>
    <div class="card" style="border-color:rgba(249,115,22,0.4)">
      <div class="value" style="font-size:16px;color:#f97316">Verify with facility operator / local authority</div>
    </div>
  </div>

  <div class="section">
    <h2>Data Provenance</h2>
    <div class="grid">
      <div class="card"><div class="label">Data Version</div><div class="value" style="font-size:14px">{event.get('data_version','N/A')}</div></div>
      <div class="card"><div class="label">Model Version</div><div class="value" style="font-size:14px">{event.get('model_version','N/A')}</div></div>
    </div>
  </div>

  <div class="footer">
    <p>ThermoTrace Intelligence Platform &bull; Report auto-generated &bull; This report is for investigative purposes only.</p>
    <p>Limitations: Classification is model-based and requires human verification. Satellite revisit gaps may affect detection completeness.</p>
  </div>
</div>
</body>
</html>"""


@router.get("/{event_id}")
async def generate_report(event_id: str):
    """Generate an HTML incident report for the given event."""
    for event in _get_all_events():
        if event.get("event_id") == event_id:
            html = _build_report_html(event)
            return HTMLResponse(content=html)
    raise HTTPException(status_code=404, detail=f"Event {event_id} not found")


@router.get("/{event_id}/json")
async def generate_report_json(event_id: str):
    """Return report data as JSON (for frontend rendering)."""
    for event in _get_all_events():
        if event.get("event_id") == event_id:
            return {
                "event_id": event_id,
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "classification": event.get("classification", {}),
                "scores": event.get("scores", {}),
                "facility_context": event.get("facility_context", {}),
                "temporal_features": event.get("temporal_features", {}),
                "evidence": event.get("evidence", []),
                "observations": event.get("observations", []),
                "status": event.get("status"),
                "data_version": event.get("data_version"),
                "model_version": event.get("model_version"),
            }
    raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
