import { useState } from 'react';
import type { ThermoEvent } from '../services/api';
import { submitAnalystAction } from '../services/api';
import RiskBadge from './RiskBadge';
import EvidenceCard from './EvidenceCard';
import { ScoreBar } from './TimelineChart';
import ReportButton from './ReportButton';

interface EventPanelProps {
  event: ThermoEvent;
  onClose: () => void;
  onNavigate?: (eventId: string) => void;
}

export default function EventPanel({ event, onClose, onNavigate }: EventPanelProps) {
  const [status, setStatus] = useState(event.status);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  const handleAction = async (action: string) => {
    try {
      const result = await submitAnalystAction(event.event_id, action, `${action} via dashboard`);
      setStatus(result.new_status || action);
      setActionFeedback(`✓ Event ${action}ed successfully`);
      setTimeout(() => setActionFeedback(null), 3000);
    } catch {
      // If backend is down, update locally
      const newStatus = action === 'confirm' ? 'confirmed' : action === 'reject' ? 'rejected' : status;
      setStatus(newStatus);
      setActionFeedback(`✓ ${action} recorded (offline)`);
      setTimeout(() => setActionFeedback(null), 3000);
    }
  };

  const risk = event.scores?.operational_risk || 0;
  const industrial = event.scores?.industrial_likelihood || 0;
  const confidence = event.classification?.confidence || 0;
  const facility = event.facility_context || {};

  return (
    <div className="event-panel">
      {/* Header */}
      <div className="event-panel__header">
        <span className="event-panel__title">🔥 {event.event_id}</span>
        <button className="event-panel__close" onClick={onClose}>✕</button>
      </div>

      <div className="event-panel__body">
        {/* Classification */}
        <div style={{ marginBottom: '12px' }}>
          <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-heading)', marginBottom: '6px' }}>
            {event.classification?.class || 'Thermal Anomaly'}
          </div>
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            <RiskBadge value={risk} type="risk" />
            <div 
              title="Confidence is derived directly from NASA MODIS/VIIRS satellite telemetry heuristics (evaluating cloud cover, background temperature variance, and sensor saturation)."
              style={{ cursor: 'help' }}
            >
              <RiskBadge value={confidence} type="confidence" />
            </div>
            <span className={`status-badge status-badge--${status}`}>{status.replace(/_/g, ' ')}</span>
          </div>
        </div>

        <hr className="event-panel__section-divider" />

        {/* Coordinates */}
        <div className="event-panel__row">
          <span className="event-panel__row-label">Coordinates</span>
          <span className="event-panel__row-value" style={{ fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
            {event.geometry?.lat?.toFixed(4)}°, {event.geometry?.lon?.toFixed(4)}°
          </span>
        </div>

        <div className="event-panel__row">
          <span className="event-panel__row-label">Time Window</span>
          <span className="event-panel__row-value" style={{ fontSize: '11px' }}>
            {event.time_window?.start?.split('T')[0]} → {event.time_window?.end?.split('T')[0]}
          </span>
        </div>

        <div className="event-panel__row">
          <span className="event-panel__row-label">FRP</span>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
            <span className="event-panel__row-value" style={{ fontFamily: 'var(--font-mono)' }}>
              {event.observations?.[0]?.frp || 'N/A'} MW
            </span>
            {event.temporal_features && event.temporal_features.baseline_frp_mean !== undefined && (
              event.temporal_features.baseline_frp_mean > 0 ? (
                <span style={{ 
                  fontSize: '10px', 
                  color: ((event.observations?.[0]?.frp || 0) - event.temporal_features.baseline_frp_mean) / event.temporal_features.baseline_frp_mean > 0.5 ? 'var(--alert-critical)' : 'var(--text-muted)' 
                }}>
                  vs 30-day avg: {event.temporal_features.baseline_frp_mean.toFixed(1)} MW 
                  (+{Math.round(((event.observations?.[0]?.frp || 0) - event.temporal_features.baseline_frp_mean) / event.temporal_features.baseline_frp_mean * 100)}%)
                </span>
              ) : (
                <span style={{ fontSize: '10px', color: 'var(--alert-high)' }}>
                  New Ignition (No baseline)
                </span>
              )
            )}
          </div>
        </div>

        <hr className="event-panel__section-divider" />

        {/* Score Bars */}
        <ScoreBar label="Industrial Likelihood" value={industrial} color="var(--accent-purple)" />
        <ScoreBar label="Operational Risk" value={risk} />

        <hr className="event-panel__section-divider" />

        {/* Facility Context */}
        {facility.name && (
          <>
            <div style={{ fontSize: '10px', fontWeight: 600, letterSpacing: '1px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px' }}>
              Facility Context
            </div>
            <div className="event-panel__row">
              <span className="event-panel__row-label">Nearest</span>
              <span className="event-panel__row-value">{facility.name}</span>
            </div>
            <div className="event-panel__row">
              <span className="event-panel__row-label">Distance</span>
              <span className="event-panel__row-value">{facility.nearby_refinery_km} km</span>
            </div>
            <div className="event-panel__row">
              <span className="event-panel__row-label">Land Cover</span>
              <span className="event-panel__row-value">{facility.land_cover}</span>
            </div>
            {facility.population_within_5km && (
              <div className="event-panel__row">
                <span className="event-panel__row-label">Population (5km)</span>
                <span className="event-panel__row-value">{facility.population_within_5km?.toLocaleString()}</span>
              </div>
            )}
            <hr className="event-panel__section-divider" />
          </>
        )}

        {/* Evidence */}
        <div style={{ fontSize: '10px', fontWeight: 600, letterSpacing: '1px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px' }}>
          Evidence Factors
        </div>
        <EvidenceCard items={Array.isArray(event.evidence) ? event.evidence : (event.evidence?.evidence_for || [])} />

        <hr className="event-panel__section-divider" />

        {/* Action Feedback */}
        {actionFeedback && (
          <div style={{
            padding: '8px 12px',
            background: 'rgba(34, 197, 94, 0.1)',
            border: '1px solid rgba(34, 197, 94, 0.3)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--accent-green)',
            fontSize: '12px',
            marginBottom: '12px',
            animation: 'slide-in-right 0.2s ease-out',
          }}>
            {actionFeedback}
          </div>
        )}

        {/* Analyst Actions */}
        <div className="action-group">
          <button className="btn btn--confirm" onClick={() => handleAction('confirm')}>✓ Confirm</button>
          <button className="btn btn--reject" onClick={() => handleAction('reject')}>✗ Reject</button>
          <ReportButton eventId={event.event_id} />
        </div>

        {/* Investigate button */}
        {onNavigate && (
          <button
            className="btn btn--secondary"
            style={{ width: '100%', marginTop: '8px', justifyContent: 'center' }}
            onClick={() => onNavigate(event.event_id)}
          >
            🔍 Full Investigation
          </button>
        )}
      </div>
    </div>
  );
}
