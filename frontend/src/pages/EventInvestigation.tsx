import { useEffect, useState } from 'react';
import MapView from '../components/MapView';
import RiskBadge from '../components/RiskBadge';
import EvidenceCard from '../components/EvidenceCard';
import TimelineChart, { ScoreBar } from '../components/TimelineChart';
import ReportButton from '../components/ReportButton';
import type { ThermoEvent } from '../services/api';
import { fetchEvents, fetchEventsFromJson, submitAnalystAction } from '../services/api';

interface EventInvestigationProps {
  eventId?: string;
  onNavigate?: (page: string) => void;
}

export default function EventInvestigation({ eventId, onNavigate }: EventInvestigationProps) {
  const [event, setEvent] = useState<ThermoEvent | null>(null);
  const [allEvents, setAllEvents] = useState<ThermoEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('');
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const res = await fetchEvents({ limit: 500 });
        setAllEvents(res.events);
        const found = res.events.find(e => e.event_id === eventId);
        if (found) {
          setEvent(found);
          setStatus(found.status);
        }
      } catch {
        const local = await fetchEventsFromJson();
        setAllEvents(local);
        const found = local.find(e => e.event_id === eventId);
        if (found) {
          setEvent(found);
          setStatus(found.status);
        }
      }
      setLoading(false);
    }
    load();
  }, [eventId]);

  const handleAction = async (action: string) => {
    if (!event) return;
    try {
      const result = await submitAnalystAction(event.event_id, action, `${action} via investigation page`);
      setStatus(result.new_status || action);
    } catch {
      setStatus(action === 'confirm' ? 'confirmed' : action === 'reject' ? 'rejected' : status);
    }
    setActionFeedback(`✓ Event ${action}ed`);
    setTimeout(() => setActionFeedback(null), 3000);
  };

  if (loading) {
    return (
      <div className="main-content">
        <div className="loading-overlay" style={{ flex: 1 }}>
          <div className="loading-spinner" />
          <span className="loading-text">Loading investigation data...</span>
        </div>
      </div>
    );
  }

  if (!event) {
    return (
      <div className="main-content">
        <div className="loading-overlay" style={{ flex: 1 }}>
          <span className="loading-text">Event not found: {eventId}</span>
          <button className="btn btn--secondary" onClick={() => onNavigate?.('dashboard')}>← Back to Dashboard</button>
        </div>
      </div>
    );
  }

  const facility = event.facility_context || {};
  const risk = event.scores?.operational_risk || 0;
  const industrial = event.scores?.industrial_likelihood || 0;
  const confidence = event.classification?.confidence || 0;

  return (
    <div className="main-content">
      <div className="investigation-layout">
        {/* Left: Map */}
        <div className="investigation-layout__map">
          <MapView
            events={allEvents}
            selectedEvent={event}
            onSelectEvent={() => {}}
          />
        </div>

        {/* Right: Detail */}
        <div className="investigation-layout__detail">
          {/* Header */}
          <div className="investigation-header">
            <button className="investigation-header__back" onClick={() => onNavigate?.('dashboard')}>
              ← Back to map
            </button>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <ReportButton eventId={event.event_id} />
            </div>
          </div>

          {/* Event Title */}
          <div style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-heading)', marginBottom: '8px' }}>
              Event {event.event_id}
            </h2>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
              <span style={{ fontSize: '15px', color: 'var(--accent-orange)', fontWeight: 500 }}>
                {event.classification?.class || 'Thermal Anomaly'}
              </span>
              <RiskBadge value={confidence} type="confidence" />
              <span className={`status-badge status-badge--${status}`}>{status.replace(/_/g, ' ')}</span>
            </div>
          </div>

          {/* Score + Classification Grid */}
          <div className="detail-grid">
            <div className="detail-card">
              <div className="detail-card__title">Industrial Likelihood</div>
              <div style={{ fontSize: '28px', fontWeight: 700, color: 'var(--accent-purple)', fontFamily: 'var(--font-mono)' }}>
                {industrial}
              </div>
              <ScoreBar label="" value={industrial} color="var(--accent-purple)" />
            </div>

            <div className="detail-card">
              <div className="detail-card__title">Operational Risk</div>
              <div style={{ fontSize: '28px', fontWeight: 700, color: risk >= 80 ? 'var(--accent-red)' : 'var(--accent-orange)', fontFamily: 'var(--font-mono)' }}>
                {risk}
              </div>
              <ScoreBar label="" value={risk} />
            </div>
          </div>

          {/* Facility Context */}
          <div className="detail-grid">
            <div className="detail-card">
              <div className="detail-card__title">Nearest Facility</div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-heading)' }}>{facility.name || 'N/A'}</div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>{facility.nearby_refinery_km} km away</div>
            </div>

            <div className="detail-card">
              <div className="detail-card__title">Land Cover</div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-heading)' }}>{facility.land_cover || 'N/A'}</div>
              {facility.population_within_5km && (
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Pop. exposure: {facility.population_within_5km.toLocaleString()}
                </div>
              )}
            </div>
          </div>

          {/* Thermal Fingerprint */}
          <div style={{ marginBottom: '24px' }}>
            <TimelineChart
              temporalFeatures={event.temporal_features}
              observations={event.observations}
            />
          </div>

          {/* Evidence */}
          <div style={{ marginBottom: '24px' }}>
            <div style={{ fontSize: '10px', fontWeight: 600, letterSpacing: '1.5px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '12px' }}>
              Evidence Factors
            </div>
            <EvidenceCard items={event.evidence || []} />
          </div>

          {/* Recommended Action */}
          <div className="detail-card detail-card--full" style={{ borderColor: 'rgba(249, 115, 22, 0.3)', marginBottom: '24px' }}>
            <div className="detail-card__title">Recommended Action</div>
            <div style={{ fontSize: '14px', color: 'var(--accent-orange)', fontWeight: 500 }}>
              Verify with facility operator / local authority
            </div>
          </div>

          {/* Action Feedback */}
          {actionFeedback && (
            <div style={{
              padding: '10px 14px',
              background: 'rgba(34, 197, 94, 0.1)',
              border: '1px solid rgba(34, 197, 94, 0.3)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--accent-green)',
              fontSize: '13px',
              marginBottom: '12px',
            }}>
              {actionFeedback}
            </div>
          )}

          {/* Analyst Actions */}
          <div style={{ fontSize: '10px', fontWeight: 600, letterSpacing: '1.5px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '12px' }}>
            Analyst Decision
          </div>
          <div className="action-group">
            <button className="btn btn--confirm" onClick={() => handleAction('confirm')}>✓ Confirm</button>
            <button className="btn btn--reject" onClick={() => handleAction('reject')}>✗ Reject</button>
            <button className="btn btn--secondary" onClick={() => handleAction('reclassify')}>🔄 Reclassify</button>
          </div>

          {/* Data Provenance */}
          <div style={{ marginTop: '24px', padding: '12px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', fontSize: '11px', color: 'var(--text-muted)' }}>
            <span>Data: {event.data_version}</span>
            <span style={{ marginLeft: '16px' }}>Model: {event.model_version}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
