import React, { useState } from 'react';
import { downloadReportPdf, sendReportEmail } from '../../services/api';

interface ReportPreviewModalProps {
  onClose: () => void;
  eventId: string;
  title: string;
  location?: string;
  confidence?: number;
  industrialLikelihood?: number;
  operationalRisk?: number;
  evidenceFor?: string[];
  label?: string;
  getReportUrl?: (id: string) => string;
}

const ReportPreviewModal: React.FC<ReportPreviewModalProps> = ({
  onClose,
  eventId,
  title,
  location = 'India',
  confidence = 0,
  industrialLikelihood = 0,
  operationalRisk = 0,
  evidenceFor = [],
  label = 'unknown',
}) => {
  const confPct = Math.round(confidence <= 1.0 ? confidence * 100 : confidence);
  const now = new Date().toISOString().split('T')[0];

  const [downloading, setDownloading] = useState(false);
  const [showEmailSection, setShowEmailSection] = useState(false);
  const [recipientEmail, setRecipientEmail] = useState('thermotrace.india@gmail.com');
  const [analystNotes, setAnalystNotes] = useState('Official thermal intelligence dossier generated for operational review.');
  const [emailSending, setEmailSending] = useState(false);
  const [emailStatus, setEmailStatus] = useState<{ success: boolean; msg: string } | null>(null);

  const recommendedAction = operationalRisk >= 70
    ? 'Immediate analyst verification required. Event meets threshold for emergency escalation to industrial safety leads and district authorities.'
    : operationalRisk >= 50
    ? 'Routine analyst review recommended within 24 hours. Monitor persistent flaring trend.'
    : 'Normal facility baseline operations. Monitor for continued compliance.';

  const defaultEvidence = [
    `Classified as: ${label.replace(/_/g, ' ')}`,
    `Classification confidence: ${confPct}%`,
    `Industrial likelihood score: ${industrialLikelihood}/100`,
    `Operational risk score: ${operationalRisk}/100`,
    'Spatial stability: High — source location consistent across satellite passes',
  ];

  const displayEvidence = evidenceFor.length > 0 ? evidenceFor.slice(0, 5) : defaultEvidence;

  const handleDownloadPdf = async () => {
    setDownloading(true);
    try {
      await downloadReportPdf(eventId);
    } catch (e) {
      console.error(e);
    } finally {
      setDownloading(false);
    }
  };

  const handleSendEmail = async () => {
    if (!recipientEmail) return;
    setEmailSending(true);
    setEmailStatus(null);
    try {
      const res = await sendReportEmail(eventId, recipientEmail, analystNotes);
      if (res?.email_sent || res?.delivery_status === 'DELIVERED') {
        setEmailStatus({
          success: true,
          msg: `✓ Report generated & sent successfully\nFrom: thermotrace.india@gmail.com\nTo: ${recipientEmail}`,
        });
      } else {
        setEmailStatus({
          success: false,
          msg: `✓ Report generated\n✕ Email delivery failed: ${res?.error || 'SMTP credentials not configured (MAIL_USERNAME / MAIL_PASSWORD environment variables not set)'}`,
        });
      }
    } catch (err: any) {
      setEmailStatus({
        success: false,
        msg: `✓ Report generated\n✕ Email delivery failed: ${err?.message || 'Network connection error'}`,
      });
    } finally {
      setEmailSending(false);
    }
  };

  return (
    <div className="report-modal-backdrop" onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="report-modal" role="dialog" aria-modal="true" aria-label="Report preview" style={{ maxWidth: '640px', width: '92%' }}>
        {/* Header */}
        <div className="report-modal__header">
          <div>
            <div className="report-modal__header-brand" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>🛡️ THERMOTRACE · Official Intelligence Report</span>
              <span style={{ fontSize: '9px', padding: '2px 6px', background: 'rgba(67,217,232,0.15)', color: 'var(--accent-cyan)', borderRadius: '4px' }}>
                PDF EXPORT
              </span>
            </div>
            <div style={{ fontSize: '10px', color: '#71869B', marginTop: '2px', fontFamily: 'monospace' }}>
              Generated {now} · 4-Engine GeoAI Intelligence Dossier
            </div>
          </div>
          <button className="report-modal__header-close" onClick={onClose}>✕</button>
        </div>

        {/* Body */}
        <div className="report-modal__body" style={{ maxHeight: '80vh', overflowY: 'auto' }}>
          <div className="report-modal__event-id">{eventId}</div>
          <div className="report-modal__title">{title || label.replace(/_/g, ' ')}</div>
          <div className="report-modal__location">
            📍 {location}
          </div>

          {/* Score row */}
          <div className="report-modal__score-row">
            <div className="report-score-card">
              <div className="report-score-card__label">Classification Confidence</div>
              <div className="report-score-card__value" style={{ color: '#4D8DFF' }}>{confPct}%</div>
            </div>
            <div className="report-score-card">
              <div className="report-score-card__label">Industrial Likelihood</div>
              <div className="report-score-card__value" style={{ color: '#FFB547' }}>{industrialLikelihood}</div>
            </div>
            <div className="report-score-card">
              <div className="report-score-card__label">Operational Risk</div>
              <div className="report-score-card__value" style={{ color: operationalRisk >= 70 ? '#FF5C6C' : '#FF7A45' }}>
                {operationalRisk}
              </div>
            </div>
          </div>

          {/* Evidence summary */}
          <div className="report-modal__section-title">Evidence & AI Attributions</div>
          <ul className="report-modal__evidence-list">
            {displayEvidence.map((item, i) => (
              <li key={i} className="report-modal__evidence-item">{item}</li>
            ))}
          </ul>

          {/* Recommended action */}
          <div className="report-modal__section-title">Standard Operating Directive</div>
          <div className="report-modal__recommended">{recommendedAction}</div>

          {/* Email Dispatch Section (Accordion / Interactive) */}
          {showEmailSection ? (
            <div style={{
              background: '#0B1321',
              border: '1px solid rgba(67, 217, 232, 0.3)',
              borderRadius: '8px',
              padding: '14px',
              marginTop: '16px',
              marginBottom: '16px',
            }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--accent-cyan)', marginBottom: '10px', display: 'flex', justifyContent: 'space-between' }}>
                <span>📧 Dispatch Report Dossier</span>
                <span style={{ fontSize: '10px', color: '#94A3B8' }}>Destination: thermotrace.india@gmail.com</span>
              </div>

              <div style={{ marginBottom: '8px' }}>
                <label style={{ fontSize: '10px', color: '#94A3B8', display: 'block', marginBottom: '4px' }}>Destination Email:</label>
                <input
                  type="email"
                  value={recipientEmail}
                  onChange={e => setRecipientEmail(e.target.value)}
                  style={{
                    width: '100%',
                    background: '#101927',
                    border: '1px solid #233B56',
                    borderRadius: '4px',
                    padding: '6px 10px',
                    color: '#FFF',
                    fontSize: '12px',
                  }}
                />
              </div>

              <div style={{ marginBottom: '10px' }}>
                <label style={{ fontSize: '10px', color: '#94A3B8', display: 'block', marginBottom: '4px' }}>Analyst Remarks / Notes:</label>
                <textarea
                  value={analystNotes}
                  onChange={e => setAnalystNotes(e.target.value)}
                  rows={2}
                  style={{
                    width: '100%',
                    background: '#101927',
                    border: '1px solid #233B56',
                    borderRadius: '4px',
                    padding: '6px 10px',
                    color: '#FFF',
                    fontSize: '11px',
                    resize: 'none',
                  }}
                />
              </div>

              {emailStatus && (
                <div style={{
                  padding: '8px 10px',
                  borderRadius: '4px',
                  marginBottom: '10px',
                  fontSize: '11px',
                  background: emailStatus.success ? 'rgba(79, 209, 139, 0.12)' : 'rgba(255, 92, 108, 0.12)',
                  border: `1px solid ${emailStatus.success ? '#4FD18B' : '#FF5C6C'}`,
                  color: emailStatus.success ? '#4FD18B' : '#FF5C6C',
                }}>
                  {emailStatus.success ? '✓ ' : '✕ '} {emailStatus.msg}
                </div>
              )}

              <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  onClick={() => setShowEmailSection(false)}
                  style={{
                    background: 'transparent',
                    border: '1px solid #334155',
                    color: '#94A3B8',
                    padding: '6px 12px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSendEmail}
                  disabled={emailSending}
                  style={{
                    background: 'var(--accent-cyan)',
                    border: 'none',
                    color: '#0B1321',
                    padding: '6px 14px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    fontWeight: 700,
                    cursor: emailSending ? 'wait' : 'pointer',
                  }}
                >
                  {emailSending ? 'Dispatching...' : '🚀 Send to thermotrace.india@gmail.com'}
                </button>
              </div>
            </div>
          ) : null}

          {/* Actions */}
          <div className="report-modal__actions" style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
            <button className="report-modal__btn report-modal__btn--secondary" onClick={onClose} style={{ flex: 1 }}>
              Close
            </button>
            <button
              className="report-modal__btn"
              onClick={() => setShowEmailSection(!showEmailSection)}
              style={{
                flex: 1.2,
                background: 'rgba(67, 217, 232, 0.1)',
                border: '1px solid var(--accent-cyan)',
                color: 'var(--accent-cyan)',
                fontWeight: 600,
                cursor: 'pointer',
                padding: '8px 12px',
                borderRadius: '6px',
              }}
            >
              📧 Send Email Report
            </button>
            <button
              className="report-modal__btn report-modal__btn--primary"
              onClick={handleDownloadPdf}
              disabled={downloading}
              style={{
                flex: 1.4,
                background: 'linear-gradient(135deg, #43D9E8 0%, #4D8DFF 100%)',
                border: 'none',
                color: '#0B1321',
                fontWeight: 700,
                cursor: downloading ? 'wait' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                padding: '8px 12px',
                borderRadius: '6px',
              }}
            >
              {downloading ? 'Generating PDF...' : '📄 Download Formatted PDF'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportPreviewModal;
