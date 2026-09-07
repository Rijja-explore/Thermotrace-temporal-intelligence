import React, { useState } from 'react';
import type { ThermoEvent } from '../../services/api';
import { verifyEvent } from '../../services/api';
import { sendAlertEmail } from '../../services/alertEmail';

interface AnalystActionBarProps {
  event: ThermoEvent;
  status: string;
  onStatusChange: (newStatus: string) => void;
}

interface AuditEntry {
  action: string;
  analyst: string;
  time: string;
}

const AnalystActionBar: React.FC<AnalystActionBarProps> = ({ event, status, onStatusChange }) => {
  const [feedback, setFeedback] = useState<string | null>(null);
  const [auditLog, setAuditLog] = useState<AuditEntry[]>([]);
  const [showNote, setShowNote] = useState(false);
  const [note, setNote] = useState('');

  const doAction = async (action: string, label?: string) => {
    const timeStr = new Date().toLocaleTimeString('en-IN', {
      hour: '2-digit', minute: '2-digit',
      timeZone: 'Asia/Kolkata',
    }) + ' IST';

    try {
      const result = await verifyEvent(event.event_id, action, label, note || undefined);
      onStatusChange(result.status || action.toLowerCase());
    } catch {
      onStatusChange(action.toLowerCase());
    }

    // Auto-dispatch confirmation email to anagesh842005@gmail.com
    if (action.includes('CONFIRM') || action.includes('DISPATCH') || action.includes('VERIF')) {
      const risk = (event as any).operational_risk?.risk_score ?? event.scores?.operational_risk ?? 75;
      const frpVal = event.observations?.[0]?.frp ?? 180.0;
      const hazardRadius = (event as any).impact?.hazard_radius_m ?? 240;
      sendAlertEmail({
        eventId: event.event_id,
        facilityName: event.facility_context?.nearest_facility_name ?? event.facility_context?.name ?? 'Industrial Installation',
        frpMw: frpVal,
        riskScore: risk,
        threatTier: risk >= 80 ? 'CRITICAL' : 'HIGH',
        hazardRadiusM: hazardRadius,
        customNotes: `Analyst Confirmation Notice: Event ${event.event_id} has been officially ${action} as ${label || event.classification?.class || 'Confirmed Event'}. Rationale: ${note || 'Confirmed via forensic multi-modal analysis'}.`,
        forceSend: true,
      });
    }

    const newEntry: AuditEntry = {
      action: label ? `Reclassified → ${label.replace(/_/g, ' ')}` : action,
      analyst: 'Analyst Lead',
      time: timeStr,
    };
    setAuditLog(prev => [newEntry, ...prev]);
    setFeedback(`✓ ${action} recorded & notified to anagesh842005@gmail.com`);
    setNote('');
    setShowNote(false);
    setTimeout(() => setFeedback(null), 3500);
  };

  const label = (event.classification?.label || event.classification?.class || '').toLowerCase();
  const isAgricultural = label.includes('agri');
  const isWildfire = label.includes('wildfire') || label.includes('forest');
  const isIndustrialFire = label.includes('fire') || label.includes('abnormal');

  return (
    <div className="analyst-action-bar">
      <div className="analyst-action-bar__title">Analyst Workflow</div>

      <div className="analyst-action-bar__actions">
        {isAgricultural ? (
          <>
            <button className="action-btn action-btn--confirm" onClick={() => doAction('CONFIRMED', 'agricultural_burning')}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12" /></svg>
              Confirm Agricultural Burning
            </button>
            <button className="action-btn action-btn--reject" onClick={() => doAction('RECLASSIFIED', 'industrial_fire_or_abnormal_event')}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
              Reclassify as Industrial Fire
            </button>
            <button className="action-btn action-btn--amber" onClick={() => doAction('INVESTIGATING')}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
              Mark Investigating
            </button>
            <button className="action-btn action-btn--primary" onClick={() => doAction('VERIFIED', 'agricultural_burning')}>
              Verified Agricultural
            </button>
          </>
        ) : isWildfire ? (
          <>
            <button className="action-btn action-btn--confirm" onClick={() => doAction('CONFIRMED', 'wildfire_or_forest_fire')}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12" /></svg>
              Confirm Forest Fire / Wildfire
            </button>
            <button className="action-btn action-btn--reject" onClick={() => doAction('RECLASSIFIED', 'industrial_fire_or_abnormal_event')}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
              Reclassify as Industrial Fire
            </button>
            <button className="action-btn action-btn--amber" onClick={() => doAction('INVESTIGATING')}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
              Mark Investigating
            </button>
            <button className="action-btn action-btn--primary" onClick={() => doAction('VERIFIED', 'wildfire_or_forest_fire')}>
              Verified Wildfire
            </button>
          </>
        ) : isIndustrialFire ? (
          <>
            <button className="action-btn action-btn--confirm" style={{ background: '#FF5C6C', borderColor: '#FF5C6C', color: '#FFF' }} onClick={() => doAction('CONFIRMED', 'industrial_fire_or_abnormal_event')}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12" /></svg>
              Confirm Industrial Fire
            </button>
            <button className="action-btn action-btn--reject" onClick={() => doAction('RECLASSIFIED', 'agricultural_burning')}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
              Mark Non-Industrial (False Alarm)
            </button>
            <button className="action-btn action-btn--amber" onClick={() => doAction('INVESTIGATING')}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
              Mark Investigating
            </button>
            <button className="action-btn action-btn--primary" onClick={() => doAction('DISPATCH_EMERGENCY', 'industrial_fire_or_abnormal_event')}>
              Dispatch Response Team
            </button>
          </>
        ) : (
          <>
            <button className="action-btn action-btn--confirm" onClick={() => doAction('CONFIRMED', 'persistent_industrial_source')}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12" /></svg>
              Confirm Industrial Source
            </button>
            <button className="action-btn action-btn--reject" onClick={() => doAction('REJECTED', 'agricultural_burning')}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
              Mark Non-Industrial
            </button>
            <button className="action-btn action-btn--amber" onClick={() => doAction('INVESTIGATING')}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
              Mark Investigating
            </button>
            <button className="action-btn action-btn--primary" onClick={() => doAction('VERIFIED', 'persistent_industrial_source')}>
              Verified Industrial
            </button>
          </>
        )}
        <button className="action-btn action-btn--neutral" onClick={() => setShowNote(s => !s)}>
          {showNote ? 'Cancel Note' : '+ Add Note'}
        </button>
        <button className="action-btn action-btn--neutral" onClick={() => doAction('ACKNOWLEDGED')}>
          Acknowledge
        </button>
      </div>

      {/* Note field */}
      {showNote && (
        <div style={{ marginBottom: '10px', animation: 'fade-in 0.2s ease-out' }}>
          <textarea
            className="modal__textarea"
            value={note}
            onChange={e => setNote(e.target.value)}
            placeholder="Add analyst rationale or note..."
            style={{ marginBottom: '6px', height: '60px' }}
          />
          <button
            className="action-btn action-btn--primary"
            onClick={() => doAction('NOTE_ADDED')}
            disabled={!note.trim()}
          >
            Save Note
          </button>
        </div>
      )}

      {/* Feedback */}
      {feedback && (
        <div className="analyst-action-bar__feedback">{feedback}</div>
      )}

      {/* Audit timeline */}
      {auditLog.length > 0 && (
        <div className="audit-timeline">
          {auditLog.map((entry, i) => (
            <div key={i} className="audit-entry">
              <div className="audit-entry__dot" style={{
                background: entry.action.includes('CONFIRMED') || entry.action.includes('Verified')
                  ? 'var(--risk-low)'
                  : entry.action.includes('REJECTED')
                  ? 'var(--risk-critical)'
                  : 'var(--border-active)'
              }} />
              <span className="audit-entry__action">{entry.action}</span>
              <span className="audit-entry__meta"> · {entry.analyst}</span>
              <span className="audit-entry__time">{entry.time}</span>
            </div>
          ))}
        </div>
      )}

      {/* Current status */}
      <div style={{ marginTop: auditLog.length > 0 ? '8px' : '4px', fontSize: '11px', color: 'var(--text-muted)' }}>
        Current status: <span className={`status-badge status-badge--${status.replace(/ /g, '_')}`}>
          {status.replace(/_/g, ' ')}
        </span>
      </div>
    </div>
  );
};

export default AnalystActionBar;
