import type { ThermoEvent } from '../services/api';
import { getReportUrl } from '../services/api';

interface EventPanelProps {
  event: ThermoEvent;
  onClose: () => void;
  onNavigate?: (eventId: string) => void;
}

function ScoreBarMini({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div style={{ marginBottom: '6px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{label}</span>
        <span style={{ fontSize: '11px', fontWeight: '700', fontFamily: 'var(--font-mono)', color }}>{value}</span>
      </div>
      <div style={{ height: '4px', background: 'var(--border-subtle)', borderRadius: '2px', overflow: 'hidden' }}>
        <div style={{ width: `${value}%`, height: '100%', background: color, borderRadius: '2px', transition: 'width 0.5s ease' }} />
      </div>
    </div>
  );
}

export default function EventPanel({ event, onClose, onNavigate }: EventPanelProps) {
  const status = event.status;

  const risk = event.scores?.operational_risk || event.operational_risk?.risk_score || 0;
  const industrial = event.scores?.industrial_likelihood || event.industrial_likelihood?.score || 0;
  const confidence = Math.round((event.classification?.confidence || 0) * (event.classification?.confidence <= 1.0 ? 100 : 1));
  const facility = event.facility_context || {};
  const classLabel = (event.classification?.class || event.classification?.label || 'Thermal Anomaly').replace(/_/g, ' ');
  const lat = event.geometry?.lat ?? event.geometry?.latitude;
  const lon = event.geometry?.lon ?? event.geometry?.longitude;

  const riskColor = risk >= 70 ? 'var(--risk-critical)' : risk >= 50 ? 'var(--risk-high)' : 'var(--risk-medium)';
  const evidenceItems = Array.isArray(event.evidence)
    ? event.evidence
    : (event.evidence?.evidence_for || event.classification?.top_evidence || []);

  return (
    <div className="event-panel">
      {/* Header */}
      <div className="event-panel__header">
        <div className="event-panel__event-id">{event.event_id}</div>
        <button className="event-panel__close" onClick={onClose} title="Close">✕</button>
      </div>

      <div className="event-panel__body">
        {/* Classification */}
        <div className="event-panel__classification">{classLabel}</div>
        <div className="event-panel__badges">
          <span className={`risk-badge risk-badge--${risk >= 70 ? 'critical' : risk >= 50 ? 'high' : risk >= 30 ? 'medium' : 'low'}`}>
            Risk {risk}
          </span>
          <span className="risk-badge risk-badge--cyan">
            Conf {confidence}%
          </span>
          <span className={`status-badge status-badge--${status}`}>
            {status?.replace(/_/g, ' ')}
          </span>
        </div>

        <hr className="event-panel__divider" />

        {/* Coordinates */}
        <div className="event-panel__row">
          <span className="event-panel__row-label">Coordinates</span>
          <span className="event-panel__row-value" style={{ fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
            {lat?.toFixed(4)}°, {lon?.toFixed(4)}°
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
          <div style={{ textAlign: 'right' }}>
            <span className="event-panel__row-value" style={{ fontFamily: 'var(--font-mono)' }}>
              {event.observations?.[0]?.frp || event.temporal_features?.current_frp || 'N/A'} MW
            </span>
            {event.temporal_features?.baseline_frp_mean !== undefined && event.temporal_features.baseline_frp_mean > 0 && (
              <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                vs avg {event.temporal_features.baseline_frp_mean.toFixed(1)} MW
              </div>
            )}
          </div>
        </div>

        <hr className="event-panel__divider" />

        {/* Score bars */}
        <ScoreBarMini label="Industrial Likelihood" value={industrial} color="var(--accent-amber)" />
        <ScoreBarMini label="Operational Risk" value={risk} color={riskColor} />

        {/* Facility context */}
        {(facility.name || facility.nearest_facility_name) && (
          <>
            <hr className="event-panel__divider" />
            <div className="event-panel__section-label">Facility Context</div>
            <div className="event-panel__row" style={{ marginTop: '6px' }}>
              <span className="event-panel__row-label">Nearest</span>
              <span className="event-panel__row-value" style={{ fontSize: '11px' }}>
                {facility.nearest_facility_name || facility.name}
              </span>
            </div>
            <div className="event-panel__row">
              <span className="event-panel__row-label">Distance</span>
              <span className="event-panel__row-value">
                {facility.distance_to_facility_m ? `${(facility.distance_to_facility_m / 1000).toFixed(2)} km` : `${facility.nearby_refinery_km || 0} km`}
              </span>
            </div>
            {facility.land_cover && (
              <div className="event-panel__row">
                <span className="event-panel__row-label">Land Cover</span>
                <span className="event-panel__row-value">{facility.land_cover}</span>
              </div>
            )}
          </>
        )}

        {/* Evidence */}
        {evidenceItems.length > 0 && (
          <>
            <hr className="event-panel__divider" />
            <div className="event-panel__section-label" style={{ marginBottom: '6px' }}>Key Evidence</div>
            <ul style={{ paddingLeft: '14px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {evidenceItems.slice(0, 3).map((item: string, i: number) => (
                <li key={i} style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>{item}</li>
              ))}
            </ul>
          </>
        )}

        {/* Actions */}
        <hr className="event-panel__divider" />

        {onNavigate && (
          <button
            className="btn btn--ghost"
            style={{ width: '100%', justifyContent: 'center', marginTop: '6px' }}
            onClick={() => onNavigate(event.event_id)}
          >
            🔍 Full Investigation →
          </button>
        )}

        <a
          href={getReportUrl(event.event_id)}
          target="_blank"
          rel="noreferrer"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '5px',
            marginTop: '4px',
            padding: '6px 12px',
            background: 'transparent',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            fontSize: '11px',
            fontWeight: '600',
            color: 'var(--text-muted)',
            textDecoration: 'none',
            transition: 'all var(--transition-fast)',
          }}
        >
          Export Report
        </a>
      </div>
    </div>
  );
}
