import React, { useState, useEffect } from 'react';
import { fetchEvents, downloadReportPdf, sendReportEmail } from '../services/api';
import type { ThermoEvent } from '../services/api';
import ReportPreviewModal from '../components/ui/ReportPreviewModal';
import { RECIPIENT_CENTRAL } from '../services/alertEmail';

interface ReportsViewProps {
  onNavigate?: (page: string, params?: any) => void;
}

export const ReportsView: React.FC<ReportsViewProps> = ({ onNavigate }) => {
  const [events, setEvents] = useState<ThermoEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedEventForModal, setSelectedEventForModal] = useState<ThermoEvent | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [sendingId, setSendingId] = useState<string | null>(null);
  const [actionNotice, setActionNotice] = useState<{ id: string; success: boolean; msg: string } | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const evs = await fetchEvents();
        setEvents(evs.events || []);
      } catch (e) {
        console.error('Failed to load events for reports:', e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleDownload = async (eventId: string) => {
    setDownloadingId(eventId);
    try {
      await downloadReportPdf(eventId);
      setActionNotice({
        id: eventId,
        success: true,
        msg: `✓ PDF dossier for ${eventId} downloaded successfully.`,
      });
    } catch {
      setActionNotice({
        id: eventId,
        success: false,
        msg: `Failed to download PDF for ${eventId}.`,
      });
    } finally {
      setDownloadingId(null);
      setTimeout(() => setActionNotice(null), 4000);
    }
  };

  const handleSendEmail = async (eventId: string) => {
    setSendingId(eventId);
    setActionNotice(null);
    try {
      const res = await sendReportEmail(
        eventId,
        RECIPIENT_CENTRAL,
        `Official ThermoTrace intelligence report dispatched by Lead Analyst for ${eventId}.`
      );
      if (res?.email_sent || res?.delivery_status === 'DELIVERED') {
        setActionNotice({
          id: eventId,
          success: true,
          msg: `✓ Report delivered to ${RECIPIENT_CENTRAL}`,
        });
      } else {
        setActionNotice({
          id: eventId,
          success: false,
          msg: `✓ Report generated · SMTP status: ${res?.error || 'Demo Mode recorded'}`,
        });
      }
    } catch (err: any) {
      setActionNotice({
        id: eventId,
        success: false,
        msg: `⚠️ Email delivery failed: ${err?.message || 'Network error'}`,
      });
    } finally {
      setSendingId(null);
      setTimeout(() => setActionNotice(null), 6000);
    }
  };

  return (
    <div className="reports-view" style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header Banner */}
      <div style={{
        padding: '20px 24px',
        background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(7, 14, 26, 0.98))',
        border: '1px solid #1E293B',
        borderRadius: '12px',
        marginBottom: '24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '16px',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.4)',
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span style={{ fontSize: '20px' }}>📑</span>
            <h1 style={{ fontSize: '18px', fontWeight: 800, color: '#F8FAFC', letterSpacing: '0.02em', margin: 0 }}>
              Reports & Incident Briefings
            </h1>
            <span style={{
              fontSize: '10px',
              fontWeight: 700,
              padding: '2px 8px',
              background: 'rgba(56, 189, 248, 0.15)',
              color: '#38BDF8',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              borderRadius: '12px'
            }}>
              TAB 6 · DOSSIER REPOSITORY
            </span>
          </div>
          <p style={{ fontSize: '12px', color: '#94A3B8', margin: 0, lineHeight: 1.5 }}>
            Executive intelligence reports generated across 4-Engine GeoAI, API 521 radiant hazard contours, and mitigation directives.
          </p>
        </div>

        <div style={{
          padding: '8px 14px',
          background: 'rgba(56, 189, 248, 0.08)',
          border: '1px solid rgba(56, 189, 248, 0.25)',
          borderRadius: '8px',
          fontSize: '11px',
          color: '#CBD5E1',
          fontFamily: 'var(--font-mono)'
        }}>
          <div>Destination: <strong style={{ color: '#38BDF8' }}>{RECIPIENT_CENTRAL}</strong></div>
          <div style={{ color: '#94A3B8', fontSize: '10px', marginTop: '2px' }}>Format: ReportLab PDF + HTML Dossier</div>
        </div>
      </div>

      {/* Action Notice Banner */}
      {actionNotice && (
        <div style={{
          padding: '12px 16px',
          marginBottom: '16px',
          borderRadius: '8px',
          background: actionNotice.success ? 'rgba(79, 209, 139, 0.12)' : 'rgba(255, 92, 108, 0.12)',
          border: `1px solid ${actionNotice.success ? 'rgba(79, 209, 139, 0.4)' : 'rgba(255, 92, 108, 0.4)'}`,
          color: actionNotice.success ? '#4FD18B' : '#FF5C6C',
          fontSize: '12px',
          fontWeight: 600,
          fontFamily: 'var(--font-mono)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          animation: 'fadeIn 0.2s ease-out'
        }}>
          <span>{actionNotice.success ? '✓' : '⚠️'}</span>
          <span>{actionNotice.msg}</span>
        </div>
      )}

      {/* Reports Table / List */}
      <div style={{
        background: '#0B132B',
        border: '1px solid #1E293B',
        borderRadius: '12px',
        overflow: 'hidden'
      }}>
        <div style={{
          padding: '14px 20px',
          background: '#070E1A',
          borderBottom: '1px solid #1E293B',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ fontSize: '12px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Generated Dossiers ({events.length} Available)
          </div>
          <div style={{ fontSize: '11px', color: '#64748B' }}>
            Click 'View Dossier' to review the 19-section analysis
          </div>
        </div>

        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#94A3B8', fontSize: '13px' }}>
            Loading report index...
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12px' }}>
              <thead>
                <tr style={{ background: 'rgba(15, 23, 42, 0.6)', borderBottom: '1px solid #1E293B', color: '#64748B', textTransform: 'uppercase', fontSize: '10px', letterSpacing: '0.04em' }}>
                  <th style={{ padding: '12px 16px' }}>Event ID</th>
                  <th style={{ padding: '12px 16px' }}>Facility / Location</th>
                  <th style={{ padding: '12px 16px' }}>Classification</th>
                  <th style={{ padding: '12px 16px' }}>Risk & FRP</th>
                  <th style={{ padding: '12px 16px' }}>Decision</th>
                  <th style={{ padding: '12px 16px' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {events.map((ev) => {
                  const facilityName = ev.facility_context?.name || ev.facility_context?.nearest_facility_name || 'Industrial Facility';
                  const label = ev.classification?.label || ev.classification?.class || 'Industrial Event';
                  const riskScore = ev.operational_risk?.risk_score ?? ev.scores?.operational_risk ?? 75;
                  const frp = ev.observations?.[0]?.frp ?? 180.0;
                  const statusLabel = ev.status || 'requires_verification';
                  const latVal = (ev as any).centroid?.lat ?? (ev as any).lat ?? ev.observations?.[0]?.latitude ?? 22.47;
                  const lonVal = (ev as any).centroid?.lon ?? (ev as any).lon ?? ev.observations?.[0]?.longitude ?? 70.07;

                  return (
                    <tr
                      key={ev.event_id}
                      style={{
                        borderBottom: '1px solid #1E293B',
                        transition: 'background 0.15s ease',
                      }}
                      onMouseEnter={e => (e.currentTarget.style.background = 'rgba(30, 41, 59, 0.4)')}
                      onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                    >
                      <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#38BDF8' }}>
                        {ev.event_id}
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        <div style={{ fontWeight: 600, color: '#F8FAFC' }}>{facilityName}</div>
                        <div style={{ fontSize: '10px', color: '#64748B' }}>
                          Lat {latVal.toFixed(3)}, Lon {lonVal.toFixed(3)}
                        </div>
                      </td>
                      <td style={{ padding: '14px 16px', color: '#CBD5E1' }}>
                        <div style={{ textTransform: 'capitalize' }}>{label.replace(/_/g, ' ')}</div>
                        <div style={{ fontSize: '10px', color: '#94A3B8' }}>
                          Conf: {Math.round(ev.classification?.confidence || 90)}%
                        </div>
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        <span style={{
                          display: 'inline-block',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          fontSize: '10px',
                          fontWeight: 700,
                          background: riskScore >= 75 ? 'rgba(255, 92, 108, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                          color: riskScore >= 75 ? '#FF5C6C' : '#F59E0B',
                          border: `1px solid ${riskScore >= 75 ? 'rgba(255, 92, 108, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`
                        }}>
                          Risk {riskScore}/100
                        </span>
                        <div style={{ fontSize: '10px', color: '#94A3B8', marginTop: '2px' }}>
                          FRP: {frp.toFixed(1)} MW
                        </div>
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        <span style={{
                          fontSize: '10px',
                          fontFamily: 'var(--font-mono)',
                          textTransform: 'uppercase',
                          color: statusLabel.includes('CONFIRM') ? '#4FD18B' : '#94A3B8'
                        }}>
                          {statusLabel.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                          {/* View Modal */}
                          <button
                            type="button"
                            onClick={() => setSelectedEventForModal(ev)}
                            style={{
                              padding: '5px 10px',
                              background: '#1E293B',
                              border: '1px solid #334155',
                              borderRadius: '4px',
                              color: '#38BDF8',
                              fontSize: '11px',
                              fontWeight: 600,
                              cursor: 'pointer',
                            }}
                          >
                            👁️ View Dossier
                          </button>

                          {/* Download PDF */}
                          <button
                            type="button"
                            onClick={() => handleDownload(ev.event_id)}
                            disabled={downloadingId === ev.event_id}
                            style={{
                              padding: '5px 10px',
                              background: '#1E293B',
                              border: '1px solid #334155',
                              borderRadius: '4px',
                              color: '#F8FAFC',
                              fontSize: '11px',
                              fontWeight: 600,
                              cursor: 'pointer',
                              opacity: downloadingId === ev.event_id ? 0.6 : 1
                            }}
                          >
                            {downloadingId === ev.event_id ? '⏳ Downloading...' : '📥 PDF'}
                          </button>

                          {/* Send Email */}
                          <button
                            type="button"
                            onClick={() => handleSendEmail(ev.event_id)}
                            disabled={sendingId === ev.event_id}
                            style={{
                              padding: '5px 10px',
                              background: 'rgba(2, 132, 199, 0.2)',
                              border: '1px solid #0284C7',
                              borderRadius: '4px',
                              color: '#38BDF8',
                              fontSize: '11px',
                              fontWeight: 600,
                              cursor: 'pointer',
                              opacity: sendingId === ev.event_id ? 0.6 : 1
                            }}
                          >
                            {sendingId === ev.event_id ? '⏳ Dispatching...' : '✉ Send Report'}
                          </button>

                          {/* Jump to Deep Dive */}
                          <button
                            type="button"
                            onClick={() => onNavigate && onNavigate(`/investigation/${ev.event_id}`, { eventId: ev.event_id })}
                            style={{
                              padding: '5px 8px',
                              background: 'transparent',
                              border: 'none',
                              color: '#64748B',
                              fontSize: '11px',
                              cursor: 'pointer',
                            }}
                            title="Open Investigation Dossier"
                          >
                            Investigate →
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Report Preview Modal */}
      {selectedEventForModal && (
        <ReportPreviewModal
          onClose={() => setSelectedEventForModal(null)}
          eventId={selectedEventForModal.event_id}
          title={selectedEventForModal.facility_context?.name || selectedEventForModal.classification?.label || 'Thermal Anomaly'}
          location={`Lat ${((selectedEventForModal as any).centroid?.lat ?? (selectedEventForModal as any).lat ?? selectedEventForModal.observations?.[0]?.latitude ?? 22.47).toFixed(3)}, Lon ${((selectedEventForModal as any).centroid?.lon ?? (selectedEventForModal as any).lon ?? selectedEventForModal.observations?.[0]?.longitude ?? 70.07).toFixed(3)}`}
          confidence={selectedEventForModal.classification?.confidence || 94}
          industrialLikelihood={selectedEventForModal.scores?.industrial_likelihood ?? 92}
          operationalRisk={selectedEventForModal.operational_risk?.risk_score ?? selectedEventForModal.scores?.operational_risk ?? 85}
          label={selectedEventForModal.classification?.label || selectedEventForModal.classification?.class || 'industrial_thermal_event'}
          evidenceFor={
            Array.isArray(selectedEventForModal.evidence)
              ? selectedEventForModal.evidence.map((e: any) => typeof e === 'string' ? e : e.description || e.name || '')
              : (selectedEventForModal.evidence as any)?.evidence_for || []
          }
        />
      )}
    </div>
  );
};

export default ReportsView;
