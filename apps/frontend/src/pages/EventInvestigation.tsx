import { useEffect, useState } from 'react';
import { MapView } from '../components/MapView';
import type { ThermoEvent } from '../services/api';
import { fetchEvents, fetchEventById, verifyEvent, getReportUrl } from '../services/api';

interface EventInvestigationProps {
  eventId?: string;
  onNavigate?: (page: string, params?: any) => void;
}

export default function EventInvestigation({ eventId = 'TT-CASE-001', onNavigate }: EventInvestigationProps) {
  const [event, setEvent] = useState<ThermoEvent | null>(null);
  const [allEvents, setAllEvents] = useState<ThermoEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('');
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  // Reclassify Modal State
  const [showReclassifyModal, setShowReclassifyModal] = useState(false);
  const [reclassifyLabel, setReclassifyLabel] = useState('persistent_industrial_source');
  const [reclassifyNotes, setReclassifyNotes] = useState('');

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [evRes, detailRes] = await Promise.all([
          fetchEvents({ limit: 500 }),
          fetchEventById(eventId).catch(() => null)
        ]);
        setAllEvents(evRes.events);

        const found = detailRes || evRes.events.find(e => e.event_id === eventId) || evRes.events[0];
        if (found) {
          setEvent(found);
          setStatus(found.status || 'NEW');
        }
      } catch (err) {
        console.error("Failed to load investigation data:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [eventId]);

  const handleAction = async (decision: string, newLabel?: string, notes?: string) => {
    if (!event) return;
    try {
      const result = await verifyEvent(event.event_id, decision, newLabel, notes);
      setStatus(result.status || decision);
      if (newLabel && event.classification) {
        event.classification.label = newLabel;
      }
      setActionFeedback(`✓ Analyst Action recorded: ${decision}`);
    } catch {
      setStatus(decision);
      setActionFeedback(`✓ Analyst Action recorded locally: ${decision}`);
    }
    setShowReclassifyModal(false);
    setTimeout(() => setActionFeedback(null), 3500);
  };

  if (loading) {
    return (
      <div style={{ padding: '60px', color: '#94a3b8', textAlign: 'center' }}>
        Loading Geospatial & Temporal Intelligence for Event {eventId}...
      </div>
    );
  }

  if (!event) {
    return (
      <div style={{ padding: '60px', textAlign: 'center', color: '#f8fafc' }}>
        <h2>Event not found: {eventId}</h2>
        <button onClick={() => onNavigate?.('dashboard')} style={{ marginTop: '16px', padding: '8px 16px', background: '#2563eb', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
          &larr; Back to Dashboard
        </button>
      </div>
    );
  }

  const facility = event.facility_context || {};
  const risk = event.operational_risk?.risk_score ?? event.scores?.operational_risk ?? 0;
  const industrial = event.industrial_likelihood?.score ?? event.scores?.industrial_likelihood ?? 0;
  const anomaly = event.anomaly?.anomaly_score ?? 0;
  const confidence = Math.round((event.classification?.confidence || 0) * (event.classification?.confidence <= 1.0 ? 100 : 1));
  const classLabel = (event.classification?.label || event.classification?.class || 'unknown_requires_verification').replace(/_/g, ' ');

  // Evidence Parsing
  let evidenceFor: string[] = [];
  let evidenceAgainst: string[] = [];
  let missingEvidence: string[] = [];

  if (typeof event.evidence === 'object' && !Array.isArray(event.evidence)) {
    evidenceFor = event.evidence.evidence_for || [];
    evidenceAgainst = event.evidence.evidence_against || [];
    missingEvidence = event.evidence.missing_evidence || [];
  } else if (Array.isArray(event.evidence)) {
    evidenceFor = event.evidence;
  }

  const probs = event.classification?.probabilities || {};

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 65px)', overflow: 'hidden', background: '#0a0e1a' }}>
      {/* ─── Left Panel: GIS Map (50% Width) ─── */}
      <div style={{ flex: 1, position: 'relative', borderRight: '1px solid #1e293b' }}>
        <MapView
          events={allEvents}
          facilities={[]}
          selectedEventId={event.event_id}
          onSelectEvent={(ev) => {
            setEvent(ev);
            setStatus(ev.status);
          }}
          center={event.geometry?.latitude && event.geometry?.longitude ? [event.geometry.latitude, event.geometry.longitude] : [21.1458, 79.0882]}
          zoom={12}
        />
      </div>

      {/* ─── Right Panel: HERO Investigation Workspace (50% Width) ─── */}
      <div style={{ flex: 1, padding: '24px', overflowY: 'auto', background: '#0f172a', color: '#f8fafc' }}>
        {/* Top Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <button
            onClick={() => onNavigate?.('dashboard')}
            style={{ background: 'transparent', color: '#60a5fa', border: 'none', cursor: 'pointer', fontSize: '13px', fontWeight: '600' }}
          >
            &larr; Back to Dashboard
          </button>
          <a
            href={getReportUrl(event.event_id)}
            target="_blank"
            rel="noreferrer"
            style={{
              background: '#ea580c',
              color: 'white',
              padding: '6px 14px',
              borderRadius: '6px',
              textDecoration: 'none',
              fontSize: '12px',
              fontWeight: '700',
              boxShadow: '0 4px 12px rgba(234, 88, 12, 0.4)'
            }}
          >
            📄 Export Incident PDF / HTML
          </a>
        </div>

        {/* Title & Status */}
        <div style={{ marginBottom: '20px' }}>
          <div style={{ fontSize: '11px', color: '#64748b', fontWeight: '700', letterSpacing: '1px', textTransform: 'uppercase' }}>
            CANONICAL EVENT ID: {event.event_id}
          </div>
          <h2 style={{ fontSize: '20px', fontWeight: '800', color: '#f8fafc', margin: '4px 0 8px 0', textTransform: 'capitalize' }}>
            {classLabel}
          </h2>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <span style={{
              background: classLabel.includes('unknown') ? 'rgba(168, 85, 247, 0.2)' : 'rgba(34, 197, 94, 0.2)',
              color: classLabel.includes('unknown') ? '#a855f7' : '#22c55e',
              border: `1px solid ${classLabel.includes('unknown') ? '#a855f7' : '#22c55e'}`,
              padding: '3px 10px',
              borderRadius: '12px',
              fontSize: '12px',
              fontWeight: '700'
            }}>
              Confidence: {confidence}%
            </span>
            <span style={{
              background: '#1e293b',
              color: '#f8fafc',
              border: '1px solid #334155',
              padding: '3px 10px',
              borderRadius: '12px',
              fontSize: '12px',
              fontWeight: '600'
            }}>
              Status: {status}
            </span>
          </div>
        </div>

        {/* Intelligence Score Grid (3 Columns) */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '20px' }}>
          <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '10px', padding: '12px' }}>
            <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase' }}>Industrial Likelihood</div>
            <div style={{ fontSize: '24px', fontWeight: '800', color: '#a855f7', marginTop: '4px' }}>{industrial} / 100</div>
          </div>

          <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '10px', padding: '12px' }}>
            <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase' }}>Operational Risk</div>
            <div style={{ fontSize: '24px', fontWeight: '800', color: risk > 60 ? '#ef4444' : '#f97316', marginTop: '4px' }}>{risk} / 100</div>
          </div>

          <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '10px', padding: '12px' }}>
            <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase' }}>Anomaly Score</div>
            <div style={{ fontSize: '24px', fontWeight: '800', color: anomaly > 50 ? '#ef4444' : '#38bdf8', marginTop: '4px' }}>{anomaly} / 100</div>
          </div>
        </div>

        {/* Probability Breakdown Bar */}
        {Object.keys(probs).length > 0 && (
          <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '10px', padding: '14px', marginBottom: '20px' }}>
            <div style={{ fontSize: '12px', fontWeight: '700', color: '#94a3b8', marginBottom: '10px', textTransform: 'uppercase' }}>
              🤖 AI Probability Breakdown across Canonical Classes
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {Object.entries(probs).map(([cls, prob]) => (
                <div key={cls} style={{ fontSize: '11px', display: 'grid', gridTemplateColumns: '2fr 3fr 1fr', alignItems: 'center' }}>
                  <span style={{ color: '#cbd5e1' }}>{cls.replace(/_/g, ' ')}</span>
                  <div style={{ background: '#0f172a', borderRadius: '4px', height: '8px', overflow: 'hidden' }}>
                    <div style={{ width: `${Math.round(prob * 100)}%`, height: '100%', background: cls === event.classification?.label ? '#22c55e' : '#3b82f6' }}></div>
                  </div>
                  <span style={{ textAlign: 'right', fontWeight: '700', color: '#f8fafc' }}>{Math.round(prob * 100)}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Facility & Landcover Context */}
        <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '10px', padding: '14px', marginBottom: '20px' }}>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#60a5fa', marginBottom: '8px', textTransform: 'uppercase' }}>
            🏢 Facility & Geographic Context
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '12px' }}>
            <div><span style={{ color: '#64748b' }}>Nearest Facility:</span> <br/><strong>{facility.nearest_facility_name || facility.name || 'None'}</strong></div>
            <div><span style={{ color: '#64748b' }}>Distance:</span> <br/><strong>{facility.distance_to_facility_m ? `${facility.distance_to_facility_m} meters` : `${facility.nearby_refinery_km || 0} km`}</strong></div>
            <div><span style={{ color: '#64748b' }}>Primary Landcover:</span> <br/><strong>{event.landcover_context?.primary_class || facility.land_cover || 'Industrial'}</strong></div>
            <div><span style={{ color: '#64748b' }}>Population (5km):</span> <br/><strong>{facility.population_within_5km ? facility.population_within_5km.toLocaleString() : 'N/A'}</strong></div>
          </div>
        </div>

        {/* Evidence Engine: FOR, AGAINST, MISSING */}
        <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '10px', padding: '14px', marginBottom: '20px' }}>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#f8fafc', marginBottom: '10px', textTransform: 'uppercase' }}>
            🔍 Explainable Evidence Engine
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12px' }}>
            {/* Evidence FOR */}
            <div>
              <div style={{ color: '#22c55e', fontWeight: '700', marginBottom: '4px' }}>✓ Evidence FOR Classification:</div>
              {evidenceFor.length === 0 ? <div style={{ color: '#64748b', paddingLeft: '12px' }}>None recorded</div> : (
                <ul style={{ margin: 0, paddingLeft: '18px', color: '#e2e8f0' }}>
                  {evidenceFor.map((e, idx) => <li key={idx}>{e}</li>)}
                </ul>
              )}
            </div>

            {/* Evidence AGAINST */}
            <div>
              <div style={{ color: '#ef4444', fontWeight: '700', marginBottom: '4px' }}>✗ Evidence AGAINST / Contradictions:</div>
              {evidenceAgainst.length === 0 ? <div style={{ color: '#64748b', paddingLeft: '12px' }}>None recorded</div> : (
                <ul style={{ margin: 0, paddingLeft: '18px', color: '#e2e8f0' }}>
                  {evidenceAgainst.map((e, idx) => <li key={idx}>{e}</li>)}
                </ul>
              )}
            </div>

            {/* Missing Evidence / Limitations */}
            <div>
              <div style={{ color: '#eab308', fontWeight: '700', marginBottom: '4px' }}>⚠️ Missing Evidence / Data Limitations:</div>
              {missingEvidence.length === 0 ? <div style={{ color: '#64748b', paddingLeft: '12px' }}>No missing parameters</div> : (
                <ul style={{ margin: 0, paddingLeft: '18px', color: '#e2e8f0' }}>
                  {missingEvidence.map((e, idx) => <li key={idx}>{e}</li>)}
                </ul>
              )}
            </div>
          </div>
        </div>

        {/* Action Feedback Notification */}
        {actionFeedback && (
          <div style={{ background: 'rgba(34, 197, 94, 0.15)', border: '1px solid #22c55e', color: '#22c55e', padding: '10px 14px', borderRadius: '8px', fontSize: '13px', fontWeight: '600', marginBottom: '16px' }}>
            {actionFeedback}
          </div>
        )}

        {/* Human Analyst Action Buttons */}
        <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '10px', padding: '16px' }}>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#94a3b8', marginBottom: '10px', textTransform: 'uppercase' }}>
            👩‍💻 Human Analyst Verification Workflow
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px' }}>
            <button
              onClick={() => handleAction('CONFIRMED')}
              style={{ background: '#16a34a', color: 'white', border: 'none', padding: '10px', borderRadius: '6px', fontWeight: '700', cursor: 'pointer', fontSize: '13px' }}
            >
              ✓ Confirm Label
            </button>
            <button
              onClick={() => handleAction('REJECTED')}
              style={{ background: '#dc2626', color: 'white', border: 'none', padding: '10px', borderRadius: '6px', fontWeight: '700', cursor: 'pointer', fontSize: '13px' }}
            >
              ✗ Reject Label
            </button>
            <button
              onClick={() => setShowReclassifyModal(true)}
              style={{ background: '#2563eb', color: 'white', border: 'none', padding: '10px', borderRadius: '6px', fontWeight: '700', cursor: 'pointer', fontSize: '13px' }}
            >
              🔄 Reclassify
            </button>
          </div>
        </div>

        {/* Reclassify Modal */}
        {showReclassifyModal && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 3000
          }}>
            <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px', width: '450px', color: '#f8fafc' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px' }}>🔄 Reclassify Event {event.event_id}</h3>

              <label style={{ fontSize: '12px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Select Correct Class:</label>
              <select
                value={reclassifyLabel}
                onChange={(e) => setReclassifyLabel(e.target.value)}
                style={{ width: '100%', background: '#0f172a', color: '#f8fafc', border: '1px solid #334155', padding: '8px', borderRadius: '6px', marginBottom: '16px' }}
              >
                <option value="persistent_industrial_source">persistent_industrial_source</option>
                <option value="industrial_fire_or_abnormal_event">industrial_fire_or_abnormal_event</option>
                <option value="wildfire_or_forest_fire">wildfire_or_forest_fire</option>
                <option value="agricultural_burning">agricultural_burning</option>
                <option value="mining_or_other_industrial_activity">mining_or_other_industrial_activity</option>
                <option value="unknown_requires_verification">unknown_requires_verification</option>
              </select>

              <label style={{ fontSize: '12px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Analyst Rationale / Notes:</label>
              <textarea
                value={reclassifyNotes}
                onChange={(e) => setReclassifyNotes(e.target.value)}
                placeholder="Enter justification for label override..."
                style={{ width: '100%', background: '#0f172a', color: '#f8fafc', border: '1px solid #334155', padding: '8px', borderRadius: '6px', height: '80px', marginBottom: '16px' }}
              />

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button
                  onClick={() => setShowReclassifyModal(false)}
                  style={{ background: '#475569', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer' }}
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleAction('RECLASSIFIED', reclassifyLabel, reclassifyNotes)}
                  style={{ background: '#2563eb', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: '700', cursor: 'pointer' }}
                >
                  Submit Reclassification
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
