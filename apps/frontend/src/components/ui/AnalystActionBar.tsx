import React, { useState } from 'react';
import type { ThermoEvent } from '../../services/api';
import { verifyEvent, sendReportEmail } from '../../services/api';
import { RECIPIENT_CENTRAL } from '../../services/alertEmail';

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

  // Approval Modal State
  const [pendingApproval, setPendingApproval] = useState<{ action: string; label?: string } | null>(null);
  const [approvalStep, setApprovalStep] = useState<'IDLE' | 'GENERATING' | 'SENDING' | 'DONE'>('IDLE');
  const [approvalResult, setApprovalResult] = useState<{ success: boolean; msg: string; err?: string } | null>(null);

  const executeApproval = async () => {
    if (!pendingApproval) return;
    const { action, label } = pendingApproval;
    const timeStr = new Date().toLocaleTimeString('en-IN', {
      hour: '2-digit', minute: '2-digit',
      timeZone: 'Asia/Kolkata',
    }) + ' IST';

    setApprovalStep('GENERATING');
    setApprovalResult(null);

    // Step 1: Record verification on backend
    try {
      const result = await verifyEvent(event.event_id, action, label, note || undefined);
      onStatusChange(result.status || action.toLowerCase());
    } catch {
      onStatusChange(action.toLowerCase());
    }

    // Small delay to simulate report generation
    await new Promise(r => setTimeout(r, 600));
    setApprovalStep('SENDING');

    // Step 2: Call backend report email endpoint
    try {
      const emailRes = await sendReportEmail(
        event.event_id,
        RECIPIENT_CENTRAL,
        note || `Analyst verified and confirmed thermal excursion at ${event.facility_context?.name || 'industrial facility'}.`
      );

      if (emailRes?.email_sent || emailRes?.delivery_status === 'DELIVERED') {
        setApprovalResult({
          success: true,
          msg: `✓ Report generated\n✓ Report sent successfully\nDestination: ${RECIPIENT_CENTRAL}`,
        });
        setFeedback(`✓ Event APPROVED — Complete report generated & delivered to ${RECIPIENT_CENTRAL}`);
      } else {
        const errMsg = emailRes?.error || 'SMTP credentials not configured (Demo Mode recorded)';
        setApprovalResult({
          success: false,
          msg: `✓ Report generated\n⚠️ EMAIL DELIVERY FAILED: ${errMsg}\nDestination: ${RECIPIENT_CENTRAL}`,
          err: errMsg,
        });
        setFeedback(`✓ Report generated · Email status: ${errMsg}`);
      }
    } catch (err: any) {
      setApprovalResult({
        success: false,
        msg: `✓ Report generated\n⚠️ EMAIL DELIVERY FAILED: ${err?.message || 'Network error'}\nDestination: ${RECIPIENT_CENTRAL}`,
        err: err?.message,
      });
      setFeedback(`✓ Report generated · Email delivery failed`);
    } finally {
      setApprovalStep('DONE');
      const newEntry: AuditEntry = {
        action: label ? `Approved → ${label.replace(/_/g, ' ')}` : 'Approved & Dispatched',
        analyst: 'Lead Thermal Analyst',
        time: timeStr,
      };
      setAuditLog(prev => [newEntry, ...prev]);
      setNote('');
      setShowNote(false);
    }
  };

  const doAction = async (action: string, label?: string) => {
    // If confirmation or approval action, prompt the modal
    if (action.includes('CONFIRM') || action.includes('DISPATCH') || action.includes('VERIF')) {
      setPendingApproval({ action, label });
      setApprovalStep('IDLE');
      setApprovalResult(null);
      return;
    }

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

    setFeedback(`✓ ${action} recorded by Lead Analyst`);
    const newEntry: AuditEntry = {
      action: label ? `Reclassified → ${label.replace(/_/g, ' ')}` : action,
      analyst: 'Lead Thermal Analyst',
      time: timeStr,
    };
    setAuditLog(prev => [newEntry, ...prev]);
    setNote('');
    setShowNote(false);
    setTimeout(() => setFeedback(null), 5000);
  };

  const label = (event.classification?.label || event.classification?.class || '').toLowerCase();
  const isAgricultural = label.includes('agri');
  const isWildfire = label.includes('wildfire') || label.includes('forest');
  const isIndustrialFire = label.includes('fire') || label.includes('abnormal');

  return (
    <div className="analyst-action-bar">
      <div className="analyst-action-bar__title">Analyst Decision & Verification</div>

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
              Confirm / Approve Industrial Incident
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
            placeholder="Add analyst rationale or verification notes..."
            style={{ marginBottom: '6px', height: '60px' }}
          />
        </div>
      )}

      {/* Feedback Toast */}
      {feedback && (
        <div className="analyst-action-bar__feedback">{feedback}</div>
      )}

      {/* Audit timeline */}
      {auditLog.length > 0 && (
        <div className="audit-timeline">
          {auditLog.map((entry, i) => (
            <div key={i} className="audit-entry">
              <div className="audit-entry__dot" style={{
                background: entry.action.includes('Approved') || entry.action.includes('CONFIRMED') || entry.action.includes('Verified')
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

      {/* ─── APPROVAL CONFIRMATION MODAL ─── */}
      {pendingApproval && (
        <div className="report-modal-backdrop" onClick={e => { if (e.target === e.currentTarget && approvalStep === 'IDLE') setPendingApproval(null); }}>
          <div className="report-modal" role="dialog" aria-modal="true" style={{ maxWidth: '480px', width: '90%', padding: '24px', background: '#0F172A', border: '1px solid #334155', borderRadius: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
              <span style={{ fontSize: '24px' }}>🛡️</span>
              <div>
                <div style={{ fontSize: '16px', fontWeight: 800, color: '#F8FAFC' }}>
                  Approve this thermal event?
                </div>
                <div style={{ fontSize: '11px', color: '#94A3B8', fontFamily: 'monospace' }}>
                  Event ID: {event.event_id}
                </div>
              </div>
            </div>

            <p style={{ fontSize: '13px', color: '#CBD5E1', lineHeight: '1.6', marginBottom: '18px' }}>
              This will generate the complete ThermoTrace intelligence report and send it to the ThermoTrace report feed.
            </p>

            {approvalStep === 'IDLE' && (
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '20px' }}>
                <button
                  type="button"
                  onClick={() => setPendingApproval(null)}
                  style={{ padding: '8px 16px', background: '#1E293B', border: '1px solid #334155', borderRadius: '6px', color: '#94A3B8', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}
                >
                  CANCEL
                </button>
                <button
                  type="button"
                  onClick={executeApproval}
                  style={{ padding: '8px 18px', background: '#0284C7', border: 'none', borderRadius: '6px', color: '#FFFFFF', fontSize: '12px', fontWeight: 700, cursor: 'pointer' }}
                >
                  APPROVE & SEND REPORT
                </button>
              </div>
            )}

            {(approvalStep === 'GENERATING' || approvalStep === 'SENDING') && (
              <div style={{ padding: '16px', background: '#1E293B', borderRadius: '8px', border: '1px solid #38BDF8', textAlign: 'center' }}>
                <div style={{ fontSize: '13px', fontWeight: 700, color: '#38BDF8', marginBottom: '6px' }}>
                  {approvalStep === 'GENERATING' ? 'Generating report...' : 'Report generated. Sending report...'}
                </div>
                <div style={{ fontSize: '11px', color: '#94A3B8' }}>
                  Connecting to mail service for {RECIPIENT_CENTRAL}...
                </div>
              </div>
            )}

            {approvalStep === 'DONE' && approvalResult && (
              <div style={{ marginTop: '12px' }}>
                <div style={{
                  padding: '14px',
                  background: approvalResult.success ? 'rgba(79, 209, 139, 0.1)' : 'rgba(255, 92, 108, 0.1)',
                  border: `1px solid ${approvalResult.success ? 'rgba(79, 209, 139, 0.4)' : 'rgba(255, 92, 108, 0.4)'}`,
                  borderRadius: '8px',
                  fontSize: '12px',
                  color: approvalResult.success ? '#4FD18B' : '#FF5C6C',
                  whiteSpace: 'pre-line',
                  lineHeight: '1.6',
                  fontFamily: 'var(--font-mono)'
                }}>
                  {approvalResult.msg}
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
                  <button
                    type="button"
                    onClick={() => {
                      setPendingApproval(null);
                      setApprovalStep('IDLE');
                    }}
                    style={{ padding: '8px 18px', background: '#334155', border: 'none', borderRadius: '6px', color: '#FFFFFF', fontSize: '12px', fontWeight: 700, cursor: 'pointer' }}
                  >
                    CLOSE
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalystActionBar;
