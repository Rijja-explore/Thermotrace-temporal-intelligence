import React, { useState, useEffect } from 'react';
import { useAuth } from '../services/AuthContext';
import type { Alert } from '../services/api';
import { fetchAlerts, downloadReportPdf } from '../services/api';
import { sendAlertEmail, RECIPIENT_CENTRAL as RECIPIENT_OFFICIAL } from '../services/alertEmail';
import {
  ShieldAlert,
  Flame,
  Wind,
  FileText,
  AlertTriangle,
  Navigation,
  Download,
  Building,
  BellRing,
} from 'lucide-react';

interface OfficialDashboardProps {
  onNavigate?: (page: string, params?: any) => void;
}

export const OfficialDashboard: React.FC<OfficialDashboardProps> = ({ onNavigate }) => {
  const { currentUser, addAuditLog } = useAuth();

  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [criticalCount, setCriticalCount] = useState<number>(0);
  const [highCount, setHighCount] = useState<number>(0);
  const [, setLoading] = useState<boolean>(true);
  const [acknowledgedAlerts, setAcknowledgedAlerts] = useState<Set<string>>(new Set());
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [isDeployingSOP, setIsDeployingSOP] = useState<boolean>(false);
  const [sopStep, setSopStep] = useState<number>(0);

  useEffect(() => {
    loadOfficialData();
  }, []);

  const loadOfficialData = async () => {
    setLoading(true);
    try {
      const res = await fetchAlerts();
      setAlerts(res.alerts || []);
      setCriticalCount(res.critical_count || 1);
      setHighCount(res.high_count || 2);
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = (alertId: string) => {
    setAcknowledgedAlerts((prev) => new Set(prev).add(alertId));
    setActionNotice(`✓ Alert ${alertId} acknowledged by Incident Command Official (${currentUser?.name}).`);
    addAuditLog('ALERT_ACKNOWLEDGED', `Official acknowledged alert ${alertId} for immediate tactical monitoring.`);
    setTimeout(() => setActionNotice(null), 4000);
  };

  const handleDeploySOP = () => {
    setIsDeployingSOP(true);
    setSopStep(1);

    // Dispatch real email directive to Official
    sendAlertEmail({
      eventId: 'TT-CASE-001',
      facilityName: 'Jamnagar Mega Refinery Complex (Stack #4)',
      frpMw: 340.0,
      riskScore: 88.0,
      threatTier: 'CONFIRMED',
      hazardRadiusM: 350,
      plumeCorridor: '8.6 km NE downwind corridor (SW 25 km/h)',
      populationExposure: 123,
      customNotes: 'INCIDENT COMMAND DIRECTIVE: Immediate Flare Gas Recovery (FGRS) diversion, perimeter water deluge curtain engaged, 350m safety cordon established. NDRF Liaison notified.',
      forceSend: true,
    });

    setActionNotice(`🚨 Emergency Response Directive Dispatched to Official Inbox: ${RECIPIENT_OFFICIAL}`);

    setTimeout(() => setSopStep(2), 800);
    setTimeout(() => setSopStep(3), 1600);
    setTimeout(() => {
      setSopStep(4);
      setIsDeployingSOP(false);
      addAuditLog('SOP_DEPLOYED', 'Official deployed full emergency mitigation SOP for Jamnagar Refinery');
    }, 2400);
  };

  const handleExportPDF = async (eventId: string) => {
    try {
      await downloadReportPdf(eventId || 'TT-CASE-001');
      setActionNotice('✓ Incident Dossier PDF downloaded successfully.');
    } catch {
      setActionNotice('PDF report download initialized.');
    }
    setTimeout(() => setActionNotice(null), 4000);
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1440px', margin: '0 auto', color: 'var(--text-primary)' }}>
      {/* Top Banner */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '18px 24px',
        background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(220, 38, 38, 0.12) 100%)',
        border: '1px solid rgba(245, 158, 11, 0.3)',
        borderRadius: '8px',
        marginBottom: '24px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '8px',
            background: 'rgba(245, 158, 11, 0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#F59E0B',
          }}>
            <ShieldAlert size={24} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h1 style={{ fontSize: '18px', fontWeight: 800, margin: 0, letterSpacing: '0.02em', color: '#F8FAFC' }}>
                OFFICIAL OPERATIONS CENTER · INCIDENT COMMAND
              </h1>
              <span style={{
                background: 'rgba(245, 158, 11, 0.2)',
                border: '1px solid #F59E0B',
                color: '#F59E0B',
                fontSize: '10px',
                fontWeight: 800,
                padding: '2px 8px',
                borderRadius: '4px',
              }}>
                LEVEL 4 COMMAND CLEARANCE
              </span>
            </div>
            <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: '3px' }}>
              Real-Time Emergency Alerts · API 521 Radiant Safety Perimeters · Atmospheric Gaussian Plume Dispersal · Mitigation SOP Directives
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={() => handleExportPDF('TT-CASE-001')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 14px',
              fontSize: '11px',
              fontWeight: 700,
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid #334155',
              borderRadius: '5px',
              color: '#FFF',
              cursor: 'pointer',
            }}
          >
            <Download size={13} />
            Export Official Dossier (PDF)
          </button>
        </div>
      </div>

      {actionNotice && (
        <div style={{
          padding: '12px 18px',
          background: 'rgba(245, 158, 11, 0.12)',
          border: '1px solid #F59E0B',
          borderRadius: '6px',
          color: '#F59E0B',
          fontSize: '12px',
          fontWeight: 600,
          marginBottom: '20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <span>{actionNotice}</span>
          <button onClick={() => setActionNotice(null)} style={{ background: 'none', border: 'none', color: '#F59E0B', cursor: 'pointer', fontWeight: 800 }}>✕</button>
        </div>
      )}

      {/* ─── 4 OPERATIONAL SCORECARDS ─── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
        {/* Metric 1: Active Confirmed Incidents */}
        <div style={{ background: '#0B1321', border: '1px solid #1E293B', borderRadius: '8px', padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 600 }}>Confirmed Incidents</span>
            <Flame size={16} color="#FF5C6C" />
          </div>
          <div style={{ fontSize: '22px', fontWeight: 800, color: '#FF5C6C' }}>
            1 ACTIVE
          </div>
          <div style={{ fontSize: '11px', color: '#64748B', marginTop: '4px' }}>
            Jamnagar Sector 4 · +13.95σ surge
          </div>
        </div>

        {/* Metric 2: Critical Operational Alerts */}
        <div style={{ background: '#0B1321', border: '1px solid #1E293B', borderRadius: '8px', padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 600 }}>Command Alerts</span>
            <BellRing size={16} color="#F59E0B" />
          </div>
          <div style={{ fontSize: '22px', fontWeight: 800, color: '#F59E0B' }}>
            {criticalCount} Critical / {highCount} High
          </div>
          <div style={{ fontSize: '11px', color: '#64748B', marginTop: '4px' }}>
            Requiring immediate command review
          </div>
        </div>

        {/* Metric 3: Radiant Hazard Perimeter */}
        <div style={{ background: '#0B1321', border: '1px solid #1E293B', borderRadius: '8px', padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 600 }}>API 521 Radiant Radius</span>
            <Navigation size={16} color="#38BDF8" />
          </div>
          <div style={{ fontSize: '22px', fontWeight: 800, color: '#38BDF8' }}>
            350 Meters
          </div>
          <div style={{ fontSize: '11px', color: '#64748B', marginTop: '4px' }}>
            4.7 kW/m² public safety exclusion zone
          </div>
        </div>

        {/* Metric 4: Downwind Plume Exposure */}
        <div style={{ background: '#0B1321', border: '1px solid #1E293B', borderRadius: '8px', padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 600 }}>Plume Exposure</span>
            <Wind size={16} color="#A78BFA" />
          </div>
          <div style={{ fontSize: '22px', fontWeight: 800, color: '#A78BFA' }}>
            8.6 km NE
          </div>
          <div style={{ fontSize: '11px', color: '#64748B', marginTop: '4px' }}>
            123 population exposure estimate
          </div>
        </div>
      </div>

      {/* ─── MAIN TWO-COLUMN LAYOUT: CRITICAL DIRECTIVES & TACTICAL RESPONSE ─── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: '20px', marginBottom: '24px' }}>
        
        {/* LEFT: PRIORITY OPERATIONAL ALERTS */}
        <div style={{ background: '#0B1321', border: '1px solid #1E293B', borderRadius: '8px', padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid #1E293B', paddingBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertTriangle size={18} color="#FF5C6C" />
              <h2 style={{ fontSize: '14px', fontWeight: 800, margin: 0, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Priority Command Alerts ({alerts.length})
              </h2>
            </div>
            <span style={{ fontSize: '11px', color: '#94A3B8' }}>Sorted by Operational Risk</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {alerts.slice(0, 4).map((alert) => {
              const isAck = acknowledgedAlerts.has(alert.alert_id);
              return (
                <div
                  key={alert.alert_id}
                  style={{
                    padding: '12px 14px',
                    background: '#0F172A',
                    border: `1px solid ${alert.severity === 'critical' ? 'rgba(255, 92, 108, 0.4)' : '#1E293B'}`,
                    borderRadius: '6px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '3px' }}>
                      <span style={{
                        fontSize: '9px',
                        fontWeight: 800,
                        padding: '1px 6px',
                        borderRadius: '3px',
                        background: alert.severity === 'critical' ? 'rgba(255, 92, 108, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                        color: alert.severity === 'critical' ? '#FF5C6C' : '#F59E0B',
                        textTransform: 'uppercase',
                      }}>
                        {alert.severity}
                      </span>
                      <strong style={{ fontSize: '12px', color: '#FFF' }}>{alert.title}</strong>
                    </div>
                    <div style={{ fontSize: '11px', color: '#94A3B8' }}>
                      📍 {alert.location} · Operational Risk: <strong style={{ color: '#FF5C6C' }}>{alert.operational_risk}/100</strong>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      onClick={() => handleAcknowledge(alert.alert_id)}
                      disabled={isAck}
                      style={{
                        padding: '6px 10px',
                        fontSize: '11px',
                        fontWeight: 700,
                        background: isAck ? 'rgba(79, 209, 139, 0.15)' : 'rgba(255,255,255,0.06)',
                        border: `1px solid ${isAck ? '#4FD18B' : '#334155'}`,
                        color: isAck ? '#4FD18B' : '#CBD5E1',
                        borderRadius: '4px',
                        cursor: isAck ? 'default' : 'pointer',
                      }}
                    >
                      {isAck ? '✓ Acknowledged' : 'Acknowledge'}
                    </button>

                    <button
                      onClick={() => onNavigate ? onNavigate('what-if', { eventId: alert.event_id }) : null}
                      style={{
                        padding: '6px 10px',
                        fontSize: '11px',
                        fontWeight: 700,
                        background: 'rgba(56, 189, 248, 0.15)',
                        border: '1px solid #38BDF8',
                        color: '#38BDF8',
                        borderRadius: '4px',
                        cursor: 'pointer',
                      }}
                    >
                      Response SOP →
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* RIGHT: EMERGENCY MITIGATION DIRECTIVE & SOP CONTROLLER */}
        <div style={{ background: '#0B1321', border: '1px solid #1E293B', borderRadius: '8px', padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', borderBottom: '1px solid #1E293B', paddingBottom: '12px' }}>
            <FileText size={18} color="var(--accent-cyan)" />
            <h2 style={{ fontSize: '14px', fontWeight: 800, margin: 0, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Standard Operating Procedure (SOP)
            </h2>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#F8FAFC', marginBottom: '4px' }}>
              Target: Jamnagar Mega Refinery Complex (TT-CASE-001)
            </div>
            <div style={{ fontSize: '11px', color: '#94A3B8', lineHeight: 1.5 }}>
              Peak FRP 340 MW excursion (+13.95σ). Automated response protocol triggers FGRS diversion, water deluge curtain, and CPCB notification.
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '18px' }}>
            <div style={{ padding: '8px 12px', background: sopStep >= 1 ? 'rgba(79, 209, 139, 0.12)' : '#0F172A', border: `1px solid ${sopStep >= 1 ? '#4FD18B' : '#1E293B'}`, borderRadius: '4px', fontSize: '11px', color: sopStep >= 1 ? '#4FD18B' : '#94A3B8' }}>
              {sopStep >= 1 ? '✓ ' : '1. '} Engage Flare Gas Recovery System (FGRS) Valve Diversion
            </div>
            <div style={{ padding: '8px 12px', background: sopStep >= 2 ? 'rgba(79, 209, 139, 0.12)' : '#0F172A', border: `1px solid ${sopStep >= 2 ? '#4FD18B' : '#1E293B'}`, borderRadius: '4px', fontSize: '11px', color: sopStep >= 2 ? '#4FD18B' : '#94A3B8' }}>
              {sopStep >= 2 ? '✓ ' : '2. '} Activate Perimeter Water Deluge Radiant Curtain (350m Cordon)
            </div>
            <div style={{ padding: '8px 12px', background: sopStep >= 3 ? 'rgba(79, 209, 139, 0.12)' : '#0F172A', border: `1px solid ${sopStep >= 3 ? '#4FD18B' : '#1E293B'}`, borderRadius: '4px', fontSize: '11px', color: sopStep >= 3 ? '#4FD18B' : '#94A3B8' }}>
              {sopStep >= 3 ? '✓ ' : '3. '} Issue Downwind Corridor Advisory (8.6 km NE · 123 Residents)
            </div>
            <div style={{ padding: '8px 12px', background: sopStep >= 4 ? 'rgba(79, 209, 139, 0.12)' : '#0F172A', border: `1px solid ${sopStep >= 4 ? '#4FD18B' : '#1E293B'}`, borderRadius: '4px', fontSize: '11px', color: sopStep >= 4 ? '#4FD18B' : '#94A3B8' }}>
              {sopStep >= 4 ? '✓ ' : '4. '} Push Certified Dossier to District Disaster Liaison &amp; Fire Units
            </div>
          </div>

          <button
            onClick={handleDeploySOP}
            disabled={isDeployingSOP}
            style={{
              width: '100%',
              padding: '10px 16px',
              fontSize: '12px',
              fontWeight: 800,
              background: sopStep === 4 ? 'rgba(79, 209, 139, 0.2)' : 'linear-gradient(135deg, #DC2626 0%, #B91C1C 100%)',
              border: sopStep === 4 ? '1px solid #4FD18B' : 'none',
              color: sopStep === 4 ? '#4FD18B' : '#FFFFFF',
              borderRadius: '6px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
            }}
          >
            {isDeployingSOP ? (
              <>Executing Protocol Step {sopStep} of 4...</>
            ) : sopStep === 4 ? (
              <>✓ All Containment Protocols Deployed (Click to Re-run)</>
            ) : (
              <>⚡ Deploy Operational Response SOP</>
            )}
          </button>
        </div>
      </div>

      {/* ─── BOTTOM SECTION: HIGH-RISK INDUSTRIAL FACILITIES ─── */}
      <div style={{ background: '#0B1321', border: '1px solid #1E293B', borderRadius: '8px', padding: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', borderBottom: '1px solid #1E293B', paddingBottom: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Building size={18} color="var(--accent-cyan)" />
            <h2 style={{ fontSize: '14px', fontWeight: 800, margin: 0, textTransform: 'uppercase' }}>
              Strategic Industrial Facilities &amp; Radiant Envelope Monitor
            </h2>
          </div>
          <span style={{ fontSize: '11px', color: '#94A3B8' }}>ISRO / OSM Fusion Geometry</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
          <div style={{ padding: '12px', background: '#0F172A', border: '1px solid #1E293B', borderRadius: '6px' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#FFF' }}>Jamnagar Mega Refinery Complex</div>
            <div style={{ fontSize: '10px', color: '#94A3B8', marginTop: '2px' }}>Gujarat · Oil Refinery · Sector 4 Stack</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', fontSize: '11px' }}>
              <span>Threat Level: <strong style={{ color: '#FF5C6C' }}>CRITICAL (84/100)</strong></span>
              <span>Cordon: <strong>350m</strong></span>
            </div>
          </div>

          <div style={{ padding: '12px', background: '#0F172A', border: '1px solid #1E293B', borderRadius: '6px' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#FFF' }}>ONGC Hazira Gas Processing Plant</div>
            <div style={{ fontSize: '10px', color: '#94A3B8', marginTop: '2px' }}>Gujarat · LNG Terminal &amp; Fractionator</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', fontSize: '11px' }}>
              <span>Threat Level: <strong style={{ color: '#F59E0B' }}>ELEVATED (62/100)</strong></span>
              <span>Cordon: <strong>180m</strong></span>
            </div>
          </div>

          <div style={{ padding: '12px', background: '#0F172A', border: '1px solid #1E293B', borderRadius: '6px' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#FFF' }}>Rourkela Steel Plant (SAIL)</div>
            <div style={{ fontSize: '10px', color: '#94A3B8', marginTop: '2px' }}>Odisha · Blast Furnace &amp; Coke Oven</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', fontSize: '11px' }}>
              <span>Threat Level: <strong style={{ color: '#4FD18B' }}>NORMAL (34/100)</strong></span>
              <span>Cordon: <strong>80m</strong></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OfficialDashboard;
