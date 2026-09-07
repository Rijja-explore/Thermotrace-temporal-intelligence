import React, { useState } from 'react';
import type { ThermoEvent } from '../../services/api';

export interface CompareEventsPanelProps {
  currentEvent: ThermoEvent;
  availableEvents: ThermoEvent[];
  onClose: () => void;
  onSelectEvent?: (eventId: string) => void;
}

export const CompareEventsPanel: React.FC<CompareEventsPanelProps> = ({
  currentEvent,
  availableEvents,
  onClose,
  onSelectEvent,
}) => {
  const otherEvents = availableEvents.filter(e => e.event_id !== currentEvent.event_id);
  const [selectedSecondId, setSelectedSecondId] = useState<string>(
    otherEvents[0]?.event_id || ''
  );

  const secondEvent = availableEvents.find(e => e.event_id === selectedSecondId) || otherEvents[0];

  const renderEventColumn = (ev: ThermoEvent | undefined, isCurrent: boolean) => {
    if (!ev) return <div style={{ color: 'var(--text-muted)' }}>No event selected</div>;

    const risk = ev.operational_risk?.risk_score ?? ev.scores?.operational_risk ?? 0;
    const industrial = ev.industrial_likelihood?.score ?? ev.scores?.industrial_likelihood ?? 0;
    const conf = Math.round((ev.classification?.confidence || 0) * (ev.classification?.confidence <= 1 ? 100 : 1));
    const label = (ev.classification?.label || ev.classification?.class || 'Unknown').replace(/_/g, ' ');
    const facility = ev.facility_context || {};
    const facilityDist = facility.distance_to_facility_m
      ? `${(facility.distance_to_facility_m / 1000).toFixed(2)} km`
      : facility.nearby_refinery_km ? `${facility.nearby_refinery_km} km` : 'N/A';
    const tf = ev.temporal_features;
    const persistenceRatio = tf?.persistence_ratio ?? tf?.window_30d?.persistence_ratio;
    const persistence = persistenceRatio !== undefined ? `${Math.round(persistenceRatio * 100)}%` : '—';
    const detectionCount = tf?.detection_count_30d ?? tf?.window_30d?.detection_count;
    const activeDetections = detectionCount !== undefined ? `${detectionCount} detections` : '—';

    return (
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <span style={{ fontSize: '10px', color: isCurrent ? 'var(--accent-cyan)' : 'var(--accent-blue)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.6px' }}>
              {isCurrent ? 'Current Target' : 'Comparison Target'}
            </span>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
              {ev.event_id}
            </div>
          </div>
          {isCurrent ? (
            <span className="status-pill status-pill--live">Inspecting</span>
          ) : (
            <button
              className="btn btn--cyan btn--sm"
              onClick={() => onSelectEvent?.(ev.event_id)}
            >
              Switch to this
            </button>
          )}
        </div>

        <div className="card" style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Classification</div>
          <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--accent-teal)' }}>{label}</div>
          <div style={{ display: 'flex', gap: '6px' }}>
            <span className={`status-badge status-badge--${ev.status}`}>{ev.status}</span>
            <span className="risk-badge risk-badge--cyan">{conf}% Conf</span>
          </div>
        </div>

        <div className="card" style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Telemetry & Spatial Metrics
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '10px' }}>Operational Risk</div>
              <div style={{ fontWeight: 700, color: risk > 60 ? 'var(--risk-critical)' : 'var(--risk-low)' }}>
                {risk}/100
              </div>
            </div>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '10px' }}>Industrial Likelihood</div>
              <div style={{ fontWeight: 700, color: industrial > 50 ? 'var(--accent-amber)' : 'var(--text-primary)' }}>
                {industrial}/100
              </div>
            </div>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '10px' }}>Persistence (30d)</div>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{persistence}</div>
            </div>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '10px' }}>30d Activity</div>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{activeDetections}</div>
            </div>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '10px' }}>Facility Distance</div>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{facilityDist}</div>
            </div>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '10px' }}>Nearest Facility</div>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {facility.nearest_facility_name || facility.name || 'Off-site'}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal"
        style={{ maxWidth: '820px', width: '90%' }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
          <div>
            <div className="modal__title" style={{ margin: 0 }}>Side-by-Side Event Comparison</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
              Contrast thermal temporal fingerprints, spatial offsets, and risk classifications
            </div>
          </div>
          <button className="btn btn--icon btn--sm" onClick={onClose} title="Close">
            ✕
          </button>
        </div>

        {/* Comparison selector */}
        <div style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <label style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 500 }}>
            Compare current with:
          </label>
          <select
            className="filter-select"
            value={selectedSecondId}
            onChange={e => setSelectedSecondId(e.target.value)}
            style={{ minWidth: '220px' }}
          >
            {otherEvents.map(e => (
              <option key={e.event_id} value={e.event_id}>
                {e.event_id} — {(e.classification?.label || 'Unknown').replace(/_/g, ' ')} ({e.region || 'India'})
              </option>
            ))}
          </select>
        </div>

        {/* 2-Column Comparison Layout */}
        <div style={{ display: 'flex', gap: '20px', alignItems: 'stretch' }}>
          {renderEventColumn(currentEvent, true)}
          <div style={{ width: '1px', background: 'var(--border-subtle)' }} />
          {renderEventColumn(secondEvent, false)}
        </div>

        <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid var(--border-subtle)', paddingTop: '14px' }}>
          <button className="btn btn--ghost" onClick={onClose}>
            Close Comparison
          </button>
        </div>
      </div>
    </div>
  );
};

export default CompareEventsPanel;
